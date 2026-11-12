Shader "EValidation/CoupledRibbon98B" {
 SubShader {Tags{"RenderPipeline"="UniversalPipeline"}
 Pass {Name "SameFeatureCellRedundancy" Cull Off ZWrite Off ZTest Always Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Full98
 #pragma fragment Compose98
 Texture2D<float4> _Base98,_Control98,_Receipt98,_Proof98,_Cell98,_World98;
 int _Width98;float2 _NativeOrigin98,_Delta98,_HeadOrigin98,_Join98;float _DepthOffset98;
 struct V{float4 pos:SV_POSITION;};V Full98(uint id:SV_VertexID){V o;o.pos=float4(id==1?3:-1,id==2?3:-1,0,1);return o;}
 bool Realized98(int2 p){if(any(p<0)||any(p>=_Width98))return false;float4 proof=_Proof98.Load(int3(p,0));if(proof.z!=1||proof.x!=0||_Receipt98.Load(int3(p,0)).w!=1)return false;
  int2 q=p+(int2)_HeadOrigin98+(int2)_Join98,np=clamp((int2)floor(_NativeOrigin98+(q+.5+_Delta98)*2),int2(0,0),int2(959,543));float4 cell=_Cell98.Load(int3(np,0)),world=_World98.Load(int3(np,0));return !any(q<0)&&!any(q>=int2(480,272))&&all(cell.xy==q)&&world.x>0&&proof.y+_DepthOffset98<=world.x+.0001&&cell.z!=1;
 }
 struct O{float4 colour:SV_Target0;float4 receipt:SV_Target1;};
 O Compose98(V v){int2 p=(int2)v.pos.xy;float4 proof=_Proof98.Load(int3(p,0)),control=_Receipt98.Load(int3(p,0));uint mask=(uint)proof.x;O o;o.colour=_Control98.Load(int3(p,0));o.receipt=float4(control.x,proof.x,proof.z,control.w);
  // A partially visible fragment is not occluded. Only redundant integer
  // representation can be removed. One common representative must exist.
  if(mask==0||control.x!=1||control.w!=1)return o;
  bool present=((mask&1)!=0&&Realized98(p+int2(-1,-1)))||((mask&2)!=0&&Realized98(p+int2(0,-1)))||((mask&4)!=0&&Realized98(p+int2(1,-1)))||((mask&8)!=0&&Realized98(p+int2(-1,0)))||((mask&32)!=0&&Realized98(p+int2(1,0)))||((mask&64)!=0&&Realized98(p+int2(-1,1)))||((mask&128)!=0&&Realized98(p+int2(0,1)))||((mask&256)!=0&&Realized98(p+int2(1,1)));if(!present)return o;
  o.colour=_Base98.Load(int3(p+int2(19*_Width98,0),0));o.receipt.w=2;return o;
 }
 ENDHLSL
 }
 }
}
