using System;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Experimental.Rendering;
using Unity.Collections;
using UnityEditor;

// Only cloned shaders and four owned comparison outputs. No global setters,
// borrowed output writes, settings replacement or C# Asset import.
public sealed class ComposeComparison87:IDisposable
{
 public const string CandidateAsset="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/CachedSourceRole87.compute";
 readonly Full319View335 view;readonly ComputeShader borrowed,original,candidate;
 public readonly RTHandle[] outputs=new RTHandle[4];bool installed,disposed;
 public bool Restored{get;private set;}public Obj58 RestoreReport{get;private set;}
 public bool InstalledAndActive=>installed&&view&&view.eyeCompose==candidate;
 public ComposeComparison87(Full319View335 v){
  view=v;borrowed=v.eyeCompose;if(!borrowed||EditorUtility.IsPersistent(v))throw new InvalidOperationException("Runtime eye view and source shader required");
  try{original=UnityEngine.Object.Instantiate(borrowed);candidate=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<ComputeShader>(CandidateAsset));original.hideFlags=candidate.hideFlags=HideFlags.DontSave;for(int i=0;i<4;i++)outputs[i]=RTHandles.Alloc(480,272,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"87 owned old333 comparison "+i);}catch{Dispose();throw;}
 }
 public void ReplayOriginal(){
  var v=view;var cs=original;int k=cs.FindKernel("Compose");var cmd=CommandBufferPool.Get("87 original333 replay into owned outputs");
  try{
   cmd.SetComputeIntParams(cs,"_LogicalSize",480,272);cmd.SetComputeIntParams(cs,"_TemplateSize",480,272);cmd.SetComputeIntParam(cs,"_CellSize",1);
   for(int i=0;i<2;i++){cmd.SetComputeMatrixParam(cs,"_Inverse262_"+i,v.eyeInverse[i]);cmd.SetComputeVectorParam(cs,"_Plane262_"+i,v.eyePlanes[i]);cmd.SetComputeIntParam(cs,"_Visible262_"+i,1);Vector4[]Pack(Vector2[]a){var r=new Vector4[32];for(int j=0;j<a.Length;j++)r[j]=a[j];return r;}cmd.SetComputeVectorArrayParam(cs,"_Parent295_"+i,Pack(v.contours.eyes[i].parent));cmd.SetComputeVectorArrayParam(cs,"_Iris295_"+i,Pack(v.contours.eyes[i].iris));cmd.SetComputeIntParam(cs,"_ParentCount295_"+i,v.contours.eyes[i].parent.Length);cmd.SetComputeIntParam(cs,"_IrisCount295_"+i,v.contours.eyes[i].iris.Length);var b=v.calibration.eyes[i].referenceBounds;cmd.SetComputeIntParams(cs,"_ColourBounds295_"+i,Mathf.FloorToInt(b.x)-1,Mathf.FloorToInt(b.y)-1,Mathf.CeilToInt(b.z)+1,Mathf.CeilToInt(b.w)+1);}
   cmd.SetComputeVectorParam(cs,"_RayBase",v.rayBase);cmd.SetComputeVectorParam(cs,"_RayX",v.rayX);cmd.SetComputeVectorParam(cs,"_RayY",v.rayY);cmd.SetComputeVectorParam(cs,"_RayDepth",v.rayDepth);
   void T(string n,RTHandle t)=>cmd.SetComputeTextureParam(cs,k,n,t.rt);
   T("_Reference",v.prepared);T("_OriginalFullMeta",v.layers[9].meta);T("_BaseRGBA",v.layers[8].rgba);T("_BaseMETA",v.layers[8].meta);T("_BackingMETA",v.layers[10].meta);T("_AllHairMETA",v.layers[6].meta);T("_TaggedHairMETA",v.layers[11].meta);T("_TaggedHairUV",v.layers[11].uv);T("_OtherHairRGBA",v.layers[12].rgba);T("_OtherHairMETA",v.layers[12].meta);T("_BrowRGBA",v.layers[7].rgba);T("_BrowMETA",v.layers[7].meta);cmd.SetComputeTextureParam(cs,k,"_TemplateRGBA",v.templateRGBA);cmd.SetComputeTextureParam(cs,k,"_TemplateRole",v.templateRole);
   foreach(var row in new[]{new{n="_Colour",i=0},new{n="_Owner",i=1},new{n="_Intrinsic",i=2},new{n="_Audit",i=3}})T(row.n,outputs[row.i]);cmd.DispatchCompute(cs,k,60,34,1);Graphics.ExecuteCommandBuffer(cmd);
  }finally{CommandBufferPool.Release(cmd);}
 }
 NativeArray<Color> Read(RenderTexture t,RectInt roi){var data=new NativeArray<Color>(roi.width*roi.height,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);try{var req=AsyncGPUReadback.RequestIntoNativeArray(ref data,t,0,roi.x,roi.width,roi.y,roi.height,0,1,TextureFormat.RGBAFloat);req.WaitForCompletion();if(req.hasError)throw new InvalidOperationException("87 bounded readback failed");return data;}catch{data.Dispose();throw;}}
 public Obj58 Calibrate(RectInt roi){
  ReplayOriginal();var rows=new Arr58();var actual=new[]{view.eyeOutput,view.eyeOwner,view.intrinsic,view.eyeAudit};bool pass=true;
  for(int channel=0;channel<4;channel++){NativeArray<Color>a=default,b=default;int count=0;float error=0;var first=new Arr58();try{a=Read(outputs[channel].rt,roi);b=Read(actual[channel].rt,roi);for(int i=0;i<a.Length;i++){var x=a[i];var y=b[i];if(x.r!=y.r||x.g!=y.g||x.b!=y.b||x.a!=y.a){count++;error=Math.Max(error,Math.Max(Math.Max(Math.Abs(x.r-y.r),Math.Abs(x.g-y.g)),Math.Max(Math.Abs(x.b-y.b),Math.Abs(x.a-y.a))));if(first.Count<4)first.Add(new Obj58{["xyBottomLeft"]=new Arr58(roi.x+i%roi.width,roi.y+i/roi.width),["replay"]=new Arr58(x.r,x.g,x.b,x.a),["actual"]=new Arr58(y.r,y.g,y.b,y.a)});}}}finally{if(a.IsCreated)a.Dispose();if(b.IsCreated)b.Dispose();}pass&=count==0;rows.Add(new Obj58{["channel"]=channel,["changedCells"]=count,["maxError"]=error,["first"]=first});}
  return new Obj58{["pass"]=pass,["source"]="same original shader/actual current inputs/reference prepared colour; owned outputs only",["rows"]=rows};
 }
 public void Install(){if(disposed||installed||view.eyeCompose!=borrowed)throw new InvalidOperationException("Unexpected compose reference before install");view.eyeCompose=candidate;installed=true;}
 public void Dispose(){if(disposed)return;disposed=true;var errors=new Arr58();void Try(Action a){try{a();}catch(Exception e){errors.Add(e.Message);}}
  bool reference=!installed;Try(()=>{if(installed){if(view&&view.eyeCompose==candidate){view.eyeCompose=borrowed;reference=view.eyeCompose==borrowed;}else if(view&&view.eyeCompose==borrowed)reference=true;else throw new InvalidOperationException("Unexpected borrowed eyeCompose reference; not overwriting foreign change");}});
  foreach(var t in outputs)Try(()=>t?.Release());Try(()=>{if(original)UnityEngine.Object.DestroyImmediate(original);});Try(()=>{if(candidate)UnityEngine.Object.DestroyImmediate(candidate);});Restored=errors.Count==0&&reference;RestoreReport=new Obj58{["composeReference"]=reference,["ownedOutputsReleaseAttempted"]=true,["ownedClonesReleaseAttempted"]=true,["borrowedResourcesReleased"]=false,["errors"]=errors,["allRestored"]=Restored};
 }
}
