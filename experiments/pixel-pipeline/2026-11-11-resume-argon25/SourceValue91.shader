// Read the existing Restore335 selected address; do not re-evaluate lighting.
Shader "EValidation/SourceValue91" {SubShader{Tags{"RenderPipeline"="UniversalPipeline"}
 Pass{Cull Off ZWrite Off ZTest Always Blend One Zero
 HLSLPROGRAM
 #pragma target 4.5
 #pragma vertex V84
 #pragma fragment F84
 Texture2D<float4> _Before84,_MainMeta84,_World84,_Cell84,_Owner84,_MainUV84,_MainSource84,_Domain84;
 Texture2D<float4> _Map84,_HeadUV84,_HeadMeta84,_Class48084,_Class96084,_Mask48084,_Mask96084,_Meta48084,_Meta96084,_Normal48084,_Normal96084,_UV48084,_UV96084;
 float2 _HeadOrigin84,_Join84,_NativeOrigin84,_Delta84;int _Width84;
 struct V{float4 pos:SV_POSITION;};V V84(uint i:SV_VertexID){V o;o.pos=float4(i==1?3:-1,i==2?3:-1,0,1);return o;}

 int _Role89;Texture2D<float4> _PreviousAtlas85,_PreviousProjection85;float2 _PreviousOrigin85;int _History85,_PreviousWidth85,_PreviousCount85,_Levels85;
 float4 Candidate85(int2 hp,float4 cls,float4 meta,float4 uv,float4 hu,float4 hm){
  bool valid=meta.y==_Role89&&cls.a>.5&&all(meta==hm)&&all(uv.xy==hu.xy)&&hu.z==cls.x;float4 result=float4(cls.x,cls.x,0,valid?1:0);
  if(!valid||_History85!=1)return result;int primitive=(int)meta.w-1;if(primitive<0||primitive>=_PreviousCount85)return result;
  uint i=3u*(uint)primitive;float4 a=_PreviousProjection85.Load(int3(i&127u,i>>7u,0));i++;float4 b=_PreviousProjection85.Load(int3(i&127u,i>>7u,0));i++;float4 c=_PreviousProjection85.Load(int3(i&127u,i>>7u,0));float2 ab=b.xy-a.xy,ac=c.xy-a.xy,d=uv.xy-a.xy;float det=ab.x*ac.y-ab.y*ac.x;if(det==0||!isfinite(det))return result;float u=(d.x*ac.y-d.y*ac.x)/det,v=(ab.x*d.y-ab.y*d.x)/det;float3 bary=float3(1-u-v,u,v);if(any(bary<0)||any(bary>1))return result;
  float2 before=bary.x*a.zw+bary.y*b.zw+bary.z*c.zw;before.y=272-before.y;if(!all(isfinite(before)))return result;float2 f=frac(before);float uncertainty=32*1.1920928955078125e-7*(1+max(abs(before.x),abs(before.y)));if(any(min(f,1-f)<=uncertainty))return result;
  int2 p=(int2)floor(before)-(int2)_PreviousOrigin85;if(any(p<0)||any(p>=_PreviousWidth85))return result;float4 oldMeta=_PreviousAtlas85.Load(int3(p+int2(9*_PreviousWidth85,0),0)),oldQ=_PreviousAtlas85.Load(int3(p+int2(16*_PreviousWidth85,0),0));if(oldQ.w!=1||any(oldMeta.yzw!=meta.yzw))return result;
  result.y=oldQ.x;float step=1.0/(_Levels85-1),cut=(cls.x+oldQ.x)*.5;bool use=abs(abs(oldQ.x-cls.x)-step)<=1e-6&&abs(cls.y-cut)<=step*.1;if(use){result.x=oldQ.x;result.z=1;}return result;
 }

 Texture2D<float> _Address89;Texture2D<float4> _Control89,_Palette89,_Original89;int _Families89;float2 _Size89,_Wrap89;
 int Wrap89(int p,int n,int mode){if(mode==1)return clamp(p,0,n-1);if(mode==0)return(p%n+n)%n;int q=(p%(2*n)+2*n)%(2*n);return q<n?q:2*n-1-q;}
 float4 F84(V v):SV_Target{
  int2 a=(int2)v.pos.xy;int plane=a.x/_Width84;int2 hp=int2(a.x%_Width84,a.y)+(int2)_HeadOrigin84,mp=hp+(int2)_Join84;
  int2 np=clamp((int2)floor(_NativeOrigin84+(mp+.5+_Delta84)*2),int2(0,0),int2(959,543));
  if(plane==0)return _Before84.Load(int3(np,0));if(plane==1)return _MainMeta84.Load(int3(mp,0));if(plane==2)return _World84.Load(int3(np,0));if(plane==3)return _Cell84.Load(int3(np,0));if(plane==4)return _Owner84.Load(int3(np,0));if(plane==5)return _MainUV84.Load(int3(mp,0));if(plane==6)return _MainSource84.Load(int3(mp,0));if(plane==7)return _Domain84.Load(int3(mp,0));
  float4 map=_Map84.Load(int3(hp,0));bool added=map.r>.5&&map.a>.5;int2 n=added?(int2)round(map.gb):hp;
  bool bounds=all(n>=0)&&all(n<(added?int2(960,544):int2(480,272)));if(!bounds)return float4(-1,-1,-1,-1);
  float4 cls=added?_Class96084.Load(int3(n,0)):_Class48084.Load(int3(n,0));float4 meta=added?_Meta96084.Load(int3(n,0)):_Meta48084.Load(int3(n,0));float4 uv=added?_UV96084.Load(int3(n,0)):_UV48084.Load(int3(n,0));
  if(plane==8)return cls;if(plane==9)return meta;if(plane==10)return added?_Normal96084.Load(int3(n,0)):_Normal48084.Load(int3(n,0));if(plane==11)return uv;
  float4 hu=_HeadUV84.Load(int3(hp,0)),hm=_HeadMeta84.Load(int3(hp,0)),mu=_MainUV84.Load(int3(mp,0)),ms=_MainSource84.Load(int3(mp,0)),domain=_Domain84.Load(int3(mp,0)),owner=_Owner84.Load(int3(np,0)),cell=_Cell84.Load(int3(np,0));
  bool ordinary=domain.x<.5&&cell.z==1&&all(cell.xy==mp)&&all(ms.xyz==owner.zxy);
  // Exact UV/address identity, not a fitted colour/depth tolerance. Keep all raw
  // evidence even if unknown. Metadata/depth equality is reviewed separately.
  bool known=ordinary&&meta.y==_Role89&&all(uv.xy==hu.xy)&&all(hu.xy==mu.xy)&&hu.z==cls.x&&all(ms.yzw==meta.yzw);
  if(plane==12)return float4(n,added?1:0,known?1:0);if(plane==13)return hu;if(plane==14)return hm;
  if(plane==15)return added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0));float4 history=Candidate85(hp,cls,meta,uv,hu,hm);if(plane==16)return history;
  float4 before=_Before84.Load(int3(np,0));if(!known){if(plane==20||plane==21)return 0;return before;}
  int2 site=(int2)floor(uv.xy*_Size89);site=int2(Wrap89(site.x,(int)_Size89.x,(int)_Wrap89.x),Wrap89(site.y,(int)_Size89.y,(int)_Wrap89.y));int family=(int)round(_Address89.Load(int3(site,0)))-1;int k=(int)round(cls.x*(_Levels85-1)),kh=(int)round(history.x*(_Levels85-1));bool valid=family>=0&&family<_Families89&&k>=0&&k<_Levels85&&kh>=0&&kh<_Levels85;
  if(plane==20)return float4(valid?family+1:-1,k,kh,1);if(plane==21)return _Original89.Load(int3(site,0));if(!valid)return float4(-10,0,0,-1);
  float4 colour=plane==17?_Control89.Load(int3(kh,family,0)):_Palette89.Load(int3(plane==18?k:kh,family,0));return float4(colour.rgb,before.a);
 }
 ENDHLSL
 }
}}
