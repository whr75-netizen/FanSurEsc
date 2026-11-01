using System;
public sealed class MotionScope98:IDisposable{
 readonly NativePlayer395 native;readonly string directory;MotionScope97 motion;MotionScope95 blink;bool blinkStage,disposed;
 public Arr58 warmup=>blinkStage?blink.warmup:motion.warmup;public Arr58 dynamicInput=>motion.dynamicInput;
 public string Stage=>blinkStage?blink.Stage:motion.Stage;public int StageIndex=>blinkStage?blink.StageIndex:motion.StageIndex;public bool HasWarmup=>blinkStage?blink.HasWarmup:motion.HasWarmup;
 public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public MotionScope98(NativePlayer395 n,string d){native=n;directory=d;motion=new MotionScope97(n,d);}
 public void Start()=>motion.Start();public bool Ready(int serial)=>blinkStage?blink.Ready(serial):motion.Ready(serial);public Obj58 Snapshot()=>blinkStage?blink.Snapshot():motion.Snapshot();
 public bool Advance(){if(blinkStage)return blink.Advance();if(motion.Advance())return true;motion.Dispose();if(!motion.Restored)throw new InvalidOperationException("98 motion scope must restore before Close scope");blinkStage=true;blink=new MotionScope95(native,directory);blink.Start();return true;}
 public void Dispose(){if(disposed)return;disposed=true;blink?.Dispose();motion?.Dispose();Restored=motion.Restored&&(blink==null||blink.Restored);RestoreReport=new Obj58{["allRestored"]=Restored,["motion"]=motion.RestoreReport,["Close"]=blink?.RestoreReport};}
}
