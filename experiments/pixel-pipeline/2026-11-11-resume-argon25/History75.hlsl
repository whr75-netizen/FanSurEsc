// Previous ACTUAL GPU owner, never previous RGB. Only equal CURRENT geometry
// candidates can use this preference. A hidden source is never admitted here.
Texture2D<float4> _CurrentProjection75,_PreviousProjection75,_PreviousOwner75;
int _HistoryEnabled75,_HistoryRole75,_HistoryCount75;
int2 _PreviousOrigin75,_PreviousSize75,_PreviousJoin75;
bool ProjectSource75(Texture2D<float4> tex,int primitive,float2 uvPoint,out float2 projected){
 projected=0;if(primitive<0||primitive>=_HistoryCount75)return false;
 uint i=3u*(uint)primitive;float4 a=tex.Load(int3(i&127u,i>>7u,0));i++;float4 b=tex.Load(int3(i&127u,i>>7u,0));i++;float4 c=tex.Load(int3(i&127u,i>>7u,0));
 float2 ab=b.xy-a.xy,ac=c.xy-a.xy,ap=uvPoint-a.xy;float det=ab.x*ac.y-ab.y*ac.x;
 if(det==0||!isfinite(det))return false;
 float v=(ap.x*ac.y-ap.y*ac.x)/det,w=(ab.x*ap.y-ab.y*ap.x)/det;float3 bary=float3(1-v-w,v,w);
 if(!all(isfinite(bary))||any(bary<0)||any(bary>1))return false;
 projected=a.zw*bary.x+b.zw*bary.y+c.zw*bary.z;return all(isfinite(projected));
}
bool CurrentHistory75(int role,int primitive,float2 uvPoint,int2 sourceQ,int2 targetQ){
 if(_HistoryEnabled75!=1||role!=_HistoryRole75)return false;
 float2 now,before;
 bool a=ProjectSource75(_CurrentProjection75,primitive,uvPoint,now),b=ProjectSource75(_PreviousProjection75,primitive,uvPoint,before);
 if(!a||!b)return false;
 // Atlas is in continuous HEAD projection, top-left. Convert once to actual
 // joined MAIN bottom-left logical cell-centre coordinates, as in68/69.
 now=float2(now.x-.5,272-now.y-.5)+_JoinOffset41;
 before=float2(before.x-.5,272-before.y-.5)+_PreviousJoin75;
 float2 wanted=before+(float2(targetQ)-now);float2 shifted=wanted+.5;
 // An exact cell-boundary tie gives no history preference; do not manufacture
 // a unique source or introduce floor-order artistic bias at that boundary.
 if(any(frac(shifted)==0))return false;
 int2 oldQ=(int2)floor(shifted)-_PreviousOrigin75;
 if(any(oldQ<0)||any(oldQ>=_PreviousSize75))return false;
 float4 key=_PreviousOwner75.Load(int3(oldQ+int2(15*_PreviousSize75.x,0),0));
 if(!all(isfinite(key))||key.x!=100+role||key.y!=primitive+1)return false;
 float2 transported;bool mapped=ProjectSource75(_CurrentProjection75,primitive,key.zw,transported);if(!mapped)return false;
 transported=float2(transported.x-.5,272-transported.y-.5)+_JoinOffset41;
 // Source-local correspondence must land in THIS current visible source
 // footprint. It can only prefer that current admitted candidate, not paint it.
 return all(abs(transported-float2(sourceQ))<.5);
}
