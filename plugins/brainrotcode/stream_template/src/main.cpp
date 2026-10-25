#include "brainrot_stream.hpp"
#include "brainrot_gl.hpp"
#include "brainrot_live_api.h"
#include <chrono>
#include <cstring>
#include <dlfcn.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <atomic>
#include <cerrno>
#include <sys/wait.h>
#include <unistd.h>
#include <string>
#include <vector>
#ifndef BR_ASSET_DIR
#define BR_ASSET_DIR "."
#endif
namespace fs=std::filesystem;
using br::stream::Vec;
using br::stream::Key;
using br::stream::World;
namespace gl=br::gl;

static std::string read_file(fs::path path) {
    std::ifstream in(path);if(!in)throw std::runtime_error("Cannot open: "+path.string());
    std::ostringstream os;os<<in.rdbuf();return os.str();
}
static std::string trim(std::string s) {
    auto first=s.find_first_not_of(" \t\r\n"),last=s.find_last_not_of(" \t\r\n");
    return first==std::string::npos?std::string():s.substr(first,last-first+1);
}
struct Controls {
    int forward=GLFW_KEY_W,back=GLFW_KEY_S,left=GLFW_KEY_A,right=GLFW_KEY_D;
    int jump=GLFW_KEY_SPACE,crouch=GLFW_KEY_LEFT_SHIFT,sprint=GLFW_KEY_LEFT_CONTROL,fly=GLFW_KEY_F;
    int break_button=GLFW_MOUSE_BUTTON_LEFT,place_button=GLFW_MOUSE_BUTTON_RIGHT;
    bool invert_mouse_y=false;
    float sensitivity=.0024f,move_speed=7.2f,fly_speed=12.f,reach=7.f;
    int view=3;
    fs::file_time_type stamp{};
    int key_of(std::string s) const {
        if(s.size()==1&&s[0]>='A'&&s[0]<='Z')return GLFW_KEY_A+s[0]-'A';
        if(s.size()==1&&s[0]>='0'&&s[0]<='9')return GLFW_KEY_0+s[0]-'0';
        if(s=="SPACE")return GLFW_KEY_SPACE;
        if(s=="LEFT_SHIFT")return GLFW_KEY_LEFT_SHIFT;
        if(s=="LEFT_CONTROL")return GLFW_KEY_LEFT_CONTROL;
        if(s=="RIGHT_SHIFT")return GLFW_KEY_RIGHT_SHIFT;
        if(s=="RIGHT_CONTROL")return GLFW_KEY_RIGHT_CONTROL;
        if(s=="UP")return GLFW_KEY_UP;if(s=="DOWN")return GLFW_KEY_DOWN;
        if(s=="LEFT_ARROW")return GLFW_KEY_LEFT;if(s=="RIGHT_ARROW")return GLFW_KEY_RIGHT;
        throw std::invalid_argument("Invalid key: "+s);
    }
    void reload(fs::path file,bool force=false) {
        std::error_code err;auto modified=fs::last_write_time(file,err);
        if(err||(!force&&stamp==modified))return;
        Controls next=*this;
        std::ifstream in(file);std::string line;
        while(std::getline(in,line)) {
            auto comment=line.find('#');if(comment!=std::string::npos)line.resize(comment);
            auto eq=line.find('=');if(eq==std::string::npos)continue;
            auto name=trim(line.substr(0,eq)),value=trim(line.substr(eq+1));
            try {
                if(name=="forward")next.forward=key_of(value);
                else if(name=="back")next.back=key_of(value);
                else if(name=="left")next.left=key_of(value);
                else if(name=="right")next.right=key_of(value);
                else if(name=="jump")next.jump=key_of(value);
                else if(name=="crouch")next.crouch=key_of(value);
                else if(name=="sprint")next.sprint=key_of(value);
                else if(name=="fly")next.fly=key_of(value);
                else if(name=="break_mouse"||name=="place_mouse") {
                    int key=value=="LEFT"?GLFW_MOUSE_BUTTON_LEFT:value=="RIGHT"?GLFW_MOUSE_BUTTON_RIGHT:value=="MIDDLE"?GLFW_MOUSE_BUTTON_MIDDLE:-1;
                    if(key<0)throw std::invalid_argument("Expected LEFT / RIGHT / MIDDLE");
                    if(name=="break_mouse")next.break_button=key;else next.place_button=key;
                }
                else if(name=="invert_mouse_y")next.invert_mouse_y=(value=="true"||value=="1");
                else if(name=="mouse_sensitivity")next.sensitivity=std::clamp(std::stof(value),.0001f,.02f);
                else if(name=="move_speed")next.move_speed=std::clamp(std::stof(value),1.f,40.f);
                else if(name=="fly_speed")next.fly_speed=std::clamp(std::stof(value),1.f,60.f);
                else if(name=="reach")next.reach=std::clamp(std::stof(value),1.f,15.f);
                else if(name=="view_chunks")next.view=std::clamp(std::stoi(value),1,12);
            }catch(const std::exception& e){std::cerr<<"controls.cfg "<<name<<": "<<e.what()<<"\n";}
        }
        *this=next;stamp=modified;std::cerr<<"[LIVE] Controls updated\n";
    }
};

struct Mat4 {float a[16]{};};
static Mat4 multiply(const Mat4& l,const Mat4& r) {
    Mat4 o;for(int c=0;c<4;++c)for(int row=0;row<4;++row)for(int k=0;k<4;++k)o.a[c*4+row]+=l.a[k*4+row]*r.a[c*4+k];return o;
}
static Mat4 view_matrix(Vec eye,float yaw,float pitch) {
    Vec f=br::stream::look(yaw,pitch),r=br::stream::right(yaw);
    Vec u={-std::sin(yaw)*std::sin(pitch),std::cos(pitch),std::cos(yaw)*std::sin(pitch)};
    Mat4 m;m.a[0]=r.x;m.a[4]=r.y;m.a[8]=r.z;m.a[12]=-br::stream::dot(r,eye);
    m.a[1]=u.x;m.a[5]=u.y;m.a[9]=u.z;m.a[13]=-br::stream::dot(u,eye);
    m.a[2]=-f.x;m.a[6]=-f.y;m.a[10]=-f.z;m.a[14]=br::stream::dot(f,eye);
    m.a[15]=1.f;return m;
}
static Mat4 perspective(float aspect) {
    Mat4 m;float f=1.f/std::tan(74.f*3.14159265f/360.f),n=.1f,far=500.f;
    m.a[0]=f/aspect;m.a[5]=f;m.a[10]=(far+n)/(n-far);m.a[11]=-1.f;m.a[14]=2*far*n/(n-far);return m;
}
class Graphics {
    struct Gpu {gl::GLuint vao=0,vbo=0;gl::GLsizei count=0;};
    std::map<Key,Gpu> chunks;
    Gpu outline;
    gl::GLuint program=0;
    fs::path folder;
    fs::file_time_type vert_stamp{},frag_stamp{};
    static void dispose(Gpu& c){if(c.vbo)gl::DeleteBuffers(1,&c.vbo);if(c.vao)gl::DeleteVertexArrays(1,&c.vao);c={};}
    static void update_buffer(Gpu& target,const std::vector<br::stream::Vertex>& data){
        if(!target.vao){gl::GenVertexArrays(1,&target.vao);gl::GenBuffers(1,&target.vbo);}
        gl::BindVertexArray(target.vao);gl::BindBuffer(gl::ARRAY_BUFFER,target.vbo);
        gl::BufferData(gl::ARRAY_BUFFER,gl::GLsizeiptr(data.size()*sizeof(data[0])),data.empty()?nullptr:data.data(),gl::STATIC_DRAW);
        constexpr int stride=sizeof(br::stream::Vertex);
        const int offsets[]={0,3*int(sizeof(float)),5*int(sizeof(float)),6*int(sizeof(float))};
        for(int i=0;i<4;++i){gl::EnableVertexAttribArray(i);gl::VertexAttribPointer(i,i==0?3:i==1?2:1,gl::FLOAT,0,stride,reinterpret_cast<void*>(std::intptr_t(offsets[i])));}
        target.count=gl::GLsizei(data.size());gl::BindVertexArray(0);
    }
public:
    explicit Graphics(fs::path dir):folder(std::move(dir)){reload_shaders(true);if(!program)throw std::runtime_error("Missing or invalid OpenGL shaders");gl::Enable(gl::DEPTH_TEST);gl::Enable(gl::CULL_FACE);}
    ~Graphics(){for(auto& c:chunks)dispose(c.second);dispose(outline);if(program)gl::DeleteProgram(program);}
    void reload_shaders(bool force=false) {
        std::error_code ec;
        const auto vp=folder/"world.vert",fp=folder/"world.frag";
        auto vt=fs::last_write_time(vp,ec);if(ec)return;
        auto ft=fs::last_write_time(fp,ec);if(ec)return;
        if(!force&&vt==vert_stamp&&ft==frag_stamp)return;
        try {auto replacement=gl::link(read_file(vp),read_file(fp));
            if(program)gl::DeleteProgram(program);program=replacement;vert_stamp=vt;frag_stamp=ft;
            std::cerr<<"[LIVE] GLSL shaders updated\n";
        }catch(const std::exception& error){std::cerr<<"GLSL reload failed (keeping old): "<<error.what()<<"\n";vert_stamp=vt;frag_stamp=ft;}
    }
    void sync(br::stream::MeshEvent event) {
        if(event.removed){auto it=chunks.find(event.key);if(it!=chunks.end()){dispose(it->second);chunks.erase(it);}return;}
        if(event.vertices.empty()){auto it=chunks.find(event.key);if(it!=chunks.end()){dispose(it->second);chunks.erase(it);}return;}
        update_buffer(chunks[event.key],event.vertices);
    }
    void render(Mat4 mvp,Vec eye,float sky_luminance,float fog_distance,br::stream::Hit highlight,bool debug) {
        (void)sky_luminance;
        gl::UseProgram(program);
        auto loc=[&](const char* s){return gl::GetUniformLocation(program,s);};
        gl::UniformMatrix4fv(loc("u_mvp"),1,0,mvp.a);
        gl::Uniform3f(loc("u_eye"),eye.x,eye.y,eye.z);
        gl::Uniform3f(loc("u_sky"),.55f,.74f,.94f);
        gl::Uniform1f(loc("u_fog_distance"),fog_distance);
        for(auto& pair:chunks)if(pair.second.count){gl::BindVertexArray(pair.second.vao);gl::DrawArrays(gl::TRIANGLES,0,pair.second.count);}
        if(debug&&highlight.found){
            const float x=highlight.x-.003f,y=highlight.y-.003f,z=highlight.z-.003f,s=1.006f;
            const Vec p[8]={{x,y,z},{x+s,y,z},{x+s,y+s,z},{x,y+s,z},{x,y,z+s},{x+s,y,z+s},{x+s,y+s,z+s},{x,y+s,z+s}};
            const int edges[24]={0,1,1,2,2,3,3,0,4,5,5,6,6,7,7,4,0,4,1,5,2,6,3,7};
            std::vector<br::stream::Vertex> lines;lines.reserve(24);
            for(int a:edges)lines.push_back({p[a].x,p[a].y,p[a].z,0,0,5,1});
            update_buffer(outline,lines);gl::Disable(gl::DEPTH_TEST);gl::BindVertexArray(outline.vao);gl::DrawArrays(gl::LINES,0,outline.count);gl::Enable(gl::DEPTH_TEST);
        }
        gl::BindVertexArray(0);
    }
};

// The hot module is an optional C ABI library that is atomically replaced by the script.
class LiveModule {
    fs::path source,temp_folder;
    fs::file_time_type stamp{};
    std::string staged;
    void* handle=nullptr;
    using Fn=void(*)(const BrainrotLiveAPI*,double);
    Fn tick=nullptr;
public:
    LiveModule(fs::path from,fs::path tmp):source(std::move(from)),temp_folder(std::move(tmp)){}
    ~LiveModule(){if(handle)dlclose(handle);if(!staged.empty()){std::error_code ec;fs::remove(staged,ec);}}
    void poll(){
        std::error_code ec;auto now=fs::last_write_time(source,ec);
        if(ec||now==stamp)return;
        fs::create_directories(temp_folder,ec);if(ec)return;
        const std::string dest=(temp_folder/("brainrot_live_"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".so")).string();
        fs::copy_file(source,dest,fs::copy_options::overwrite_existing,ec);
        if(ec){std::cerr<<"Live copy failed: "<<ec.message()<<"\n";return;}
        void* next=dlopen(dest.c_str(),RTLD_NOW|RTLD_LOCAL);
        if(!next){std::cerr<<"Live dlopen: "<<dlerror()<<"\n";fs::remove(dest);stamp=now;return;}
        using Version=uint32_t(*)();
        auto ver=reinterpret_cast<Version>(dlsym(next,"brainrot_live_version"));
        auto update=reinterpret_cast<Fn>(dlsym(next,"brainrot_live_tick"));
        if(!ver||ver()!=BRAINROT_LIVE_ABI||!update){std::cerr<<"Live module ABI mismatch\n";dlclose(next);fs::remove(dest);stamp=now;return;}
        if(handle)dlclose(handle);if(!staged.empty())fs::remove(staged,ec);
        handle=next;tick=update;staged=dest;stamp=now;std::cerr<<"[LIVE] New C++ gameplay module loaded\n";
    }
    static uint8_t get(void* ctx,int x,int y,int z){return static_cast<World*>(ctx)->get(x,y,z);}
    static int set(void* ctx,int x,int y,int z,uint8_t b){return static_cast<World*>(ctx)->set(x,y,z,b)?1:0;}
    void call(World& world,double dt) {if(tick){BrainrotLiveAPI api{BRAINROT_LIVE_ABI,&world,&get,&set};tick(&api,dt);}}
};

// Detect gameplay .cpp changes and compile the shared module OFF the render thread.
// The previous library keeps running if compilation fails.
class LiveCompiler {
    fs::path script,source;
    fs::file_time_type checked{};
    std::atomic<bool> running{false};
    std::thread compilation;
public:
    LiveCompiler(fs::path sh,fs::path cpp):script(std::move(sh)),source(std::move(cpp)){}
    ~LiveCompiler(){if(compilation.joinable())compilation.join();}
    void poll(){
        std::error_code ec;
        auto modified=fs::last_write_time(source,ec);
        if(ec||modified==checked||running.load())return;
        if(compilation.joinable())compilation.join();
        checked=modified;running=true;
        compilation=std::thread([this]{
            pid_t pid=fork();
            if(pid==0){execl("/usr/bin/bash","bash",script.c_str(),(char*)nullptr);_exit(127);}
            if(pid>0){int status=0;while(waitpid(pid,&status,0)<0&&errno==EINTR){}
                if(!WIFEXITED(status)||WEXITSTATUS(status)!=0)
                    std::cerr<<"[LIVE] C++ build failed; previous gameplay stays active\n";
            }else std::cerr<<"[LIVE] Could not fork C++ compiler\n";
            running=false;
        });
    }
};

static bool collide(World& world,float x,float y,float z) {
    constexpr float R=.28f,H=1.74f;
    if(!world.ready(int(std::floor(x)),int(std::floor(z))))return true;
    for(int bx=int(std::floor(x-R));bx<=int(std::floor(x+R));++bx)
    for(int bz=int(std::floor(z-R));bz<=int(std::floor(z+R));++bz)
    for(int by=int(std::floor(y));by<=int(std::floor(y+H-.01f));++by)
        if(br::stream::opaque(world.get(bx,by,bz)))return true;
    return false;
}
static void movement(World& world,float& x,float& y,float& z,float& vy,float dt,float vx,float vz,float vertical,bool fly,bool& grounded) {
    auto move_axis=[&](float& coord,float displacement) {
        const int steps=std::max(1,int(std::ceil(std::abs(displacement)/.12f)));
        const float step=displacement/steps;
        for(int i=0;i<steps;++i){float next=coord+step;
            float cx=&coord==&x?next:x,cy=&coord==&y?next:y,cz=&coord==&z?next:z;
            if(collide(world,cx,cy,cz))return false;coord=next;}
        return true;
    };
    move_axis(x,vx*dt);move_axis(z,vz*dt);
    if(fly){vy=0;move_axis(y,vertical*dt);grounded=false;}
    else {
        if(grounded&&vertical>0){vy=8.5f;grounded=false;}
        vy=std::max(-38.f,vy-24.f*dt);
        if(!move_axis(y,vy*dt)){if(vy<0)grounded=true;vy=0;}else grounded=false;
    }
}
int main() {
    const fs::path assets=BR_ASSET_DIR;
    try {
        br::stream::Settings settings;settings.height=96;settings.view=3;settings.workers=std::clamp(int(std::thread::hardware_concurrency()/2),2,4);
        settings.save_dir=assets/"saves_phase02";
        World world(settings);
        if(!glfwInit())throw std::runtime_error("GLFW failed to initialize: check GPU / Wayland / X11");
        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR,3);glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR,3);
        glfwWindowHint(GLFW_OPENGL_PROFILE,GLFW_OPENGL_CORE_PROFILE);
        GLFWwindow* window=glfwCreateWindow(1280,720,"BrainrotCode 3.1 | Biomas / Streaming Voxel",nullptr,nullptr);
        if(!window){glfwTerminate();throw std::runtime_error("OpenGL 3.3 context failed");}
        glfwMakeContextCurrent(window);glfwSwapInterval(1);gl::load();
        {
            Graphics renderer(assets/"shaders");
            LiveModule live(assets/"live/live_rules.so",assets/"live/.runtime");
            LiveCompiler auto_compile(assets/"tools/rebuild_live.sh",assets/"src/live_rules.cpp");
            Controls controls;controls.reload(assets/"controls.cfg",true);world.view(controls.view);
            glfwSetInputMode(window,GLFW_CURSOR,GLFW_CURSOR_DISABLED);
            float x=0.5f,y=72.f,z=0.5f,yaw=0,pitch=-.15f,vy=0;
            bool fly=true,grounded=false,captured=true,started=false,debug=false;
            bool oldBreak=false,oldPlace=false,oldF=false,oldEsc=false,oldF3=false,oldF6=false,oldF7=false;
            double mx=0,my=0,last=glfwGetTime(),check=last,fps_start=last;
            glfwGetCursorPos(window,&mx,&my);int frames=0;
            std::deque<br::stream::MeshEvent> gpu_events;
            while(!glfwWindowShouldClose(window)) {
                const double now=glfwGetTime();float dt=std::clamp(float(now-last),0.f,.05f);last=now;
                glfwPollEvents();
                if(now-check>.5) {
                    controls.reload(assets/"controls.cfg");world.view(controls.view);
                    renderer.reload_shaders();auto_compile.poll();live.poll();check=now;
                }
                if(glfwGetKey(window,GLFW_KEY_Q)==GLFW_PRESS)glfwSetWindowShouldClose(window,1);
                auto key=[&](int k){return glfwGetKey(window,k)==GLFW_PRESS;};
                auto pressed=[&](int k,bool& previous){bool cur=key(k);bool once=cur&&!previous;previous=cur;return once;};
                if(pressed(GLFW_KEY_F3,oldF3))debug=!debug;
                if(pressed(GLFW_KEY_F6,oldF6)){controls.reload(assets/"controls.cfg",true);world.view(controls.view);}
                if(pressed(GLFW_KEY_F7,oldF7))renderer.reload_shaders(true);
                if(pressed(GLFW_KEY_ESCAPE,oldEsc)){
                    captured=!captured;glfwSetInputMode(window,GLFW_CURSOR,captured?GLFW_CURSOR_DISABLED:GLFW_CURSOR_NORMAL);
                    glfwGetCursorPos(window,&mx,&my);
                }
                if(pressed(controls.fly,oldF))fly=!fly;
                double new_x,new_y;glfwGetCursorPos(window,&new_x,&new_y);
                if(captured){yaw+=float(new_x-mx)*controls.sensitivity;
                    pitch=std::clamp(pitch+(controls.invert_mouse_y?1.f:-1.f)*float(new_y-my)*controls.sensitivity,-1.52f,1.52f);}
                mx=new_x;my=new_y;
                world.tick(int(std::floor(x)),int(std::floor(z)));
                for(auto& event:world.take_events())gpu_events.push_back(std::move(event));
                for(int i=0;i<2&&!gpu_events.empty();++i){renderer.sync(std::move(gpu_events.front()));gpu_events.pop_front();}
                if(!started&&world.ready(0,0)) {
                    for(int top=world.height()-4;top>=4;--top)if(br::stream::opaque(world.get(0,top,0))){y=top+4.f;break;}
                    started=true;
                }
                if(started&&captured) {
                    Vec f=br::stream::look(yaw,0),r=br::stream::right(yaw);
                    float dx=0,dz=0;
                    if(key(controls.forward)){dx+=f.x;dz+=f.z;}
                    if(key(controls.back)){dx-=f.x;dz-=f.z;}
                    if(key(controls.right)){dx+=r.x;dz+=r.z;}
                    if(key(controls.left)){dx-=r.x;dz-=r.z;}
                    float len=std::hypot(dx,dz);if(len>.001f){dx/=len;dz/=len;}
                    const float speed=(fly?controls.fly_speed:controls.move_speed)*(key(controls.sprint)?1.8f:1.f);
                    float up=(key(controls.jump)?1.f:0.f)-(fly&&key(controls.crouch)?1.f:0.f);
                    movement(world,x,y,z,vy,dt,dx*speed,dz*speed,fly?up*speed:up,fly,grounded);
                    if(y<1) {y=70;vy=0;fly=true;}
                }
                Vec eye{x,y+1.62f,z};
                auto hit=world.raycast(eye,br::stream::look(yaw,pitch),controls.reach);
                const bool clickBreak=captured&&glfwGetMouseButton(window,controls.break_button)==GLFW_PRESS;
                const bool clickPlace=captured&&glfwGetMouseButton(window,controls.place_button)==GLFW_PRESS;
                if(started&&hit.found&&clickBreak&&!oldBreak)world.set(hit.x,hit.y,hit.z,br::stream::Air);
                if(started&&hit.found&&clickPlace&&!oldPlace){
                    int tx=hit.x+hit.nx,ty=hit.y+hit.ny,tz=hit.z+hit.nz;
                    if(!((std::abs(float(tx+.5f-x))<.85f)&&std::abs(float(tz+.5f-z))<.85f&&ty<=int(y+1.8f)&&ty>=int(y)-1))
                        world.set(tx,ty,tz,br::stream::Stone);
                }
                oldBreak=clickBreak;oldPlace=clickPlace;
                live.call(world,dt); // optional hot-swappable C gameplay rules
                int width=0,height=0;glfwGetFramebufferSize(window,&width,&height);
                if(width>0&&height>0){
                    gl::Viewport(0,0,width,height);gl::ClearColor(.55f,.74f,.94f,1);
                    gl::Clear(gl::COLOR_BUFFER_BIT|gl::DEPTH_BUFFER_BIT);
                    Mat4 vp=multiply(perspective(float(width)/height),view_matrix(eye,yaw,pitch));
                    renderer.render(vp,eye,1.f,float(world.view()*br::stream::EDGE*1.5f),hit,debug);
                    glfwSwapBuffers(window);
                }
                ++frames;if(now-fps_start>=1.0){
                    auto s=world.stats();std::ostringstream title;
                    title<<"BrainrotCode 3.0 Phase 01 | "<<frames<<" FPS | "<<s.loaded<<" chunks | "<<s.faces<<" quads | "<<s.queued<<" jobs";
                    title<<(fly?" | FLY":" | WALK");
                    if(debug&&hit.found)title<<" | hit("<<hit.x<<","<<hit.y<<","<<hit.z<<") normal("<<hit.nx<<","<<hit.ny<<","<<hit.nz<<")";
                    glfwSetWindowTitle(window,title.str().c_str());frames=0;fps_start=now;
                }
            }
            world.save_all();
        }
        glfwDestroyWindow(window);glfwTerminate();return 0;
    }catch(const std::exception& ex){std::cerr<<"BrainrotCode: "<<ex.what()<<"\n";return 1;}
}
