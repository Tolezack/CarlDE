#include "brainrot_stream.hpp"
#include <cassert>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <thread>
namespace fs=std::filesystem;
using namespace br::stream;
static void spin(World& w,int x=0,int z=0,int limit=10000){
    for(int i=0;i<limit;++i){w.tick(x,z);auto s=w.stats();if(s.loaded>=9&&s.faces>0&&s.pending==0&&s.queued==0)return;
        std::this_thread::sleep_for(std::chrono::milliseconds(2));}
    std::cerr << "TIMEOUT: loaded=" <<w.stats().loaded <<" faces="<<w.stats().faces<<" jobs="<<w.stats().queued<<"\n";
    throw std::runtime_error("streaming timeout");
}
int main() {
    assert(div_floor(-1,EDGE)==-1 && mod_floor(-1,EDGE)==EDGE-1);
    assert(div_floor(-16,EDGE)==-1 && mod_floor(-16,EDGE)==0);
    auto f=look(0,0),r=right(0);assert(f.z<-.99f&&r.x>.99f);
    auto g=look(3.14159265f/2,0);assert(g.x>.99f);
    fs::path path=fs::temp_directory_path()/("br_stream_test_"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    fs::remove_all(path);
    Settings opt;opt.view=1;opt.height=64;opt.workers=2;opt.save_dir=path;opt.seed=121;
    std::uint8_t old=Air;
    {
        World w(opt);spin(w);
        assert(w.loaded_count()>=9);
        old=w.get(1,62,1);assert(old==Air);
        assert(w.set(1,62,1,Stone));
        Hit hit=w.raycast({1.5f,62.5f,4.5f},{0,0,-1},6.f);
        assert(hit.found&&hit.x==1&&hit.y==62&&hit.z==1&&hit.nz==1);
        assert(w.get(hit.x+hit.nx,hit.y+hit.ny,hit.z+hit.nz)==Air);
        assert(w.set(-1,62,0,Grass));
        for(int i=0;i<150;++i){w.tick(0,0);std::this_thread::sleep_for(std::chrono::milliseconds(1));}
        w.save_all();
        auto s=w.stats();assert(s.loaded<=9 && s.faces>0);
        std::cout<<"loaded="<<s.loaded<<" faces="<<s.faces<<"\n";
    }
    {
        World w(opt);spin(w);
        assert(w.get(1,62,1)==Stone && w.get(-1,62,0)==Grass);
        w.tick(EDGE*30,EDGE*30); // unload and persist
        assert(w.loaded_count()==0);
        spin(w,EDGE*30,EDGE*30);
        assert(w.loaded_count()<=9);
        w.tick(0,0);spin(w);
        assert(w.get(1,62,1)==Stone);
    }
    fs::remove_all(path);
    std::cout << "All streaming / DDA / persistence tests passed\n";
}
