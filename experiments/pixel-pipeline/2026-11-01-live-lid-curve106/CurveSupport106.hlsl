// Same geometric support rule as105, evaluated live from current source curve.
// Protect existing iris/white selections. No pose/Close-value gate or budget.
struct CurveSegment106{float4 a,b;};
StructuredBuffer<CurveSegment106> _Curves106;
StructuredBuffer<float4> _BaselineColour106,_BaselineIdentity106,_BaselineDecision106;
RWStructuredBuffer<float4> _CurveColour106,_CurveIdentity106,_CurveDecision106,_CurveAudit106;
int _CurveCount106;
int2 _CurveEyeIds106;
bool Intersects106(float2 a,float2 b,int2 cell){
 float lower=0,upper=1;float2 d=b-a;
 [unroll]for(int axis=0;axis<2;axis++){
  if(d[axis]==0){if(a[axis]<cell[axis]||a[axis]>cell[axis]+1)return false;}
  else{float x=(cell[axis]-a[axis])/d[axis],y=(cell[axis]+1-a[axis])/d[axis];lower=max(lower,min(x,y));upper=min(upper,max(x,y));}
 }
 return upper>=lower&&dot(d,d)>0;
}
float Distance106(float2 p,float2 a,float2 b){float2 d=b-a;float t=saturate(dot(p-a,d)/max(dot(d,d),1e-30));float2 r=a+t*d-p;return dot(r,r);}
[numthreads(8,8,1)]void ApplyCurve106(uint3 tid:SV_DispatchThreadID){
 int2 p=tid.xy,cs=_Size96>>2;if(any(p>=cs))return;int cell=p.y*cs.x+p.x,n=_Size96.x*_Size96.y;
 float4 colour=_BaselineColour106[cell],identity=_BaselineIdentity106[cell],decision=_BaselineDecision106[cell];
 float4 audit=0;bool touched=false,has=false,tied=false;float bestD=3.402823e38,bestAlpha=-1;int chosen=-1,chosenEye=0;bool differentEyes=false;bool2 ownerTouched=false;int firstSupportedOwner=0;
 for(int s=0;s<_CurveCount106;s++){
  CurveSegment106 segment=_Curves106[s];if(!Intersects106(segment.a.xy,segment.b.xy,p))continue;touched=true;int owner=(int)round(segment.a.w);if(owner==_CurveEyeIds106.x)ownerTouched.x=true;if(owner==_CurveEyeIds106.y)ownerTouched.y=true;
 }
 if(touched){
  [unroll]for(int y=0;y<4;y++)[unroll]for(int x=0;x<4;x++){
   int2 q=p*4+int2(x,y);int at=q.y*_Size96.x+q.x;float4 visibility=_Visibility96[3*n+at],meta=Layer96(3,1,at);
   int owner=(int)round(meta.z);bool selectedOwner=(ownerTouched.x&&owner==_CurveEyeIds106.x)||(ownerTouched.y&&owner==_CurveEyeIds106.y);
   if(visibility.x<=0||visibility.x!=visibility.y||!selectedOwner)continue;
   if(firstSupportedOwner==0)firstSupportedOwner=owner;else if(firstSupportedOwner!=owner)differentEyes=true;
   float d=3.402823e38;for(int s=0;s<_CurveCount106;s++){CurveSegment106 segment=_Curves106[s];if(round(segment.a.w)==owner)d=min(d,Distance106((q+.5)*.25,segment.a.xy,segment.b.xy));}float alpha=visibility.x;
   if(d<bestD||(d==bestD&&alpha>bestAlpha)){has=true;tied=false;bestD=d;bestAlpha=alpha;chosen=at;chosenEye=owner;}
   else if(d==bestD&&alpha==bestAlpha&&chosen>=0){if(any(Layer96(3,0,at).rgb!=Layer96(3,0,chosen).rgb))tied=true;}
  }
 }
 if(touched){
  audit=float4(1,has?1:0,0,has?bestD:0);
  // This protection is explicit and tested. A native curve that collides with
  // another selected eye part is reported; no hidden lid-first overwrite.
  if(round(identity.x)==1||round(identity.x)==4)audit.x=2;
  else if(!has)audit.x=-1;
  else if(differentEyes)audit.x=-3;
  else if(tied)audit.x=-2;
  else{
   float4 meta=Layer96(3,1,chosen);colour=float4(Layer96(3,0,chosen).rgb,1);identity=float4(6,chosenEye,meta.x,Layer96(3,3,chosen).z);decision=float4(6,106,decision.zw);audit.x=3;audit.z=chosen+1;
  }
 }
 _CurveColour106[cell]=colour;_CurveIdentity106[cell]=identity;_CurveDecision106[cell]=decision;_CurveAudit106[cell]=audit;
}
