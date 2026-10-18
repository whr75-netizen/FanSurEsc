Shader "EValidation/E205AuthoredSurface"{
 Properties{_MainTex("Own semantic palette",2D)="white"{} _Role("Semantic",Float)=4 _EyeOwner("Stable source eye",Float)=2}
 SubShader{Tags{"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"}
 Pass{Name "Eye205Independent" Tags{"LightMode"="Eye205Independent"} Cull Off ZWrite On ZTest LEqual Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Vertex205
 #pragma fragment Fragment205
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 CBUFFER_START(UnityPerMaterial)
 float4 _MainTex_ST;float _Role,_EyeOwner;
 CBUFFER_END
 struct A{float3 positionOS:POSITION;float2 uv:TEXCOORD0;};
 struct V{float4 positionCS:SV_POSITION;float3 world:TEXCOORD0;float2 uv:TEXCOORD1;};
 V Vertex205(A a){V o;o.world=TransformObjectToWorld(a.positionOS);o.positionCS=TransformWorldToHClip(o.world);o.uv=a.uv;return o;}
 struct O{float4 rgba:SV_Target0;float4 meta:SV_Target1;float4 world:SV_Target2;float4 uv:SV_Target3;};
 O Fragment205(V i){O o;float4 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv);o.rgba=float4(c.rgb,1);o.meta=float4(-TransformWorldToView(i.world).z,_Role+1,_EyeOwner,1);o.world=float4(i.world,1);o.uv=float4(i.uv,0,1);return o;}
 ENDHLSL}}}
