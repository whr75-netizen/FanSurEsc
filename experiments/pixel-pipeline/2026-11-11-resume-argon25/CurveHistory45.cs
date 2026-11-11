// Source-point correspondence, never cached screen RGB or visibility override.
using System;using System.Collections.Generic;using System.Linq;using UnityEngine;
public sealed class CurveHistory45 {
 public readonly struct Scope {
  public readonly string actor,view,model,inputKey;public readonly uint lifetime;
  public Scope(string actor,string view,string model,string inputKey,uint lifetime){
   if(!UInt64.TryParse(actor,out var a)||a==0||!UInt64.TryParse(view,out var v)||v==0||model==null||model.Length!=64||inputKey==null||inputKey.Length!=64||lifetime==0)throw new ArgumentException("45 explicit live actor/view/model/lifetime required");
   this.actor=actor;this.view=view;this.model=model;this.inputKey=inputKey;this.lifetime=lifetime;
  }
  public string Key=>actor+"/"+view+"/"+model+"/"+inputKey+"/lifetime"+lifetime;
 }
 public sealed class Match {
  public bool currentKnown,visible,historyKnown,ambiguous;public string ownerKey,reason,previousSource;
  public CurveCarrier43.Sample current;public Vector3[] previousReprojected=Array.Empty<Vector3>();public float[] previousT=Array.Empty<float>();
 }
 sealed class Point {public int edge;public float t;public string source;}
 readonly Scope scope;readonly CurveCarrier43 carrier;readonly int maxSamples;
 List<Point> previous=new List<Point>(),staging;int committedFrame=-1,stagingFrame;long committedSerial=-1,stagingSerial;string stagingSource;bool retired;
 public string ScopeKey=>scope.Key;public bool Pending=>staging!=null;public int RetainedSamples=>previous.Count;
 public CurveHistory45(Scope scope,CurveCarrier43 carrier,int maxSamples){if(carrier==null||scope.inputKey!=carrier.InputKey||maxSamples<1)throw new ArgumentException("45 source cache/sample budget");this.scope=scope;this.carrier=carrier;this.maxSamples=maxSamples;}
 public void Begin(Scope current,int frame,long serial,string source){
  if(retired||Pending||current.Key!=ScopeKey||frame<0||serial<0||String.IsNullOrEmpty(source)||frame<=committedFrame||serial<=committedSerial)throw new InvalidOperationException("45 invalid lifetime/scope/frame/serial or pending producer");
  staging=new List<Point>();stagingFrame=frame;stagingSerial=serial;stagingSource=source;
 }
 public Match Observe(int edge,float t,Vector3[] evaluatedWorld,bool currentVisible){
  if(!Pending)throw new InvalidOperationException("45 no current source packet");
  var current=carrier.At(scope.model,edge,t,evaluatedWorld);var result=new Match{currentKnown=current.known,visible=currentVisible,ownerKey=ScopeKey+"/SourceCurve/"+current.key,current=current};
  if(!current.known){result.reason=current.reason;return result;}
  if(!currentVisible){result.reason="current source/occlusion rejects history; never restore previous pixels";return result;}
  if(staging.Count>=maxSamples)throw new InvalidOperationException("45 bounded source sample budget exceeded");
  staging.Add(new Point{edge=edge,t=t,source=stagingSource});
  if(committedFrame!=stagingFrame-1){result.reason="first frame or missing consecutive source packet";return result;}
  var candidates=previous.Where(p=>p.edge==edge).ToArray();if(candidates.Length==0){result.reason="source edge newly visible; no invented correspondence";return result;}
  double best=candidates.Min(p=>Math.Abs((double)p.t-t));var nearest=candidates.Where(p=>Math.Abs((double)p.t-t)==best).GroupBy(p=>p.t).Select(g=>g.First()).OrderBy(p=>p.t).ToArray();
  var mapped=nearest.Select(p=>carrier.At(scope.model,p.edge,p.t,evaluatedWorld)).ToArray();if(mapped.Any(p=>!p.known)){result.reason="previous source point no longer has a current valid carrier";return result;}
  result.historyKnown=true;result.ambiguous=mapped.Length>1;result.previousSource=nearest[0].source;result.previousT=nearest.Select(p=>p.t).ToArray();result.previousReprojected=mapped.Select(p=>p.world).ToArray();result.reason=result.ambiguous?"equal source-parameter correspondences retained, not ordered tie-break":"previous feature point re-evaluated on current deformed carrier";return result;
 }
 public void Complete(bool gpuDone,bool gpuError){
  if(!Pending||!gpuDone||gpuError)throw new InvalidOperationException("45 pending/error is not a completed source packet; no history commit");
  previous=staging;staging=null;committedFrame=stagingFrame;committedSerial=stagingSerial;stagingSource=null;
 }
 public void AbortCompletedFailure(bool gpuDone){if(!Pending||!gpuDone)throw new InvalidOperationException("45 cannot discard uncertain in-flight producer");staging=null;previous.Clear();committedFrame=-1;committedSerial=-1;}
 public void Retire(){if(Pending)throw new InvalidOperationException("45 do not retire pending producer");previous.Clear();retired=true;}
}
