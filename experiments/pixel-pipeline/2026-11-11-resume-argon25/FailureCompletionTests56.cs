using System;
public static class FailureCompletionTests56 {
 static void Check(bool b,string why){if(!b)throw new Exception(why);}
 static Submission40 Ticket(){var s=new Submission40("owned",1);s.BeforeCommands();return s;}
 public static void Main(){
  int errors=0,calls=0;bool registered=false;Action<bool,bool,int> callback=null;var s=Ticket();s.Stop();
  Check(FailureCompletion56.AfterStop(ref registered,true,s,"owned",1,c=>{calls++;callback=c;},e=>errors++),"no drain request");Check(calls==1&&!s.CanRelease&&!s.CanUsePixels,"request is not completion");
  Check(!FailureCompletion56.AfterStop(ref registered,true,s,"owned",1,c=>calls++,e=>errors++),"duplicate request");callback(true,false,16);Check(s.CanRelease&&!s.CanUsePixels&&s.HasError,"failed frame became valid");
  registered=false;s=Ticket();s.Stop();FailureCompletion56.AfterStop(ref registered,true,s,"owned",1,c=>{callback=c;throw new Exception("uncertain enqueue");},e=>errors++);Check(!s.CanRelease&&registered,"uncertain enqueue released");Check(!FailureCompletion56.AfterStop(ref registered,true,s,"owned",1,c=>calls++,e=>errors++),"uncertain enqueue retried");callback(true,false,16);Check(s.CanRelease&&!s.CanUsePixels,"real late completion rejected");
  foreach(var status in new[]{new[]{0,0,16},new[]{1,1,16},new[]{1,0,8}}){registered=false;s=Ticket();s.Stop();FailureCompletion56.AfterStop(ref registered,true,s,"owned",1,c=>callback=c,e=>errors++);callback(status[0]==1,status[1]==1,status[2]);Check(!s.CanRelease&&!s.CanUsePixels,"invalid completion released");}
  registered=false;s=Ticket();s.Stop();FailureCompletion56.AfterStop(ref registered,true,s,"other",1,c=>callback=c,e=>errors++);callback(true,false,16);Check(!s.CanRelease,"foreign identity released");
  registered=true;s=Ticket();s.BeforeBarrier();Check(!FailureCompletion56.AfterStop(ref registered,true,s,"owned",1,c=>calls++,e=>errors++),"existing graph completion duplicated");
  registered=false;s=new Submission40("unused",1);s.Stop();Check(!FailureCompletion56.AfterStop(ref registered,true,s,"unused",1,c=>calls++,e=>errors++),"unsubmitted work received GPU request");
  bool rejected=false;registered=false;try{FailureCompletion56.AfterStop(ref registered,false,Ticket(),"owned",1,c=>calls++,e=>errors++);}catch(InvalidOperationException){rejected=true;}Check(rejected,"live recorder drained");
  Console.WriteLine("{\"assertionGroups\":8,\"realCompletionRequired\":true,\"failedPixelsRemainInvalid\":true,\"noRetryAfterUncertainty\":true,\"GPUOrUnityCalls\":0}");
 }
}
