using System;
using System.IO;
using UnityEngine;
// Stimulus owner only. No test label or morph value is supplied to the solver.
public sealed class Sequence107:IDisposable{
 readonly NativePlayer395 n;readonly string directory;MotionClose106 close;MotionScope97 motion;HoldMorph107 hold;HairDrawScope107 hair;int phase;bool disposed;readonly Arr58 reports=new Arr58();
 public Sequence107(NativePlayer395 value,string path){n=value;directory=path;}
 public string Stage=>phase==0?close.Stage:phase==3?"partial-hair-"+(hair==null?"prepare":hair.Stage):(phase==2?"closed-":"open-")+motion.Stage;
 public int StageIndex=>phase==0?close.StageIndex:phase==3?(hair==null?-1:hair.StageIndex):motion.StageIndex;
 public Arr58 warmup=>phase==0?close.warmup:phase==3?(hair==null?new Arr58():hair.warmup):motion.warmup;
 public Arr58 dynamicInput=>phase==0?close.dynamicInput:phase==3?(hair==null?new Arr58():hair.dynamicInput):motion.dynamicInput;
 public bool HasWarmup=>true;public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public bool CaptureThis=>phase!=2||motion.Stage=="turn"||(motion.Stage=="measured-phase"&&(motion.StageIndex==0||motion.StageIndex==4||motion.StageIndex==8||motion.StageIndex==9));
 public void Start(){string path=Path.Combine(directory,"blink107");Directory.CreateDirectory(path);close=new MotionClose106(n,path);close.Start();}
 public bool Ready(int serial){if(phase==0)return close.Ready(serial);if(phase==3){if(!hold.Ready())return false;if(hair==null){hair=new HairDrawScope107(n,Path.Combine(directory,"partial-hair107"));hair.Start();return false;}return hair.Ready(serial);}return motion.Ready(serial)&&(phase!=2||hold.Ready());}
 public Obj58 Snapshot(){var r=phase==0?close.Snapshot():phase==3?hair.Snapshot():motion.Snapshot();r["sequenceStage107"]=Stage;if(phase==2||phase==3){r["actualClose107"]=phase==2?100:25;r["evaluatedCloseError107"]=hold.Error;}return r;}
 void StartMotion(){var path=Path.Combine(directory,phase==1?"open-motion107":"closed-motion107");Directory.CreateDirectory(path);motion=new MotionScope97(n,path);motion.Start();}
 public bool Advance(){
  if(phase==0){if(close.Advance())return true;close.Dispose();reports.Add(close.RestoreReport);if(!close.Restored)throw new InvalidOperationException("107 blink restore failed");phase=1;StartMotion();return true;}
  if(phase==3)return hair.Advance();
  if(motion.Advance())return true;motion.Dispose();reports.Add(motion.RestoreReport);if(!motion.Restored)throw new InvalidOperationException("107 motion restore failed");
  if(phase==1){phase=2;StartMotion();hold=new HoldMorph107(n,directory,100);return true;}
  hold.Dispose();reports.Add(hold.Report);if(!hold.Restored)throw new InvalidOperationException("107 closed morph restore failed");hold=null;phase=3;
  string d=Path.Combine(directory,"partial-hair107");Directory.CreateDirectory(d);hold=new HoldMorph107(n,d,25);return true;
 }
 public void Dispose(){if(disposed)return;disposed=true;hold?.Dispose();hair?.Dispose();motion?.Dispose();close?.Dispose();if(hold!=null)reports.Add(hold.Report);if(hair!=null)reports.Add(hair.RestoreReport);if(motion!=null)reports.Add(motion.RestoreReport);Restored=(close==null||close.Restored)&&(motion==null||motion.Restored)&&(hold==null||hold.Restored)&&(hair==null||hair.Restored);RestoreReport=new Obj58{["allRestored"]=Restored,["scopeReports"]=reports,["InputSettingsReplacement"]=false};}
}
