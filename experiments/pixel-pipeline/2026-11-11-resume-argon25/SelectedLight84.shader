// Read the existing Restore335 selected address; do not re-evaluate lighting.
Shader "EValidation/SelectedLight84" {SubShader{Tags{"RenderPipeline"="UniversalPipeline"}
 Pass{Cull Off ZWrite Off ZTest Always Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex V84
 #pragma fragment F84
 Texture2D<float4> _Before84,_MainMeta84,_World84,_Cell84,_Owner84,_MainUV84,_MainSource84,_Domain84;
 Texture2D<float4> _Map84,_HeadUV84,_HeadMeta84,_Class48084,_Class96084,_Mask48084,_Mask96084,_Meta48084,_Meta96084,_Normal48084,_Normal96084,_UV48084,_UV96084;
 float2 _HeadOrigin84,_Join84,_NativeOrigin84,_Delta84;int _Width84;
 struct V{float4 pos:SV_POSITION;};V V84(uint i:SV_VertexID){V o;o.pos=float4(i==1?3:-1,i==2?3:-1,0,1);return o;}
 float4 F84(V v):SV_Target{
  int2 a=(int2)v.pos.xy;int plane=a.x/_Width84;int2 hp=int2(a.x%_Width84,a.y)+(int2)_HeadOrigin84,mp=hp+(int2)_Join84;
  int2 np=clamp((int2)floor(_NativeOrigin84+(mp+.5+_Delta84)*2),int2(0,0),int2(959,543));
  if(plane==0)return _Before84.Load(int3(np,0));if(plane==1)return _MainMeta84.Load(int3(mp,0));if(plane==2)return _World84.Load(int3(np,0));if(plane==3)return _Cell84.Load(int3(np,0));if(plane==4)return _Owner84.Load(int3(np,0));if(plane==5)return _MainUV84.Load(int3(mp,0));if(plane==6)return _MainSource84.Load(int3(mp,0));if(plane==7)return _Domain84.Load(int3(mp,0));
  float4 map=_Map84.Load(int3(hp,0));bool added=map.r>.5&&map.a>.5;int2 n=added?(int2)round(map.gb):hp;
  bool bounds=all(n>=0)&&all(n<(added?int2(960,544):int2(480,272)));if(!bounds)return float4(-1,-1,-1,-1);
  float4 cls=added?_Class96084.Load(int3(n,0)):_Class48084.Load(int3(n,0));float4 meta=added?_Meta96084.Load(int3(n,0)):_Meta48084.Load(int3(n,0));float4 uv=added?_UV96084.Load(int3(n,0)):_UV48084.Load(int3(n,0));
  if(plane==8)return cls;if(plane==9)return meta;if(plane==10)return added?_Normal96084.Load(int3(n,0)):_Normal48084.Load(int3(n,0));if(plane==11)return uv;
  float4 hu=_HeadUV84.Load(int3(hp,0)),hm=_HeadMeta84.Load(int3(hp,0)),mu=_MainUV84.Load(int3(mp,0)),ms=_MainSource84.Load(int3(mp,0)),domain=_Domain84.Load(int3(mp,0)),owner=_Owner84.Load(int3(np,0)),cell=_Cell84.Load(int3(np,0));
  bool ordinary=domain.x<.5&&cell.z==1&&all(cell.xy==mp)&&all(ms.xyz==owner.zxy);
  // Exact UV/address identity, not a fitted colour/depth tolerance. Keep all raw
  // evidence even if unknown. Metadata/depth equality is reviewed separately.
  bool known=ordinary&&meta.y==4&&all(uv.xy==hu.xy)&&all(hu.xy==mu.xy)&&hu.z==cls.x&&all(ms.yzw==meta.yzw);
  if(plane==12)return float4(n,added?1:0,known?1:0);if(plane==13)return hu;if(plane==14)return hm;
  return added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0));
 }
 ENDHLSL
 }
}}
