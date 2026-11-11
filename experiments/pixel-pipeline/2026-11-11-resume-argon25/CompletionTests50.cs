using System;
public static class CompletionTests50 {
 static Submission40 Submitted(){var t=new Submission40("frame",1);t.BeforeCommands();foreach(int s in new[]{1,2,4,8})t.StageRecorded(s);return t;}
 static void Require(bool b,string why){if(!b)throw new Exception(why);}
 public static void Main(){
  var failed=Submitted();int fences=0;CompletionScope50.Record(()=>throw new InvalidOperationException("managed mode guard"),e=>failed.Fail(),()=>{fences++;failed.BeforeBarrier();});Require(fences==1&&failed.HasError&&!failed.CanRelease,"failure skipped real fence wait");failed.AcceptCallback("frame",1,true,false);Require(failed.CanRelease&&!failed.CanUsePixels,"cleanup turned failed pixels valid");
  var ok=Submitted();CompletionScope50.Record(()=>{},e=>ok.Fail(),ok.BeforeBarrier);Require(!ok.CanRelease,"recording treated as GPU completion");ok.AcceptCallback("frame",1,true,false);Require(ok.CanRelease&&ok.CanUsePixels,"normal completion");
  var uncertain=Submitted();CompletionScope50.Record(()=>throw new Exception("fail"),e=>uncertain.Fail(),uncertain.BeforeBarrier);uncertain.AcceptCallback("frame",1,false,false);Require(!uncertain.CanRelease,"incomplete callback freed resources");
  var error=Submitted();CompletionScope50.Record(()=>{},e=>error.Fail(),error.BeforeBarrier);error.AcceptCallback("frame",1,true,true);Require(!error.CanRelease,"error callback freed resources");
  var foreign=Submitted();CompletionScope50.Record(()=>{},e=>foreign.Fail(),foreign.BeforeBarrier);foreign.AcceptCallback("other",1,true,false);Require(!foreign.CanRelease,"foreign completion accepted");
  bool retryRejected=false;try{foreign.BeforeBarrier();}catch(InvalidOperationException){retryRejected=true;}Require(retryRejected,"uncertain barrier repeated");
  Console.WriteLine("{\"assertionGroups\":6,\"failedPixelsRemainInvalid\":true,\"GPUCompletionSeparateFromNormalExit\":true,\"pendingAndErrorRetained\":true,\"GPUOrUnityCalls\":0,\"running49CodeUpdated\":false}");
 }
}
