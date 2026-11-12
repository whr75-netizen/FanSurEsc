Shader "EValidation/FeatureCurve81" {
 Properties {_DepthCompare81("Depth compare",Float)=7}
 SubShader {Tags{"RenderPipeline"="UniversalPipeline"}
 Pass {Name "CurrentSourceCurve" Cull Off ZWrite On ZTest [_DepthCompare81] Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Vert81
 #pragma fragment Frag81
 float4x4 _ContourVP40,_OriginalVP81,_ContourView40;
 float4 _ContourRGB40,_QROI81,_ContourSize44;float _UVStartsAtTop81;
 Texture2D<float4> _WidthMap40;SamplerState sampler_WidthMap40;
 // Reuse44's canonical endpoint payload and nearest valid carrier calculation.
 struct A{float3 position:POSITION;float2 proof:TEXCOORD0;float3 carrierA:TEXCOORD2;float3 carrierB:TEXCOORD3;float4 uvAB:TEXCOORD4;float2 incident:TEXCOORD5;};
 struct V{float4 pos:SV_POSITION;nointerpolation float edge:TEXCOORD0;nointerpolation float4 ends:TEXCOORD1;nointerpolation float2 depths:TEXCOORD2;nointerpolation float2 device:TEXCOORD3;nointerpolation float2 width:TEXCOORD4;nointerpolation float4 sourceEnds:TEXCOORD5;nointerpolation float2 incident:TEXCOORD6;};
 float2 Raster81(float4 clip){float2 p=clip.xy/clip.w;if(_UVStartsAtTop81>.5)p.y=-p.y;return(p*.5+.5)*_ContourSize44.xy;}
 V Vert81(A a){V o;o.pos=mul(_ContourVP40,float4(a.position,1));float4 ca=mul(_ContourVP40,float4(a.carrierA,1)),cb=mul(_ContourVP40,float4(a.carrierB,1)),oa=mul(_OriginalVP81,float4(a.carrierA,1)),ob=mul(_OriginalVP81,float4(a.carrierB,1));o.edge=a.proof.x;o.ends=float4(Raster81(ca),Raster81(cb));o.depths=float2(-mul(_ContourView40,float4(a.carrierA,1)).z,-mul(_ContourView40,float4(a.carrierB,1)).z);o.device=float2(ca.z/ca.w,cb.z/cb.w);o.width=float2(_WidthMap40.SampleLevel(sampler_WidthMap40,a.uvAB.xy,0).g,_WidthMap40.SampleLevel(sampler_WidthMap40,a.uvAB.zw,0).g);o.sourceEnds=float4(_QROI81.xy+(oa.xy/oa.w+1)*_QROI81.zw*.5,_QROI81.xy+(ob.xy/ob.w+1)*_QROI81.zw*.5);o.incident=a.incident;return o;}
 struct O{float4 colour:SV_Target0;float4 proof:SV_Target1;float4 projection:SV_Target2;float depth:SV_Depth;};
 O Frag81(V v){float2 d=v.ends.zw-v.ends.xy;float den=dot(d,d);if(!isfinite(den)||den<=0)discard;float t=saturate(dot(v.pos.xy-v.ends.xy,d)/den);float g=lerp(v.width.x,v.width.y,t),z=lerp(v.depths.x,v.depths.y,t);if(!isfinite(g)||g<=0||!isfinite(z)||z<=0)discard;O o;o.colour=float4(_ContourRGB40.rgb,1);o.proof=float4(z,v.edge,t,g);o.projection=float4(lerp(v.sourceEnds.xy,v.sourceEnds.zw,t),v.incident);o.depth=lerp(v.device.x,v.device.y,t);return o;}
 ENDHLSL
 }
 Pass {Name "CurrentSampleExterior" Cull Off ZWrite Off ZTest Always Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Full81
 #pragma fragment Compose81
 Texture2D<float4> _NativeBefore81,_CurveColour81,_CurveProof81,_CurveProjection81,_NativeCell81,_NativeOwner81,_NativeWorld81,_MainMeta81,_SelectedSource81,_Domain81;
 float2 _NativeOrigin81,_Delta81,_HeadOrigin81,_Join81;int _Role81,_Triangles81,_TraceMode81;float _DepthOffset81;
 struct V{float4 pos:SV_POSITION;};
 V Full81(uint id:SV_VertexID){V o;o.pos=float4(id==1?3:-1,id==2?3:-1,0,1);return o;}
 int2 Native81(float2 q){return clamp((int2)floor(_NativeOrigin81+(q+.5+_Delta81)*2),int2(0,0),int2(959,543));}
 struct O{float4 colour:SV_Target0;float4 receipt:SV_Target1;};
 O Compose81(V v){int2 p=(int2)v.pos.xy,q=p+(int2)_HeadOrigin81+(int2)_Join81,np=Native81(q);O o;o.colour=_NativeBefore81.Load(int3(np,0));o.receipt=0;float4 line81=_CurveColour81.Load(int3(p,0)),proof=_CurveProof81.Load(int3(p,0)),projection=_CurveProjection81.Load(int3(p,0)),cell=_NativeCell81.Load(int3(np,0)),world=_NativeWorld81.Load(int3(np,0)),meta=_MainMeta81.Load(int3(q,0));
 if(any(q<0)||any(q>=int2(480,272))||line81.a!=1||proof.x<=0||!all(isfinite(proof))||!all(isfinite(projection))||any(cell.xy!=q))return o;
 // Current native samples establish source eligibility. This is not an exact
 // alpha/coverage query over an entire displaced cell footprint.
 float2 src=float2(projection.x-.5,272-projection.y-.5)+_Join81;int2 sq=(int2)floor(src+.5);if(any(sq<0)||any(sq>=int2(480,272)))return o;int2 sn=Native81(src);float4 sc=_NativeCell81.Load(int3(sn,0)),so=_NativeOwner81.Load(int3(sn,0)),selected=_SelectedSource81.Load(int3(sq,0)),domain=_Domain81.Load(int3(sq,0));
 if(_TraceMode81==1){o.colour=sc;o.receipt=so;return o;}if(_TraceMode81==2){o.colour=selected;o.receipt=domain;return o;}
 bool source=all(sc.xy==sq)&&sc.z==1&&so.x==_Role81&&domain.x<.5&&selected.x==so.z&&selected.y==so.x&&selected.z==so.y&&selected.w>=1&&selected.w<=_Triangles81&&(selected.w==projection.z||selected.w==projection.w);
 float z=proof.x+_DepthOffset81;bool depth=world.x>0&&z<=world.x+.0001&&(meta.x<=0||z<=meta.x+.0001);bool target=cell.z!=1;o.receipt=float4(source?1:0,depth?1:0,target?1:0,0);if(source&&depth&&target){o.colour=line81;o.receipt.w=1;}return o;
 }
 ENDHLSL
 }
 }
}
