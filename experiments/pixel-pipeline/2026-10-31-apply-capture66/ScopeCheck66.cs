using System;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEngine.Profiling;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

internal class CommandScript : IRunCommand
{
 public void Execute(ExecutionResult result)
 {
  if(EditorApplication.isCompiling||EditorApplication.isUpdating||EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Stable Edit required");
  var scene=SceneManager.GetActiveScene();bool dirty=scene.isDirty;
  long before=Profiler.GetTotalAllocatedMemoryLong();var checks=NativeScope65Parity.Run();
  checks["utc"]=DateTime.UtcNow.ToString("O");checks["sceneBefore"]=scene.path;checks["sceneDirtyBefore"]=dirty;checks["sceneDirtyAfter"]=scene.isDirty;checks["allocatedBefore"]=before;checks["allocatedAfter"]=Profiler.GetTotalAllocatedMemoryLong();
  checks["limits"]="Extracted production owner logic with real Unity buffers/materials; does not invoke the private production dictionary or render a frame. Actual runtime bindings must be checked before capture.";
  File.WriteAllText(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\apply-capture66\SCOPE_NATIVE65.json",checks.ToString());
  result.Log("65 native owner parity/material scope checks passed; owned buffers released; no Play/render/global-buffer writes");
 }
}

static class NativeScope65Parity
{
 // EXTRACT_OWNER65
 static void Require(bool condition,string reason){if(!condition)throw new InvalidOperationException(reason);}
 public static Obj58 Run()
 {
  var a=new BodyScopeResources551();var b=new BodyScopeResources551();UnityEngine.Material ma=null,mb=null;
  ComputeBuffer first=null,second=null,mask=null;var r=new Obj58();
  try
  {
   first=a.Buffer();second=b.Buffer();Require(ReferenceEquals(first,a.Buffer()),"duplicate native fallback");
   var data=new float[1];first.GetData(data);Require(data[0]==1f,"fallback data changed");
   var shader=Shader.Find("EValidation/VisibilityMotion331Probe");if(!shader)throw new InvalidOperationException("Existing Probe331 shader unavailable");
   ma=new UnityEngine.Material(shader){hideFlags=HideFlags.HideAndDontSave};mb=new UnityEngine.Material(shader){hideFlags=HideFlags.HideAndDontSave};
   ma.SetBuffer("_BodyScope551",first);mb.SetBuffer("_BodyScope551",second);
   var one=ma.GetBuffer("_BodyScope551");var two=mb.GetBuffer("_BodyScope551");
   Require(!one.Equals(default(GraphicsBufferHandle))&&!two.Equals(default(GraphicsBufferHandle))&&!one.Equals(two),"material-local native bindings not isolated");
   mb.SetBuffer("_BodyScope551",first);Require(ma.GetBuffer("_BodyScope551").Equals(mb.GetBuffer("_BodyScope551")),"local handle comparison");
   a.Commit(null,null,new[]{true,false,true},new[]{1f,0f,1f},2);mask=a.Buffer();Require(!first.IsValid()&&mask.IsValid(),"atomic replacement lifetime");
   var actual=new float[3];mask.GetData(actual);Require(actual[0]==1&&actual[1]==0&&actual[2]==1&&a.Count==2,"mask data changed");
   ma.SetBuffer("_BodyScope551",mask);Require(!ma.GetBuffer("_BodyScope551").Equals(one),"material not rebound after replacement");
   try{a.Commit(null,null,new bool[0],new float[0],0);throw new Exception("invalid mask accepted");}catch(ArgumentException){}
   Require(ReferenceEquals(mask,a.Buffer())&&mask.IsValid(),"invalid candidate lost previous buffer");
   UnityEngine.Object.DestroyImmediate(ma);ma=null;UnityEngine.Object.DestroyImmediate(mb);mb=null;
   a.Dispose();a.Dispose();Require(!mask.IsValid()&&second.IsValid(),"owner A disposal touched owner B");
   b.Dispose();b.Dispose();Require(!second.IsValid(),"owner B not released");
   r["passed"]=true;r["nativeBuffersCreated"]=3;r["ownedBuffersAllInvalidAfterDispose"]=!first.IsValid()&&!second.IsValid()&&!mask.IsValid();r["materialHandleIsolation"]=true;r["uploadDataMatches"]=true;r["repeatDisposeSafe"]=true;r["invalidMaskPreservesPrevious"]=true;r["globalBufferWrites"]=0;r["GPUDispatches"]=0;r["readbackFloatCount"]=4;
  }
  finally{if(ma)UnityEngine.Object.DestroyImmediate(ma);if(mb)UnityEngine.Object.DestroyImmediate(mb);a.Dispose();b.Dispose();}
  return r;
 }
}
