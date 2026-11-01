// The shared parent/iris compositor has already placed these source features.
// A second independent top-K must not replace a still-visible part with another
// part. Require current native source support; closed/fully occluded parts are
// not made visible by their cached identity. Generic skin is not globally ignored.
bool ComposedSource76(int2 p,float4 old,float4 owner,bool domain,out int eyeId,out int feature,out float weight,out int sampleIndex){
 eyeId=0;feature=0;weight=0;sampleIndex=-1;if(!LayerMode19()||old.a<=0||owner.z<=0)return false;
 int role=(int)round(owner.x),source=role==2?2:role==5?1:role==7?3:-1;
 if(source<0||((role==2||role==5)&&!domain))return false;
 // Domain.y is colour-support provenance, NOT an eye identity.
 float4 composedOwner=_OldEyeOwner.Load(int3(p,0));
 if(role!=7&&round(composedOwner.x)!=role)return false;
 float wanted=composedOwner.y;float closest=1e30;
 for(uint sample76=0;sample76<16;sample76++){
  int2 q=(p-_ROI348.xy)*4+int2(sample76&3,sample76>>2);float4 m=M(source,q);
  if(!cov(m)||P(source,q).w<=.5||m.z<.5||m.z>2.5)continue;
  if(role!=7&&round(m.z)!=round(wanted))continue;
  float visible=saturate(m.w);float4 sk=M(0,q);
  if(cov(sk)&&sk.x<m.x)visible*=1-saturate(sk.w);
  if(source==1){float4 ir=M(2,q);if(cov(ir)&&ir.x<m.x)visible*=1-saturate(ir.w);}
  if(source!=3){float4 lid=M(3,q);if(cov(lid)&&lid.x<m.x)visible*=1-saturate(lid.w);}
  float4 hair=_S4META.Load(int3(q,0)),brow=_S5META.Load(int3(q,0)),body=_S6META.Load(int3(q,0));
  if(cov(hair)&&hair.x<m.x)visible*=1-saturate(hair.w);
  if(cov(brow)&&brow.x<m.x)visible*=1-saturate(brow.w);
  if(cov(body)&&body.x<m.x)visible=0;
  if(visible<=0)continue;weight+=visible;
  float d=abs(m.x-owner.z);if(d<closest){closest=d;eyeId=(int)round(m.z);sampleIndex=(int)sample76;}
 }
 feature=role==2?2:role==5?1:5;return weight>0&&eyeId>0;
}
float4 ComposedPigment76(float2 screen,int eye,int role){
 float2 ref=reference(screen,eye);int2 top=(int2)floor(ref);
 if(all(top>=0)&&all(top<int2(480,272))){float4 r=_TemplateRole.Load(int3(top.x,271-top.y,0));if(round(r.x)==role&&round(r.y)==round(_Centres348[eye].w))return float4(top,role,1);}
 float4 provenance=0;float4 sampled76=Own(ref,eye,role,provenance);return provenance;
}
