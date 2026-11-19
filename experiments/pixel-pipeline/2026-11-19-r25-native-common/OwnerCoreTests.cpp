#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
using uint=unsigned int;
struct uint4 {
    uint a[4];
    uint operator[](uint k) const { return a[k]; }
};
#define R25_SHARED
#define R25_LOOP
#include "NativeConnectedCore154.hlsl"

struct Source { uint index, ax, ay, region, levels, key; float light; };
struct Expected { uint physical, index, ax, ay, role, r, q; };
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    std::ifstream input(argv[1]);
    for(uint n=0;n<2;n++) {
        uint w,h,count;
        std::string view;
        if(!(input>>view>>w>>h>>count))return 3;
        R25Reset(w,h);
        std::vector<Source> sources(4*count);
        std::vector<Expected> expected(count);
        for(uint c=0;c<count;c++) {
            uint x,y;
            auto& e=expected[c];
            input>>x>>y>>e.index>>e.ax>>e.ay>>e.role>>e.r>>e.q;
            e.physical=y*w+x;
            if(!input||x>=w||y>=h||r25Map[e.physical]!=0)return 4;
            uint4 code{},weight{};
            for(uint j=0;j<4;j++) {
                auto& s=sources[4*c+j];
                input>>code.a[j]>>weight.a[j]>>s.index>>s.ax>>s.ay>>s.region>>s.levels>>s.light;
                if(!input)return 5;
                s.key=code[j]&63u;
            }
            const uint fixed=R25FixedForeground(code,weight);
            if(fixed!=R25_NONE) {
                r25Map[e.physical]=R25_DIRECT|((code[fixed]>>8)<<2)|fixed;
            } else {
                if(!R25Add(e.physical))return 4;
                for(uint j=0;j<4;j++){
                    r25Codes[4*(r25N-1)+j]=code[j];
                    r25Weight[4*(r25N-1)+j]=weight[j];
                }
            }
        }
        if(R25Solve(1)!=5)return 11;
        const uint result=R25Solve(R25_EVAL_MAX);
        if(result!=0){std::cerr<<view<<" solver status "<<result<<"\n";return 6;}
        for(uint c=0;c<count;c++) {
            const auto& e=expected[c];
            uint domain=r25Map[e.physical];
            bool direct=(domain&R25_DIRECT)!=0;
            uint tap=direct?domain&3u:r25Pick[domain-1u]&3u;
            const auto& s=sources[4*c+tap];
            uint q=0;
            float g=std::clamp(s.light,0.f,1.f);
            for(uint k=0;k+1<s.levels;k++)q+=g>=float((double(k)+.5)/double(s.levels-1));
            uint role=s.key&15u;
            if(s.index!=e.index||s.ax!=e.ax||s.ay!=e.ay||role!=e.role||s.region!=e.r||q!=e.q) {
                std::cerr<<view<<" differs at domain "<<c<<"\n";
                return 7;
            }
        }
        std::cout<<view<<" matched owner, source and palette "<<count<<"; connected "<<r25N
                 <<"; direct "<<count-r25N<<"\n";
    }
    R25Reset(17,16);
    for(uint i=0;i<R25_CELLS;i++)if(!R25Add(i))return 9;
    if(R25Add(R25_CELLS)||r25N!=R25_CELLS)return 10;
    R25Reset(17,16);
    if(!R25Add(1)||R25Add(1)||r25N!=1)return 12;
    std::cout<<"cell capacity 256; overflow, duplicate and evaluation cutoff rejected\n";
    return 0;
}
