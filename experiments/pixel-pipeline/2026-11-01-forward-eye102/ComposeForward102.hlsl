// Source-local eye composition is finished before ANY hair texture is read.
Texture2D<float4> _CanvasRGBA102,_CanvasMeta102,_HairRGBA102,_HairMeta102;
RWTexture2D<float4> _EyeRGBA102,_EyeOwner102,_FinalRGBA102,_FinalOwner102;
int4 _ForwardROI102;float4 _ForwardAnchor102;
[numthreads(8,8,1)]void ComposeForward102(uint3 tid:SV_DispatchThreadID){
 int2 p=(int2)tid.xy;if(any(p>=_ForwardROI102.zw))return;
 int2 sample=p*4+1;float4 c=_CanvasRGBA102.Load(int3(sample,0)),m=_CanvasMeta102.Load(int3(sample,0));
 float4 owner=m.x>0?float4(4,m.z,m.x,m.y):0;
 float2 absolute=float2(_ForwardROI102.x+p.x+.5,272-(_ForwardROI102.y+p.y+.5));int2 cell=(int2)floor(absolute-_ForwardAnchor102.xy),size=_Size96>>2;
 if(all(cell>=0)&&all(cell<size)){int at=cell.y*size.x+cell.x;float4 id=_ReadIdentity96[at],decision=_ReadDecision96[at];
  if(id.x>0&&decision.x>=0){c=_ReadColour96[at];owner=float4(id.x+1,id.y,id.z,id.w);}
 }
 _EyeRGBA102[p]=c;_EyeOwner102[p]=owner;
 // Hard visible choice. No lerp, screen-space history or eye-budget feedback.
 float coverage=0,best=-1;float4 hc=0,hm=0;
 [unroll]for(int y=0;y<4;y++)[unroll]for(int x=0;x<4;x++){
  int2 s=p*4+int2(x,y);float4 h=_HairMeta102.Load(int3(s,0)),v=_HairRGBA102.Load(int3(s,0));
  if(h.x>0&&h.w>0&&v.a>0&&(owner.z<=0||h.x<owner.z-3e-5)){
   float weight=saturate(h.w);coverage+=weight;if(weight>best){best=weight;hc=v;hm=h;}
  }
 }
 if(coverage>=8){c=float4(hc.rgb,1);owner=float4(round(hm.y),round(hm.z),hm.x,0);}
 _FinalRGBA102[p]=c;_FinalOwner102[p]=owner;
}
