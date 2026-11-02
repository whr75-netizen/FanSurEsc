using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
// Own current renderer/view only. No GPU->CPU selection feedback.
public sealed class RegionDriver115:IDisposable{
 public const int Capacity=128;
 public readonly RegionDriver113 Cells;
 public readonly GraphicsBuffer moments,references,state,candidates,metrics,survivors,primary;
 readonly List<GraphicsBuffer> extra=new List<GraphicsBuffer>();readonly EyeFeature348 eye;readonly string topology;
 public bool Disposed{get;private set;}public int DrawnFrame{get;private set;}=-1;
 public GraphicsBuffer cells=>Cells.cells;public GraphicsBuffer tags=>Cells.tags;public GraphicsBuffer frame=>Cells.frame;public GraphicsBuffer points=>Cells.points;public GraphicsBuffer best=>Cells.best;public GraphicsBuffer exposure=>Cells.exposure;
 public IEnumerable<GraphicsBuffer> Buffers=>Cells.Buffers.Concat(extra);public long OwnedBytes=>Cells.OwnedBytes+extra.Sum(b=>(long)b.count*b.stride);
 GraphicsBuffer B(int n,int stride){var b=new GraphicsBuffer(GraphicsBuffer.Target.Structured,n,stride);extra.Add(b);return b;}
 public RegionDriver115(EyeFeature348 e){eye=e;topology=e.modelTopologySHA256;try{Cells=new RegionDriver113(e);moments=B(512*Cells.keys.count,32);references=B(Cells.keys.count,32);state=B(2,16);candidates=B(2*Capacity,16);metrics=B(2*Capacity,80);survivors=B(2*Capacity,4);primary=B(2,48);}catch{Dispose();throw;}}
 public void QueryBindings(WholeEye107 e,bool exposure)=>Cells.QueryBindings(e,exposure);
 public void PrepareCarrier(CommandBuffer cmd,WholeEye107 e,Vector2 origin){var cs=e.Shader;int k=cs.FindKernel("CarrierQueries115");cmd.SetComputeIntParams(cs,"_CarrierSize115",e.Width,e.Height);cmd.SetComputeVectorParam(cs,"_CarrierOrigin115",new Vector4(origin.x,origin.y,0,0));cmd.SetComputeBufferParam(cs,k,"_WriteQueries113",e.Queries);cmd.SetComputeBufferParam(cs,k,"_SrcLayers113",e.Layers);cmd.DispatchCompute(cs,k,(e.Width*e.Height*4+63)/64,1,1);}
 public void Draw(CommandBuffer cmd,WholeEye107 target,WholeEye107 source,WholeEye107 carrier,SourcePigment113 curve,GraphicsBuffer[] output,Vector2 carrierOrigin){
  if(Disposed||eye.modelTopologySHA256!=topology)throw new InvalidOperationException("115 scope invalidated");int w=source.Width/8,h=source.Height/8;if(w*h>512||w*4!=target.Width||h*4!=target.Height||carrier.Width!=target.Width||carrier.Height!=target.Height)throw new InvalidOperationException("115 intrinsic8x/destination4x grid contract");var cs=target.Shader;
  cmd.SetComputeIntParams(cs,"_SourceSize113",source.Width,source.Height);cmd.SetComputeIntParams(cs,"_CellsSize113",w,h);cmd.SetComputeIntParams(cs,"_CarrierSize115",carrier.Width,carrier.Height);cmd.SetComputeVectorParam(cs,"_CarrierOrigin115",new Vector4(carrierOrigin.x,carrierOrigin.y,0,0));cmd.SetComputeIntParam(cs,"_KeyCount113",Cells.keys.count);cmd.SetComputeIntParam(cs,"_CurveCount106",curve.Count);cmd.SetComputeIntParams(cs,"_CurveEyeIds106",curve.EyeId(0),curve.EyeId(1));Cells.BindFixedPalette115(cmd,cs);
  foreach(string name in new[]{"PrepareCells115","GatherEye113","BuildSubsets113","Enumerate115","Reduce115","BeginForm115","KeyReferences115","CollectForm115","EvaluateForm115","Pareto115","Write113"}){
   int k=cs.FindKernel(name);void Bind(string n,GraphicsBuffer b)=>cmd.SetComputeBufferParam(cs,k,n,b);
   Bind("_Keys113",Cells.keys);Bind("_SrcLayers113",source.Layers);Bind("_SrcVisibility113",source.Visibility);Bind("_Cells113",Cells.cells);Bind("_CellTags113",Cells.tags);Bind("_Frame113",Cells.frame);Bind("_Points113",Cells.points);Bind("_Groups113",Cells.groups);Bind("_Best113",Cells.best);Bind("_Subsets113",Cells.subsets);Bind("_Curves106",curve.Buffer);Bind("_CellKey115",moments);Bind("_ReferenceKey115",references);Bind("_FormState115",state);Bind("_Candidates115",candidates);Bind("_Metrics115",metrics);Bind("_Survivors115",survivors);Bind("_PrimaryBest115",primary);
   for(int i=0;i<4;i++)Bind(new[]{"_CurveColour106","_CurveIdentity106","_CurveDecision106","_CurveAudit106"}[i],output[i]);
   if(name=="PrepareCells115"||name=="Write113")cmd.DispatchCompute(cs,k,(w+7)/8,(h+7)/8,1);
   else if(name=="BuildSubsets113")cmd.DispatchCompute(cs,k,64,4,1);
   else if(name=="Enumerate115"||name=="CollectForm115")cmd.DispatchCompute(cs,k,32768,2,1);
   else if(name=="EvaluateForm115")cmd.DispatchCompute(cs,k,Capacity,2,1);
   else if(name=="KeyReferences115")cmd.DispatchCompute(cs,k,Cells.keys.count,1,1);
   else cmd.DispatchCompute(cs,k,2,1,1);
  }DrawnFrame=Time.frameCount;
 }
 public void ComposeBindings(CommandBuffer cmd,ComputeShader cs,int k,WholeEye107 carrier){Cells.ComposeBindings(cmd,cs,k,carrier);}
 public Obj58 Info=>new Obj58{["runtimeGPUEnumeration"]=true,["runtimeGPUReadbacks"]=0,["form22SourceDistributionAndRelativeGeometry"]=true,["sourceKeyCountProxyRemoved"]=true,["outwardFloatIntervals"]=true,["unobservedPairIsNotZero"]=true,["poolCapacity"]=Capacity,["overflowAccepted"]=false,["sourceSampler"]=8,["destinationAndHairSampler"]=4,["historyImplemented"]=false,["nativeOwnSocketMetres"]=.012,["ownedBytes"]=OwnedBytes,["drawnFrame"]=DrawnFrame};
 public void Dispose(){if(Disposed)return;Disposed=true;foreach(var b in extra)b?.Dispose();extra.Clear();Cells?.Dispose();}
}
