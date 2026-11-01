using System;
public sealed class Sequence102:IDisposable{
 readonly NativePlayer395 n;readonly string directory;HairDrawScope100 hair;MotionScope95 close;bool closing,disposed;
 public Arr58 warmup=>closing?close.warmup:hair.warmup;public Arr58 dynamicInput=>closing?close.dynamicInput:hair.dynamicInput;
 public string Stage=>closing?close.Stage:hair.Stage;public int StageIndex=>closing?close.StageIndex:hair.StageIndex;public bool HasWarmup=>true;
 public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public Sequence102(NativePlayer395 value,string d){n=value;directory=d;hair=new HairDrawScope100(n,d);}
 public void Start(){hair.Start();if(!hair.Advance())throw new InvalidOperationException("102 initial hair-off scope unavailable");}
 public bool Ready(int serial)=>closing?close.Ready(serial):hair.Ready(serial);
 public Obj58 Snapshot()=>closing?close.Snapshot():hair.Snapshot();
 public bool Advance(){if(closing)return close.Advance();if(hair.Advance())return true;hair.Dispose();if(!hair.Restored)throw new InvalidOperationException("102 hair restoration failed before evaluated Close");closing=true;close=new MotionScope95(n,directory);close.Start();return true;}
 public void Dispose(){if(disposed)return;disposed=true;close?.Dispose();hair?.Dispose();Restored=hair.Restored&&(close==null||close.Restored);RestoreReport=new Obj58{["hair"]=hair.RestoreReport,["Close"]=close?.RestoreReport,["allRestored"]=Restored};}
}
