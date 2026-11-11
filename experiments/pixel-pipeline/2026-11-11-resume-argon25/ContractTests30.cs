using System;using System.IO;using System.Collections.Generic;using System.Text.Json;
public static class ContractTests30 {
 public sealed class Fixture {public string sourceId{get;set;}public string modelKey{get;set;}public int frame{get;set;}public int[]roi{get;set;}public int[]denseSize{get;set;}public float[]physicalClip{get;set;}public float[]canonicalClip{get;set;}}
 static List<string> passed=new List<string>();
 static void Need(bool ok,string label){if(!ok)throw new Exception(label);passed.Add(label);}
 static void Reject(Action action,string label){bool bad=false;try{action();}catch(ArgumentException){bad=true;}catch(InvalidOperationException){bad=true;}Need(bad,label);}
 public static void Main(string[] args){
  var f=JsonSerializer.Deserialize<Fixture>(File.ReadAllText(args[0]));var r=f.roi;
  GridBinding30 Make(GridSpace30 space=GridSpace30.PhysicalHead,string sid=null,string view="head-view-a",string model=null,int seq=1,int dx=0,int scale=8,float[]matrix=null,int?pw=null,int?frame=null){return new GridBinding30(sid??f.sourceId,view,model??f.modelKey,space,frame??f.frame,seq,r[0]+dx,r[1],r[2],r[3],scale,pw??r[2]*scale,r[3]*scale,matrix??f.physicalClip);}
  var expected=Make();Need(f.denseSize[0]==expected.pixelWidth&&f.denseSize[1]==expected.pixelHeight,"actual27 canonical and proposed physical extents coincide; extents alone insufficient");
  GridBinding30.RequirePair(expected,Make(),Make());passed.Add("synthetic physical pair from recorded camera fixture accepted; not a GPU result");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(GridSpace30.CanonicalAuthored,matrix:f.canonicalClip)),"actual canonical descriptor rejected before graph actions");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(matrix:f.canonicalClip)),"mislabelled canonical projection rejected even with equal extents");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(sid:"different-frame")),"mixed source/frame rejected");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(view:"head-view-b")),"independent view cannot borrow another source grid");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(model:"new-model")),"model generation mismatch rejected");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(seq:2)),"stale submission sequence rejected");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(frame:f.frame+1)),"same source label with a different numeric frame rejected");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(dx:1)),"one-cell origin shift rejected despite same dimensions");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(scale:4)),"4x input cannot be claimed as8x");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(pw:expected.pixelWidth-1)),"partial row cannot be claimed as complete raster");
  var bad=expected.CopyClip();bad[0]=Single.NaN;Reject(()=>GridBinding30.RequirePair(expected,Make(),Make(matrix:bad)),"nonfinite matrix rejected");
  var copied=expected.CopyClip();copied[0]+=1;GridBinding30.RequirePair(expected,expected,Make());passed.Add("descriptor matrix is not aliased to caller array");
  var argument=(float[])f.physicalClip.Clone();var preserved=Make(matrix:argument);argument[0]+=100;GridBinding30.RequirePair(expected,preserved,Make());passed.Add("constructor copies the caller matrix before later mutation");
  Reject(()=>GridBinding30.RequirePair(expected,Make(),new GridBinding30(f.sourceId,"head-view-a",f.modelKey,GridSpace30.PhysicalHead,f.frame,1,0,0,Int32.MaxValue,1,8,Int32.MaxValue,8,f.physicalClip)),"overflow-sized extent rejected before multiplication/addressing");
  Need(expected.HeadX(0)==r[0]+.0625&&expected.HeadY(0)==r[1]+r[3]-.0625,"first8x sample centre uses explicit top-left/bottom-left conversion");
  Need(expected.HeadX(expected.pixelWidth-1)==r[0]+r[2]-.0625&&expected.HeadY(expected.pixelHeight-1)==r[1]+.0625,"last sample centre is inside exact full footprint");
  var guard=new FailureBoundary30();int callbacks=0;bool succeeded=guard.Run(()=>{GridBinding30.RequirePair(expected,Make(),Make(GridSpace30.CanonicalAuthored));callbacks++;});Need(!succeeded&&callbacks==0,"bad grid cannot enqueue graph action");
  Need(!guard.Run(()=>callbacks++)&&callbacks==0,"failed producer does not automatically retry");Reject(()=>guard.ThrowOutsideGraph(),"first failure is delivered outside renderer callback");
  var pending=new WorkReceipt30("a/frame99");pending.MarkCommands();pending.Fail();Reject(()=>pending.RequireCanRelease(),"partial recorded work cannot be immediately disposed");
  pending.ObserveCompletion("a/frame99",false,false,true);Need(!pending.CanRelease,"pending callback is not completion");
  pending.ObserveCompletion("a/frame99",true,true,true);Need(!pending.CanRelease,"error receipt does not prove safe completion");
  pending.ObserveCompletion("a/frame99",true,false,false);Need(!pending.CanRelease,"CPU finished flag without GPU evidence is insufficient");
  Reject(()=>pending.ObserveCompletion("b/frame99",true,false,true),"another view receipt cannot release current resources");
  pending.ObserveCompletion("a/frame99",true,false,true);Need(pending.CanRelease&&!pending.CanUsePixels,"verified barrier may permit release but failed pixels stay invalid");
  var good=new WorkReceipt30("x");good.MarkCommands();good.StageReady(1);good.StageReady(2);good.StageReady(4);good.ObserveCompletion("x",true,false,true);Need(good.CanUsePixels&&good.CanRelease,"synthetic full acknowledgement protocol accepted");
  var missing=new WorkReceipt30("x");missing.MarkCommands();missing.StageReady(1);missing.ObserveCompletion("x",true,false,true);Need(!missing.CanUsePixels&&missing.CanRelease,"missing producer stage is not valid output even after barrier");
  var order=new WorkReceipt30("order");order.MarkCommands();order.StageReady(1);Reject(()=>order.StageReady(4),"classifier cannot precede second producer/its completion barrier");Reject(()=>order.StageReady(1),"duplicate producer stage cannot conceal a missing stage");
  Reject(()=>good.MarkCommands(),"cannot append commands after acknowledged end barrier");Reject(()=>good.StageReady(1),"cannot alter stages after acknowledged end barrier");good.ObserveCompletion("x",true,true,true);Need(!good.CanUsePixels&&good.CanRelease,"late error invalidates pixels without undoing a previously proven end barrier");
  var cancelled=new WorkReceipt30("c");cancelled.Fail();Need(cancelled.CanRelease&&!cancelled.CanUsePixels,"cancellation before commands needs no GPU release proof");
  Reject(()=>cancelled.MarkCommands(),"cancelled frame cannot restart recording");var idle=new WorkReceipt30("idle");Reject(()=>idle.StageReady(1),"no recorded commands cannot become a producer output");Reject(()=>idle.ObserveCompletion("idle",true,false,true),"no command/frame cannot fabricate a GPU acknowledgement");
  Console.WriteLine(JsonSerializer.Serialize(new{checks=passed.Count,passed=passed,actualGpuCalls=0,actualGpuAcknowledgementObserved=false,liveDisposeGateIntegrated=false}));
 }
}
