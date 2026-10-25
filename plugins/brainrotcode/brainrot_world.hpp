#pragma once
// BrainrotCode Voxel World 2.0 (prototype), C++17.
// Headless generation/meshing works without GLFW. run() needs BRAINROT_ENABLE_GLFW,
// GLFW 3 and a compatibility OpenGL context.
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <deque>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace br {
inline std::uint32_t hash3(int x, int y, int z, std::uint32_t seed) {
    return hash(x ^ int(hash(y, z, seed)), z ^ int(seed), seed ^ 0x928fad37u);
}
inline float noise3(float x, float y, float z, unsigned seed=42) {
    const int ix=int(std::floor(x)), iy=int(std::floor(y)), iz=int(std::floor(z));
    const float fx=smooth(x-ix), fy=smooth(y-iy), fz=smooth(z-iz);
    auto r=[seed](int a,int b,int c) { return float(hash3(a,b,c,seed)&0xffffffu)/8388607.5f-1.f; };
    float xy0=mix(mix(r(ix,iy,iz),r(ix+1,iy,iz),fx),mix(r(ix,iy+1,iz),r(ix+1,iy+1,iz),fx),fy);
    float xy1=mix(mix(r(ix,iy,iz+1),r(ix+1,iy,iz+1),fx),mix(r(ix,iy+1,iz+1),r(ix+1,iy+1,iz+1),fx),fy);
    return mix(xy0,xy1,fz);
}
inline float fbm3(float x, float y, float z, unsigned seed, int octaves=4) {
    float amp=1, freq=1, sum=0, total=0;
    for(int o=0;o<std::clamp(octaves,1,8);++o) {
        sum+=noise3(x*freq,y*freq,z*freq,seed+unsigned(o)*137u)*amp;
        total+=amp; amp*=0.5f; freq*=2;
    }
    return sum/total;
}
enum Block : std::uint8_t { Air, Grass, Dirt, Stone, Sand, Snow, Log, Leaves, Water, Lava };
inline bool is_liquid(Block b) {return b==Water || b==Lava;}
inline bool solid(Block b) {return b!=Air && !is_liquid(b);}
struct Quad { std::array<Vec3,4> v; Block type; unsigned char face; float light; };
struct MeshChunk { int cx=0, cz=0; std::vector<Quad> faces; };
class World {
public:
    int width, depth, height, chunk_size=16, view_chunks=5, sea_level=19;
    unsigned seed;
    bool enable_biomes=true, enable_greedy=true, enable_caves=true, enable_trees=true;
    bool generated=false;
    std::vector<std::uint8_t> voxels, liquid_levels;
    std::vector<MeshChunk> meshes;
    struct LiquidNode {int x,y,z; Block kind; std::uint8_t level;};
    std::deque<LiquidNode> flow_queue;
    explicit World(int w=80,int d=80,int h=72,unsigned s=42)
        :width(w),depth(d),height(h),seed(s) {
        if(w<8||d<8||h<8||w>512||d>512||h>192||size_t(w)*d*h>14000000u)
            throw std::invalid_argument("Invalid or oversized voxel world");
        voxels.resize(size_t(w)*d*h,Air); liquid_levels.resize(voxels.size(),0);
    }
    World& terrain3D(unsigned s) {seed=s; generate(); return *this;}
    World& chunks(int edge,int max_height=0) {chunk_size=std::clamp(edge,4,64); (void)max_height; return *this;}
    World& biomes(bool v) {enable_biomes=v; return *this;}
    World& greedyMeshing(bool v) {enable_greedy=v; return *this;}
    World& renderDistance(int chunks) {view_chunks=std::clamp(chunks,1,32); return *this;}
    size_t index(int x,int y,int z) const {return (size_t(z)*width+size_t(x))*height+size_t(y);}
    bool inside(int x,int y,int z) const {return x>=0&&x<width&&y>=0&&y<height&&z>=0&&z<depth;}
    Block get(int x,int y,int z) const {
        if(y<0) return Stone;
        if(!inside(x,y,z)) return Air;
        return Block(voxels[index(x,y,z)]);
    }
    void set(int x,int y,int z,Block block, int level=7) {
        if(!inside(x,y,z)) return;
        auto p=index(x,y,z); voxels[p]=std::uint8_t(block);
        liquid_levels[p]=is_liquid(block)?std::uint8_t(std::clamp(level,1,7)):0;
    }
    int surface(int x,int z) const {
        for(int y=height-1;y>=0;--y) if(solid(get(x,y,z))) return y;
        return 0;
    }
    void generate() {
        std::fill(voxels.begin(),voxels.end(),Air);
        std::fill(liquid_levels.begin(),liquid_levels.end(),0);
        flow_queue.clear();
        for(int z=0;z<depth;++z) for(int x=0;x<width;++x) {
            float plateau=fbm3(x/72.f,0,z/72.f,seed,5);
            float ridges=1.f-std::fabs(fbm3(x/29.f,4,z/29.f,seed+11u,4));
            float mountains=std::clamp((fbm3(x/96.f,3,z/96.f,seed+23u,3)+0.20f)*1.5f,0.f,1.f);
            float biome=fbm3(x/60.f,8,z/60.f,seed+19u,3);
            int top=std::clamp(int(24+plateau*18 + mountains*ridges*22),5,height-5);
            bool arid=enable_biomes && biome < -0.20f;
            for(int y=0;y<=top;++y) {
                bool carve=enable_caves && y>4 && y<top-2 &&
                    fbm3(x/18.f,y/14.f,z/18.f,seed+91u,3)>0.36f;
                if(carve) continue;
                Block b=Stone;
                if(y==top) b=(top>50)?Snow:(arid?Sand:Grass);
                else if(y>top-4) b=arid?Sand:Dirt;
                set(x,y,z,b);
            }
            // Seawater fills accessible low ground columns (not an infinite fluid solver).
            if(top<sea_level) for(int y=top+1;y<=sea_level && y<height;++y)
                set(x,y,z,Water,7);
            // Sparse underground lava pockets at low altitude.
            if(top>12 && (hash(x,z,seed+451u)%900==0)) {
                for(int y=2;y<=3;++y) if(get(x,y,z)==Air) set(x,y,z,Lava,7);
            }
        }
        if(enable_trees) for(int z=3;z<depth-3;++z) for(int x=3;x<width-3;++x) {
            if(hash(x,z,seed+349u)%97 != 0) continue;
            int y=surface(x,z);
            if(get(x,y,z)!=Grass || y+8>=height) continue;
            int trunk=3+int(hash(x,z,seed+48u)%3);
            for(int i=1;i<=trunk;++i) set(x,y+i,z,Log);
            for(int dy=-2;dy<=2;++dy) for(int dz=-2;dz<=2;++dz) for(int dx=-2;dx<=2;++dx) {
                if(dx*dx+dy*dy+dz*dz>7) continue;
                int xx=x+dx, yy=y+trunk+dy, zz=z+dz;
                if(get(xx,yy,zz)==Air) set(xx,yy,zz,Leaves);
            }
        }
        generated=true;
        build_meshes();
    }
    // A reduced level fluid flood: downwards retains level, horizontal loses one.
    // Only newly placed liquids are simulated; ocean generated initially is static.
    void place_liquid(int x,int y,int z,Block kind) {
        if(!is_liquid(kind) || !inside(x,y,z) || solid(get(x,y,z))) return;
        set(x,y,z,kind,7); flow_queue.push_back({x,y,z,kind,7});
    }
    size_t step_fluids(size_t budget=200) {
        size_t changed=0;
        for(size_t n=0;n<budget&&!flow_queue.empty();++n) {
            auto q=flow_queue.front();flow_queue.pop_front();
            const int dirs[5][3]={{0,-1,0},{1,0,0},{-1,0,0},{0,0,1},{0,0,-1}};
            for(int j=0;j<5;++j) {
                int x=q.x+dirs[j][0],y=q.y+dirs[j][1],z=q.z+dirs[j][2];
                if(!inside(x,y,z)) continue;
                if(solid(get(x,y,z))) continue;
                if(get(x,y,z)!=Air && get(x,y,z)!=q.kind) continue;
                // Horizontal lava spreads slowly, one every two source levels.
                int next = j==0 ? 7 : int(q.level)-(q.kind==Lava?2:1);
                if(next<=0) continue;
                size_t at=index(x,y,z);
                if(get(x,y,z)==q.kind && liquid_levels[at]>=next) continue;
                set(x,y,z,q.kind,next);flow_queue.push_back({x,y,z,q.kind,std::uint8_t(next)});++changed;
            }
        }
        return changed;
    }
    // Greedy mesher: merges coplanar neighboring faces with equal material.
    // Each chunk is meshed separately; liquids are rendered in a transparent pass.
    void build_meshes() {
        meshes.clear();
        for(int cz=0;cz<depth;cz+=chunk_size) for(int cx=0;cx<width;cx+=chunk_size) {
            MeshChunk chunk;chunk.cx=cx;chunk.cz=cz;
            const int sizes[3]={std::min(chunk_size,width-cx),height,std::min(chunk_size,depth-cz)};
            const int offsets[3]={cx,0,cz};
            for(int axis=0;axis<3;++axis) {
                int u=(axis+1)%3,v=(axis+2)%3;
                int du=sizes[u],dv=sizes[v];
                std::vector<int> mask(size_t(du)*dv);
                int pos[3]={0,0,0};
                for(int side=-1;side<=1;side+=2) for(int plane=0;plane<sizes[axis];++plane) {
                    std::fill(mask.begin(),mask.end(),0);
                    for(int j=0;j<dv;++j) for(int i=0;i<du;++i) {
                        pos[axis]=plane;pos[u]=i;pos[v]=j;
                        int xyz[3]={pos[0]+offsets[0],pos[1],pos[2]+offsets[2]};
                        Block a=get(xyz[0],xyz[1],xyz[2]);
                        if(!solid(a)) continue;
                        xyz[axis]+=side;
                        Block adjacent=get(xyz[0],xyz[1],xyz[2]);
                        if(solid(adjacent)) continue;
                        mask[size_t(j)*du+i]=int(a);
                    }
                    for(int j=0;j<dv;++j) for(int i=0;i<du;) {
                        int type=mask[size_t(j)*du+i];
                        if(!type) {++i;continue;}
                        int rw=1,rh=1;
                        if(enable_greedy) {
                            while(i+rw<du && mask[size_t(j)*du+i+rw]==type) ++rw;
                            bool can=true;
                            while(j+rh<dv && can) {
                                for(int k=0;k<rw;++k) if(mask[size_t(j+rh)*du+i+k]!=type) {can=false;break;}
                                if(can) ++rh;
                            }
                        }
                        int c[3]={0,0,0};c[axis]=plane+(side>0?1:0);c[u]=i;c[v]=j;
                        auto vertex=[&](int a,int b) -> Vec3 {
                            int p[3]={c[0]+offsets[0],c[1],c[2]+offsets[2]};
                            p[u]+=a*rw;p[v]+=b*rh;
                            return {float(p[0]),float(p[1]),float(p[2])};
                        };
                        Quad face;
                        if(side<0) face.v={vertex(0,0),vertex(0,1),vertex(1,1),vertex(1,0)};
                        else face.v={vertex(0,0),vertex(1,0),vertex(1,1),vertex(0,1)};
                        face.type=Block(type);
                        face.face=std::uint8_t(axis*2+(side>0?1:0));
                        face.light= axis==1?(side>0?1.f:.48f):(axis==0?.75f:.87f);
                        chunk.faces.push_back(face);
                        for(int yy=j;yy<j+rh;++yy) for(int xx=i;xx<i+rw;++xx)
                            mask[size_t(yy)*du+xx]=0;
                        i+=rw;
                    }
                }
            }
            meshes.push_back(std::move(chunk));
        }
    }
    size_t face_count() const {size_t n=0;for(auto& c:meshes)n+=c.faces.size();return n;}
    bool collides(float x,float y,float z,float radius=.28f,float tall=1.75f) const {
        for(int iz=int(std::floor(z-radius));iz<=int(std::floor(z+radius));++iz)
            for(int ix=int(std::floor(x-radius));ix<=int(std::floor(x+radius));++ix)
                for(int iy=int(std::floor(y));iy<=int(std::floor(y+tall-0.001f));++iy)
                    if(solid(get(ix,iy,iz))) return true;
        return false;
    }
#ifdef BRAINROT_ENABLE_GLFW
    void run(const std::string& title="BrainrotCode · Voxel World",int window_width=1280,int window_height=720);
#else
    void run(const std::string& ="BrainrotCode · Voxel World",int=1280,int=720) {
        throw std::runtime_error("Voxel renderer requires BRAINROT_ENABLE_GLFW and GLFW/OpenGL");
    }
#endif
};
} // namespace br

#ifdef BRAINROT_ENABLE_GLFW
namespace br {
inline void World::run(const std::string& title,int ww,int hh) {
    if(!generated) generate();
    if(!glfwInit()) throw std::runtime_error("GLFW initialization failed (check DISPLAY/Wayland)");
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR,2);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR,1);  // intentionally uses portable compatibility renderer
    GLFWwindow* win=glfwCreateWindow(ww,hh,title.c_str(),nullptr,nullptr);
    if(!win) {glfwTerminate();throw std::runtime_error("Cannot create OpenGL context");}
    glfwMakeContextCurrent(win);glfwSwapInterval(1);
    glfwSetInputMode(win,GLFW_CURSOR,GLFW_CURSOR_DISABLED);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_TEXTURE_2D);
    glDisable(GL_CULL_FACE);
    glEnable(GL_FOG);glFogi(GL_FOG_MODE,GL_LINEAR);
    glFogf(GL_FOG_START,75.f);glFogf(GL_FOG_END,140.f);
    // Small deterministic 4x4 texture atlas, generated automatically in RAM.
    constexpr int tile_size=16, atlas_side=4, tex_size=tile_size*atlas_side;
    std::vector<unsigned char> image(size_t(tex_size)*tex_size*3,0);
    const int colors[16][3]={{106,163,65},{95,71,46},{120,119,115},{187,170,110},
        {223,229,239},{98,73,46},{48,117,45},{43,110,164},{224,110,35},{92,155,51},
        {80,125,65},{150,132,94},{140,140,140},{49,99,160},{242,133,65},{96,96,96}};
    for(int tile=0;tile<16;++tile) for(int py=0;py<tile_size;++py) for(int px=0;px<tile_size;++px) {
        int x=(tile%atlas_side)*tile_size+px;
        int y=(tile/atlas_side)*tile_size+py;
        int noise=int(hash(x,y,seed+17u)%31u)-15;
        size_t off=(size_t(y)*tex_size+x)*3;
        for(int k=0;k<3;++k) image[off+k]=static_cast<unsigned char>(std::clamp(colors[tile][k]+noise,0,255));
    }
    GLuint atlas=0;glGenTextures(1,&atlas);glBindTexture(GL_TEXTURE_2D,atlas);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
    glPixelStorei(GL_UNPACK_ALIGNMENT,1);
    glTexImage2D(GL_TEXTURE_2D,0,GL_RGB,tex_size,tex_size,0,GL_RGB,GL_UNSIGNED_BYTE,image.data());
    auto texture_for=[](Block b,int face)->int {
        if(b==Grass) return face==3?0:(face==2?1:9);
        return b==Dirt?1:b==Stone?2:b==Sand?3:b==Snow?4:b==Log?5:b==Leaves?6:b==Water?7:b==Lava?8:2;
    };
    GLuint display_list=glGenLists(1);
    bool dirty=true;
    auto upload=[&]() {
        build_meshes();
        glNewList(display_list,GL_COMPILE);
        glBindTexture(GL_TEXTURE_2D,atlas);
        glBegin(GL_QUADS);
        for(const auto& chunk:meshes) for(const auto& face:chunk.faces) {
            auto uv=block_uv(texture_for(face.type,face.face),atlas_side,atlas_side,0.04f);
            glColor3f(face.light,face.light,face.light);
            for(int i=0;i<4;++i) {
                glTexCoord2f(uv[i].u,uv[i].v);
                glVertex3f(face.v[i].x,face.v[i].y,face.v[i].z);
            }
        }
        glEnd();glEndList();dirty=false;
    };
    float x=width*0.5f,z=depth*0.5f,y=float(surface(width/2,depth/2))+2.8f;
    float yaw=0,pitch=0,velocity_y=0;
    bool fly=false, captured=true,on_ground=false;
    bool prior_f=false,prior_esc=false,prior_l=false,prior_r=false;
    double previous_x=0,previous_y=0,last=glfwGetTime(),fps_t=last;
    int frames=0;
    glfwGetCursorPos(win,&previous_x,&previous_y);
    Block selected=Stone;
    while(!glfwWindowShouldClose(win)) {
        double now=glfwGetTime();float dt=std::clamp(float(now-last),0.f,0.05f);last=now;
        glfwPollEvents();
        if(glfwGetKey(win,GLFW_KEY_Q)==GLFW_PRESS) glfwSetWindowShouldClose(win,1);
        bool esc=glfwGetKey(win,GLFW_KEY_ESCAPE)==GLFW_PRESS;
        if(esc&&!prior_esc) {
            captured=!captured;
            glfwSetInputMode(win,GLFW_CURSOR,captured?GLFW_CURSOR_DISABLED:GLFW_CURSOR_NORMAL);
            glfwGetCursorPos(win,&previous_x,&previous_y);
        }
        prior_esc=esc;
        bool f=glfwGetKey(win,GLFW_KEY_F)==GLFW_PRESS;
        if(f&&!prior_f) fly=!fly;
        prior_f=f;
        if(glfwGetKey(win,GLFW_KEY_1)==GLFW_PRESS) selected=Stone;
        if(glfwGetKey(win,GLFW_KEY_2)==GLFW_PRESS) selected=Water;
        if(glfwGetKey(win,GLFW_KEY_3)==GLFW_PRESS) selected=Lava;
        if(glfwGetKey(win,GLFW_KEY_4)==GLFW_PRESS) selected=Log;
        double mouse_x,mouse_y;glfwGetCursorPos(win,&mouse_x,&mouse_y);
        if(captured) {
            yaw+=float(mouse_x-previous_x)*0.0024f;
            pitch=std::clamp(pitch-float(mouse_y-previous_y)*0.0024f,-1.53f,1.53f);
        }
        previous_x=mouse_x;previous_y=mouse_y;
        float fx=std::sin(yaw),fz=-std::cos(yaw);
        float rx=std::cos(yaw),rz=std::sin(yaw);
        float dx=0,dz=0;
        if(glfwGetKey(win,GLFW_KEY_W)==GLFW_PRESS) {dx+=fx;dz+=fz;}
        if(glfwGetKey(win,GLFW_KEY_S)==GLFW_PRESS) {dx-=fx;dz-=fz;}
        if(glfwGetKey(win,GLFW_KEY_D)==GLFW_PRESS) {dx+=rx;dz+=rz;}
        if(glfwGetKey(win,GLFW_KEY_A)==GLFW_PRESS) {dx-=rx;dz-=rz;}
        float len=std::hypot(dx,dz);if(len>0) {dx/=len;dz/=len;}
        float speed=glfwGetKey(win,GLFW_KEY_LEFT_CONTROL)==GLFW_PRESS?15.f:7.2f;
        auto try_move=[&](float nx,float ny,float nz) {
            if(!collides(nx,ny,nz)) {x=nx;y=ny;z=nz;return true;} return false;
        };
        try_move(x+dx*speed*dt,y,z);try_move(x,y,z+dz*speed*dt);
        if(fly) {
            velocity_y=0;
            float v=(glfwGetKey(win,GLFW_KEY_SPACE)==GLFW_PRESS?1.f:0.f)
                -(glfwGetKey(win,GLFW_KEY_LEFT_SHIFT)==GLFW_PRESS?1.f:0.f);
            try_move(x,y+v*speed*dt,z);
        } else {
            if(on_ground && glfwGetKey(win,GLFW_KEY_SPACE)==GLFW_PRESS) {velocity_y=8.f;on_ground=false;}
            velocity_y=std::max(velocity_y-23.f*dt,-36.f);
            float next_y=y+velocity_y*dt;
            if(!try_move(x,next_y,z)) {on_ground=velocity_y<0;velocity_y=0;} else on_ground=false;
        }
        if(y < -8.f) {x=width/2.f;z=depth/2.f;y=float(surface(width/2,depth/2))+4;velocity_y=0;}
        // Pick a block with a small ray march, edit on mouse down transitions.
        bool left=captured&&glfwGetMouseButton(win,GLFW_MOUSE_BUTTON_LEFT)==GLFW_PRESS;
        bool right=captured&&glfwGetMouseButton(win,GLFW_MOUSE_BUTTON_RIGHT)==GLFW_PRESS;
        if((left&&!prior_l)||(right&&!prior_r)) {
            int hit_x=0,hit_y=0,hit_z=0,prev_x=0,prev_y=0,prev_z=0;bool hit=false;
            float cos_pitch=std::cos(pitch);
            for(float t=0.16f;t<7.5f;t+=0.08f) {
                int bx=int(std::floor(x+std::sin(yaw)*cos_pitch*t));
                int by=int(std::floor(y+1.62f+std::sin(pitch)*t));
                int bz=int(std::floor(z-std::cos(yaw)*cos_pitch*t));
                if(solid(get(bx,by,bz))) {hit=true;hit_x=bx;hit_y=by;hit_z=bz;break;}
                prev_x=bx;prev_y=by;prev_z=bz;
            }
            if(hit) {
                if(left) {set(hit_x,hit_y,hit_z,Air);dirty=true;}
                if(right && !solid(get(prev_x,prev_y,prev_z))) {
                    if(selected==Water||selected==Lava) place_liquid(prev_x,prev_y,prev_z,selected);
                    else set(prev_x,prev_y,prev_z,selected);
                    dirty=true;
                }
            }
        }
        prior_l=left;prior_r=right;
        // Simulation step with a hard budget, avoiding unbounded frame stalls.
        if(flow_queue.size()>80000) flow_queue.clear();
        size_t changed=step_fluids(80);
        if(changed) dirty=true;
        if(dirty) upload();
        int screen_w=0,screen_h=0;glfwGetFramebufferSize(win,&screen_w,&screen_h);
        if(screen_w>0&&screen_h>0) {
            glViewport(0,0,screen_w,screen_h);
            // Simplified day/night cycle, constant directional shading on block faces.
            float daylight=0.73f+0.27f*std::cos(float(now)*0.05f);
            const GLfloat sky[4]={.51f*daylight,.73f*daylight,.94f*daylight,1.f};
            glClearColor(sky[0],sky[1],sky[2],1);
            glFogfv(GL_FOG_COLOR,sky);
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
            glMatrixMode(GL_PROJECTION);glLoadIdentity();
            float top=0.1f*std::tan(75.f*3.14159265f/360.f);
            float side=top*float(screen_w)/float(screen_h);
            glFrustum(-side,side,-top,top,0.1f,220.f);
            glMatrixMode(GL_MODELVIEW);glLoadIdentity();
            glRotatef(-pitch*57.29578f,1,0,0);
            glRotatef(-yaw*57.29578f,0,1,0);
            glTranslatef(-x,-(y+1.62f),-z);
            glEnable(GL_TEXTURE_2D);
            glCallList(display_list);
            // Semi-transparent animated water and glowing lava top surfaces.
            glDisable(GL_TEXTURE_2D);glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
            glDepthMask(GL_FALSE);
            glBegin(GL_QUADS);
            for(int wz=0;wz<depth;++wz) for(int wx=0;wx<width;++wx) for(int wy=1;wy<height;++wy) {
                Block b=get(wx,wy,wz);
                if(!is_liquid(b)) continue;
                if(get(wx,wy+1,wz)==b) continue;
                if(std::fabs(float(wx)-x)>view_chunks*chunk_size || std::fabs(float(wz)-z)>view_chunks*chunk_size) continue;
                float level=liquid_levels[index(wx,wy,wz)]/7.f;
                float surf=wy+0.08f+level*.84f+(b==Water?std::sin(float(now)*1.7f+wx*.6f+wz*.6f)*.035f:0.f);
                if(b==Water) glColor4f(.12f,.38f,.67f,.65f);
                else glColor4f(1.f,.28f,.045f,.86f);
                glVertex3f(wx,surf,wz);glVertex3f(wx,surf,wz+1);
                glVertex3f(wx+1,surf,wz+1);glVertex3f(wx+1,surf,wz);
            }
            glEnd();glDepthMask(GL_TRUE);glDisable(GL_BLEND);
            glfwSwapBuffers(win);
        }
        ++frames;
        if(now-fps_t>=1.0) {
            std::string label=title+" | FPS "+std::to_string(frames)+" | faces "+std::to_string(face_count())+
                (fly?" | FLY":" | SURVIVAL")+" | LMB:break RMB:place 1-4:material F:fly Esc:mouse Q:quit";
            glfwSetWindowTitle(win,label.c_str());frames=0;fps_t=now;
        }
    }
    glDeleteLists(display_list,1);glDeleteTextures(1,&atlas);
    glfwDestroyWindow(win);glfwTerminate();
}
} // namespace br
#endif
