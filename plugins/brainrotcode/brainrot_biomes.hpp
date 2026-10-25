#pragma once
// BrainrotCode 3.1 alpha / Fase 02: biomas, erosão, geologia e cavernas.
// As funções abaixo são PURAS, determinadas por coordenadas globais e seed.
// Isso evita costuras entre chunks, inclusive em coordenadas negativas.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include "brainrot.hpp"
namespace br::biomes {
inline float v2(float x,float z,unsigned s){return br::value_noise(x,z,s);}
inline float fbm(float x,float z,unsigned seed,int oct=4){
    float sum=0,weight=1,total=0;
    for(int i=0;i<oct;++i){sum+=v2(x,z,seed+unsigned(i)*67)*weight;total+=weight;
        x*=2.03f;z*=2.03f;weight*=.51f;}
    return sum/std::max(total,.01f);
}
inline float hash3(int x,int y,int z,unsigned seed){
    auto mix=[](std::uint32_t v){v^=v>>16;v*=0x7feb352du;v^=v>>15;v*=0x846ca68bu;v^=v>>16;return v;};
    const auto a=mix(std::uint32_t(x)^seed*33u), b=mix(std::uint32_t(y)^a),c=mix(std::uint32_t(z)^b);
    return float(c&0xffffffu)/8388607.5f-1.f;
}
inline float noise3(float x,float y,float z,unsigned seed){
    const int ix=int(std::floor(x)),iy=int(std::floor(y)),iz=int(std::floor(z));
    const float fx=br::smooth(x-ix),fy=br::smooth(y-iy),fz=br::smooth(z-iz);
    float data[2][2];
    for(int k=0;k<2;++k)for(int j=0;j<2;++j)
        data[k][j]=br::mix(hash3(ix,iy+j,iz+k,seed),hash3(ix+1,iy+j,iz+k,seed),fx);
    return br::mix(br::mix(data[0][0],data[0][1],fy),br::mix(data[1][0],data[1][1],fy),fz);
}
inline float fbm3(float x,float y,float z,unsigned seed){
    return .57f*noise3(x,y,z,seed)+.29f*noise3(x*2.02f,y*2.02f,z*2.02f,seed+71)+
           .14f*noise3(x*4.07f,y*4.07f,z*4.07f,seed+145);
}
enum class Biome : std::uint8_t { Ocean,Plains,Forest,Desert,Taiga,Alpine,Highlands,Marsh };
struct Climate {float temperature=0,humidity=0,continentalness=0,erosion=0,mountains=0,river=0;Biome biome=Biome::Plains;float elevation=26;};
inline Climate sample(int x,int z,unsigned s){
    const float px=float(x),pz=float(z);
    const float warp_x=fbm(px/230.f,pz/230.f,s+100)*47.f;
    const float warp_z=fbm(px/230.f+121.f,pz/230.f-113.f,s+151)*47.f;
    const float X=px+warp_x,Z=pz+warp_z;
    Climate c;
    c.temperature=fbm(X/390.f,Z/390.f,s+3)*.75f-float(std::abs(z))/4500.f;
    c.humidity=fbm(X/330.f,Z/330.f,s+13);
    c.continentalness=fbm(X/510.f,Z/510.f,s+35);
    c.erosion=fbm(X/160.f,Z/160.f,s+50);
    float ridge=1.f-std::abs(fbm(X/105.f,Z/105.f,s+76));
    c.mountains=std::clamp((c.continentalness+.12f)*2.1f,0.f,1.f)*
         std::pow(std::clamp(ridge,0.f,1.f),1.7f);
    const float base=27.f+c.continentalness*21.f+c.erosion*6.f;
    const float plateau=std::clamp(c.mountains,0.f,1.f)*(24.f+10.f*std::max(0.f,c.erosion));
    c.river=std::abs(fbm(X/210.f,Z/210.f,s+202));
    const float carved=std::max(0.f,1.f-c.river/.065f);
    c.elevation=base+plateau-carved*(4.f+std::max(0.f,base-25.f)*.25f);
    if(c.continentalness<-.35f)c.biome=Biome::Ocean;
    else if(c.elevation>59.f)c.biome=Biome::Alpine;
    else if(c.temperature<-.24f)c.biome=Biome::Taiga;
    else if(c.temperature>.22f&&c.humidity<-.12f)c.biome=Biome::Desert;
    else if(c.humidity>.30f&&c.elevation<33.f)c.biome=Biome::Marsh;
    else if(c.humidity>.05f)c.biome=Biome::Forest;
    else if(c.mountains>.28f)c.biome=Biome::Highlands;
    return c;
}
// 3D cave mask. Extra warped tunnel field plus chambers, no chunk-local inputs.
inline bool cave(int x,int y,int z,unsigned seed,int surface){
    if(y<5||y>surface-4)return false;
    const float X=x/31.f,Y=y/22.f,Z=z/31.f;
    const float warp=noise3(X*.42f,Y*.42f,Z*.42f,seed+500);
    const float tunnel=std::abs(noise3(X+warp*.34f,Y,Z-warp*.34f,seed+601));
    const float chamber=fbm3(x/17.f,y/17.f,z/17.f,seed+608);
    return (tunnel<.069f && chamber>-.32f) || (chamber>.48f && y<surface-10);
}
// geological bands; return stable stone IDs provided by host engine.
inline std::uint8_t geology(int x,int y,int z,unsigned s){
    const float shift=fbm(x/105.f,z/105.f,s+801)*8.f;
    const int layer=int(std::floor((y+shift)/13.f));
    const float reg=fbm(x/200.f,z/200.f,s+808);
    std::uint8_t material=(layer%4==0?10:(layer%4==1?11:(layer%4==2?12:13)));
    if(reg>.25f&&layer%3==0)material=10;
    if(y<36&&hash3(x/3,y/3,z/3,s+880)>.91f && noise3(x/11.f,y/9.f,z/11.f,s+900)>.12f)material=14;
    return material;
}
} // namespace br::biomes
