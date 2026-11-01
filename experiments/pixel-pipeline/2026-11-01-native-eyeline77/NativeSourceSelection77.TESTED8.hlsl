FeatureSample583 NativeSample77(int2 p,int eye,int k,out float intrinsic,out int component){
 FeatureSample583 r=(FeatureSample583)0;r.support=-1;intrinsic=0;component=0;int2 q=(p-_ROI348.xy)*4+int2(k&3,k>>2);int owner=(int)round(_Centres348[eye].w);
 if(!ValidLayer19(3,q,owner))return r;float4 m=M(3,q);component=NativeComponent77((int)round(U(3,q).z));if(component<=0||NativeEye77(component)!=owner)return r;
 float w=saturate(m.w);float4 skin=M(0,q);if(ValidLayer19(0,q,owner)&&skin.x<m.x)w*=1-saturate(skin.w);intrinsic=w;
 float4 hair=_UseHairRegion502!=0?_HairMETA.Load(int3(p,0)):_S4META.Load(int3(q,0)),brow=_S5META.Load(int3(q,0)),body=_S6META.Load(int3(q,0));
 if(cov(hair)&&hair.x<m.x){w*=1-saturate(hair.w);r.hairBlocked=1;}if(cov(brow)&&brow.x<m.x)w*=1-saturate(brow.w);if(cov(body)&&body.x<m.x){w=0;r.bodyBlocked=1;}
 r.feat=5;r.support=3;r.depth=m.x;r.weight=w;r.rest=P(3,q).xyz;return r;
}
float NativeIntrinsic77(int2 p,int eye){float total=0;for(int k77=0;k77<16;k77++){float intrinsic;int component;NativeSample77(p,eye,k77,intrinsic,component);total+=intrinsic;}return total;}
float NativeVisible77(int2 p,int eye,out float3 mean,out int component){float total=0;mean=0;component=0;for(int k77=0;k77<16;k77++){float intrinsic;int cid;FeatureSample583 s=NativeSample77(p,eye,k77,intrinsic,cid);if(s.support<0||s.weight<=0)continue;total+=s.weight;mean+=s.rest*s.weight;component=cid;}if(total>0)mean/=total;return total;}
float NativeError77(float3 p,float3 centre,int eye){float3 d=p-centre;float2 delta=float2(dot(d,_AxesX348[eye].xyz)/_AxesX348[eye].w,dot(d,_AxesY348[eye].xyz)/_AxesY348[eye].w);return dot(delta,delta);}
bool NativeAllocated77(int2 p,int eye){FeaturePacket19 own=Packet19(p,eye);if(own.uv.z>0||IrisAllocated19(p,eye))return false;float3 ownMean;int component;if(NativeVisible77(p,eye,ownMean,component)<=0)return false;
 float area=0;int reserved=0;for(int y77=_ROI348.y;y77<_ROI348.y+_ROI348.w;y77++)for(int x77=_ROI348.x;x77<_ROI348.x+_ROI348.z;x77++){FeaturePacket19 c=Packet19(int2(x77,y77),eye);area+=NativeIntrinsic77(int2(x77,y77),eye)/16;if(round(c.uv.z)==1){int sample77=(int)round(c.uv.w)-1;int2 q77=(int2(x77,y77)-_ROI348.xy)*4+int2(sample77&3,sample77>>2);if(sample77>=0&&NativeComponent77((int)round(U(3,q77).z))>0)reserved++;}}
 int budget=max(0,(int)floor(area+.5)-reserved);if(budget<=0)return false;float3 centre=NativeCentre77(component);float ownError=NativeError77(ownMean,centre,eye);int rank=0;
 for(int y77=_ROI348.y;y77<_ROI348.y+_ROI348.w;y77++)for(int x77=_ROI348.x;x77<_ROI348.x+_ROI348.z;x77++){int2 q=int2(x77,y77);if(Packet19(q,eye).uv.z>0||IrisAllocated19(q,eye))continue;float3 mean;int cid;if(NativeVisible77(q,eye,mean,cid)<=0||cid!=component)continue;float error=NativeError77(mean,centre,eye);
  bool tieSource=mean.x!=ownMean.x?mean.x<ownMean.x:mean.y!=ownMean.y?mean.y<ownMean.y:mean.z!=ownMean.z?mean.z<ownMean.z:q.y!=p.y?q.y<p.y:q.x<p.x;if(error<ownError||(error==ownError&&tieSource))rank++;}
 return rank<budget;
}

float IrisCount19(FeaturePacket19 c){return c.a.z+c.a.w+c.b.x;}
