using System;using System.Linq;using UnityEngine;using UnityEditor;using UnityEngine.Rendering;using UnityEngine.Rendering.RenderGraphModule;using UnityEngine.Rendering.Universal;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public sealed partial class SourceOutline40 {
 HeadLocal367 host41;Full319View335 main41;ComputeShader final41;int finalKernel41;bool finalRecorded41;FinalPass41 pass41;
 Vector2Int join41,delta41;float depth41;
 public Action BeforePrepare41;public Func<Obj40> WorldProof41;Obj40 worldProof41;
 void PrepareWorld41(){BeforePrepare41?.Invoke();worldProof41=WorldProof41?.Invoke();}
 public Camera MainCamera41=>main41.motion.camera;
 public ScriptableRenderPass FinalPass41Instance=>pass41;
 public bool RequiresFinal41=>recorded&&!finalRecorded41;
 void InitFinal41(){
  host41=HeadLocal367.Active;if(!host41||host41.head!=eye.full||!host41.headEnabled)throw new InvalidOperationException("41 exact active head/main host required");main41=host41.main;
  var asset=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/SourceBoundary41/ContourFinal41.compute");if(!asset)throw new InvalidOperationException("41 final shader not imported");final41=UnityEngine.Object.Instantiate(asset);finalKernel41=final41.FindKernel("FinalContour41");final41.GetKernelThreadGroupSizes(finalKernel41,out uint x,out uint y,out uint z);if(x!=8||y!=8||z!=1)throw new InvalidOperationException("41 final ABI mismatch");pass41=new FinalPass41(this);
 }
 void ReleaseFinal41(){if(final41)UnityEngine.Object.DestroyImmediate(final41);}
 sealed class FinalPass41:ScriptableRenderPass {
  readonly SourceOutline40 owner;public FinalPass41(SourceOutline40 owner){this.owner=owner;renderPassEvent=(RenderPassEvent)555;}
  public override void RecordRenderGraph(RenderGraph graph,ContextContainer context){owner.RecordFinal41(graph,context);}
 }
 void RecordFinal41(RenderGraph graph,ContextContainer context){
  if(!RequiresFinal41)return;
  try{
   if(Time.frameCount!=frame||context.Get<UniversalCameraData>().camera!=MainCamera41||!host41.headReady||!main41.contourReady)throw new InvalidOperationException("41 final source/view/frame/order mismatch");
   finalRecorded41=true;join41=host41.offset;depth41=host41.depthOffset;delta41=new Vector2Int(Mathf.RoundToInt(main41.motion.composeDelta.x),Mathf.RoundToInt(main41.motion.composeDelta.y));
   foreach(var t in new[]{main41.motion.output,main41.resolvedMeta,main41.motion.worldInfo,main41.motion.audit})if(t.rt.width!=480||t.rt.height!=272)throw new InvalidOperationException("41 main texture grid mismatch");
   if(FrameInfo40!=null)FrameInfo40["finalComposite41"]=new Obj40{["sameFrame"]=frame,["sourceId"]=FrameKey,["headTextureOrigin"]=new Arr40(QROI.x,272-QROI.y-QROI.height),["joinOffset"]=new Arr40(join41.x,join41.y),["composeDelta"]=new Arr40(delta41.x,delta41.y),["depthOffset"]=depth41,["mainCamera"]=MainCamera41.GetEntityId().ToString(),["mainEvaluatedFrame"]=main41.motion.evaluatedFrame,["mainSourceFrame"]=main41.motion.sourceFrame,["hostHeadReady"]=host41.headReady,["mainContourReady"]=main41.contourReady,["policy"]="existing GridJoin367/Compose333 depth transport and 0.0001 comparisons; private RGB proposal only; no history write"};
   if(FrameInfo40!=null&&worldProof41!=null)FrameInfo40["worldFixture41"]=worldProof41;
   using(var b=graph.AddUnsafePass<Data>("41 final style/world-depth candidate",out var d)){d.owner=this;foreach(var t in new[]{Fields[8],Fields[9],main41.motion.output,main41.resolvedMeta,main41.motion.worldInfo,main41.motion.audit})b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);b.UseTexture(graph.ImportTexture(Fields[12]),AccessFlags.ReadWrite);b.AllowPassCulling(false);b.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.ProduceFinal41(c));}
   using(var b=graph.AddUnsafePass<Data>("41 end barrier after both head and main consumers",out var d)){d.owner=this;foreach(var t in Fields.Concat(QFields).Concat(new[]{Classification,depth,qDepth,fineDepth,styleDepth39}))b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);b.AllowPassCulling(false);b.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.EndBarrier(c));}
  }catch(Exception e){Fail(e);}
 }
 void ProduceFinal41(UnsafeGraphContext context){
  if(Failure!=null)return;
  try{
   if(Time.frameCount!=frame)throw new InvalidOperationException("41 stale main graph");var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
   void T(string name,RTHandle value)=>cmd.SetComputeTextureParam(final41,finalKernel41,name,value.rt);
   T("_Line41",Fields[8]);T("_Proof41",Fields[9]);T("_MainColour41",main41.motion.output);T("_MainMeta41",main41.resolvedMeta);T("_WorldInfo41",main41.motion.worldInfo);T("_MainAudit41",main41.motion.audit);T("_Atlas41",Fields[12]);
   cmd.SetComputeIntParams(final41,"_Size41",QROI.width,QROI.height);cmd.SetComputeIntParams(final41,"_HeadTextureOrigin41",QROI.x,272-QROI.y-QROI.height);cmd.SetComputeIntParams(final41,"_JoinOffset41",join41.x,join41.y);cmd.SetComputeIntParams(final41,"_ComposeDelta41",delta41.x,delta41.y);cmd.SetComputeFloatParam(final41,"_DepthOffset41",depth41);cmd.SetComputeVectorParam(final41,"_Ink41",sourceInk);cmd.DispatchCompute(final41,finalKernel41,(QROI.width+7)/8,(QROI.height+7)/8,1);
  }catch(Exception e){Fail(e);}
 }
}
}
