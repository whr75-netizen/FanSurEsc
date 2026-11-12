using System;
public static class ConsumerRegression65 {
 static int checks;
 static void Check(bool ok){checks++;if(!ok)throw new Exception("consumer regression "+checks);}
 static bool Reject(Action a){try{a();return false;}catch(InvalidOperationException){return true;}catch(ArgumentException){return true;}}
 public static void Main(){
  var owners=new ConsumerReads40[6];var tickets=new ConsumerReads40.Ticket[6];
  for(int i=0;i<6;i++){owners[i]=new ConsumerReads40();tickets[i]=owners[i].Begin(262144);Check(!owners[i].CanRelease);int j=i;Check(Reject(()=>owners[j].Begin(16)));}
  // Out-of-order callbacks across owners are legitimate; neither source ID nor
  // disposal depends on the cohort's traversal order.
  foreach(int i in new[]{5,1,3,0,4,2}){owners[i].Complete(tickets[i],true,false,262144);Check(owners[i].CanRelease&&!owners[i].HasError);}
  var a=new ConsumerReads40();var b=new ConsumerReads40();var ta=a.Begin(16);var tb=b.Begin(16);
  a.Complete(tb,true,false,16);Check(a.HasError&&!a.CanRelease&&!b.CanRelease);
  a.Complete(ta,true,false,16);b.Complete(tb,true,false,16);Check(a.CanRelease&&b.CanRelease&&a.HasError);
  var pending=new ConsumerReads40();var ticket=pending.Begin(16);pending.Seal();Check(!pending.CanRelease&&Reject(()=>pending.Begin(16)));pending.Complete(ticket,true,false,16);Check(pending.CanRelease&&!pending.HasError&&Reject(()=>pending.Begin(16)));
  foreach(int kind in new[]{0,1,2}){var x=new ConsumerReads40();var t=x.Begin(16);x.Complete(t,kind!=0,kind==1,kind==2?15:16);Check(x.HasError&&!x.CanRelease);x.Seal();Check(!x.CanRelease&&Reject(()=>x.Begin(16)));}
  Check(Reject(()=>new ConsumerReads40().Begin(262145)));Check(ConsumerReads40.ColourBytes(0,0,256,64,256,64)==262144);
  Check(Reject(()=>ConsumerReads40.ColourBytes(0,0,257,64,257,64)));
  Console.WriteLine("ConsumerRegression65 checks="+checks+"; actual captured one-ticket guard; six distinct owners; no Unity/GPU/device use");
 }
}
