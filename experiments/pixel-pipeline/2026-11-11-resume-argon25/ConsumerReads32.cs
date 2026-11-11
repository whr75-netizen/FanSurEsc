// Pure managed lifetime for later diagnostic consumers of producer-owned RTs.
using System;
public sealed class ConsumerReads32 {
 public sealed class Ticket{internal Ticket(){}}
 readonly object sync=new object();Ticket active;int bytes;bool closed,failed,rejected;
 public Ticket Begin(int expectedBytes){lock(sync){if(closed||failed||active!=null)throw new InvalidOperationException("32 closed/failed/pending consumer; no duplicate submission");if(expectedBytes<=0||expectedBytes>262144)throw new ArgumentOutOfRangeException(nameof(expectedBytes));bytes=expectedBytes;active=new Ticket();return active;}}
 public void Complete(Ticket token,bool done,bool error,int actualBytes){lock(sync){
  if(token==null||!Object.ReferenceEquals(token,active)){failed=true;return;}
  if(rejected){failed=true;return;}
  if(!done||error||actualBytes!=bytes){failed=true;rejected=true;return;}
  active=null;bytes=0;
 }}
 public void Fail(){lock(sync){failed=true;}}
 public void Seal(){lock(sync){closed=true;}}
 public bool CanRelease{get{lock(sync){return active==null;}}}
 public bool HasError{get{lock(sync){return failed;}}}
 public static int ColourBytes(int x,int y,int width,int height,int targetWidth,int targetHeight){
  if(x<0||y<0||width<=0||height<=0||targetWidth<=0||targetHeight<=0||(long)x+width>targetWidth||(long)y+height>targetHeight)throw new ArgumentException("32 readback ROI");
  long pixels=(long)width*height;if(pixels>262144/16)throw new ArgumentException("32 one bounded row/strip at a time");return checked((int)pixels*16);
 }
}

// Readback callbacks may request exit without touching any Editor API. Only the
// creating Editor thread can drain the request in its explicit observer tick.
public sealed class EditorExitRequest32 {
 readonly int ownerThread=Environment.CurrentManagedThreadId;int queued;bool handled;
 public void Request(){System.Threading.Interlocked.Exchange(ref queued,1);}
 public void RequireOwner(){if(Environment.CurrentManagedThreadId!=ownerThread)throw new InvalidOperationException("32 drain on the creating Editor thread only");}
 public void Drain(Action begin){RequireOwner();if(!handled&&System.Threading.Volatile.Read(ref queued)!=0){handled=true;begin();}}
 public bool Requested=>System.Threading.Volatile.Read(ref queued)!=0;
}
