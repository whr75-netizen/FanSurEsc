// Isolated live GPU region enumeration. Source visibility and destination
// visibility are separate. Resource limits fail explicitly, never truncate.
#pragma kernel PrepareCells113
#pragma kernel GatherEye113
#pragma kernel BuildSubsets113
#pragma kernel Enumerate113
#pragma kernel Reduce113
#pragma kernel Write113
#pragma kernel ComposeWhole113
#pragma kernel ComposeRegion113
#pragma kernel CarrierQueries113
#define K113 65536.0
#define MAXP113 24
#define GROUPS113 32768u
struct Key113{float4 id,rgba,tag;};
struct Group113{float4 score;uint4 masks,tail;};
struct Subset113{uint4 a,b;};
StructuredBuffer<Key113> _Keys113;
int _KeyCount113;
StructuredBuffer<float4> _SrcLayers113,_SrcVisibility113;
StructuredBuffer<float4> _CarrierVisibility113;
StructuredBuffer<float4> _CarrierLayers113;
RWStructuredBuffer<float4> _Cells113;
RWStructuredBuffer<uint4> _CellTags113,_Frame113,_Points113;
RWStructuredBuffer<Group113> _Groups113,_Best113;
RWStructuredBuffer<Subset113> _Subsets113;
RWStructuredBuffer<float4> _Exposure113;
RWStructuredBuffer<float4> _WriteQueries113;
float4 _LidPalette113[2];
float4 _CarrierOrigin113;
int2 _CellsSize113,_SourceSize113;
Texture2D<float4> _FullBase113,_CandidateTile113;
RWTexture2D<float4> _FullOut113;
int4 _TileRect113;
float4 C113(int cell,int ch){return _Cells113[cell*7+ch];}
[numthreads(64,1,1)]void CarrierQueries113(uint3 tid:SV_DispatchThreadID){uint n=(uint)(_SourceSize113.x*_SourceSize113.y);if(tid.x>=n*4)return;uint part=tid.x/n,at=tid.x%n;float4 meta=_SrcLayers113[(part*5+1)*n+at];float2 xy=_CarrierOrigin113.xy+(float2(at%(uint)_SourceSize113.x,at/(uint)_SourceSize113.x)+.5)/8;_WriteQueries113[tid.x]=float4(xy,meta.x,round(meta.z));}
float4 SL113(int part,int ch,int p){return _SrcLayers113[(part*5+ch)*(_SourceSize113.x*_SourceSize113.y)+p];}
void Weight113(int at,out float3 lo,out float3 hi){
 int n=_SourceSize113.x*_SourceSize113.y;float3 a,b,z;
 for(int p=0;p<3;p++){float4 v=_SrcVisibility113[(p+1)*n+at];a[p]=v.x;b[p]=v.y;z[p]=SL113(p+1,1,at).x;}
 lo=a;hi=b;
 for(int p=0;p<3;p++)for(int q=0;q<3;q++)if(q!=p&&z[q]>0&&b[q]>0){if(z[q]<z[p]-3e-5){lo[p]*=1-b[q];hi[p]*=1-a[q];}else if(abs(z[q]-z[p])<=3e-5)lo[p]*=1-b[q];}
}
uint3 Encode113(float3 v){v=max(v,0);float3 c=float3(v.x<=.0031308?v.x*12.92:1.055*pow(v.x,1.0/2.4)-.055,v.y<=.0031308?v.y*12.92:1.055*pow(v.y,1.0/2.4)-.055,v.z<=.0031308?v.z*12.92:1.055*pow(v.z,1.0/2.4)-.055);return(uint3)round(saturate(c)*255);}
int SourceKey113(int owner,int part,int at){
 float4 r=float4(SL113(part,2,at).xyz,1);int oi=owner==_SourceEyeIds96.x?0:1;float4 px=_SourceProjectionX96[oi],py=_SourceProjectionY96[oi];float2 xy=float2(dot(r,px),dot(r,py));float2 eps=8*1.192092896e-7*float2(dot(abs(r),abs(px)),dot(abs(r),abs(py)));float3 rgb=SL113(part,0,at).rgb;int chosen=-1;
 for(int k=0;k<_KeyCount113;k++){Key113 key=_Keys113[k];if(round(key.id.z)!=owner||round(key.id.w)!=(part==1?1:4))continue;if(all(xy>=key.id.xy-eps)&&all(xy<key.id.xy+1+eps)&&all(Encode113(rgb)==(uint3)round(key.tag.yzw))){if(chosen>=0)return -2;chosen=k;}}
 return chosen;
}
bool Upper113(int owner,int x,out float mean){float total=0,mass=0;
 for(int s=0;s<_CurveCount106;s++){CurveSegment106 v=_Curves106[s];if(round(v.a.w)!=owner)continue;float2 a=v.a.xy,b=v.b.xy,d=b-a;float u=0,t=1;if(abs(d.x)<1e-12){if(a.x<x||a.x>x+1)continue;}else{float p=(x-a.x)/d.x,q=(x+1-a.x)/d.x;u=max(0,min(p,q));t=min(1,max(p,q));if(t<=u)continue;}float2 aa=a+u*d,bb=a+t*d;float len=length(bb-aa);total+=len*(aa.y+bb.y)*.5;mass+=len;}
 mean=mass>0?total/mass:0;return mass>1e-12;
}
[numthreads(8,8,1)]void PrepareCells113(uint3 tid:SV_DispatchThreadID){int2 p=tid.xy;if(any(p>=_CellsSize113))return;int cell=p.y*_CellsSize113.x+p.x;float4 mass=0,ci=0,cw=0;float2 depth=0;uint4 tags=0;int owner=0,errors=0;float bi=-1,bw=-1;int ki=999,kw=999;
 for(int y=0;y<8;y++)for(int x=0;x<8;x++){int at=(p.y*8+y)*_SourceSize113.x+p.x*8+x;float3 lo,hi;Weight113(at,lo,hi);
  for(int part=1;part<=2;part++){int o=(int)round(SL113(part,1,at).z);if(lo[part-1]<=0)continue;if(owner==0)owner=o;else if(owner!=o)errors|=1;int key=SourceKey113(o,part,at);if(key<0){errors|=2;continue;}float lower=lo[part-1]*1024,upper=hi[part-1]*1024;
   if(part==1){mass.xy+=float2(lower,upper);tags.x|=(uint)_Keys113[key].tag.x;tags.z|=1u<<key;if(lo.x>bi||(lo.x==bi&&key<ki)){bi=lo.x;ki=key;ci=_Keys113[key].rgba;depth.x=SL113(1,1,at).x;}}
   else{mass.zw+=float2(lower,upper);tags.y|=(uint)_Keys113[key].tag.x;tags.w|=1u<<key;if(lo.y>bw||(lo.y==bw&&key<kw)){bw=lo.y;kw=key;cw=_Keys113[key].rgba;depth.y=SL113(2,1,at).x;}}
  }
 }
 int boundaryOwner=0,row=0;for(int i=0;i<2;i++){int o=_CurveEyeIds106[i];float mean;if(Upper113(o,p.x,mean)&&p.y==(int)floor(mean)){if(boundaryOwner!=0)errors|=8;boundaryOwner=o;row=(int)floor(mean);}}
 int policy=1;if(boundaryOwner>0){owner=boundaryOwner;policy=2;}else if(owner>0){float mean;if(Upper113(owner,p.x,mean)){row=(int)floor(mean);policy=p.y<row?-1:1;}}
 float4 lid=0;float best=-1;int chosen=-1;
 if(policy==2)for(int y=0;y<8;y++)for(int x=0;x<8;x++){int at=(p.y*8+y)*_SourceSize113.x+p.x*8+x;float4 v=_SrcVisibility113[3*_SourceSize113.x*_SourceSize113.y+at],m=SL113(3,1,at);if(round(m.z)!=owner||v.x<=0||v.x!=v.y)continue;float d=3.402823e38;for(int s=0;s<_CurveCount106;s++)if(round(_Curves106[s].a.w)==owner)d=min(d,Distance106((float2(p*8+int2(x,y))+.5)/8,_Curves106[s].a.xy,_Curves106[s].b.xy));if(d<best||chosen<0){best=d;chosen=at;lid=float4(_LidPalette113[owner==_CurveEyeIds106.x?0:1].rgb,m.x);}}
 _Cells113[cell*7]=mass;_Cells113[cell*7+1]=ci;_Cells113[cell*7+2]=cw;_Cells113[cell*7+3]=float4(owner,depth,row);_Cells113[cell*7+4]=lid;_Cells113[cell*7+5]=float4(policy,chosen+1,errors,0);_Cells113[cell*7+6]=0;_CellTags113[cell]=tags;
}
float Interval113(float value,float low,float high){return value<low?low-value:value>high?value-high:0;}
uint AtBit113(uint a[16],int cell){return(a[cell>>5]>>(cell&31))&1;}
bool RawConnected113(int owner,int part,uint bit){uint seen[16];for(int j=0;j<16;j++)seen[j]=0;int seed=-1,total=0,n=_CellsSize113.x*_CellsSize113.y;for(int i=0;i<n;i++)if(round(C113(i,3).x)==owner&&((_CellTags113[i][part]&bit)!=0)){seed=i;total++;}if(total<2)return true;seen[seed>>5]|=1u<<(seed&31);int count=1;
 for(int iteration=0;iteration<512;iteration++){bool changed=false;for(int i=0;i<n;i++){if(AtBit113(seen,i)||round(C113(i,3).x)!=owner||(_CellTags113[i][part]&bit)==0)continue;int x=i%_CellsSize113.x;bool near=(x>0&&AtBit113(seen,i-1))||(x+1<_CellsSize113.x&&AtBit113(seen,i+1))||(i>=_CellsSize113.x&&AtBit113(seen,i-_CellsSize113.x))||(i+_CellsSize113.x<n&&AtBit113(seen,i+_CellsSize113.x));if(near){seen[i>>5]|=1u<<(i&31);count++;changed=true;}}if(!changed)break;}return count==total;
}
[numthreads(1,1,1)]void GatherEye113(uint3 tid:SV_DispatchThreadID){int eye=tid.x;if(eye>=2)return;int owner=_CurveEyeIds106[eye];uint np=0,ni=0,nw=0,bad=0;float4 mass=0;uint ai=0,aw=0,keys=0;
 for(int i=0;i<32;i++)_Frame113[eye*32+i]=0;
 int n=_CellsSize113.x*_CellsSize113.y;if(n>512)bad|=16;
 float canvas=0;for(int cell=0;cell<n;cell++){float4 info=C113(cell,3);if(round(info.x)!=owner)continue;float4 v=C113(cell,0);mass+=v;uint4 bits=_CellTags113[cell];ai|=bits.x;aw|=bits.y;keys|=bits.z|bits.w;bad|=(uint)round(C113(cell,5).z);if(C113(cell,5).x!=1||v.x+v.z==0)continue;if(np>=MAXP113){bad|=32;continue;}canvas+=v.x+v.z;_Points113[eye*MAXP113+np]=uint4(cell,v.x>0?ni:0xffffffff,v.z>0?nw:0xffffffff,0);ni+=(v.x>0?1u:0u);nw+=(v.z>0?1u:0u);np++;}
 if(ni+nw>21)bad|=64;if(ni>12||nw>12)bad|=128;
 for(uint p=0;p<np;p++){uint4 q=_Points113[eye*MAXP113+p];uint cell=q.x,nb=0;for(uint k=0;k<np;k++){uint b=_Points113[eye*MAXP113+k].x;int2 d=int2(cell%_CellsSize113.x,cell/_CellsSize113.x)-int2(b%_CellsSize113.x,b/_CellsSize113.x);if(abs(d.x)+abs(d.y)==1)nb|=1u<<k;}q.w=nb;_Points113[eye*MAXP113+p]=q;}
 for(uint part=0;part<2;part++)for(uint bit=0;bit<8;bit++){uint active=part==0?ai:aw,scope=0;if((active&(1u<<bit))&&RawConnected113(owner,part,1u<<bit)){for(uint p=0;p<np;p++)if(_CellTags113[_Points113[eye*MAXP113+p].x][part]&(1u<<bit))scope|=1u<<p;}_Frame113[eye*32+4+part*8+bit]=uint4(scope,0,0,0);}
 _Frame113[eye*32]=uint4(np,ni,nw,bad);_Frame113[eye*32+1]=asuint(mass);_Frame113[eye*32+2]=uint4(ai,aw,keys,0);_Frame113[eye*32+3]=uint4(asuint(canvas),0,0,0);
}
bool Connected113(uint mask,int eye){if(mask==0)return true;uint reach=1u<<firstbitlow(mask);for(int i=0;i<MAXP113;i++){uint next=reach;for(int p=0;p<MAXP113;p++)if(reach&(1u<<p))next|=_Points113[eye*MAXP113+p].w&mask;if(next==reach)break;reach=next;}return reach==mask;}
Group113 Invalid113(){Group113 v;v.score=3.402823e38;v.masks=0;v.tail=uint4(0xffffffff,0,0,0);return v;}
bool Less113(Group113 a,Group113 b){for(int j=0;j<4;j++)if(a.score[j]!=b.score[j])return a.score[j]<b.score[j];return a.tail.x<b.tail.x;}
Group113 Merge113(Group113 a,Group113 b){if(a.tail.y==0)return b;if(b.tail.y==0)return a;if(Less113(a,b))return a;if(Less113(b,a))return b;a.masks=uint4(a.masks.x&b.masks.x,a.masks.y|b.masks.y,a.masks.z&b.masks.z,a.masks.w|b.masks.w);a.tail.y+=b.tail.y;return a;}
groupshared Group113 Shared113[64];
[numthreads(64,1,1)]void BuildSubsets113(uint3 tid:SV_DispatchThreadID){int eye=tid.y/2,part=tid.y%2;uint state=tid.x;uint4 head=_Frame113[eye*32];Subset113 outValue;outValue.a=0;outValue.b=0;uint count=part==0?head.y:head.z;if(head.w==0&&state<(1u<<count)){uint mask=0,component=0,keys=0,n=0;float cost=0;bool valid=true;for(uint p=0;p<head.x;p++){uint4 entry113=_Points113[eye*MAXP113+p];uint index=part==0?entry113.y:entry113.z;if(index==0xffffffff||!(state&(1u<<index)))continue;float4 mass=C113(entry113.x,0);uint4 tag=_CellTags113[entry113.x];mask|=1u<<p;n++;component|=tag[part];keys|=tag[part+2];cost+=K113-mass.x-mass.z-(part==0?mass.x:mass.z);}for(int bit=0;bit<8;bit++){uint scope=_Frame113[eye*32+4+part*8+bit].x;if(scope&&!Connected113(mask&scope,eye))valid=false;}outValue.a=uint4(mask,component,keys,n);outValue.b=uint4(asuint(cost),valid?1:0,0,0);}_Subsets113[(eye*2+part)*4096+state]=outValue;}
[numthreads(64,1,1)]void Enumerate113(uint3 gid:SV_GroupID,uint3 local:SV_GroupThreadID){int eye=gid.y;uint state=gid.x*64+local.x;uint4 header=_Frame113[eye*32];Group113 r=Invalid113();
 if(header.w==0&&state<(1u<<(header.y+header.z))){uint si=state&((1u<<header.y)-1),sw=state>>header.y;Subset113 a=_Subsets113[eye*8192+si],b=_Subsets113[eye*8192+4096+sw];if(a.b.y&&b.b.y&&(a.a.x&b.a.x)==0){float4 mass=asfloat(_Frame113[eye*32+1]);uint4 active=_Frame113[eye*32+2];float reconstruction=asfloat(_Frame113[eye*32+3].x)+asfloat(a.b.x)+asfloat(b.b.x);r.score=float4(countbits(active.x&~a.a.y)+countbits(active.y&~b.a.y),Interval113((a.a.w+b.a.w)*K113,mass.x+mass.z,mass.y+mass.w),Interval113(a.a.w*K113,mass.x,mass.y)+Interval113(b.a.w*K113,mass.z,mass.w),max(reconstruction,0));r.masks=uint4(a.a.x,a.a.x,b.a.x,b.a.x);r.tail=uint4(countbits(active.z&~(a.a.z|b.a.z)),1,0,0);}
 }
 Shared113[local.x]=r;GroupMemoryBarrierWithGroupSync();for(uint stride=32;stride>0;stride>>=1){if(local.x<stride)Shared113[local.x]=Merge113(Shared113[local.x],Shared113[local.x+stride]);GroupMemoryBarrierWithGroupSync();}if(local.x==0)_Groups113[eye*GROUPS113+gid.x]=Shared113[0];
}
[numthreads(64,1,1)]void Reduce113(uint3 gid:SV_GroupID,uint3 local:SV_GroupThreadID){int eye=gid.x;Group113 r=Invalid113();for(uint i=local.x;i<GROUPS113;i+=64)r=Merge113(r,_Groups113[eye*GROUPS113+i]);Shared113[local.x]=r;GroupMemoryBarrierWithGroupSync();for(uint stride=32;stride>0;stride>>=1){if(local.x<stride)Shared113[local.x]=Merge113(Shared113[local.x],Shared113[local.x+stride]);GroupMemoryBarrierWithGroupSync();}if(local.x==0)_Best113[eye]=Shared113[0];}
[numthreads(8,8,1)]void Write113(uint3 tid:SV_DispatchThreadID){int2 p=tid.xy;if(any(p>=_CellsSize113))return;int cell=p.y*_CellsSize113.x+p.x;float4 info=C113(cell,3),policy=C113(cell,5);int owner=(int)round(info.x),eye=owner==_CurveEyeIds106.x?0:1;float4 colour=0,id=0,decision=0,audit=0;
 if(owner>0&&_Frame113[eye*32].w==0){if(policy.x==2){float4 lid=C113(cell,4);if(lid.w>0){colour=float4(lid.rgb,1);id=float4(6,owner,lid.w,0);decision=float4(6,113,0,0);audit.x=3;}else audit.x=-1;}else if(policy.x==1){uint4 header=_Frame113[eye*32];Group113 best=_Best113[eye];for(uint k=0;k<header.x;k++)if(_Points113[eye*MAXP113+k].x==cell){uint bit=1u<<k;bool isI=(best.masks.x&bit)!=0,isW=(best.masks.z&bit)!=0;bool uncertain=((best.masks.y^best.masks.x)|(best.masks.w^best.masks.z))&bit;if(uncertain){decision.x=-1;audit.x=-2;}else if(isI||isW){colour=C113(cell,isI?1:2);id=float4(isI?1:4,owner,isI?info.y:info.z,0);decision=float4(isI?1:4,113,0,0);audit.x=1;}break;}}}
 else if(owner>0){decision.x=-1;audit=float4(-64,_Frame113[eye*32].w,_Frame113[eye*32].y,_Frame113[eye*32].z);}
 _CurveColour106[cell]=colour;_CurveIdentity106[cell]=id;_CurveDecision106[cell]=decision;_CurveAudit106[cell]=audit;
}
[numthreads(8,8,1)]void ComposeWhole113(uint3 tid:SV_DispatchThreadID){int2 p=tid.xy;if(any(p>=int2(480,272)))return;float4 c=_FullBase113.Load(int3(p,0));int2 q=p-_TileRect113.xy;if(all(q>=0)&&all(q<_TileRect113.zw)){float4 tile=_CandidateTile113.Load(int3(q,0));if(tile.a>0)c=tile;}_FullOut113[p]=c;}
[numthreads(8,8,1)]void ComposeRegion113(uint3 tid:SV_DispatchThreadID){int2 p=tid.xy;if(any(p>=_ForwardROI102.zw))return;float4 c=_CanvasRGBA102.Load(int3(p*4+1,0)),m=_CanvasMeta102.Load(int3(p*4+1,0));float4 owner=m.x>0?float4(4,m.z,m.x,m.y):0;
 float2 centre=float2(_ForwardROI102.x+p.x+.5,272-(_ForwardROI102.y+p.y+.5));int2 cell=(int2)floor(centre-_ForwardAnchor102.xy),size=_Size96>>2;int chosenPart=0,chosenOwner=0;float4 selected=0;float minDepth=3.402823e38;float faceLo=0,faceHi=0;float cvDepth[16];bool known[16];for(int i=0;i<16;i++){cvDepth[i]=0;known[i]=false;}
 if(all(cell>=0)&&all(cell<size)){int at=cell.y*size.x+cell.x;float4 id=_ReadIdentity96[at],decision=_ReadDecision96[at];if(id.x>0&&decision.x>=0){chosenPart=round(id.x)==1?1:round(id.x)==4?2:3;chosenOwner=(int)round(id.y);selected=_ReadColour96[at];int n=_SourceSize113.x*_SourceSize113.y;
   for(int y=0;y<4;y++)for(int x=0;x<4;x++){int si=y*4+x;float2 absolute=float2(_ForwardROI102.x+p.x+(x+.5)/4,272-(_ForwardROI102.y+p.y+(y+.5)/4));int2 q=(int2)floor((absolute-_CarrierOrigin113.xy)*8);if(any(q<0)||any(q>=_SourceSize113))continue;int index=q.y*_SourceSize113.x+q.x;float4 meta=_CarrierLayers113[(chosenPart*5+1)*n+index],v=_CarrierVisibility113[chosenPart*n+index];if(meta.x<=0||round(meta.z)!=chosenOwner)continue;cvDepth[si]=v.z;known[si]=true;faceLo+=v.x;faceHi+=v.y;if(v.y>0)minDepth=min(minDepth,v.z);}
   if(faceLo>=8){c=selected;owner=float4(round(id.x)+1,chosenOwner,minDepth,id.w);}else{int knownCount=0;for(int a113=0;a113<16;a113++)if(known[a113])knownCount++;owner.w=faceHi>=8?-114:knownCount<8?-116:-117;chosenPart=0;}
 }}
 _EyeRGBA102[p]=c;_EyeOwner102[p]=owner;
 float hairLo=0,hairHi=0,best=-1;float4 hc=0,hm=0;
 for(int y=0;y<4;y++)for(int x=0;x<4;x++){int2 q=p*4+int2(x,y);float4 h=_HairMeta102.Load(int3(q,0)),v=_HairRGBA102.Load(int3(q,0));if(h.x<=0||h.w<=0||v.a<=0)continue;float weight=saturate(h.w);bool front=chosenPart>0?known[y*4+x]&&h.x<cvDepth[y*4+x]-3e-5:owner.z<=0||h.x<owner.z-3e-5;bool uncertain=chosenPart>0&&!known[y*4+x];if(front){hairLo+=weight;hairHi+=weight;}else if(uncertain)hairHi+=weight;if((front||uncertain)&&weight>best){best=weight;hc=v;hm=h;}}
 if(hairLo>=8){c=float4(hc.rgb,1);owner=float4(round(hm.y),round(hm.z),hm.x,0);}else if(hairHi>=8){c=_CanvasRGBA102.Load(int3(p*4+1,0));owner=float4(4,m.z,m.x,-113);}
 int knownCount113=0;for(int a113=0;a113<16;a113++)if(known[a113])knownCount113++;int evidence113=(p.y*_ForwardROI102.z+p.x)*2;_Exposure113[evidence113]=float4(faceLo,faceHi,hairLo,hairHi);_Exposure113[evidence113+1]=float4(chosenPart,chosenOwner,knownCount113,owner.w);
 _FinalRGBA102[p]=c;_FinalOwner102[p]=owner;
}
