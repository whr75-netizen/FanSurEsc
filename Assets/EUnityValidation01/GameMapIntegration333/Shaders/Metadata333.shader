Shader "EValidation/GameMap333Metadata"{Properties{_MainTex("Source",2D)="white"{} _Color("Factor",Color)=(1,1,1,1) _Cutoff("Cutoff",Float)=.5 _M_CullMode("Cull",Float)=2 _Auto245Role("Role",Float)=0 _Surface252DefaultPart("Other source part",Float)=0}SubShader{Tags{"RenderPipeline"="UniversalPipeline"}Pass{Cull [_M_CullMode] ZWrite On ZTest LEqual Blend One Zero HLSLPROGRAM
#pragma vertex Vert
#pragma fragment Frag
#pragma multi_compile __ _ALPHATEST_ON _ALPHABLEND_ON
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
sampler2D _MainTex;float4 _MainTex_ST,_Color;float _Cutoff,_Auto245Role,_Surface252DefaultPart,_Surface255Filter;sampler2D _Auto245CreamMember,_Auto245StockMember,_Auto245BodySkinMember;
struct A{float4 positionOS:POSITION;float3 normalOS:NORMAL;float2 uv:TEXCOORD0;float4 info:TEXCOORD3;};struct V{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float depth:TEXCOORD1;float4 info:TEXCOORD2;float3 normal:TEXCOORD3;};
float4 _ClipShift333;V Vert(A a){V v;float3 w=TransformObjectToWorld(a.positionOS.xyz);v.pos=TransformWorldToHClip(w);v.pos.xy+=_ClipShift333.xy*v.pos.w;v.depth=-TransformWorldToView(w).z;v.uv=a.uv*_MainTex_ST.xy+_MainTex_ST.zw;v.info=a.info;v.normal=TransformWorldToViewDir(TransformObjectToWorldNormal(a.normalOS));return v;}
struct O{float4 surface:SV_Target0;float4 smoothNormal:SV_Target1;float4 family:SV_Target2;};O Frag(V v,bool facing:SV_IsFrontFace){float alpha=tex2D(_MainTex,v.uv).a*_Color.a;
#if defined(_ALPHATEST_ON)
clip(alpha-_Cutoff);
#else
clip(alpha-.000001);
#endif
float part=_Surface252DefaultPart>0?_Surface252DefaultPart:v.info.x;if(_Surface255Filter>.5&&_Surface255Filter<1.5&&round(part)!=1)clip(-1);if(_Surface255Filter>1.5&&(round(part)!=2&&round(part)!=3))clip(-1);O o;o.surface=float4(v.depth,_Auto245Role+1,part,_Surface252DefaultPart>0?0:v.info.y>.5?-v.info.z:v.info.z);o.smoothNormal=float4(normalize(v.normal)*(facing?1:-1),1);float family=0;int role=(int)round(_Auto245Role);if(role==10&&tex2D(_Auto245CreamMember,v.uv).r>.5)family=3;if(role==7&&tex2D(_Auto245StockMember,v.uv).r<=.5&&tex2D(_Auto245BodySkinMember,v.uv).r>.5)family=1;o.family=float4(family,role+1,v.depth,alpha);return o;}
ENDHLSL}}}
