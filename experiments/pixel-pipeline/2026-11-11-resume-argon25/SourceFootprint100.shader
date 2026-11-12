// Read-only reason receipt in previously zero packet padding. No new selection.
Shader "EValidation/SourceFootprint100" {SubShader{Tags{"RenderPipeline"="UniversalPipeline"}
Pass{Cull Off ZWrite Off ZTest Always Blend One Zero
HLSLPROGRAM
#pragma target 4.5
#pragma vertex Full96
#pragma fragment Read96
Texture2D<float4> _RawWorld95,_Atlas95,_LineProof95,_LineProjection95,_LineFootprint95,_LineFinal95,_LineReceipt95,_NativeCell96,_JointFinal97,_JointReceipt97,_CoupledFinal98,_CoupledReceipt98;
Texture2D<float4> _MainUV100,_MainSource100,_MainDomain100,_Owner100;
Texture2D<float> _RawDepth95;
int _Width95,_Role100;float2 _HeadOrigin95,_Join95,_NativeOrigin95,_Delta95;float4 _NearFar95;
struct V{float4 pos:SV_POSITION;};V Full96(uint i:SV_VertexID){V o;o.pos=float4(i==1?3:-1,i==2?3:-1,0,1);return o;}
float4 Read96(V v):SV_Target{
 int index=(int)v.pos.x+(int)v.pos.y*(24*_Width95);int size=2*_Width95+1,count=size*size;
 int2 start=(int2)floor(_NativeOrigin95+2*(_HeadOrigin95+_Join95+_Delta95));
 if(index<count){int2 p=start+int2(index%size,index/size);return _RawWorld95.Load(int3(p,0));}
 if(index<2*count){int i=index-count;int2 p=start+int2(i%size,i/size);float d=_RawDepth95.Load(int3(p,0));return float4(lerp(_NearFar95.x,_NearFar95.y,_NearFar95.z>.5?1-d:d),d,p);}
 index-=2*count;int plane=index/(_Width95*_Width95);int at=index%(_Width95*_Width95);int2 p=int2(at%_Width95,at/_Width95);
 if(plane==0)return _Atlas95.Load(int3(p+int2(9*_Width95,0),0));
 if(plane==1)return _Atlas95.Load(int3(p+int2(11*_Width95,0),0));
 if(plane==2)return _Atlas95.Load(int3(p+int2(8*_Width95,0),0));
 if(plane==3)return _JointReceipt97.Load(int3(p,0));
 if(plane==4)return _Atlas95.Load(int3(p+int2(20*_Width95,0),0));
 if(plane==5)return _Atlas95.Load(int3(p+int2(19*_Width95,0),0));
 if(plane==6)return _LineProof95.Load(int3(p,0));
 if(plane==7)return _CoupledFinal98.Load(int3(p,0));
 if(plane==8)return _CoupledReceipt98.Load(int3(p,0));
 if(plane==9)return _LineFinal95.Load(int3(p,0));
 if(plane==10)return _LineReceipt95.Load(int3(p,0));
 if(plane==11)return _Atlas95.Load(int3(p,0));
 if(plane==12)return _JointFinal97.Load(int3(p,0));
 int2 q=p+(int2)(_HeadOrigin95+_Join95),np=(int2)floor(_NativeOrigin95+2*(q+.5+_Delta95));
 if(plane==13)return _NativeCell96.Load(int3(np,0));
 if(plane==14){
  float4 cls=_Atlas95.Load(int3(p+int2(8*_Width95,0),0)),meta=_Atlas95.Load(int3(p+int2(9*_Width95,0),0)),uv=_Atlas95.Load(int3(p+int2(11*_Width95,0),0)),hu=_Atlas95.Load(int3(p+int2(13*_Width95,0),0));
  float4 domain=_MainDomain100.Load(int3(q,0)),cell=_NativeCell96.Load(int3(np,0)),owner=_Owner100.Load(int3(np,0)),ms=_MainSource100.Load(int3(q,0)),mu=_MainUV100.Load(int3(q,0));
  uint flags=0;
  if(!(domain.x<.5))flags|=1;
  if(cell.z!=1)flags|=2;
  if(any(cell.xy!=q))flags|=4;
  if(any(ms.xyz!=owner.zxy))flags|=8;
  if(meta.y!=_Role100)flags|=16;
  if(any(uv.xy!=hu.xy))flags|=32;
  if(any(hu.xy!=mu.xy))flags|=64;
  if(hu.z!=cls.x)flags|=128;
  if(any(ms.yzw!=meta.yzw))flags|=256;
  float4 map=_Atlas95.Load(int3(p+int2(12*_Width95,0),0)),history=_Atlas95.Load(int3(p+int2(16*_Width95,0),0));
  return float4(flags,domain.x,map.w,history.w);
 }
 return 0;
}
ENDHLSL
}}}
