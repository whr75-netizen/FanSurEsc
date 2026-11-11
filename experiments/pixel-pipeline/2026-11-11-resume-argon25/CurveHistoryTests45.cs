using System;using UnityEngine;
public static class CurveHistoryTests45 {
 static void Require(bool b,string why){if(!b)throw new Exception(why);}static bool Throws(Action a){try{a();return false;}catch(InvalidOperationException){return true;}}
 public static void Main(){
  string m=new string('a',64);var uv=new[]{Vector2.zero,Vector2.right,Vector2.up,new Vector2(.5f,.5f),Vector2.one};var tri=new[]{0,1,2,3,2,4};var weld=new[]{0,1,2,0,1};var p=new[]{Vector3.zero,Vector3.right,Vector3.up,Vector3.zero,Vector3.right};var c=new CurveCarrier43(m,1,3,tri,weld,uv);var s=new CurveHistory45.Scope("123","456",m,c.InputKey,1);var h=new CurveHistory45(s,c,16);
  h.Begin(s,10,20,"packet-A");Require(!h.Observe(2,.25f,p,true).historyKnown,"first frame invented history");h.Observe(2,.75f,p,true);Require(Throws(()=>h.Complete(false,false))&&h.Pending&&h.RetainedSamples==0,"pending committed");Require(Throws(()=>h.Begin(s,11,21,"duplicate")),"pending resubmitted");h.Complete(true,false);
  for(int i=0;i<p.Length;i++)p[i]+=new Vector3(.1f,.2f,.3f);
  h.Begin(s,11,22,"packet-B");var t=h.Observe(2,.5f,p,true);Require(t.historyKnown&&t.ambiguous&&t.previousT.Length==2&&t.previousT[0]==.25f&&t.previousT[1]==.75f,"equal correspondences silently ordered");Require(t.previousReprojected[0].Equals(Vector3.LerpUnclamped(p[0],p[2],.25f)),"history frozen in screen/world coordinates");Require(!h.Observe(2,.25f,p,false).historyKnown,"occlusion revived previous pixels");h.Complete(true,false);
  Require(Throws(()=>h.Begin(new CurveHistory45.Scope("124","456",m,c.InputKey,1),12,23,"foreign")),"actor cache mixed");Require(Throws(()=>h.Begin(new CurveHistory45.Scope("123","457",m,c.InputKey,1),12,23,"foreign")),"view cache mixed");Require(Throws(()=>h.Begin(new CurveHistory45.Scope("123","456",m,c.InputKey,2),12,23,"reinit")),"lifetime mixed");
  h.Begin(s,13,24,"gap");Require(!h.Observe(2,.5f,p,true).historyKnown,"missing frame treated continuous");Require(Throws(()=>h.Retire()),"pending retired");h.AbortCompletedFailure(true);Require(h.RetainedSamples==0&&!h.Pending,"completed failure retained history");h.Retire();Require(Throws(()=>h.Begin(s,14,25,"retired")),"retired lifetime reused");
  Console.WriteLine("{\"assertionGroups\":13,\"scopeIsolation\":true,\"occlusionOverridesHistory\":true,\"equalCorrespondencesRetained\":true,\"pendingBlocksCommitAndReuse\":true,\"GPUCalls\":0}");
 }
}
