Shader "EValidation/VariableSourceStroke46" {
 SubShader {Pass {Cull Off ZWrite Off ZTest Always Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Vert46
 #pragma fragment Frag46
 float4 _Segment46,_RadiiDepth46,_Ink46,_Size46;float _Edge46;
 struct A {float4 vertex:POSITION;};
 struct V {float4 pos:SV_POSITION;};
 V Vert46(A a){V o;o.pos=a.vertex;return o;}
 // Finite feasible source interval extrema for |A+tD-P|^2 <= r(t)^2.
 bool Interval46(float a,float b,float c,out float lo,out float hi){
  lo=0;hi=1;
  if(a==0){if(b==0)return c<=0;float root=-c/b;if(b>0)hi=min(1,root);else lo=max(0,root);return lo<=hi;}
  float disc=b*b-4*a*c;if(disc<0)return a<0;
  float q=sqrt(disc),x=(-b-q)/(2*a),y=(-b+q)/(2*a);float low=min(x,y),high=max(x,y);
  if(a>0){lo=max(0,low);hi=min(1,high);return lo<=hi;}
  bool left=low>=0,right=high<=1;if(!left&&!right)return false;
  lo=left?0:max(0,high);hi=right?1:min(1,low);return lo<=hi;
 }
 struct O {float4 colour:SV_Target0;float4 proof:SV_Target1;};
 O Frag46(V v){
  float2 d=_Segment46.zw-_Segment46.xy,p=_Segment46.xy-v.pos.xy;float dr=_RadiiDepth46.y-_RadiiDepth46.x,lo,hi;
  if(!Interval46(dot(d,d)-dr*dr,2*(dot(p,d)-_RadiiDepth46.x*dr),dot(p,p)-_RadiiDepth46.x*_RadiiDepth46.x,lo,hi))discard;
  float t=_RadiiDepth46.w>=_RadiiDepth46.z?lo:hi;float radius=lerp(_RadiiDepth46.x,_RadiiDepth46.y,t);if(radius<=0)discard;
  O o;o.colour=float4(_Ink46.rgb,1);o.proof=float4(lerp(_RadiiDepth46.z,_RadiiDepth46.w,t),_Edge46,t,radius);return o;
 }
 ENDHLSL
 }}
}
