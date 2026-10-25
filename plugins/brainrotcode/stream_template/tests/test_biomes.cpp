#include "brainrot_biomes.hpp"
#include "brainrot_stream.hpp"
#include <cassert>
#include <iostream>
#include <set>
using namespace br;
int main(){
    using namespace br::biomes;
    const auto a=sample(-16,48,42u),b=sample(-16,48,42u);
    assert(a.elevation==b.elevation && a.biome==b.biome);
    assert(noise3(-1.25f,3.75f,0.23f,42u)==noise3(-1.25f,3.75f,0.23f,42u));
    // stable result independent from chunk coordinate system
    for(int cx=-3;cx<=3;cx++) for(int lx=0;lx<16;lx++){
        int world_x=cx*16+lx;
        const auto region=sample(world_x,21,42u);
        assert(region.elevation>-200&&region.elevation<200);
        assert(region.biome<=Biome::Marsh);
        assert(geology(world_x,13,21,42u)>=10 && geology(world_x,13,21,42u)<=14);
    }
    std::set<int> biomes;float min_h=999,max_h=-999;int cave_count=0;
    for(int z=-1400;z<1400;z+=37)for(int x=-1400;x<1400;x+=37){
        const auto c=sample(x,z,2026u);
        min_h=std::min(min_h,c.elevation);max_h=std::max(max_h,c.elevation);
        biomes.insert(int(c.biome));
        for(int y=5;y<32;y+=5)if(cave(x,y,z,2026u,int(c.elevation)))++cave_count;
    }
    assert(biomes.size()>=4);
    assert(max_h-min_h>15);
    assert(cave_count>10);
    std::cout<<"Fase02: biomes="<<biomes.size()<<" elevation="<<min_h<<".."<<max_h<<" caves="<<cave_count<<"\n";
}
