// Cleanup-only completion for submitted work whose final camera never recorded.
// Called only by the existing owner-thread exit pump after recording is stopped.
// Never manufactures a completion, enables pixels, or retries an uncertain API.
using System;
public static class FailureCompletion56 {
 public static bool AfterStop(ref bool registered,bool stopped,Submission40 ticket,string key,int generation,
     Action<Action<bool,bool,int>> enqueue,Action<Exception> failed){
  if(!stopped)throw new InvalidOperationException("56 completion drain requires stopped recording");
  if(registered||ticket==null||!ticket.CommandsPossible||ticket.CanRelease)return false;
  registered=true;ticket.Fail();
  try{
   ticket.BeforeBarrier();
   enqueue((done,error,bytes)=>{
    try{bool invalid=error||bytes!=16;ticket.AcceptCallback(key,generation,done,invalid);if(!done||invalid)failed(new InvalidOperationException("56 incomplete/error/size completion; retain resources"));}
    catch(Exception e){failed(e);}
   });
  }catch(Exception e){failed(e);}
  return true;
 }
}
