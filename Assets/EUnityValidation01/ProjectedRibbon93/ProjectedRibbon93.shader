Shader "EValidation/ProjectedRibbon93" {
 Properties {_DepthCompare81("Depth compare",Float)=4}
 SubShader {Tags{"RenderPipeline"="UniversalPipeline"}
 Pass {Name "NativeProjectedRibbon" Cull Off ZWrite On ZTest [_DepthCompare81] Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Vert93
 #pragma fragment Frag93
 float4x4 _ContourVP40,_OriginalVP81,_ContourView40;float4 _ContourRGB40,_QROI81,_ContourSize44;float _UVStartsAtTop81,_WidthMetres93,_ParameterWidth93;
 Texture2D<float4> _WidthMap40;SamplerState sampler_WidthMap40;
 struct A{float3 position:POSITION;float3 cornerEdge:TEXCOORD0;float3 a:TEXCOORD2;float3 b:TEXCOORD3;float4 uv:TEXCOORD4;float2 incident:TEXCOORD5;float3 na:TEXCOORD6;float3 nb:TEXCOORD7;};
 struct V{float4 pos:SV_POSITION;nointerpolation float4 ab:TEXCOORD0;nointerpolation float4 expanded:TEXCOORD1;nointerpolation float4 z:TEXCOORD2;nointerpolation float4 device:TEXCOORD3;nointerpolation float4 sourceEnds:TEXCOORD4;nointerpolation float4 edgeGreen:TEXCOORD5;nointerpolation float2 incident:TEXCOORD6;};
 float2 Raster93(float4 clip){float2 p=clip.xy/clip.w;if(_UVStartsAtTop81>.5)p.y=-p.y;return(p*.5+.5)*_ContourSize44.xy;}
 V Vert93(A a){V o;float ga=_ParameterWidth93>.5?_WidthMap40.SampleLevel(sampler_WidthMap40,a.uv.xy,0).g:1,gb=_ParameterWidth93>.5?_WidthMap40.SampleLevel(sampler_WidthMap40,a.uv.zw,0).g:1;float3 ea=a.a+a.na*(_WidthMetres93*ga),eb=a.b+a.nb*(_WidthMetres93*gb);float4 ca=mul(_ContourVP40,float4(a.a,1)),cb=mul(_ContourVP40,float4(a.b,1)),xa=mul(_ContourVP40,float4(ea,1)),xb=mul(_ContourVP40,float4(eb,1)),oa=mul(_OriginalVP81,float4(a.a,1)),ob=mul(_OriginalVP81,float4(a.b,1));o.ab=float4(Raster93(ca),Raster93(cb));o.expanded=float4(Raster93(xa),Raster93(xb));o.z=-float4(mul(_ContourView40,float4(a.a,1)).z,mul(_ContourView40,float4(a.b,1)).z,mul(_ContourView40,float4(ea,1)).z,mul(_ContourView40,float4(eb,1)).z);o.device=float4(ca.z/ca.w,cb.z/cb.w,xa.z/xa.w,xb.z/xb.w);float2 lo=min(min(o.ab.xy,o.ab.zw),min(o.expanded.xy,o.expanded.zw))-.5,hi=max(max(o.ab.xy,o.ab.zw),max(o.expanded.xy,o.expanded.zw))+.5;float2 pixel=lerp(lo,hi,a.cornerEdge.xy);float2 ndc=pixel/_ContourSize44.xy*2-1;if(_UVStartsAtTop81>.5)ndc.y=-ndc.y;o.pos=float4(ndc,ca.z/ca.w,1);o.sourceEnds=float4(_QROI81.xy+(oa.xy/oa.w+1)*_QROI81.zw*.5,_QROI81.xy+(ob.xy/ob.w+1)*_QROI81.zw*.5);o.edgeGreen=float4(a.cornerEdge.z,ga,gb,_WidthMetres93);o.incident=a.incident;return o;}
 // Strict triangle/square separating axes reject boundary-only contact.
 // A witness is an actual ribbon point; it is not a full-pixel occlusion proof.
 bool AxisOutside93(float2 axis,float2 a,float2 b,float2 c){float r=.5*(abs(axis.x)+abs(axis.y));float x=dot(axis,a),y=dot(axis,b),z=dot(axis,c);return min(x,min(y,z))>=r||max(x,max(y,z))<=-r;}
 bool ClipSegment93(float2 a,float2 b,out float2 witness){float lo=0,hi=1;float2 d=b-a;witness=0;if(d.x==0){if(abs(a.x)>.5)return false;}else{float t0=(-.5-a.x)/d.x,t1=(.5-a.x)/d.x;lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1));}if(d.y==0){if(abs(a.y)>.5)return false;}else{float t0=(-.5-a.y)/d.y,t1=(.5-a.y)/d.y;lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1));}if(lo>=hi)return false;witness=a+d*((lo+hi)*.5);return true;}
 bool Witness93(float2 a,float2 b,float2 c,float3 z,float3 device,float3 sourceT,out float4 witness,out float2 extra){witness=0;extra=0;float2 ab=b-a,ac=c-a;float det=ab.x*ac.y-ab.y*ac.x;if(det==0)return false;if(min(a.x,min(b.x,c.x))>=.5||max(a.x,max(b.x,c.x))<=-.5||min(a.y,min(b.y,c.y))>=.5||max(a.y,max(b.y,c.y))<=-.5)return false;float2 bc=c-b,ca=a-c;if(AxisOutside93(float2(-ab.y,ab.x),a,b,c)||AxisOutside93(float2(-bc.y,bc.x),a,b,c)||AxisOutside93(float2(-ca.y,ca.x),a,b,c))return false;
 float2 p=(a+b+c)/3;float u=0,v=0;if(any(abs(p)>.5)){float2 d=-a;u=(d.x*ac.y-d.y*ac.x)/det;v=(ab.x*d.y-ab.y*d.x)/det;if(u>=0&&v>=0&&u+v<=1)p=0;else{float2 trial=0;bool found=ClipSegment93(a,b,trial);if(found)p=trial;if(!found){found=ClipSegment93(b,c,trial);if(found)p=trial;}if(!found){found=ClipSegment93(c,a,trial);if(found)p=trial;}if(!found)return false;}}
 float2 d=p-a;u=(d.x*ac.y-d.y*ac.x)/det;v=(ab.x*d.y-ab.y*d.x)/det;float3 w=float3(1-u-v,u,v);witness=float4(dot(w,z),dot(w,sourceT),dot(w,device),abs(det)*.5);extra=p;return all(isfinite(witness));}
 struct O{float4 colour:SV_Target0;float4 proof:SV_Target1;float4 projection:SV_Target2;float4 footprint:SV_Target3;float depth:SV_Depth;};
 O Frag93(V v){float2 centre=v.pos.xy;float4 one,two;float2 p1,p2;bool yes1=Witness93(v.ab.xy-centre,v.ab.zw-centre,v.expanded.zw-centre,v.z.xyw,v.device.xyw,float3(0,1,1),one,p1);bool yes2=Witness93(v.ab.xy-centre,v.expanded.zw-centre,v.expanded.xy-centre,v.z.xwz,v.device.xwz,float3(0,1,0),two,p2);if(!yes1&&!yes2)discard;bool first=yes1&&(!yes2||one.x<=two.x);float4 w=first?one:two;float2 p=first?p1:p2;float g=lerp(v.edgeGreen.y,v.edgeGreen.z,w.y);if(v.edgeGreen.w<=0||g<=0||w.x<=0||w.y<0||w.y>1)discard;O o;o.colour=float4(_ContourRGB40.rgb,1);o.proof=float4(w.x,v.edgeGreen.x,w.y,g);o.projection=float4(lerp(v.sourceEnds.xy,v.sourceEnds.zw,w.y),v.incident);o.footprint=float4(w.w,p,first?0:1);o.depth=w.z;return o;}
 ENDHLSL
 }
 Pass {Name "CurrentExteriorComposite" Cull Off ZWrite Off ZTest Always Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex Full93
 #pragma fragment Compose93
 Texture2D<float4> _BaseAtlas93,_CurveColour81,_CurveProof81,_CurveProjection81,_NativeCell81,_NativeWorld81,_MainMeta81;
 float2 _NativeOrigin81,_Delta81,_HeadOrigin81,_Join81;int _Triangles81,_Width93;float _DepthOffset81;
 struct V{float4 pos:SV_POSITION;};V Full93(uint id:SV_VertexID){V o;o.pos=float4(id==1?3:-1,id==2?3:-1,0,1);return o;}
 int2 Native93(float2 q){return clamp((int2)floor(_NativeOrigin81+(q+.5+_Delta81)*2),int2(0,0),int2(959,543));}
 struct O{float4 colour:SV_Target0;float4 receipt:SV_Target1;};
 O Compose93(V v){int2 p=(int2)v.pos.xy,q=p+(int2)_HeadOrigin81+(int2)_Join81,np=Native93(q);O o;o.colour=_BaseAtlas93.Load(int3(p+int2(19*_Width93,0),0));o.receipt=0;float4 stroke93=_CurveColour81.Load(int3(p,0)),proof=_CurveProof81.Load(int3(p,0)),projection=_CurveProjection81.Load(int3(p,0)),cell=_NativeCell81.Load(int3(np,0)),world=_NativeWorld81.Load(int3(np,0)),meta=_MainMeta81.Load(int3(q,0));if(any(q<0)||any(q>=int2(480,272))||stroke93.a!=1||proof.x<=0||!all(isfinite(proof))||!all(isfinite(projection))||any(cell.xy!=q))return o;
 // Current native mesh/alpha depth raster above is source visibility at its
 // samples. This final representative sample remains explicitly separate from
 // a whole displaced-pixel alpha/coverage proof.
 bool source=projection.z>=1&&projection.w>=1&&projection.z<=_Triangles81&&projection.w<=_Triangles81;float z=proof.x+_DepthOffset81;bool depth=world.x>0&&z<=world.x+.0001&&(meta.x<=0||z<=meta.x+.0001);bool target=cell.z!=1;o.receipt=float4(source?1:0,depth?1:0,target?1:0,0);if(source&&depth&&target){o.colour=stroke93;o.receipt.w=1;}return o;}
 ENDHLSL
 }
 }
}
