using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;

namespace FantasySurvival.EditorTools.NativeGridR25
{
// R25 test-only recorder. It does not run the CPU selector or acquire
// buffers. The same trial owner owns the three buffers and the last-use proof.
internal sealed class NativeOwnerGraph154
{
    const string ExactKernel = "SelectConnectedOwners154";
    public readonly NativePlayer395 View;
    readonly R25EyeAtlas Eye;
    public readonly ComputeShader Shader;
    public readonly RectInt Crop;
    public RectInt Window { get; private set; }
    public RectInt Atlas { get; private set; }
    public Vector3 HeadMapping { get; private set; }
    public readonly GraphicsBuffer WorldProof, Owners;
    public GraphicsBuffer Candidates { get; private set; }
    public readonly int Ticket, Frame;
    readonly int beforePreparation;
    readonly NativeOwnerOrder154 order;
    readonly int prepareKernel, selectKernel;

    // This descriptor contains no pixels. The exact selection kernel must be
    // present before enabling this trial. Never fall back to a local vote.
    public NativeOwnerGraph154(NativePlayer395 view, R25EyeAtlas eye, ComputeShader shader, RectInt crop,
        GraphicsBuffer proof, GraphicsBuffer owners)
    {
        if(!view||eye == null||!shader||!shader.HasKernel(ExactKernel)||
           !shader.HasKernel("CaptureWorldStamped154")||!shader.HasKernel("PresentNativeCommon154"))
            throw new InvalidOperationException("154 exact R25 kernels are not installed");
        if(!Inside(crop,960,544,480*272)||!Shape(proof,1)||!Shape(owners,crop.width*crop.height)||
           ReferenceEquals(proof,owners))
            throw new InvalidOperationException("154 invalid native crop ownership");
        View=view;Eye=eye;Shader=shader;Crop=crop;WorldProof=proof;Owners=owners;
        Frame=Time.frameCount;beforePreparation=view.presentSerial;Ticket=checked(beforePreparation+2);
        order=new NativeOwnerOrder154(Frame,Ticket);
        prepareKernel=shader.FindKernel("PrepareNativeOwnerRays154");
        selectKernel=shader.FindKernel(ExactKernel);
    }

    public void SetLocalLayout(RectInt window,RectInt atlas,Vector3 mapping,GraphicsBuffer candidates)
    {
        if(Candidates!=null||Frame!=Time.frameCount||View.presentSerial!=beforePreparation||
           !Inside(window,960,544,2048)||!Inside(atlas,480,272,512)||
           !float.IsFinite(mapping.x)||!float.IsFinite(mapping.y)||!float.IsFinite(mapping.z)||
           !Shape(candidates,window.width*window.height*4)||
           ReferenceEquals(WorldProof,candidates)||ReferenceEquals(Owners,candidates))
            throw new InvalidOperationException("154 invalid or stale R25 local eye layout");
        Window=window;Atlas=atlas;HeadMapping=mapping;Candidates=candidates;
    }

    static bool Inside(RectInt r,int w,int h,int max) =>
        r.x>=0&&r.y>=0&&r.width>0&&r.height>0&&r.xMax<=w&&r.yMax<=h&&(long)r.width*r.height<=max;
    static bool Shape(GraphicsBuffer b,int count) => b!=null&&b.stride==16&&b.count==count;
    int CurrentTicket => checked(View.presentSerial+1);

    public bool ForWorldCapture(Camera camera) => camera == View.gameCamera;

    public int BindStampedCapture(CommandBuffer cmd)
    {
        RequireBeforePreparation();
        order.WorldIssued(Time.frameCount,Ticket);
        var cs=Shader;
        int kernel=cs.FindKernel("CaptureWorldStamped154");
        BindStamp(cmd);
        cmd.SetComputeBufferParam(cs,kernel,"_R25WorldIssued154",WorldProof);
        return kernel;
    }

    public void OnEyeLayerIssued(R25EyeAtlas eye,int layer)
    {
        if(eye==Eye&&layer>=0&&layer<5)
        {
            if(Candidates==null||eye.Roi.x!=Atlas.x||272-eye.Roi.yMax!=Atlas.y||
               eye.Roi.width!=Atlas.width||eye.Roi.height!=Atlas.height)
                throw new InvalidOperationException("154 R25 eye atlas changed after binding");
            RequireBeforePreparation();
            order.EyeIssued(Time.frameCount,Ticket,layer);
        }
    }

    void RequireBeforePreparation()
    {
        if(View.presentSerial!=beforePreparation)
            throw new InvalidOperationException("R25 world or head pass ran after preparation");
    }

    void BindStamp(CommandBuffer cmd)
    {
        cmd.SetComputeIntParam(Shader,"_R25EngineFrame154",Frame);
        cmd.SetComputeIntParam(Shader,"_R25ProducerTicket154",Ticket);
    }

    void DeclareSources(RenderGraph graph,IUnsafeRenderGraphBuilder pass)
    {
        pass.UseTexture(graph.ImportTexture(View.worldDepth),AccessFlags.Read);
        pass.UseBuffer(graph.ImportBuffer(WorldProof),AccessFlags.Read);
        for(int layer=0;layer<5;layer++)
        {
            pass.UseTexture(graph.ImportTexture(Eye.Layers[layer].meta),AccessFlags.Read);
            pass.UseTexture(graph.ImportTexture(Eye.Layers[layer].shade),AccessFlags.Read);
        }
    }

    void BindSources(CommandBuffer cmd,int kernel,bool needsShade)
    {
        var cs=Shader;
        cmd.SetComputeIntParams(cs,"_R25EyeWindow154",Window.x,Window.y,Window.width,Window.height);
        cmd.SetComputeIntParams(cs,"_LiveEyeAtlas348",Atlas.x,Atlas.y,Atlas.width,Atlas.height);
        cmd.SetComputeVectorParam(cs,"_LiveHeadMapping",new Vector4(HeadMapping.x,HeadMapping.y,HeadMapping.z,0));
        cmd.SetComputeVectorParam(cs,"_NearFar395",new Vector4(
            View.gameCamera.nearClipPlane,View.gameCamera.farClipPlane,SystemInfo.usesReversedZBuffer?1:0,0));
        cmd.SetComputeTextureParam(cs,kernel,"_WorldDepth395",View.worldDepth.rt);
        cmd.SetComputeBufferParam(cs,kernel,"_R25WorldProof154",WorldProof);
        string[] names={"Skin","White","Iris","Lash","Hair"};
        for(int layer=0;layer<5;layer++)
        {
            string name=layer==0?"_LivePhysicalSkinMeta348":"_Cell"+names[layer]+"Meta154";
            cmd.SetComputeTextureParam(cs,kernel,name,Eye.Layers[layer].meta.rt);
            if(needsShade)cmd.SetComputeTextureParam(cs,kernel,"_Cell"+names[layer]+"Input154",Eye.Layers[layer].shade.rt);
        }
        BindStamp(cmd);
    }

    sealed class Data { public NativeOwnerGraph154 owner; public RTHandle meta,lighting; }

    // A live exact selector must consume candidates + unmodified source
    // weights, write each owner packet once, and emit ticket=0 on failure.
    public void Record(RenderGraph graph, RTHandle nativeMeta, RTHandle nativeLight)
    {
        if(Candidates==null||Frame!=Time.frameCount||Ticket!=CurrentTicket)
            throw new InvalidOperationException("154 R25 local layout was not bound before recording");
        using(var pass=graph.AddUnsafePass<Data>("154 same-frame eye and world candidate rays",out var data))
        {
            data.owner=this;
            DeclareSources(graph,pass);
            pass.UseBuffer(graph.ImportBuffer(Candidates),AccessFlags.Write);
            pass.AllowGlobalStateModification(true);
            pass.SetRenderFunc(static(Data d,UnsafeGraphContext context)=>{
                var x=d.owner;
                x.order.PrepareIssued(Time.frameCount,x.CurrentTicket);
                var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
                x.BindSources(cmd,x.prepareKernel,false);
                cmd.SetComputeBufferParam(x.Shader,x.prepareKernel,"_R25CandidatesWrite154",x.Candidates);
                cmd.DispatchCompute(x.Shader,x.prepareKernel,(x.Window.width+7)/8,(x.Window.height+7)/8,1);
            });
        }
        using(var pass=graph.AddUnsafePass<Data>("154 exact connected owners",out var data))
        {
            data.owner=this;data.meta=nativeMeta;data.lighting=nativeLight;
            DeclareSources(graph,pass);
            pass.UseTexture(graph.ImportTexture(nativeMeta),AccessFlags.Read);
            pass.UseTexture(graph.ImportTexture(nativeLight),AccessFlags.Read);
            pass.UseBuffer(graph.ImportBuffer(Candidates),AccessFlags.Read);
            pass.UseBuffer(graph.ImportBuffer(Owners),AccessFlags.Write);
            pass.AllowGlobalStateModification(true);
            pass.SetRenderFunc(static(Data d,UnsafeGraphContext context)=>{
                var x=d.owner;
                x.order.SelectionIssued(Time.frameCount,x.CurrentTicket);
                var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);
                var cs=x.Shader;
                int k=x.selectKernel;
                x.BindSources(cmd,k,true);
                var phase=x.View.manualDelta?x.View.delta:x.View.host.main.motion.composeDelta;
                cmd.SetComputeVectorParam(cs,"_Delta395",new Vector4(phase.x,phase.y,0,0));
                cmd.SetComputeIntParams(cs,"_Origin395",x.View.origin.x,x.View.origin.y);
                cmd.SetComputeIntParams(cs,"_NativeCharacterCrop154",x.Crop.x,x.Crop.y,x.Crop.width,x.Crop.height);
                cmd.SetComputeTextureParam(cs,k,"_IntegratedMeta154",d.meta.rt);
                cmd.SetComputeTextureParam(cs,k,"_IntegratedLight154",d.lighting.rt);
                cmd.SetComputeBufferParam(cs,k,"_R25CandidatesRead154",x.Candidates);
                cmd.SetComputeBufferParam(cs,k,"_R25OwnersWrite154",x.Owners);
                cmd.DispatchCompute(cs,k,1,1,1); // bounded deterministic solver ABI
            });
        }
    }

    public void ConsumeOnce()
    {
        order.ConsumeOnce(Time.frameCount,CurrentTicket);
    }

    public void Abort(Action detach,Func<bool> lastUseConfirmed,Action release)
    {
        order.Abort(detach,lastUseConfirmed,release);
    }
}
}
