using System;
using System.IO;
using UnityEngine;
// Existing validated stimuli, narrowed to Close/reopen and same-pose hair controls.
// No test value or phase label enters any feature allocation or visibility pass.
public sealed class Sequence111:IDisposable{
 readonly NativePlayer395 n;readonly string root;MotionClose106 blink;HoldMorph107 hold;HairDrawScope107 hair;int phase;bool disposed;readonly Arr58 reports=new Arr58();
 public Sequence111(NativePlayer395 value,string path){n=value;root=path;}
 public string Stage=>phase==0?blink.Stage:"Close75-"+(hair==null?"waiting":hair.Stage);
 public int StageIndex=>phase==0?blink.StageIndex:hair==null?-1:hair.StageIndex;
 public Arr58 warmup=>phase==0?blink.warmup:hair==null?new Arr58():hair.warmup;
 public Arr58 dynamicInput=>phase==0?blink.dynamicInput:hair==null?new Arr58():hair.dynamicInput;
 public bool HasWarmup=>true;public bool CaptureThis=>true;public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public void Start(){var p=Path.Combine(root,"blink111");Directory.CreateDirectory(p);blink=new MotionClose106(n,p);blink.Start();}
 public bool Ready(int serial){if(phase==0)return blink.Ready(serial);if(!hold.Ready())return false;if(hair==null){var p=Path.Combine(root,"hair111");Directory.CreateDirectory(p);hair=new HairDrawScope107(n,p);hair.Start();return false;}return hair.Ready(serial);}
 public Obj58 Snapshot(){var q=phase==0?blink.Snapshot():hair.Snapshot();if(phase==1){q["requestedClose"]=75;q["evaluatedCloseError111"]=hold.Error;}return q;}
 public bool Advance(){if(phase==1)return hair.Advance();if(blink.Advance())return true;blink.Dispose();reports.Add(blink.RestoreReport);if(!blink.Restored)throw new InvalidOperationException("111 blink restoration failed");phase=1;var p=Path.Combine(root,"hold111");Directory.CreateDirectory(p);hold=new HoldMorph107(n,p,75);return true;}
 public void Dispose(){if(disposed)return;disposed=true;hair?.Dispose();hold?.Dispose();blink?.Dispose();if(hair!=null)reports.Add(hair.RestoreReport);if(hold!=null)reports.Add(hold.Report);Restored=(blink==null||blink.Restored)&&(hold==null||hold.Restored)&&(hair==null||hair.Restored);RestoreReport=new Obj58{["allRestored"]=Restored,["reports"]=reports,["InputSettingsReplacement"]=false};}
}
