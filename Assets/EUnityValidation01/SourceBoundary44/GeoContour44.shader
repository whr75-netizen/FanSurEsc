Shader "EValidation/SourceCurveNearest44" {
 SubShader {Tags{"RenderPipeline"="UniversalPipeline"}
 Pass {Name "SourceCurveNearest44" Cull Off ZWrite On ZTest LEqual Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Vert44
 #pragma fragment Frag44
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 float4x4 _ContourVP40,_ContourView40;float4 _ContourRGB40,_ContourSize44;float _WidthMapEnabled40;
 TEXTURE2D(_WidthMap40);SAMPLER(sampler_WidthMap40);
 struct A {float3 position:POSITION;float2 proof:TEXCOORD0;float3 carrierA:TEXCOORD2;float3 carrierB:TEXCOORD3;float4 uvAB:TEXCOORD4;};
 struct V {float4 pos:SV_POSITION;nointerpolation float edge:TEXCOORD0;nointerpolation float4 ends:TEXCOORD1;nointerpolation float2 depth:TEXCOORD2;nointerpolation float2 device:TEXCOORD3;nointerpolation float2 width:TEXCOORD4;};
 float2 Raster44(float4 clip){float2 p=clip.xy/clip.w;
 #if UNITY_UV_STARTS_AT_TOP
 p.y=-p.y;
 #endif
 return (p*.5+.5)*_ContourSize44.xy;}
 V Vert44(A a){V o;o.pos=mul(_ContourVP40,float4(a.position,1));float4 ca=mul(_ContourVP40,float4(a.carrierA,1)),cb=mul(_ContourVP40,float4(a.carrierB,1));o.edge=a.proof.x;o.ends=float4(Raster44(ca),Raster44(cb));o.depth=float2(-mul(_ContourView40,float4(a.carrierA,1)).z,-mul(_ContourView40,float4(a.carrierB,1)).z);o.device=float2(ca.z/ca.w,cb.z/cb.w);o.width=_WidthMapEnabled40>.5?float2(SAMPLE_TEXTURE2D_LOD(_WidthMap40,sampler_WidthMap40,a.uvAB.xy,0).g,SAMPLE_TEXTURE2D_LOD(_WidthMap40,sampler_WidthMap40,a.uvAB.zw,0).g):float2(1,1);return o;}
 struct O {float4 colour:SV_Target0;float4 proof:SV_Target1;float z:SV_Depth;};
 O Frag44(V v){float2 d=v.ends.zw-v.ends.xy;float den=dot(d,d);if(!isfinite(den)||den<=0)discard;float t=saturate(dot(v.pos.xy-v.ends.xy,d)/den);float width=lerp(v.width.x,v.width.y,t);if(!isfinite(width)||width<=0)discard;O o;o.colour=float4(_ContourRGB40.rgb,1);o.proof=float4(lerp(v.depth.x,v.depth.y,t),v.edge,t,width);o.z=lerp(v.device.x,v.device.y,t);return o;}
 ENDHLSL
 }
 }
}
