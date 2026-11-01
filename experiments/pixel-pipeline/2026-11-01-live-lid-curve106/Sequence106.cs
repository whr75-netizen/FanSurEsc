using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;

// Observer stimuli only. Algorithm receives no Close value or test-stage flag.
public sealed class HoldClose106:IDisposable{
 readonly NativePlayer395 n;readonly SkinnedMeshRenderer source;readonly int morph;readonly float previous;readonly Action hook;
 readonly UnityEngine.Mesh expected;readonly List<Vector3> wanted=new List<Vector3>(),actual=new List<Vector3>();bool disposed;int waits;
 public bool Restored{get;private set;}public float Error{get;private set;}public Obj58 Report{get;private set;}
 void Apply(){if(source)source.SetBlendShapeWeight(morph,100);}
 public HoldClose106(NativePlayer395 native,string path){n=native;source=n.host.main.motion.surface.source[1];morph=source.sharedMesh.GetBlendShapeIndex("Fcl_EYE_Close");if(morph<0)throw new InvalidOperationException("106 supported Close source missing");previous=source.GetBlendShapeWeight(morph);hook=n.host.afterPose;CreateOnly73.Text(Path.Combine(path,"CLOSED_MOTION_BEFORE106.json"),new Obj58{["morph"]=morph,["value"]=previous,["sourceId"]=source.GetEntityId().ToString(),["hookPresent"]=hook!=null}.ToString());expected=new UnityEngine.Mesh{name="106 owned closed motion reference",hideFlags=HideFlags.DontSave};n.host.afterPose+=Apply;}
 public bool Ready(){if(disposed||!source||source.GetBlendShapeWeight(morph)!=100)return false;source.BakeMesh(expected,true);expected.GetVertices(wanted);var filter=n.host.head.motion.surface.outputs[1];filter.sharedMesh.GetVertices(actual);if(wanted.Count!=actual.Count)throw new InvalidOperationException("106 closed motion evaluated topology mismatch");var map=filter.transform.worldToLocalMatrix*source.localToWorldMatrix;Error=0;for(int i=0;i<wanted.Count;i++)Error=Mathf.Max(Error,(map.MultiplyPoint3x4(wanted[i])-actual[i]).magnitude);if(Error<=2e-6f){waits=0;return true;}if(++waits>12)throw new InvalidOperationException("106 evaluated Close motion source mismatch; no timeout extension");return false;}
 public void Dispose(){if(disposed)return;disposed=true;var errors=new Arr58();try{if(!n||!n.host||!source)throw new InvalidOperationException("106 borrowed morph/hook owner lost");n.host.afterPose-=Apply;if(n.host.afterPose!=hook)throw new InvalidOperationException("106 borrowed hook changed");source.SetBlendShapeWeight(morph,previous);}catch(Exception e){errors.Add(e.ToString());}if(expected)UnityEngine.Object.DestroyImmediate(expected);Restored=errors.Count==0&&source&&source.GetBlendShapeWeight(morph)==previous;Report=new Obj58{["restored"]=Restored,["errors"]=errors,["ownedReferenceDisposed"]=!expected};}
}
public sealed class Sequence106:IDisposable{
 readonly NativePlayer395 n;readonly string directory;MotionClose106 close;MotionScope97 motion;HoldClose106 hold;int phase;bool disposed;readonly Arr58 restorations=new Arr58();
 public Sequence106(NativePlayer395 value,string path){n=value;directory=path;}
 public string Stage=>phase==0?close.Stage:(phase==2?"closed-":"open-")+motion.Stage;
 public int StageIndex=>phase==0?close.StageIndex:motion.StageIndex;
 public Arr58 warmup=>phase==0?close.warmup:motion.warmup;public Arr58 dynamicInput=>phase==0?close.dynamicInput:motion.dynamicInput;
 public bool HasWarmup=>true;public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public bool CaptureThis=>phase!=2||motion.Stage=="turn"||(motion.Stage=="measured-phase"&&(motion.StageIndex==0||motion.StageIndex==4||motion.StageIndex==8||motion.StageIndex==9));
 public void Start(){var path=Path.Combine(directory,"blink106");Directory.CreateDirectory(path);close=new MotionClose106(n,path);close.Start();}
 public bool Ready(int serial)=>phase==0?close.Ready(serial):motion.Ready(serial)&&(phase!=2||hold.Ready());
 public Obj58 Snapshot(){var r=phase==0?close.Snapshot():motion.Snapshot();r["sequenceStage106"]=Stage;if(phase==2){r["actualClose106"]=100;r["evaluatedCloseError106"]=hold.Error;}return r;}
 public bool Advance(){if(phase==0){if(close.Advance())return true;close.Dispose();restorations.Add(close.RestoreReport);if(!close.Restored)throw new InvalidOperationException("106 blink stimulus restore failed");phase=1;StartMotion();return true;}if(motion.Advance())return true;motion.Dispose();restorations.Add(motion.RestoreReport);if(!motion.Restored)throw new InvalidOperationException("106 open motion restore failed");if(phase==1){phase=2;StartMotion();hold=new HoldClose106(n,directory);return true;}return false;}
 void StartMotion(){var path=Path.Combine(directory,phase==1?"open-motion106":"closed-motion106");Directory.CreateDirectory(path);motion=new MotionScope97(n,path);motion.Start();}
 public void Dispose(){if(disposed)return;disposed=true;hold?.Dispose();motion?.Dispose();close?.Dispose();if(hold!=null)restorations.Add(hold.Report);if(motion!=null)restorations.Add(motion.RestoreReport);Restored=(close==null||close.Restored)&&(motion==null||motion.Restored)&&(hold==null||hold.Restored);RestoreReport=new Obj58{["allRestored"]=Restored,["scopeReports"]=restorations,["InputSettingsReplacement"]=false};}
}
