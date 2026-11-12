Shader "EValidation/JointRibbon97" {
 SubShader {Tags{"RenderPipeline"="UniversalPipeline"}
 Pass {Name "SamePointJointSourceDestination" Cull Off ZWrite Off ZTest Always Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Full97
 #pragma fragment Compose97
 Texture2D<float4> _Base97,_Control97,_ControlReceipt97,_Proof97,_Cell97,_World97;
 int _Width97;float2 _NativeOrigin97,_Delta97,_HeadOrigin97,_Join97;float _DepthOffset97;float4 _Ink97;
 struct V{float4 pos:SV_POSITION;};V Full97(uint id:SV_VertexID){V o;o.pos=float4(id==1?3:-1,id==2?3:-1,0,1);return o;}
 struct O{float4 colour:SV_Target0;float4 receipt:SV_Target1;};
 O Compose97(V v){int2 p=(int2)v.pos.xy;float4 proof=_Proof97.Load(int3(p,0)),area=_Proof97.Load(int3(p+int2(_Width97,0),0));O o;o.colour=_Base97.Load(int3(p+int2(19*_Width97,0),0));o.receipt=float4(proof.x,area.x,area.y,0);float4 controlReceipt=_ControlReceipt97.Load(int3(p,0));
  // Unknown is explicit and retains the exact control appearance. It is
  // neither transparency nor evidence of a correct source/opacity decision.
  if(proof.x==3||(proof.x==0&&controlReceipt.w==1)){o.colour=_Control97.Load(int3(p,0));o.receipt.x=3;o.receipt.w=controlReceipt.w==1?-1:0;return o;}
  if(proof.x!=1)return o;
  int2 q=p+(int2)_HeadOrigin97+(int2)_Join97,np=clamp((int2)floor(_NativeOrigin97+(q+.5+_Delta97)*2),int2(0,0),int2(959,543));float4 cell=_Cell97.Load(int3(np,0)),world=_World97.Load(int3(np,0));float z=proof.w+_DepthOffset97;
  // Keep the existing world representative-sample gate separate. No claim
  // that this single world sample proves continuous destination coverage.
  if(any(q<0)||any(q>=int2(480,272))||any(cell.xy!=q)||world.x<=0||z>world.x+.0001||cell.z==1)return o;
  o.colour=float4(_Ink97.rgb,1);o.receipt.w=1;return o;
 }
 ENDHLSL
 }
 }
}
