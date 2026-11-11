// Pure managed policy used by the unactivated diagnostic candidate.
using System;using System.Collections.Generic;
public sealed class Submission31 {
 readonly object sync=new object();readonly string key;readonly int generation;
 int stages;bool commands,barrierAttempted,callbackSeen,complete,failed,closed;
 public Submission31(string key,int generation){if(String.IsNullOrEmpty(key)||generation<=0)throw new ArgumentException("submission identity");this.key=key;this.generation=generation;}
 public void BeforeCommands(){lock(sync){if(closed||barrierAttempted)throw new InvalidOperationException("submission sealed");commands=true;}}
 public void StageRecorded(int stage){lock(sync){
  if(!commands||failed||closed||barrierAttempted)throw new InvalidOperationException("no active submission");
  if(stage!=1&&stage!=2&&stage!=4&&stage!=8)throw new ArgumentException("stage");
  if((stages&stage)!=0||(stage==8&&stages!=7))throw new InvalidOperationException("duplicate or unordered producer");stages|=stage;
 }}
 public void Fail(){lock(sync){failed=true;}}
 // Set before invoking the API. An exception here is uncertain, never a retry.
 public void BeforeBarrier(){lock(sync){if(barrierAttempted)throw new InvalidOperationException("end barrier already attempted");barrierAttempted=true;}}
 public void AcceptCallback(string ownerKey,int ownerGeneration,bool done,bool error){lock(sync){
  if(ownerKey!=key||ownerGeneration!=generation){failed=true;return;}
  if(!barrierAttempted||!commands){failed=true;return;}
  if(callbackSeen){failed=true;return;} // Never turn a later callback into a retry.
  if(!done){failed=true;return;}callbackSeen=true;
  if(error){failed=true;return;}complete=true;
 }}
 public void Stop(){lock(sync){closed=true;}}
 public bool CanRelease{get{lock(sync){return !commands||complete;}}}
 public bool CanUsePixels{get{lock(sync){return complete&&!failed&&stages==15;}}}
 public bool HasError{get{lock(sync){return failed;}}}
 public bool CommandsPossible{get{lock(sync){return commands;}}}
}

// Stop/request-exit, owned-resource drain, and Edit restoration have separate
// idempotent progress. Pending GPU work never prevents the one normal-exit call
// or causes a timeout/retry/forced resource release.
public sealed class ExitCoordinator31 {
 readonly List<string> errors=new List<string>();bool begun,releaseAttempted,restoreAttempted,completionBroken;
 public bool ExitAttempted{get;private set;}public bool Released{get;private set;}public bool Restored{get;private set;}
 public string[] Errors=>errors.ToArray();
 void Attempt(string stage,Action action){try{action();}catch(Exception e){errors.Add(stage+": "+e.GetType().Name+": "+e.Message);}}
 public void Begin(Action stop,Action restoreBeforeExit,Action requestNormalExit){
  if(begun)return;begun=true;
  Attempt("stop producers",stop);Attempt("restore before exit",restoreBeforeExit);
  ExitAttempted=true;Attempt("normal exit",requestNormalExit);
 }
 public void Pump(bool stableEdit,Func<bool> mayRelease,Action releaseOwned,Action restoreAfterEdit){
  if(!begun)return;
  if(!releaseAttempted&&!completionBroken){bool allowed=false;try{allowed=mayRelease();}catch(Exception e){completionBroken=true;errors.Add("completion check: "+e.GetType().Name+": "+e.Message);}
   if(allowed){releaseAttempted=true;Attempt("release owned",()=>{releaseOwned();Released=true;});}}
  if(stableEdit&&!restoreAttempted){restoreAttempted=true;Attempt("restore after Edit",()=>{restoreAfterEdit();Restored=true;});}
 }
 public bool Finished=>begun&&Released&&Restored;
}

// Small strong-root table for pending owners, not a resource manager. One owner
// per live view; another view and another owner cannot release its slot.
public sealed class PendingViews31<T> where T:class {
 readonly Dictionary<string,T> slots=new Dictionary<string,T>();
 public void Acquire(string view,T owner){if(String.IsNullOrEmpty(view)||owner==null)throw new ArgumentException("view owner");if(slots.ContainsKey(view))throw new InvalidOperationException("view has unsettled owner");slots.Add(view,owner);}
 public void Release(string view,T owner){if(!slots.TryGetValue(view,out var current)||!Object.ReferenceEquals(current,owner))throw new InvalidOperationException("foreign owner cannot release view");slots.Remove(view);}
 public bool Owns(string view,T owner)=>slots.TryGetValue(view,out var current)&&Object.ReferenceEquals(current,owner);
 public int Count=>slots.Count;
}

public static class QMetaLattice31 {
 public static int[] RasterOrigin(int[]qROI,bool startsAtTop){return new[]{qROI[0],startsAtTop?qROI[1]:272-qROI[1]-qROI[3]};}
 public static void Require(int[] sourceROI,int[] qROI,int qWidth,int qHeight,int metaWidth,int metaHeight){
  if(sourceROI==null||qROI==null||sourceROI.Length!=4||qROI.Length!=4)throw new ArgumentException("ROI");
  int x=qROI[0],y=qROI[1],w=qROI[2],h=qROI[3];
  if(x<0||y<0||w<=0||h<=0||(long)x+w>480||(long)y+h>272||qWidth!=w||qHeight!=h||metaWidth!=w||metaHeight!=h)throw new ArgumentException("same-fragment logical grid required");
  if(sourceROI[0]<x||sourceROI[1]<y||sourceROI[2]<=0||sourceROI[3]<=0||(long)sourceROI[0]+sourceROI[2]>(long)x+w||(long)sourceROI[1]+sourceROI[3]>(long)y+h)throw new ArgumentException("source outside Q/meta domain");
 }
 public static int[] MapBottomLeft(int headX,int headYBottom,int[]qROI){
  int x=headX-qROI[0],y=headYBottom-(272-qROI[1]-qROI[3]);
  if(x<0||y<0||x>=qROI[2]||y>=qROI[3])throw new ArgumentOutOfRangeException("Q/meta sample outside paired domain");return new[]{x,y};
 }
 public static bool Known(float level,float qDepth,float qAlpha,float metaDepth,float metaAlpha){
  foreach(float v in new[]{level,qDepth,qAlpha,metaDepth,metaAlpha})if(Single.IsNaN(v)||Single.IsInfinity(v))return false;
  return qDepth>0&&qAlpha>0&&qDepth==metaDepth&&qAlpha==metaAlpha;
 }
}
