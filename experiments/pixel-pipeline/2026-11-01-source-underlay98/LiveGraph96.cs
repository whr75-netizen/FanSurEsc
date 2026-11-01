using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;

// Attached only to the isolated source pass, after source field writes.
public sealed class LiveGraph96:IDisposable{
 public readonly LiveSurface96 Source;readonly EyeFeature348 eye;readonly NativeRetarget96 retarget;public int RecordedFrame{get;private set;}=-1;public bool Disposed{get;private set;}
 sealed class Data{public LiveGraph96 owner;public Matrix4x4 view,projection;}
 public LiveGraph96(EyeFeature348 e,NativeRetarget96 native,string registration){eye=e;retarget=native;var reg=Json58.Parse(File.ReadAllText(registration));var ids=reg["eyes"].Select(x=>(int)x["eye"]).OrderBy(x=>x).ToArray();var px=new Vector4[2];var py=new Vector4[2];for(int i=0;i<2;i++){var row=reg["eyes"].Single(x=>(int)x["eye"]==ids[i]);for(int c=0;c<4;c++){px[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][0];py[i][c]=(float)(double)row["nativeToAuthoredProjection"][c][1];}}Source=new LiveSurface96(e,AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/WholeEye98.compute"),ids,px,py);}
 public void Record(RenderGraph graph){if(Disposed)throw new ObjectDisposedException(nameof(LiveGraph96));var e=Source.Engine;Source.Update();e.Resize(retarget.currentWidth,retarget.currentHeight,Source.Scope);using var builder=graph.AddUnsafePass<Data>("96 owned source-local BVH and joint selection",out var d);d.owner=this;d.view=eye.full.motion.camera.worldToCameraMatrix;d.projection=eye.full.motion.camera.projectionMatrix;foreach(var b in e.Buffers)builder.UseBuffer(graph.ImportBuffer(b),AccessFlags.ReadWrite);foreach(var a in retarget.Handles96)foreach(var t in a)builder.UseTexture(graph.ImportTexture(t),AccessFlags.Read);builder.AllowPassCulling(false);builder.AllowGlobalStateModification(true);builder.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.Draw(p,c));}
 void Draw(Data d,UnsafeGraphContext c){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(c.cmd);for(int p=0;p<4;p++)Source.Engine.Pack(cmd,p,retarget.layers[p],true);Source.Engine.Dispatch(cmd,d.view,d.projection,false);RecordedFrame=Time.frameCount;}
 public void Dispose(){if(Disposed)return;Disposed=true;Source.Dispose();}
}
