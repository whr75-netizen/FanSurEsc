// Observation only: read pre-Present native rasters, not its replicated output.
Shader "EValidation/SourceFootprint95" { SubShader { Tags {"RenderPipeline"="UniversalPipeline"}
Pass {Cull Off ZWrite Off ZTest Always Blend One Zero
HLSLPROGRAM
#pragma target 4.5
#pragma vertex Full95
#pragma fragment Read95
Texture2D<float4> _RawWorld95,_RawMeta95,_RawUV95,_Atlas95;
Texture2D<float> _RawDepth95;
Texture2D<float4> _LineProof95,_LineProjection95,_LineFootprint95,_LineFinal95,_LineReceipt95;
int _Width95;float2 _HeadOrigin95,_Join95,_NativeOrigin95,_Delta95;float4 _NearFar95;
struct V {float4 pos:SV_POSITION;};
V Full95(uint i:SV_VertexID){V o;o.pos=float4(i==1?3:-1,i==2?3:-1,0,1);return o;}
float4 Read95(V v):SV_Target {
 int2 a=(int2)v.pos.xy;int plane=a.x/_Width95;int2 local=int2(a.x%_Width95,a.y);
 int2 hp=local+(int2)_HeadOrigin95;int sample=plane%4;int2 corner=int2(sample&1,sample>>1);
 // Exactly two native pixel centres in the half-open two-pixel-wide footprint.
 // No clamp: the external producer rejects out-of-bounds ROIs before submit.
 int2 np=(int2)ceil(_NativeOrigin95+2*(hp+_Join95+_Delta95)-.5)+corner;
 int2 rawHead=2*hp+corner;
 if(plane<4)return _RawWorld95.Load(int3(np,0));
 if(plane<8){float d=_RawDepth95.Load(int3(np,0));float z=lerp(_NearFar95.x,_NearFar95.y,_NearFar95.z>.5?1-d:d);return float4(z,d,np);}
 if(plane<12)return _RawMeta95.Load(int3(rawHead,0));
 if(plane<16)return _RawUV95.Load(int3(rawHead,0));
 if(plane==16){int2 p=(int2)floor(_NativeOrigin95+2*(hp+_Join95+.5+_Delta95));return float4(p,local);}
 if(plane==17)return _Atlas95.Load(int3(local+int2(20*_Width95,0),0));
 if(plane==18)return _Atlas95.Load(int3(local+int2(19*_Width95,0),0));
 if(plane==19)return _LineProof95.Load(int3(local,0));
 if(plane==20)return _LineProjection95.Load(int3(local,0));
 if(plane==21)return _LineFootprint95.Load(int3(local,0));
 if(plane==22)return _LineFinal95.Load(int3(local,0));
 return _LineReceipt95.Load(int3(local,0));
}
ENDHLSL
}}}
