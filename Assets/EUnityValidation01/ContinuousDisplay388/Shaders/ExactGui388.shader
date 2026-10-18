Shader "EValidation/ExactGuiPayload388"{Properties{_MainTex("Original sRGB bytes",2D)="white"{}}SubShader{Pass{ZTest Always ZWrite Off Cull Off Blend Off ColorMask RGBA HLSLPROGRAM
#pragma vertex vert
#pragma fragment frag
#include "UnityCG.cginc"
sampler2D _MainTex;
struct A{float4 p:POSITION;float2 uv:TEXCOORD0;};struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;};
V vert(A a){V v;v.p=UnityObjectToClipPos(a.p);v.uv=a.uv;return v;}
float4 frag(V v):SV_Target{float4 c=tex2D(_MainTex,v.uv);float3 x=max(c.rgb,0);float3 lo=12.92*x;float3 hi=1.055*pow(x,1.0/2.4)-.055;c.rgb=float3(x.r<=.0031308?lo.r:hi.r,x.g<=.0031308?lo.g:hi.g,x.b<=.0031308?lo.b:hi.b);return c;}
ENDHLSL}}}
