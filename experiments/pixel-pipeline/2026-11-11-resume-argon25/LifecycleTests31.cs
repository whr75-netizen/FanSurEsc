using System;using System.Collections.Generic;using System.Text.Json;
public static class LifecycleTests31 {
 static readonly List<string> passed=new List<string>();
 static void Check(bool ok,string name){if(!ok)throw new Exception(name);passed.Add(name);}
 static void Reject(Action a,string name){bool bad=false;try{a();}catch(InvalidOperationException){bad=true;}catch(ArgumentException){bad=true;}Check(bad,name);}
 static Submission31 Full(string key="view-a/frame99",int gen=1){var r=new Submission31(key,gen);r.BeforeCommands();r.StageRecorded(1);r.StageRecorded(2);r.StageRecorded(4);r.StageRecorded(8);r.BeforeBarrier();return r;}
 public static void Main(){
  var idle=new Submission31("idle",1);idle.Stop();Check(idle.CanRelease&&!idle.CanUsePixels,"no GPU commands allows owned release only");Reject(()=>idle.BeforeCommands(),"stopped submission cannot restart");
  var r=Full();Check(!r.CanRelease&&!r.CanUsePixels,"recorded stages are not GPU completion");r.AcceptCallback("view-a/frame99",1,true,false);Check(r.CanRelease&&r.CanUsePixels,"same request successful completion allows output and release");
  Reject(()=>r.BeforeBarrier(),"no automatic barrier resubmission");Reject(()=>r.BeforeCommands(),"completed resource generation cannot be reused");
  var late=Full();late.AcceptCallback("view-a/frame99",1,true,false);late.AcceptCallback("view-a/frame99",1,true,true);Check(late.CanRelease&&!late.CanUsePixels,"duplicate/late callback invalidates output without undoing release proof");
  var foreign=Full();foreign.AcceptCallback("view-b/frame99",1,true,false);Check(!foreign.CanRelease&&!foreign.CanUsePixels,"foreign view callback cannot acknowledge ownership");
  var stale=Full();stale.AcceptCallback("view-a/frame99",2,true,false);Check(!stale.CanRelease,"stale resource generation cannot release");
  var pending=Full();pending.AcceptCallback("view-a/frame99",1,false,false);Check(!pending.CanRelease&&!pending.CanUsePixels,"noncompleted request remains retained and invalid");
  var failed=Full();failed.AcceptCallback("view-a/frame99",1,true,true);Check(!failed.CanRelease&&!failed.CanUsePixels,"device/readback error is no release proof");failed.AcceptCallback("view-a/frame99",1,true,false);Check(!failed.CanRelease,"error callback cannot be replaced by retry receipt");
  var partial=new Submission31("partial",1);partial.BeforeCommands();partial.StageRecorded(1);partial.Fail();partial.BeforeBarrier();partial.AcceptCallback("partial",1,true,false);Check(partial.CanRelease&&!partial.CanUsePixels,"end readback can drain partial work without validating failed pixels");
  var stopped=new Submission31("stopped",1);stopped.BeforeCommands();stopped.Stop();stopped.Fail();stopped.BeforeBarrier();stopped.AcceptCallback("stopped",1,true,false);Check(stopped.CanRelease&&!stopped.CanUsePixels,"stop cannot suppress the already-recorded frame drain");
  var missing=new Submission31("missing",1);missing.BeforeCommands();missing.StageRecorded(1);Reject(()=>missing.StageRecorded(8),"classifier requires both hair producers and Q/meta producer");Reject(()=>missing.StageRecorded(1),"duplicate stage cannot substitute missing producer");missing.BeforeBarrier();missing.AcceptCallback("missing",1,true,false);Check(missing.CanRelease&&!missing.CanUsePixels,"missing stages cannot become valid output");
  var apiThrow=new Submission31("throw",1);apiThrow.BeforeCommands();apiThrow.BeforeBarrier();apiThrow.Fail();Check(!apiThrow.CanRelease,"uncertain API enqueue failure retains owned resources");Reject(()=>apiThrow.BeforeBarrier(),"uncertain enqueue does not automatically retry");
  var forged=new Submission31("empty",1);forged.BeforeBarrier();forged.AcceptCallback("empty",1,true,false);Check(!forged.CanUsePixels,"no commands cannot fabricate valid GPU output");
  var log=new List<string>();var exit=new ExitCoordinator31();var wait=Full();
  exit.Begin(()=>log.Add("stop"),()=>log.Add("before"),()=>log.Add("exit"));exit.Begin(()=>log.Add("again"),()=>{},()=>log.Add("exit again"));
  exit.Pump(false,()=>wait.CanRelease,()=>log.Add("release"),()=>log.Add("restore"));Check(String.Join(",",log)=="stop,before,exit"&&!exit.Released,"pending work does not prevent normal exit and is not freed");
  exit.Pump(true,()=>wait.CanRelease,()=>log.Add("release"),()=>log.Add("restore"));Check(exit.Restored&&!exit.Released&&log.Count==4,"Edit options restore independently of pending GPU resources");
  wait.AcceptCallback("view-a/frame99",1,true,false);exit.Pump(true,()=>wait.CanRelease,()=>log.Add("release"),()=>log.Add("restore again"));Check(exit.Finished&&String.Join(",",log)=="stop,before,exit,restore,release","late successful callback drains once after normal exit");
  exit.Pump(true,()=>true,()=>log.Add("release again"),()=>{});Check(log.Count==5,"repeated exit pump is idempotent");
  var broken=new ExitCoordinator31();int requests=0;broken.Begin(()=>throw new Exception("detach"),()=>throw new Exception("restore"),()=>requests++);Check(requests==1&&broken.Errors.Length==2,"detach or pre-exit restore failure cannot skip exit request");
  broken.Pump(true,()=>true,()=>throw new Exception("dispose"),()=>log.Add("restored despite dispose"));Check(broken.Restored&&!broken.Released&&broken.Errors.Length==3,"dispose failure cannot suppress Edit restoration");
  broken.Pump(true,()=>true,()=>throw new Exception("retry"),()=>{});Check(broken.Errors.Length==3,"failed release is reported without forced retry");
  var exitThrow=new ExitCoordinator31();exitThrow.Begin(()=>{},()=>{},()=>throw new Exception("exit API"));exitThrow.Begin(()=>{},()=>{},()=>requests++);Check(exitThrow.ExitAttempted&&exitThrow.Errors.Length==1&&requests==1,"uncertain normal-exit call is not resent");
  var restoreThrow=new ExitCoordinator31();restoreThrow.Begin(()=>{},()=>{},()=>{});restoreThrow.Pump(true,()=>true,()=>{},()=>throw new Exception("restore"));restoreThrow.Pump(true,()=>true,()=>{},()=>requests++);Check(restoreThrow.Released&&!restoreThrow.Restored&&restoreThrow.Errors.Length==1,"restoration failure remains explicit without guessed retry");
  var brokenQuery=new ExitCoordinator31();int queries=0;brokenQuery.Begin(()=>{},()=>{},()=>{});brokenQuery.Pump(true,()=>{queries++;throw new Exception("unknown completion");},()=>{},()=>{});brokenQuery.Pump(true,()=>{queries++;return true;},()=>{},()=>{});Check(queries==1&&brokenQuery.Restored&&!brokenQuery.Released&&brokenQuery.Errors.Length==1,"completion query failure blocks retries/release but not Edit restoration");
  var views=new PendingViews31<object>();var a=new object();var b=new object();views.Acquire("camera-a",a);views.Acquire("camera-b",b);Check(views.Count==2&&views.Owns("camera-a",a)&&views.Owns("camera-b",b),"independent views retain independent pending owners");
  Reject(()=>views.Acquire("camera-a",b),"duplicate arm blocked while original view owner is pending");Reject(()=>views.Release("camera-a",b),"foreign view owner cannot release another owner");views.Release("camera-b",b);Check(views.Count==1&&views.Owns("camera-a",a),"releasing one view preserves another view strong root");views.Release("camera-a",a);views.Acquire("camera-a",b);Check(views.Owns("camera-a",b)&&!views.Owns("camera-a",a),"settled view can be explicitly initialized with a new owner");
  int[] source={211,48,18,8},qr={210,47,20,10};QMetaLattice31.Require(source,qr,20,10,20,10);passed.Add("paired Q and metadata share exact logical ROI and dimensions");
  var top=QMetaLattice31.RasterOrigin(qr,true);var bottom=QMetaLattice31.RasterOrigin(qr,false);Check(top[0]==210&&top[1]==47&&bottom[0]==210&&bottom[1]==215,"cropped lighting SV_Position restored in both backend Y conventions");
  int checkedSamples=0;for(int y=0;y<8;y++)for(int x=0;x<18;x++){int hx=211+x,hy=272-48-8+y;var p=QMetaLattice31.MapBottomLeft(hx,hy,qr);if(p[0]!=x+1||p[1]!=y+1)throw new Exception("sample centre");checkedSamples++;}
  Check(checkedSamples==144,"all actual27 ROI cells map to same Q/meta sample with halo");
  foreach(var edge in new[]{new[]{0,0,1,1},new[]{479,271,1,1}}){QMetaLattice31.Require(edge,edge,1,1,1,1);var p=QMetaLattice31.MapBottomLeft(edge[0],272-edge[1]-1,edge);Check(p[0]==0&&p[1]==0,"clipped head border preserves sample centre "+edge[0]);}
  Reject(()=>QMetaLattice31.Require(source,qr,20,10,40,20),"legacy2x metadata cannot be bound to logical Q");
  Reject(()=>QMetaLattice31.Require(source,new[]{212,48,18,8},18,8,18,8),"shifted paired ROI rejected");
  Reject(()=>QMetaLattice31.Require(source,new[]{0,0,Int32.MaxValue,1},1,1,1,1),"overflow-sized Q ROI rejected");
  Reject(()=>QMetaLattice31.MapBottomLeft(209,220,qr),"outside-domain lookup is unknown rather than clamped");
  Check(QMetaLattice31.Known(2,1.25f,.5f,1.25f,.5f),"same-fragment depth/coverage accepted without interpolation");
  Check(!QMetaLattice31.Known(2,1.25f,.5f,1.250001f,.5f),"different surface depth cannot become valid through epsilon");
  Check(!QMetaLattice31.Known(2,1.25f,.5f,1.25f,1),"different alpha coverage rejected");
  Check(!QMetaLattice31.Known(Single.NaN,1,1,1,1)&&!QMetaLattice31.Known(0,0,1,0,1),"nonfinite Q or absent surface remains unknown");
  Check(!QMetaLattice31.Known(1,Single.PositiveInfinity,1,Single.PositiveInfinity,1),"infinite equal depth is rejected like shader isfinite");
  Check(!QMetaLattice31.Known(1,1,Single.PositiveInfinity,1,Single.PositiveInfinity),"infinite equal coverage is rejected like shader isfinite");
  Console.WriteLine(JsonSerializer.Serialize(new{checks=passed.Count,passed,actualUnityGPUCalls=0,actualReadbackObserved=false,liveEditorLoaded=false}));
 }
}
