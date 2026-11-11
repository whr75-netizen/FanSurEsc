using System;using System.Linq;using UnityEngine;using UnityEditor;using UnityEngine.Rendering;using UnityEngine.Rendering.RenderGraphModule;using UnityEngine.Rendering.Universal;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
public sealed partial class SourceOutline40 {
 HeadLocal367 host41;Full319View335 main41;NativePlayer395 native42;ComputeShader final41;int finalKernel41;bool finalRecorded41;FinalPass41 pass41;
 Vector2Int join41,nativeMin42;Vector2 delta42;float depth41;int serialBefore42;
 public Action BeforePrepare41;public Func<Obj40> WorldProof41;Obj40 worldProof41;
 void PrepareWorld41(){BeforePrepare41?.Invoke();worldProof41=WorldProof41?.Invoke();}
 public Camera MainCamera41=>main41.motion.camera;
 public ScriptableRenderPass FinalPass41Instance=>pass41;
 public bool RequiresFinal41=>recorded&&!finalRecorded41;
 void InitFinal41(){
  host41=HeadLocal367.Active;native42=NativePlayer395.Active;if(!host41||host41.head!=eye.full||!host41.headEnabled||!native42||native42.host!=host41||!native42.ready||native42.nativePixelsPerCell!=2)throw new InvalidOperationException("42 exact active Native395/head host and scale2 required");main41=host41.main;
  var asset=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/SourceBoundary42/ContourNative42.compute");if(!asset)throw new InvalidOperationException("42 native final shader not imported");final41=UnityEngine.Object.Instantiate(asset);finalKernel41=final41.FindKernel("NativeContour42");final41.GetKernelThreadGroupSizes(finalKernel41,out uint x,out uint y,out uint z);if(x!=8||y!=8||z!=1)throw new InvalidOperationException("42 native ABI mismatch");pass41=new FinalPass41(this);
 }
 void ReleaseFinal41(){if(final41)UnityEngine.Object.DestroyImmediate(final41);}
 sealed class FinalPass41:ScriptableRenderPass {readonly SourceOutline40 owner;public FinalPass41(SourceOutline40 owner){this.owner=owner;renderPassEvent=(RenderPassEvent)605;}public override void RecordRenderGraph(RenderGraph graph,ContextContainer context){owner.RecordFinal41(graph,context);}}
 void RecordFinal41(RenderGraph graph,ContextContainer context){
  if(!RequiresFinal41)return;
  try{
   if(Time.frameCount!=frame||context.Get<UniversalCameraData>().camera!=MainCamera41||!host41.headReady||!main41.contourReady||!native42.ready)throw new InvalidOperationException("42 native source/view/frame/order mismatch");
   finalRecorded41=true;join41=host41.offset;depth41=host41.depthOffset;delta42=native42.manualDelta?native42.delta:main41.motion.composeDelta;serialBefore42=native42.presentSerial;
   int qx=QROI.x+join41.x,qy=272-QROI.y-QROI.height+join41.y;
   nativeMin42=new Vector2Int(Mathf.CeilToInt(native42.origin.x+2*(qx+delta42.x)-.5f),Mathf.CeilToInt(native42.origin.y+2*(qy+delta42.y)-.5f));
   if(nativeMin42.x<0||nativeMin42.y<0||nativeMin42.x+2*QROI.width>960||nativeMin42.y+2*QROI.height>544)throw new InvalidOperationException("42 native footprint clipped; no guessed crop");
   foreach(var t in new[]{native42.output,native42.cellID,native42.depthAudit})if(t.rt.width!=960||t.rt.height!=544)throw new InvalidOperationException("42 native output grid mismatch");
   if(FrameInfo40!=null)FrameInfo40["nativeComposite42"]=new Obj40{["sameFrame"]=frame,["sourceId"]=FrameKey,["headTextureOrigin"]=new Arr40(QROI.x,272-QROI.y-QROI.height),["joinOffset"]=new Arr40(join41.x,join41.y),["deliveredDelta"]=new Arr40(delta42.x,delta42.y),["depthOffset"]=depth41,["nativeOrigin"]=new Arr40(native42.origin.x,native42.origin.y),["nativeScale"]=2,["nativeROI"]=new Arr40(nativeMin42.x,nativeMin42.y,2*QROI.width,2*QROI.height),["presentSerialBeforeGraphExecute"]=serialBefore42,["worldSerial"]=native42.worldSerial,["presenterAsset"]=AssetDatabase.GetAssetPath(native42.compute),["policy"]="Native395.Present exact shared-cell/world sample; actual native depthAudit/cellID; private native RGB proposal only; owner/history not replaced"};
   if(FrameInfo40!=null&&worldProof41!=null)FrameInfo40["worldFixture41"]=worldProof41;
   using(var b=graph.AddUnsafePass<Data>("42 actual Native395 final-depth candidate",out var d)){d.owner=this;foreach(var t in new[]{Fields[8],Fields[9],native42.output,main41.resolvedMeta,native42.depthAudit,native42.cellID})b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var t in new[]{Fields[12],Fields[13],Fields[14]})b.UseTexture(graph.ImportTexture(t),AccessFlags.ReadWrite);b.AllowPassCulling(false);b.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.ProduceFinal41(c));}
   using(var b=graph.AddUnsafePass<Data>("42 end barrier after actual native presentation",out var d)){d.owner=this;foreach(var t in Fields.Concat(QFields).Concat(new[]{Classification,depth,qDepth,fineDepth,styleDepth39}))b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);b.AllowPassCulling(false);b.SetRenderFunc(static(Data p,UnsafeGraphContext c)=>p.owner.EndBarrier(c));}
  }catch(Exception e){Fail(e);}
 }
 void ProduceFinal41(UnsafeGraphContext context){
  if(Failure!=null)return;
  try{
   if(Time.frameCount!=frame||native42.presentSerial<=serialBefore42||native42.deliveredDelta!=delta42)throw new InvalidOperationException("42 actual Native395 Present did not precede consumer with same delta");
   FrameInfo40["nativeComposite42"]["presentSerialExecuted"]=native42.presentSerial;var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
   void T(string name,RTHandle value)=>cmd.SetComputeTextureParam(final41,finalKernel41,name,value.rt);
   T("_Line41",Fields[8]);T("_Proof41",Fields[9]);T("_NativeColour42",native42.output);T("_MainMeta41",main41.resolvedMeta);T("_NativeDepth42",native42.depthAudit);T("_NativeCell42",native42.cellID);T("_Atlas41",Fields[12]);T("_NativeAfter42",Fields[14]);
   cmd.SetComputeIntParams(final41,"_Size41",QROI.width,QROI.height);cmd.SetComputeIntParams(final41,"_HeadTextureOrigin41",QROI.x,272-QROI.y-QROI.height);cmd.SetComputeIntParams(final41,"_JoinOffset41",join41.x,join41.y);cmd.SetComputeIntParams(final41,"_NativeOrigin42",native42.origin.x,native42.origin.y);cmd.SetComputeIntParam(final41,"_NativeScale42",2);cmd.SetComputeVectorParam(final41,"_DeliveredDelta42",new Vector4(delta42.x,delta42.y,0,0));cmd.SetComputeFloatParam(final41,"_DepthOffset41",depth41);cmd.SetComputeVectorParam(final41,"_Ink41",sourceInk);cmd.DispatchCompute(final41,finalKernel41,(QROI.width+7)/8,(QROI.height+7)/8,1);
   cmd.CopyTexture(native42.output.rt,0,0,nativeMin42.x,nativeMin42.y,2*QROI.width,2*QROI.height,Fields[13].rt,0,0,0,0);
  }catch(Exception e){Fail(e);}
 }
}
}
