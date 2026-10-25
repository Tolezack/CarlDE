#pragma once
// BrainrotCode 3.0 alpha - Fase 01: streamed voxel world / CPU core (C++17)
// No OpenGL dependency: generation and greedy mesh happen in bounded workers;
// GPU uploads MUST be performed by the render thread consuming mesh_events().
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <deque>
#include <filesystem>
#include <fstream>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <set>
#include <stdexcept>
#include <string>
#include <thread>
#include <unordered_map>
#include <utility>
#include <vector>
#include "brainrot.hpp"

namespace br::stream {
constexpr int EDGE=16;
inline int div_floor(int a,int b) { int q=a/b,r=a%b;return q-((r!=0)&&(r<0)!=(b<0)); }
inline int mod_floor(int a,int b) {return a-div_floor(a,b)*b;}
struct Key {int x=0,z=0;bool operator<(const Key& b) const{return x!=b.x?x<b.x:z<b.z;}bool operator==(const Key& b)const{return x==b.x&&z==b.z;}};
struct Vec {float x=0,y=0,z=0;};
inline Vec look(float yaw,float pitch) {return {std::sin(yaw)*std::cos(pitch),std::sin(pitch),-std::cos(yaw)*std::cos(pitch)};}
inline Vec right(float yaw) {return {std::cos(yaw),0,std::sin(yaw)};}
inline float dot(Vec a,Vec b) {return a.x*b.x+a.y*b.y+a.z*b.z;}
inline Vec plus(Vec a,Vec b) {return {a.x+b.x,a.y+b.y,a.z+b.z};}
inline Vec scale(Vec a,float t) {return {a.x*t,a.y*t,a.z*t};}
inline Vec normalize(Vec a) {float len=std::sqrt(dot(a,a));return len>1.e-6f?scale(a,1.f/len):Vec{};}
enum Block : std::uint8_t {Air=0,Grass=1,Dirt=2,Stone=3,Sand=4,Snow=5,Log=6,Leaves=7,Water=8,Lava=9};
inline bool opaque(std::uint8_t id) {return id!=Air && id!=Water && id!=Lava;}
struct Hit {bool found=false;int x=0,y=0,z=0;int nx=0,ny=0,nz=0;float distance=0;};
struct Vertex {float x,y,z,u,v,material,shade;};
struct MeshEvent {Key key;bool removed=false;std::vector<Vertex> vertices;};
struct Stats {std::size_t loaded=0,queued=0,pending=0,faces=0;};
struct Settings {int height=96,view=3,workers=2;unsigned seed=42;std::filesystem::path save_dir="brainrot_saves";};

class World {
    using Blocks=std::vector<std::uint8_t>;
    struct Chunk {Blocks blocks;std::map<std::uint32_t,std::uint8_t> edits;std::uint64_t version=1;
        bool dirty=true,busy=false,save_dirty=false;std::size_t faces=0;};
    struct Job {enum Kind {Generate,Mesh} kind;Key key;std::uint64_t version=0;
        Blocks center, west,east,north,south;};
    struct Result {Job::Kind kind;Key key;std::uint64_t version;Blocks blocks;
        std::map<std::uint32_t,std::uint8_t> edits;std::vector<Vertex> vertices;};
    Settings config_;
    std::map<Key,Chunk> loaded_;
    std::set<Key> generating_;
    std::deque<Job> jobs_;
    std::deque<Result> results_;
    std::vector<MeshEvent> events_;
    std::mutex mutex_;
    std::condition_variable wake_;
    std::vector<std::thread> threads_;
    bool quit_=false;
    std::size_t inflight_=0;
    std::size_t job_limit_=12;
    static std::size_t slot(int x,int y,int z,int h) {return (std::size_t(z)*EDGE+x)*h+y;}
    std::filesystem::path path(Key k) const {return config_.save_dir / ("c_"+std::to_string(k.x)+"_"+std::to_string(k.z)+".brc");}
    static void wr32(std::ostream& o,std::uint32_t v) {for(int i=0;i<4;++i)o.put(char((v>>(i*8))&255));}
    static bool rd32(std::istream& in,std::uint32_t& v) {v=0;for(int i=0;i<4;++i){int x=in.get();if(x==EOF)return false;v|=std::uint32_t(x)<<(8*i);}return true;}
    void read_edits(Key key,Blocks& blocks,std::map<std::uint32_t,std::uint8_t>& edits) const {
        std::ifstream in(path(key),std::ios::binary);if(!in)return;
        char tag[4];if(!in.read(tag,4)||std::string(tag,4)!="BRC3")return;
        std::uint32_t seed=0,height=0,count=0;
        if(!rd32(in,seed)||!rd32(in,height)||!rd32(in,count) ||seed!=config_.seed||height!=unsigned(config_.height)||count>blocks.size())return;
        for(std::uint32_t i=0;i<count;++i) {std::uint32_t pos=0;if(!rd32(in,pos))break;int id=in.get();
            if(id==EOF)break;if(pos<blocks.size()&&id<=Lava){blocks[pos]=std::uint8_t(id);edits[pos]=std::uint8_t(id);}}
    }
    void save_chunk(Key key,Chunk& c) {
        if(!c.save_dirty)return;
        std::filesystem::create_directories(config_.save_dir);
        const auto dst=path(key), tmp=std::filesystem::path(dst.string()+".tmp");
        {std::ofstream out(tmp,std::ios::binary|std::ios::trunc);
            if(!out)throw std::runtime_error("Cannot save chunk " + dst.string());
            out.write("BRC3",4);wr32(out,config_.seed);wr32(out,std::uint32_t(config_.height));wr32(out,std::uint32_t(c.edits.size()));
            for(auto [at,id]:c.edits){wr32(out,at);out.put(char(id));}
            out.flush();if(!out)throw std::runtime_error("Cannot write chunk " + dst.string());}
        std::filesystem::rename(tmp,dst);c.save_dirty=false;
    }
    static float terrain_height(int x,int z,unsigned seed) {
        const float plains=br::value_noise(x/85.f,z/85.f,seed);
        const float ridges=1.f-std::abs(br::value_noise(x/47.f,z/47.f,seed+11));
        const float mountains=std::max(0.f,br::value_noise(x/135.f,z/135.f,seed+23)+.22f);
        return 26.f+plains*12.f+mountains*ridges*28.f;
    }
    static float cave_noise(int x,int y,int z,unsigned s) {
        // Two independent 3D-like value fields (smooth trilinear interpolation).
        auto n=[&](float xx,float yy,float zz,unsigned salt) {
            int ix=int(std::floor(xx)),iy=int(std::floor(yy)),iz=int(std::floor(zz));
            float fx=br::smooth(xx-ix),fy=br::smooth(yy-iy),fz=br::smooth(zz-iz);
            auto r=[&](int a,int b,int c) {return float(br::hash(a^int(br::hash(b,c,salt)),c,salt)&0xffffu)/32767.5f-1.f;};
            float p00=br::mix(r(ix,iy,iz),r(ix+1,iy,iz),fx),p10=br::mix(r(ix,iy+1,iz),r(ix+1,iy+1,iz),fx);
            float p01=br::mix(r(ix,iy,iz+1),r(ix+1,iy,iz+1),fx),p11=br::mix(r(ix,iy+1,iz+1),r(ix+1,iy+1,iz+1),fx);
            return br::mix(br::mix(p00,p10,fy),br::mix(p01,p11,fy),fz);
        };
        return n(x/19.f,y/15.f,z/19.f,s+91)*.75f+n(x/8.f,y/9.f,z/8.f,s+191)*.25f;
    }
    Blocks generate(Key key) const {
        Blocks blocks(std::size_t(EDGE)*EDGE*config_.height,Air);
        const int H=config_.height;
        for(int z=0;z<EDGE;++z)for(int x=0;x<EDGE;++x) {
            const int wx=key.x*EDGE+x,wz=key.z*EDGE+z;
            int top=std::clamp(int(terrain_height(wx,wz,config_.seed)),3,H-5);
            const bool arid=br::value_noise(wx/102.f,wz/102.f,config_.seed+50)<-.29f;
            for(int y=0;y<=top;++y) {
                if(y>4&&y<top-3&&cave_noise(wx,y,wz,config_.seed)>.48f)continue;
                const std::uint8_t id=y==top?(top>55?Snow:(arid?Sand:Grass)):(y>top-4?(arid?Sand:Dirt):Stone);
                blocks[slot(x,y,z,H)]=id;
            }
            // Cross-chunk deterministic trees: sample neighboring candidate roots.
        }
        for(int lz=-3;lz<EDGE+3;++lz)for(int lx=-3;lx<EDGE+3;++lx) {
            const int wx=key.x*EDGE+lx,wz=key.z*EDGE+lz;
            if(br::hash(wx,wz,config_.seed+77)%139!=0)continue;
            const int top=std::clamp(int(terrain_height(wx,wz,config_.seed)),3,H-5);
            if(top>=50||top+8>=H||br::value_noise(wx/102.f,wz/102.f,config_.seed+50)<-.29f)continue;
            auto place=[&](int X,int Y,int Z,std::uint8_t id,bool empty_only) {
                int xx=X-key.x*EDGE,zz=Z-key.z*EDGE;
                if(xx<0||xx>=EDGE||zz<0||zz>=EDGE||Y<0||Y>=H)return;
                auto i=slot(xx,Y,zz,H);if(!empty_only||blocks[i]==Air)blocks[i]=id;};
            for(int a=1;a<=4;++a)place(wx,top+a,wz,Log,false);
            for(int dy=-2;dy<=2;++dy)for(int dz=-2;dz<=2;++dz)for(int dx=-2;dx<=2;++dx)
                if(dx*dx+dz*dz+dy*dy<=6)place(wx+dx,top+5+dy,wz+dz,Leaves,true);
        }
        return blocks;
    }
    static std::vector<Vertex> make_mesh(const Job& j,int H) {
        const auto& c=j.center;
        auto sample=[&](int x,int y,int z)->std::uint8_t {
            if(y<0)return Stone;if(y>=H)return Air;
            if(x<0)return j.west.empty()?Air:j.west[slot(x+EDGE,y,z,H)];
            if(x>=EDGE)return j.east.empty()?Air:j.east[slot(x-EDGE,y,z,H)];
            if(z<0)return j.north.empty()?Air:j.north[slot(x,y,z+EDGE,H)];
            if(z>=EDGE)return j.south.empty()?Air:j.south[slot(x,y,z-EDGE,H)];
            return c[slot(x,y,z,H)];
        };
        std::vector<Vertex> vertices;
        const int sizes[3]={EDGE,H,EDGE};
        for(int axis=0;axis<3;++axis) {
            const int u=(axis+1)%3,v=(axis+2)%3;
            std::vector<std::uint8_t> mask(std::size_t(sizes[u])*sizes[v]);
            for(int side:{-1,1})for(int plane=0;plane<sizes[axis];++plane) {
                for(int b=0;b<sizes[v];++b)for(int a=0;a<sizes[u];++a) {
                    int p[3]={};p[axis]=plane;p[u]=a;p[v]=b;
                    auto block=sample(p[0],p[1],p[2]);
                    p[axis]+=side;
                    mask[std::size_t(b)*sizes[u]+a]=opaque(block)&&!opaque(sample(p[0],p[1],p[2]))?block:Air;
                }
                for(int b=0;b<sizes[v];++b)for(int a=0;a<sizes[u];) {
                    auto block=mask[std::size_t(b)*sizes[u]+a];if(!block){++a;continue;}
                    int w=1,h=1;while(a+w<sizes[u]&&mask[std::size_t(b)*sizes[u]+a+w]==block)++w;
                    bool extend=true;
                    while(b+h<sizes[v]&&extend) {
                        for(int k=0;k<w;++k)if(mask[std::size_t(b+h)*sizes[u]+a+k]!=block){extend=false;break;}
                        if(extend)++h;
                    }
                    int base[3]={};base[axis]=plane+(side>0?1:0);base[u]=a;base[v]=b;
                    auto emit=[&](int U,int V)->Vertex {
                        int p[3]={base[0],base[1],base[2]};p[u]+=U*w;p[v]+=V*h;
                        return {float(p[0]+j.key.x*EDGE),float(p[1]),float(p[2]+j.key.z*EDGE),
                            float(U*w),float(V*h),float(block),axis==1?(side>0?1.f:.43f):(axis==0?.76f:.87f)};
                    };
                    Vertex quad[4];if(side>0){quad[0]=emit(0,0);quad[1]=emit(1,0);quad[2]=emit(1,1);quad[3]=emit(0,1);}
                    else {quad[0]=emit(0,0);quad[1]=emit(0,1);quad[2]=emit(1,1);quad[3]=emit(1,0);}
                    for(int tri:{0,1,2,0,2,3})vertices.push_back(quad[tri]);
                    for(int yy=b;yy<b+h;++yy)for(int xx=a;xx<a+w;++xx)mask[std::size_t(yy)*sizes[u]+xx]=Air;
                    a+=w;
                }
            }
        }
        return vertices;
    }
    void worker() {
        for(;;) {
            Job job;
            {std::unique_lock<std::mutex> lock(mutex_);
                wake_.wait(lock,[&]{return quit_||!jobs_.empty();});
                if(quit_&&jobs_.empty())return;
                job=std::move(jobs_.front());jobs_.pop_front();}
            Result out;out.kind=job.kind;out.key=job.key;out.version=job.version;
            if(job.kind==Job::Generate){out.blocks=generate(job.key);read_edits(job.key,out.blocks,out.edits);}
            else out.vertices=make_mesh(job,config_.height);
            {std::lock_guard<std::mutex> lock(mutex_);results_.push_back(std::move(out));}
        }
    }
    void post(Job job) {
        {std::lock_guard<std::mutex> lock(mutex_);jobs_.push_back(std::move(job));}wake_.notify_one();
    }
    void mark_dirty(Key k) {auto it=loaded_.find(k);if(it!=loaded_.end()){++it->second.version;it->second.dirty=true;}}
    void mark_neighbors(Key k) {mark_dirty(k);mark_dirty({k.x-1,k.z});mark_dirty({k.x+1,k.z});mark_dirty({k.x,k.z-1});mark_dirty({k.x,k.z+1});}
    void integrate() {
        std::deque<Result> completed;
        {std::lock_guard<std::mutex> lock(mutex_);completed.swap(results_);}
        for(auto& out:completed) {
            if(inflight_)--inflight_;
            if(out.kind==Job::Generate) {
                generating_.erase(out.key);
                if(loaded_.count(out.key))continue;
                Chunk c;c.blocks=std::move(out.blocks);c.edits=std::move(out.edits);
                loaded_.emplace(out.key,std::move(c));mark_neighbors(out.key);
            } else {
                auto it=loaded_.find(out.key);if(it==loaded_.end())continue;
                auto& c=it->second;c.busy=false;
                if(c.version!=out.version)continue;
                c.dirty=false;c.faces=out.vertices.size()/6;
                events_.push_back({out.key,false,std::move(out.vertices)});
            }
        }
    }
public:
    explicit World(Settings config={}):config_(std::move(config)) {
        if(config_.height<16||config_.height>256||config_.view<1||config_.view>12)throw std::invalid_argument("Invalid stream world settings");
        config_.workers=std::clamp(config_.workers,1,8);
        job_limit_=std::size_t(config_.workers*4+4);
        for(int i=0;i<config_.workers;++i)threads_.emplace_back([this]{worker();});
    }
    World(const World&)=delete;World& operator=(const World&)=delete;
    ~World(){
        try{save_all();}catch(...){}
        {std::lock_guard<std::mutex> lock(mutex_);quit_=true;jobs_.clear();}
        wake_.notify_all();for(auto& t:threads_)t.join();
    }
    int height() const {return config_.height;}
    int view() const {return config_.view;}
    void view(int value) {config_.view=std::clamp(value,1,12);}
    std::size_t loaded_count() const{return loaded_.size();}
    bool ready(int x,int z) const {return loaded_.count({div_floor(x,EDGE),div_floor(z,EDGE)})!=0;}
    std::uint8_t get(int x,int y,int z) const {
        if(y<0)return Stone;if(y>=config_.height)return Air;
        const Key k{div_floor(x,EDGE),div_floor(z,EDGE)};
        auto it=loaded_.find(k);if(it==loaded_.end())return Air;
        return it->second.blocks[slot(mod_floor(x,EDGE),y,mod_floor(z,EDGE),config_.height)];
    }
    bool set(int x,int y,int z,std::uint8_t id) {
        if(y<0||y>=config_.height||id>Lava)return false;
        Key k{div_floor(x,EDGE),div_floor(z,EDGE)};auto it=loaded_.find(k);if(it==loaded_.end())return false;
        auto& c=it->second;std::uint32_t at=std::uint32_t(slot(mod_floor(x,EDGE),y,mod_floor(z,EDGE),config_.height));
        if(c.blocks[at]==id)return false;
        c.blocks[at]=id;c.edits[at]=id;c.save_dirty=true;
        mark_dirty(k);
        if(mod_floor(x,EDGE)==0)mark_dirty({k.x-1,k.z});
        if(mod_floor(x,EDGE)==EDGE-1)mark_dirty({k.x+1,k.z});
        if(mod_floor(z,EDGE)==0)mark_dirty({k.x,k.z-1});
        if(mod_floor(z,EDGE)==EDGE-1)mark_dirty({k.x,k.z+1});
        return true;
    }
    void save_all() {for(auto& entry:loaded_)save_chunk(entry.first,entry.second);}
    void tick(int world_x,int world_z) {
        integrate();const Key center{div_floor(world_x,EDGE),div_floor(world_z,EDGE)};
        // Unload far chunks and persist sparse edits.
        for(auto it=loaded_.begin();it!=loaded_.end();) {
            if(std::max(std::abs(it->first.x-center.x),std::abs(it->first.z-center.z))>config_.view+1) {
                save_chunk(it->first,it->second);events_.push_back({it->first,true,{}});
                Key old=it->first;it=loaded_.erase(it);mark_neighbors(old);
            } else ++it;
        }
        std::vector<std::pair<int,Key>> candidates;
        for(int dz=-config_.view;dz<=config_.view;++dz)for(int dx=-config_.view;dx<=config_.view;++dx) {
            Key k{center.x+dx,center.z+dz};
            if(!loaded_.count(k)&&!generating_.count(k)) candidates.push_back({dx*dx+dz*dz,k});
        }
        std::sort(candidates.begin(),candidates.end(),[](auto& a,auto& b){return a.first<b.first;});
        for(auto& c:candidates){if(inflight_>=job_limit_)break;generating_.insert(c.second);post({Job::Generate,c.second});++inflight_;}
        for(auto& entry:loaded_) {
            if(inflight_>=job_limit_)break;
            auto& c=entry.second;if(!c.dirty||c.busy)continue;
            Job j;j.kind=Job::Mesh;j.key=entry.first;j.version=c.version;j.center=c.blocks;
            auto neighbor=[&](Key k)->Blocks {auto it=loaded_.find(k);return it==loaded_.end()?Blocks{}:it->second.blocks;};
            j.west=neighbor({j.key.x-1,j.key.z});j.east=neighbor({j.key.x+1,j.key.z});
            j.north=neighbor({j.key.x,j.key.z-1});j.south=neighbor({j.key.x,j.key.z+1});
            c.busy=true;post(std::move(j));++inflight_;
        }
    }
    std::vector<MeshEvent> take_events(){auto r=std::move(events_);events_.clear();return r;}
    Stats stats() const {Stats s;s.loaded=loaded_.size();s.pending=generating_.size();s.queued=inflight_;
        for(auto& [key,c]:loaded_)s.faces+=c.faces;return s;}
    // Amanatides-Woo voxel traversal: hit normal points OUT of struck face.
    Hit raycast(Vec origin,Vec dir,float max_distance=7.f) const {
        dir=normalize(dir);if(dot(dir,dir)<.1f||max_distance<=0)return {};
        int p[3]={int(std::floor(origin.x)),int(std::floor(origin.y)),int(std::floor(origin.z))};
        float pos[3]={origin.x,origin.y,origin.z},d[3]={dir.x,dir.y,dir.z};
        float next[3],delta[3];int step[3];
        for(int a=0;a<3;++a){step[a]=(d[a]>0)?1:(d[a]<0?-1:0);
            delta[a]=step[a]?std::abs(1.f/d[a]):std::numeric_limits<float>::infinity();
            next[a]=step[a]>0?(float(p[a]+1)-pos[a])*delta[a]:step[a]<0?(pos[a]-float(p[a]))*delta[a]:std::numeric_limits<float>::infinity();}
        Hit hit;float distance=0;
        for(int n=0;n<2048 &&distance<=max_distance;++n) {
            if(opaque(get(p[0],p[1],p[2]))) {hit.found=true;hit.x=p[0];hit.y=p[1];hit.z=p[2];hit.distance=distance;return hit;}
            int axis=(next[0]<=next[1]&&next[0]<=next[2])?0:(next[1]<=next[2]?1:2);
            distance=next[axis];if(distance>max_distance)break;
            p[axis]+=step[axis];next[axis]+=delta[axis];
            hit.nx=hit.ny=hit.nz=0;
            if(axis==0)hit.nx=-step[0];else if(axis==1)hit.ny=-step[1];else hit.nz=-step[2];
        }
        return {};
    }
};
} // namespace br::stream
