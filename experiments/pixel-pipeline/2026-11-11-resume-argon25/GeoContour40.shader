Shader "EValidation/SourceGeometryContour40" {
 SubShader {Tags{"RenderPipeline"="UniversalPipeline"}
 Pass {Name "NativeGeometryContour40" Cull Off ZWrite On ZTest LEqual Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Vert40
 #pragma fragment Frag40
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 float4x4 _ContourVP40,_ContourView40;float4 _ContourRGB40;
 struct A {float3 position:POSITION;float2 proof:TEXCOORD0;};
 struct V {float4 pos:SV_POSITION;float2 proof:TEXCOORD0;float depth:TEXCOORD1;};
 V Vert40(A a){V o;o.pos=mul(_ContourVP40,float4(a.position,1));o.proof=a.proof;o.depth=-mul(_ContourView40,float4(a.position,1)).z;return o;}
 struct O {float4 colour:SV_Target0;float4 proof:SV_Target1;};
 O Frag40(V v){O o;o.colour=float4(_ContourRGB40.rgb,1);o.proof=float4(v.depth,v.proof.x,v.proof.y,1);return o;}
 ENDHLSL
 }
 }
}
