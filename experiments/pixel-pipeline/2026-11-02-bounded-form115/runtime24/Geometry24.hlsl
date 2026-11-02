// Runtime-candidate declarations and scalar geometry functions. NOT imported.
// The existing Query traversal is copied mechanically as TraceExternal24 by
// prepare_runtime.py; it keeps its bounded BVH stack32 and unknown overflow.
struct CurveProof24 { float4 uv; uint4 primitive; };
struct ColumnRecord24 { float4 midpoint,source,visibility; };
StructuredBuffer<CurveProof24> _CurveProof24;
RWStructuredBuffer<ColumnRecord24> _Columns24;
RWStructuredBuffer<float4> _AssignedDepth24,_AssignedVisibility24;
float4 _RingDepth24;
int _PhysicalCount24;

float SocketLimit24(int eye){return eye==_CurveEyeIds106.x?_SocketLimit113.x:eye==_CurveEyeIds106.y?_SocketLimit113.y:0;}
float2 RingDepth24(int eye){return eye==_CurveEyeIds106.x?_RingDepth24.xy:eye==_CurveEyeIds106.y?_RingDepth24.zw:float2(1,0);}
bool Clip24(float3 a,float3 b,int x,out float low,out float high,out float arc){
 low=0;high=1;arc=0;float3 d=b-a;
 if(abs(d.x)<1e-12){if(a.x<x||a.x>x+1)return false;}
 else{float p=(x-a.x)/d.x,q=(x+1-a.x)/d.x;low=max(0,min(p,q));high=min(1,max(p,q));if(high<=low)return false;}
 arc=length(d.xy)*(high-low);return arc>0;
}
bool ClipCell24(float3 a,float3 b,int x,int y,out float low,out float high,out float arc){
 if(!Clip24(a,b,x,low,high,arc))return false;float3 d=b-a;
 if(abs(d.y)<1e-12){if(a.y<y||a.y>y+1)return false;}
 else{float p=(y-a.y)/d.y,q=(y+1-a.y)/d.y;low=max(low,min(p,q));high=min(high,max(p,q));if(high<=low)return false;}
 arc=length(d.xy)*(high-low);return arc>0;
}

// Each source-ordered clipped path is reduced to its arc-length midpoint,
// which stays on ONE actual segment rather than averaging disconnected paths.
[numthreads(64,1,1)]void CurveColumns24(uint3 tid:SV_DispatchThreadID){
 uint at=tid.x;if(at>=(uint)_CellsSize113.x*2)return;int eye=at/_CellsSize113.x,x=at%_CellsSize113.x,owner=_CurveEyeIds106[eye];
 ColumnRecord24 r;r.midpoint=0;r.source=0;r.visibility=0;float total=0,meanY=0;
 for(int s=0;s<_CurveCount106;s++)if(round(_Curves106[s].a.w)==owner){float low,high,arc;if(Clip24(_Curves106[s].a.xyz,_Curves106[s].b.xyz,x,low,high,arc)){total+=arc;meanY+=arc*lerp(_Curves106[s].a.y,_Curves106[s].b.y,(low+high)*.5);}}
 if(total<=0){_Columns24[at]=r;return;}meanY/=total;int row=(int)floor(meanY);
 // Boundary classification keeps113's arc-weighted mean. A recovery point
 // must separately lie on a real curve piece INSIDE that already chosen cell.
 r.midpoint=float4(x+.5,meanY,0,owner);r.visibility.z=meanY;float cellArc=0;
 for(int t0=0;t0<_CurveCount106;t0++)if(round(_Curves106[t0].a.w)==owner){float low,high,arc;if(ClipCell24(_Curves106[t0].a.xyz,_Curves106[t0].b.xyz,x,row,low,high,arc))cellArc+=arc;}
 float cursor=0;bool chosen=false;
 for(int t=0;t<_CurveCount106;t++)if(!chosen&&round(_Curves106[t].a.w)==owner){float low,high,arc;
  if(!ClipCell24(_Curves106[t].a.xyz,_Curves106[t].b.xyz,x,row,low,high,arc))continue;
  if(cursor+arc<cellArc*.5){cursor+=arc;continue;}chosen=true;
  float u=lerp(low,high,saturate((cellArc*.5-cursor)/arc));float3 mid=lerp(_Curves106[t].a.xyz,_Curves106[t].b.xyz,u);
  CurveProof24 proof=_CurveProof24[t];float2 uv=lerp(proof.uv.xy,proof.uv.zw,u);
  // Source proof uses the original native face primitive's material, not a
  // screenshot colour or a fabricated carrier at the destination.
  uint primitive=proof.primitive.x;float2 alpha=0;
  if(primitive>0&&primitive<=(uint)_FacePrimitiveStride96&&proof.primitive.y<4){int ti=_PartTriangles96[proof.primitive.y*_FacePrimitiveStride96+primitive-1];if(ti>=0){Tri96 t=_Triangles96[ti];if(t.source.x==(int)proof.primitive.w&&t.source.y==(int)proof.primitive.z&&t.source.z==(int)primitive)alpha=AlphaBounds96(t.verticesMaterial.w,uv);}}
  r.midpoint=float4(mid,owner);r.source=float4(uv,primitive,alpha.x);
  r.visibility=float4(0,0,meanY,alpha.y);
 }
 _Columns24[at]=r;
}
[numthreads(64,1,1)]void ColumnVisibility24(uint3 tid:SV_DispatchThreadID){
 uint at=tid.x;if(at>=(uint)_CellsSize113.x*2)return;ColumnRecord24 r=_Columns24[at];
 if(r.midpoint.w>0&&r.source.w>0)r.visibility.xy=TraceExternal24(_ForwardAnchor102.xy+r.midpoint.xy,r.midpoint.z,(int)round(r.midpoint.w));
 _Columns24[at]=r;
}

// The same function defines coordinates in producer and consumer. Y is the
// existing physical top-down view convention; no 8x pixel-centre surrogate.
float2 Destination24(int2 p,int si){uint x=(uint)si%4u,y=(uint)si/4u;return float2(_ForwardROI102.x+p.x+(x+.5)/4,272-(_ForwardROI102.y+p.y+(y+.5)/4));}
float DirectDepth24(int2 p,int si,int part,int owner){
 float2 xy=Destination24(p,si);int2 q=(int2)floor((xy-_CarrierOrigin113.xy)*8);
 if(any(q<0)||any(q>=_SourceSize113))return 0;int n=_SourceSize113.x*_SourceSize113.y;
 float4 m=_SrcLayers113[(part*5+1)*n+q.y*_SourceSize113.x+q.x];
 return m.x>0&&round(m.z)==owner?m.x:0;
}
[numthreads(64,1,1)]void CarrierQueries113(uint3 tid:SV_DispatchThreadID){
 uint sample=tid.x;if(sample>=(uint)_PhysicalCount24*16u)return;uint pixel=sample/16u;int si=(int)(sample%16u);int2 p=int2(pixel%(uint)_ForwardROI102.z,pixel/(uint)_ForwardROI102.z);
 float2 xy=Destination24(p,si);float4 query=0,visibility=0;
 float2 centre=float2(_ForwardROI102.x+p.x+.5,272-(_ForwardROI102.y+p.y+.5));int2 cell=(int2)floor(centre-_ForwardAnchor102.xy);
 if(all(cell>=0)&&all(cell<_CellsSize113)){
  int at=cell.y*_CellsSize113.x+cell.x;float4 id=_ReadIdentity96[at],decision=_ReadDecision96[at];
  int role=(int)round(id.x),owner=(int)round(id.y),part=role==1?1:role==4?2:role==6?3:0;
  if(part>0&&decision.x>=0){float sum=0;uint count=0;for(int i=0;i<16;i++){float z=DirectDepth24(p,i,part,owner);if(z>0){sum+=z;count++;}}
   float z=DirectDepth24(p,si,part,owner);float2 range=RingDepth24(owner);
   if(z<=0)z=count>0?sum/count:(id.z>=range.x&&id.z<=range.y?id.z:0);
   if(isfinite(z)&&z>0){query=float4(xy,z,owner);visibility=float4(0,0,z,count>0?1:2);}
  }
 }
 _AssignedDepth24[sample]=query;_AssignedVisibility24[sample]=visibility;
}
[numthreads(64,1,1)]void AssignedVisibility24(uint3 tid:SV_DispatchThreadID){
 int sample=(int)tid.x;if(sample>=_PhysicalCount24*16)return;float4 q=_AssignedDepth24[sample],v=_AssignedVisibility24[sample];
 if(q.z>0&&q.w>0)v.xy=TraceExternal24(q.xy,q.z,(int)round(q.w));_AssignedVisibility24[sample]=v;
}

[numthreads(8,8,1)]void ComposeRegion113(uint3 tid:SV_DispatchThreadID){
 int2 p=tid.xy;if(any(p>=_ForwardROI102.zw))return;
 float4 c=_CanvasRGBA102.Load(int3(p*4+1,0)),m=_CanvasMeta102.Load(int3(p*4+1,0));float4 owner=m.x>0?float4(4,m.z,m.x,m.y):0;
 float2 centre=float2(_ForwardROI102.x+p.x+.5,272-(_ForwardROI102.y+p.y+.5));int2 cell=(int2)floor(centre-_ForwardAnchor102.xy);
 int chosenPart=0,chosenOwner=0;float faceLo=0,faceHi=0,minDepth=3.402823e38;int valid=0;
 if(all(cell>=0)&&all(cell<_CellsSize113)){int at=cell.y*_CellsSize113.x+cell.x;float4 id=_ReadIdentity96[at],decision=_ReadDecision96[at];
  if(id.x>0&&decision.x>=0){chosenPart=round(id.x)==1?1:round(id.x)==4?2:3;chosenOwner=round(id.y);
   for(int i=0;i<16;i++){int n=(p.y*_ForwardROI102.z+p.x)*16+i;float4 q=_AssignedDepth24[n],v=_AssignedVisibility24[n];
    if(q.z>0&&round(q.w)==chosenOwner&&all(q.xy==Destination24(p,i))){faceLo+=v.x;faceHi+=v.y;minDepth=min(minDepth,q.z);valid++;}}
   if(valid==16&&faceLo>=8){c=_ReadColour96[at];owner=float4(round(id.x)+1,chosenOwner,minDepth,id.w);}
   else{owner.w=valid<16?-116:faceHi>=8?-114:-117;chosenPart=0;}
  }
 }
 _EyeRGBA102[p]=c;_EyeOwner102[p]=owner;float hairLo=0,hairHi=0,best=-1;float4 hc=0,hm=0;
 for(int y=0;y<4;y++)for(int x=0;x<4;x++){int i=y*4+x;float4 h=_HairMeta102.Load(int3(p*4+int2(x,y),0)),v=_HairRGBA102.Load(int3(p*4+int2(x,y),0));if(h.x<=0||h.w<=0||v.a<=0)continue;
  float4 q=_AssignedDepth24[(p.y*_ForwardROI102.z+p.x)*16+i];float weight=saturate(h.w);bool front=chosenPart>0?q.z>0&&h.x<q.z-3e-5:owner.z<=0||h.x<owner.z-3e-5;bool uncertain=chosenPart>0&&q.z<=0;
  if(front){hairLo+=weight;hairHi+=weight;}else if(uncertain)hairHi+=weight;if((front||uncertain)&&weight>best){best=weight;hc=v;hm=h;}
 }
 if(hairLo>=8){c=float4(hc.rgb,1);owner=float4(round(hm.y),round(hm.z),hm.x,0);}else if(hairHi>=8){c=_CanvasRGBA102.Load(int3(p*4+1,0));owner=float4(4,m.z,m.x,-113);}
 int e=(p.y*_ForwardROI102.z+p.x)*2;_Exposure113[e]=float4(faceLo,faceHi,hairLo,hairHi);_Exposure113[e+1]=float4(chosenPart,chosenOwner,valid,owner.w);
 _FinalRGBA102[p]=c;_FinalOwner102[p]=owner;
}
