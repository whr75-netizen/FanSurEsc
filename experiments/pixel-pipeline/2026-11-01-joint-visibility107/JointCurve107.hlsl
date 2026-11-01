// Three source parts share identical external visibility and depth conditions.
// The thin curve is a geometric constraint, not a blanket lid-first priority.
int _CurveSampleScale107;
void Contributions107(int at,out float4 lo,out float4 hi){
 float3 a,b,z;int n=_Size96.x*_Size96.y;
 [unroll]for(int loadPart107=0;loadPart107<3;loadPart107++){float4 v=_Visibility96[(loadPart107+1)*n+at];a[loadPart107]=v.x;b[loadPart107]=v.y;z[loadPart107]=Layer96(loadPart107+1,1,at).x;}
 lo=float4(a,1);hi=float4(b,1);
 [unroll]for(int part107=0;part107<3;part107++){
  lo.w*=1-b[part107];hi.w*=1-a[part107];
  [unroll]for(int other107=0;other107<3;other107++){
   if(part107==other107||z[other107]<=0||b[other107]<=0)continue;
   if(z[other107]<z[part107]-3e-5){lo[part107]*=1-b[other107];hi[part107]*=1-a[other107];}
   else if(abs(z[other107]-z[part107])<=3e-5)lo[part107]*=1-b[other107];
  }
 }
}
[numthreads(8,8,1)]void ResolveCurve107(uint3 tid:SV_DispatchThreadID){
 int2 p=tid.xy,cs=_Size96/_CurveSampleScale107;if(any(p>=cs))return;int cell=p.y*cs.x+p.x,n=_Size96.x*_Size96.y;
 float4 colour=_BaselineColour106[cell],identity=_BaselineIdentity106[cell],decision=_BaselineDecision106[cell];
 bool touched=false;bool2 owners=false;
 for(int s=0;s<_CurveCount106;s++){CurveSegment106 v=_Curves106[s];if(Intersects106(v.a.xy,v.b.xy,p)){touched=true;int o=(int)round(v.a.w);if(o==_CurveEyeIds106.x)owners.x=true;if(o==_CurveEyeIds106.y)owners.y=true;}}
 float4 audit=0;bool raw=false,blocked=false,unknown=false,tied=false,multiple=false;int chosen=-1,chosenEye=0,firstOwner=0;float bestD=3.402823e38,bestAlpha=-1;
 if(touched){
  for(int y=0;y<_CurveSampleScale107;y++)for(int x=0;x<_CurveSampleScale107;x++){
   int2 q=p*_CurveSampleScale107+int2(x,y);int at=q.y*_Size96.x+q.x;float4 v=_Visibility96[3*n+at],meta=Layer96(3,1,at);int owner=(int)round(meta.z);
   if(v.x<=0||v.x!=v.y||!((owners.x&&owner==_CurveEyeIds106.x)||(owners.y&&owner==_CurveEyeIds106.y)))continue;
   raw=true;float4 lo,hi;Contributions107(at,lo,hi);
   if(!(lo.z>max(hi.x,max(hi.y,hi.w)))){bool definite=lo.x>hi.z||lo.y>hi.z||lo.w>hi.z;blocked=blocked||definite;unknown=unknown||!definite;continue;}
   if(firstOwner==0)firstOwner=owner;else if(firstOwner!=owner)multiple=true;
   float d=3.402823e38;for(int s=0;s<_CurveCount106;s++){CurveSegment106 v=_Curves106[s];if(round(v.a.w)==owner)d=min(d,Distance106((q+.5)/_CurveSampleScale107,v.a.xy,v.b.xy));}
   if(d<bestD||(d==bestD&&lo.z>bestAlpha)){bestD=d;bestAlpha=lo.z;chosen=at;chosenEye=owner;tied=false;}
   else if(d==bestD&&lo.z==bestAlpha&&chosen>=0){if(any(Layer96(3,0,at).rgb!=Layer96(3,0,chosen).rgb))tied=true;}
  }
  int flag=chosen<0?(raw?(blocked&&!unknown?4:-4):-1):(multiple?-3:tied?-2:3);
  audit=float4(flag,raw?1:0,0,chosen>=0?bestD:0);
  if(flag==3){float4 meta=Layer96(3,1,chosen);colour=float4(Layer96(3,0,chosen).rgb,1);identity=float4(6,chosenEye,meta.x,Layer96(3,3,chosen).z);decision=float4(6,107,decision.zw);audit.z=chosen+1;}
 }
 _CurveColour106[cell]=colour;_CurveIdentity106[cell]=identity;_CurveDecision106[cell]=decision;_CurveAudit106[cell]=audit;
}
