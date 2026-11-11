// CPU-only contracts shared by the reviewed candidate. No Unity dependency.
using System;

public enum GridSpace30 { PhysicalHead, CanonicalAuthored }
public sealed class GridBinding30 {
 public readonly string sourceId,viewId,modelKey;
 public readonly GridSpace30 space;
 public readonly int frame,sequence,x,y,width,height,scale,pixelWidth,pixelHeight;
 readonly float[] clip;
 public GridBinding30(string sourceId,string viewId,string modelKey,GridSpace30 space,int frame,int sequence,
  int x,int y,int width,int height,int scale,int pixelWidth,int pixelHeight,float[] clip){
  this.sourceId=sourceId;this.viewId=viewId;this.modelKey=modelKey;this.space=space;this.frame=frame;this.sequence=sequence;
  this.x=x;this.y=y;this.width=width;this.height=height;this.scale=scale;this.pixelWidth=pixelWidth;this.pixelHeight=pixelHeight;
  this.clip=clip==null?null:(float[])clip.Clone();
 }
 public float[] CopyClip(){return clip==null?null:(float[])clip.Clone();}
 public double HeadX(int u){if(u<0||u>=pixelWidth)throw new ArgumentOutOfRangeException();return x+(u+.5)/scale;}
 public double HeadY(int v){if(v<0||v>=pixelHeight)throw new ArgumentOutOfRangeException();return y+height-(v+.5)/scale;}
 static void Need(bool ok,string why){if(!ok)throw new ArgumentException(why);}
 static void Validate(GridBinding30 g){
  Need(g!=null,"grid missing");Need(g.space==GridSpace30.PhysicalHead,"canonical input is not a physical source grid");
  Need(!String.IsNullOrEmpty(g.sourceId)&&!String.IsNullOrEmpty(g.viewId)&&!String.IsNullOrEmpty(g.modelKey),"source/view/model identity missing");
  Need(g.frame>=0&&g.sequence>0,"frame/sequence missing");
  Need(g.x>=0&&g.y>=0&&g.width>0&&g.height>0&&(long)g.x+g.width<=480&&(long)g.y+g.height<=272,"head ROI outside fixed480x272 contract");
  Need(g.scale==8&&(long)g.width*g.height<=4096,"physical8x ROI budget");
  Need(g.pixelWidth==(long)g.width*g.scale&&g.pixelHeight==(long)g.height*g.scale&&(long)g.pixelWidth*g.pixelHeight<=262144,"raster dimensions do not match sample lattice");
  Need(g.clip!=null&&g.clip.Length==16,"world-to-cropped-clip matrix missing");
  foreach(float v in g.clip)Need(!Single.IsNaN(v)&&!Single.IsInfinity(v),"nonfinite projection");
 }
 public static void RequirePair(GridBinding30 expected,GridBinding30 outline,GridBinding30 pigment){
  Validate(expected);Validate(outline);Validate(pigment);
  foreach(var g in new[]{outline,pigment}){
   Need(g.sourceId==expected.sourceId&&g.viewId==expected.viewId&&g.modelKey==expected.modelKey&&g.frame==expected.frame&&g.sequence==expected.sequence,"frame/view/source generation mismatch");
   Need(g.x==expected.x&&g.y==expected.y&&g.width==expected.width&&g.height==expected.height&&g.scale==expected.scale,"physical sample origin/ROI mismatch");
   for(int i=0;i<16;i++)Need(g.clip[i]==expected.clip[i],"producer projection differs from shared frame");
  }
 }
}

public sealed class FailureBoundary30 {
 public Exception Failure{get;private set;}
 public void Remember(Exception error){if(Failure==null)Failure=error??new InvalidOperationException("unknown producer failure");}
 public bool Run(Action action){if(Failure!=null)return false;try{action();return true;}catch(Exception error){Remember(error);return false;}}
 public void ThrowOutsideGraph(){if(Failure!=null)throw new InvalidOperationException("Deferred producer failure outside RenderGraph",Failure);}
}

// Models a required future GPU acknowledgement boundary. It does NOT manufacture
// a fence/readback, poll a device, or integrate Dispose into the live runner.
public sealed class WorkReceipt30 {
 readonly string key;bool possibleCommands,acknowledged,failed;int stages;
 public WorkReceipt30(string frameKey){if(String.IsNullOrEmpty(frameKey))throw new ArgumentException("frame key");key=frameKey;}
 public void MarkCommands(){if(failed||acknowledged)throw new InvalidOperationException("failed/completed frame cannot record more commands");possibleCommands=true;}
 public void StageReady(int bit){
  if(failed||acknowledged||!possibleCommands)throw new InvalidOperationException("frame cannot become ready without active recorded work");
  if(bit!=1&&bit!=2&&bit!=4)throw new ArgumentException("stage");
  if((stages&bit)!=0||((stages&4)!=0)||(bit==4&&stages!=3))throw new InvalidOperationException("duplicate/out-of-order producer stage");
  stages|=bit;
 }
 public void Fail(){failed=true;}
 public void ObserveCompletion(string frameKey,bool done,bool error,bool matchingGpuStampOrPassedFence){
  if(frameKey!=key)throw new ArgumentException("wrong owner/view/frame receipt");
  if(!possibleCommands)throw new InvalidOperationException("no commands exist for GPU receipt");
  if(done&&error){failed=true;return;}
  if(done&&!error&&matchingGpuStampOrPassedFence)acknowledged=true;
 }
 public bool CanRelease=>!possibleCommands||acknowledged;
 public bool CanUsePixels=>acknowledged&&!failed&&stages==7;
 public void RequireCanRelease(){if(!CanRelease)throw new InvalidOperationException("GPU outcome pending/uncertain; retain owned resources");}
}
