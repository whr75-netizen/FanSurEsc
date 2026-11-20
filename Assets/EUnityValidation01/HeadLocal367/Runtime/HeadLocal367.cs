using System;using System.Linq;using System.Reflection;using System.Collections.Generic;using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Rendering.RenderGraphModule;
#if UNITY_EDITOR
using UnityEditor;
#endif
[ExecuteAlways,DefaultExecutionOrder(500)]public sealed class HeadLocal367:MonoBehaviour{
 public Full319View335 main;public EyeFeature348 mainEyes;public PostView366 post;public ComputeShader join;public bool headEnabled=true,automatic=false,showControls=true;
 // Default-OFF: compare centre-sampled hair with body depth on that same head-camera ray.
 public static bool UseCentreBodyRay550;
 public static HeadLocal367 Active;[NonSerialized]public Full319View335 head;[NonSerialized]public EyeFeature348 headEyes;[NonSerialized]public MotionView331 headMotion;[NonSerialized]public PostView366 headPost;[NonSerialized]public Camera headCamera;[NonSerialized]public Vector2Int offset;[NonSerialized]public float depthOffset,exactFollowError;[NonSerialized]public Vector2 headPivot,mainPivot;[NonSerialized]public Action afterPose;[NonSerialized]public int mainOutlineDispatches,headOutlineDispatches,joinedOutlineDispatches;[NonSerialized]public bool headReady;
 UnityEngine.Rendering.ShadowCastingMode[] priorShadow;Vector3 anchorHead,anchorCamera,anchorActor;Quaternion anchorRotation;Vector4 anchorShift;[NonSerialized]public RTHandle[][]sampleJoin;RenderTexture target;GameObject headObject;bool ready,busy;bool scheduledNativeLoop,scheduledMainPrepared;int scheduledFrame=-1;NativePlayer395 scheduledPlayer;public float Cell=>2*main.motion.camera.orthographicSize/272;
 static void CopyFields(object source,object target){foreach(var f in source.GetType().GetFields(BindingFlags.Public|BindingFlags.Instance))if(!f.IsInitOnly&&!f.IsDefined(typeof(NonSerializedAttribute)))f.SetValue(target,f.GetValue(source));}
 void OnEnable(){Active=this;RenderPipelineManager.beginCameraRendering+=OnBeginCameraRendering;RenderPipelineManager.endCameraRendering+=OnEndCameraRendering;
#if UNITY_EDITOR
 EditorApplication.update+=EditorTick;
#endif
 }
 public void Initialise(){if(ready||!main||!mainEyes||!post||!join)return;Active=this;main.automatic=false;post.showControls=false;main.Initialise();mainEyes.Initialise();main.PrepareCurrent();var m=main.motion;priorShadow=m.surface.outputs.Select(x=>x.GetComponent<Renderer>().shadowCastingMode).ToArray();anchorHead=m.animation.target.GetBoneTransform(HumanBodyBones.Head).position;anchorActor=m.animation.target.transform.position;anchorCamera=m.camera.transform.position;anchorRotation=m.camera.transform.rotation;anchorShift=m.clipShift;
 headObject=new GameObject("365 current348 head local grid runtime"){hideFlags=HideFlags.HideAndDontSave};headCamera=headObject.AddComponent<Camera>();headCamera.CopyFrom(m.camera);headCamera.tag="Untagged";headCamera.depth=-1f;headCamera.enabled=false;NativePlayer395.ConfigureCharacterOffscreenCamera(headCamera,NativePlayer395.Active?NativePlayer395.Active.gameCamera:m.camera);target=new RenderTexture(960,544,24,RenderTextureFormat.ARGB32){filterMode=FilterMode.Point,hideFlags=HideFlags.DontSave,name="365 same480 logical head canvas;no change in pixel pitch"};target.Create();headCamera.targetTexture=target;headCamera.transform.SetPositionAndRotation(anchorCamera,anchorRotation);
 headMotion=headObject.AddComponent<MotionView331>();CopyFields(m,headMotion);headMotion.camera=headCamera;headMotion.playing=false;headMotion.showControls=false;headMotion.enabled=false;headMotion.Initialise();head=headObject.AddComponent<Full319View335>();CopyFields(main,head);head.motion=headMotion;head.automatic=false;head.Initialise();headEyes=headObject.AddComponent<EyeFeature348>();CopyFields(mainEyes,headEyes);headEyes.full=head;headEyes.showControls=false;headEyes.samplesOnly=true;headEyes.Initialise();headPost=headObject.AddComponent<PostView366>();headPost.full=head;headPost.sourceShader=post.sourceShader;headPost.inject=post.inject;headPost.candidateEnabled=false;headPost.showControls=false;var readyField=typeof(Full319View335).GetField("ready",BindingFlags.NonPublic|BindingFlags.Instance);readyField.SetValue(head,false);head.enabled=false;readyField.SetValue(head,true);SetContext(false);ready=true;
 }
 public static void CountOutline(Full319View335 v){var e=Active;if(!e)return;if(v==e.head)e.headOutlineDispatches++;if(v==e.main){e.mainOutlineDispatches++;if(e.headEnabled&&v.contourReady)e.joinedOutlineDispatches++;}}
 public static bool IsHead(Full319View335 v)=>Active&&Active.headEnabled&&v==Active.head;
 public static bool Split(Full319View335 v)=>Active&&Active.headEnabled&&(v==Active.main||v==Active.head);
 public static bool DrawSource(Full319View335 v,int renderer)=>!Split(v)||(IsHead(v)?renderer>0:renderer==0);
 public static Full319View335 ForCamera(Camera c){var e=Active;if(!e)return Full319View335.Active;if(c==e.main.motion.camera)return e.main;if(e.headEnabled&&c==e.headCamera)return e.head;return null;}
 public static EyeFeature348 EyesForCamera(Camera c){var e=Active;if(!e)return EyeFeature348.Active;if(c==e.main.motion.camera)return e.headEnabled?null:e.mainEyes;if(e.headEnabled&&c==e.headCamera)return e.headEyes;return null;}
 void SetContext(bool local){Full319View335.Active=local?head:main;EyeFeature348.Active=local?headEyes:mainEyes;PostView366.Active=local?headPost:post;MotionView331.Active=local?headMotion:main.motion;}
 void Refresh(Full319View335 f){var m=f.motion;var p=f.phases[f.phaseIndex];f.providerMatrix=m.animation.target.GetBoneTransform(HumanBodyBones.Head).localToWorldMatrix*p.head.inverse;f.UpdateProxyMeshes();f.BindEyes();}
 void PrepareHead(){var m=main.motion;head.motion=headMotion;headMotion.sourceFrame=m.sourceFrame;headMotion.evaluatedFrame=m.evaluatedFrame;headMotion.clipShift=anchorShift;headMotion.composeDelta=Vector2.zero;var current=m.animation.target.GetBoneTransform(HumanBodyBones.Head).position;// Follow the current gameplay view; keep only the head-relative pose offset.
 // The old fixed anchorCamera lost the head when the player orbited the view.
 var expected=m.camera.transform.position+(current-m.animation.target.transform.position)-(anchorHead-anchorActor);headCamera.transform.SetPositionAndRotation(expected,m.camera.transform.rotation);headCamera.orthographicSize=m.camera.orthographicSize;headCamera.aspect=m.camera.aspect;headCamera.ResetWorldToCameraMatrix();headCamera.projectionMatrix=m.camera.projectionMatrix;exactFollowError=Vector3.Distance(headCamera.transform.position,expected);head.phaseIndex=main.phaseIndex;head.contourReady=false;head.effectiveProjection=headCamera.projectionMatrix;float flip=GL.GetGPUProjectionMatrix(headCamera.projectionMatrix,true)[1,1]/headCamera.projectionMatrix[1,1];head.effectiveProjection.SetRow(0,head.effectiveProjection.GetRow(0)+anchorShift.x*head.effectiveProjection.GetRow(3));head.effectiveProjection.SetRow(1,head.effectiveProjection.GetRow(1)+anchorShift.y/flip*head.effectiveProjection.GetRow(3));head.nativeShift=anchorShift+new Vector4(.5f/480,.5f/272*flip,0,0);Refresh(head);headPivot=head.Project(current);mainPivot=main.Project(current);var delta=mainPivot-headPivot;offset=new Vector2Int(Mathf.RoundToInt(delta.x),-Mathf.RoundToInt(delta.y));depthOffset=Vector3.Dot(headCamera.transform.position-m.camera.transform.position,m.camera.transform.forward);}
 internal void EnableScheduledNativeLoop(NativePlayer395 player,bool enableChar,bool enableHead){
  Initialise();if(!ready)return;
  scheduledPlayer=player;scheduledNativeLoop=true;headEnabled=enableHead;
  if(headCamera){headCamera.depth=-1f;headCamera.enabled=enableChar&&enableHead;}
  if(main&&main.motion&&main.motion.camera){main.motion.camera.depth=0f;main.motion.camera.enabled=true;}
 }
 internal void DisableScheduledNativeLoop(){
  scheduledNativeLoop=false;scheduledPlayer=null;scheduledMainPrepared=false;
  if(headCamera)headCamera.enabled=false;
  if(main&&main.motion&&main.motion.camera)main.motion.camera.enabled=false;
 }
 void PrepareScheduledMainOnce(){
  if(scheduledMainPrepared&&scheduledFrame==Time.frameCount)return;
  scheduledFrame=Time.frameCount;scheduledMainPrepared=true;
  mainOutlineDispatches=headOutlineDispatches=joinedOutlineDispatches=0;headReady=false;
  if(scheduledPlayer&&scheduledPlayer.worldSerial>0)scheduledPlayer.SetLocalCamera();
  SetContext(false);
  if(PixelRenderPipelineControl399.EnableCharacterPass){
   main.PrepareCurrent();afterPose?.Invoke();main.ClearActionMapIfNeeded();
  }
  if(PixelRenderPipelineControl399.Active)PixelRenderPipelineControl399.Active.lastFrameReadbacks=0;
 }
 void OnBeginCameraRendering(ScriptableRenderContext context,Camera camera){
  if(!scheduledNativeLoop||!ready||!Application.isPlaying||PixelRenderPipelineControl399.BypassPresentation)return;
  if(camera==headCamera&&headEnabled&&PixelRenderPipelineControl399.EnableCharacterPass){
   PrepareScheduledMainOnce();
   PrepareHead();
   SetContext(true);
  }else if(main&&main.motion&&camera==main.motion.camera){
   PrepareScheduledMainOnce();
   main.contourReady=true;
   SetContext(false);
  }
 }
 void OnEndCameraRendering(ScriptableRenderContext context,Camera camera){
  if(!scheduledNativeLoop||!ready||!Application.isPlaying)return;
  if(camera==headCamera){
   headReady=true;
   SetContext(false);
  }else if(main&&main.motion&&camera==main.motion.camera){
   if(PixelRenderPipelineControl399.EnableCharacterPass){
    main.capturePending=false;main.renderedSerial335++;main.renderedSource335=main.motion.sourceFrame;main.renderedFrame335=main.motion.evaluatedFrame;
   }
   scheduledMainPrepared=false;
   SetContext(false);
  }
 }
 ClothRequestBits525 clothRequestBits;
 PreparedClothDepth525 preparedClothDepth;
 bool collectingClothDepth;

 internal static void PublishClothDepth(Full319View335 view)
 {
  var host = Active;
  if(host && host.collectingClothDepth && view == host.main && !view.contourReady)
   host.preparedClothDepth = new PreparedClothDepth525(view);
 }

 bool ReleaseClothRequestBits()
 {
  if(clothRequestBits==null)return true;
  if(!clothRequestBits.CanRelease)return false;
  clothRequestBits.Dispose();
  clothRequestBits=null;
  return true;
 }

 void PrepareClothSurface(Full319View335 f, in PreparedClothDepth525 depth)
 {
  if(!depth.IsCurrent(f))throw new InvalidOperationException("No prepared body depth for the current clothing request");
  var player=NativePlayer395.Active;
  if(Application.isPlaying && player && player.ready && player.host==this &&
     SystemInfo.supportsAsyncGPUReadback && SystemInfo.graphicsDeviceType==UnityEngine.Rendering.GraphicsDeviceType.Direct3D11)
  {
   clothRequestBits??=new ClothRequestBits525(f);
   if(clothRequestBits.TryRead(depth,out var bits))
   {
    ClothSurface525.PreparePacked(f,bits);
    return;
   }
  }
  var centre=Full319View335.Read(depth.Centre);
  var owner=Full319View335.Read(depth.Owner);
  clothRequestBits?.ObserveCompletedFallback();
  if(!depth.IsCurrent(f))throw new InvalidOperationException("Clothing fallback depth no longer matches its frame");
  ClothSurface525.Prepare(f,centre,owner);
 }

 public void RenderFrame(){
  Initialise();post.depthEnabled=true;if(headPost)headPost.depthEnabled=true;if(!ready||busy)return;busy=true;
  try{
   mainOutlineDispatches=headOutlineDispatches=joinedOutlineDispatches=0;headReady=false;SetContext(false);main.PrepareCurrent();afterPose?.Invoke();
   bool useClothCPU=PixelRenderPipelineControl399.EnableClothingRegionCPU;
   bool useOpenContour=PixelRenderPipelineControl399.EnableOpenContourCPU;
   bool usePost366=post.IsRuntimeActive;
   if(useClothCPU){ClothSurface525.BeginFrame();ClothRegion524.Prepare(main);}else ClothSurface525.BeginFrame();
   if(headEnabled&&PixelRenderPipelineControl399.EnableCharacterPass){PrepareHead();SetContext(true);headCamera.Render();headReady=true;SetContext(false);}
   var f=main;var m=f.motion;
   if(PixelRenderPipelineControl399.Active)PixelRenderPipelineControl399.Active.lastFrameReadbacks=0;
   bool clothReady=useClothCPU&&ClothRegion524.Ready(f);
   if(clothReady||useOpenContour||usePost366){
    f.contourReady=false;
    preparedClothDepth=default;
    collectingClothDepth=clothReady;
    try{m.camera.Render();}finally{collectingClothDepth=false;}
    f.validateRender?.Invoke();
    if(clothReady){
     PrepareClothSurface(f,preparedClothDepth);
     if(PixelRenderPipelineControl399.Active)PixelRenderPipelineControl399.Active.lastFrameReadbacks=1;
    }
    if(useOpenContour&&!clothReady){
     var geometry=(Camera)typeof(Full319View335).GetField("geometryCamera",BindingFlags.NonPublic|BindingFlags.Instance).GetValue(f);
     var src=Full319View335.Read(f.meta[0]);
     var pal=Full319View335.Read(f.family);
     var raw=Full319View335.Read(f.native[0]);
     var phys=Full319View335.Read(f.native[3]);
     var uv=Full319View335.Read(f.native[6]);
     var world=Full319View335.Read(f.native[7]);
     var key=Full319View335.Read(f.native[5]);
     var own=Full319View335.Read(f.colourNative);
     var corr0=new Color[960*544];
     for(int i=0;i<corr0.Length;i++)
      corr0[i]=new Color(uv[i].r,uv[i].g,key[i].g,key[i].a);
     var sig=new Color[7][];sig[2]=phys;sig[3]=raw;sig[5]=raw;sig[6]=key;
     var selected=ContourSelect333.Build(new ContourSelect333.Input{phase=f.phaseIndex,y0=f.y0,y1=f.y1,underlayAvailable=true,camera=geometry,renderers=m.surface.outputs.Select(x=>x.GetComponent<Renderer>()).ToArray(),surface=src,palette=pal,centreSurface=Full319View335.Read(f.centreMeta[0]),centrePalette=Full319View335.Read(f.centreFamily),line=Full319View335.Read(f.audit),signals=sig,corr=new[]{corr0,world,own,own},worldCell=Cell,backgroundUniform=false});
     if(PixelRenderPipelineControl399.Active)PixelRenderPipelineControl399.Active.lastFrameReadbacks=11;
     f.receipt=selected.receipt;f.SetActionMap(selected.map);
    }else{
     f.receipt=new ContourSelect333.Receipt{status=clothReady?"524 closed clothing region replaces open arm frontier":"Fast GPU path (no CPU contour readbacks)"};
     f.ClearActionMapIfNeeded();
    }
   }else{
    f.receipt=new ContourSelect333.Receipt{status="Fast GPU single-pass path"};
    f.ClearActionMapIfNeeded();
   }
   f.contourReady=true;m.camera.Render();f.validateRender?.Invoke();f.capturePending=false;f.renderedSerial335++;f.renderedSource335=m.sourceFrame;f.renderedFrame335=m.evaluatedFrame;
  }finally{preparedClothDepth=default;SetContext(false);busy=false;}
 }
 void Params(CommandBuffer cmd){cmd.SetComputeIntParams(join,"_Offset365",offset.x,offset.y);cmd.SetComputeFloatParam(join,"_DepthOffset365",depthOffset);}
 void BindMain(CommandBuffer cmd,int k){void T(string n,RTHandle t)=>cmd.SetComputeTextureParam(join,k,n,t.rt);T("_MBefore",main.before);T("_MColour",main.colour);T("_MOwner",main.owner);T("_MMeta",main.preparedMeta);T("_MUV",main.preparedUV);T("_MDomain",main.domain);}
 public static void JoinBare(CommandBuffer cmd,Full319View335 v){var e=Active;if(!e||!e.headEnabled||!e.headReady||v!=e.main)return;e.Params(cmd);int k=e.join.FindKernel("JoinBare");e.BindMain(cmd,k);void T(string n,RTHandle t)=>cmd.SetComputeTextureParam(e.join,k,n,t.rt);T("_HColour",e.head.prepared);T("_HOwner",e.head.preparedOwner);T("_HMeta",e.head.preparedMeta);T("_HUV",e.head.preparedUV);T("_HPalette",e.head.gridPalette);T("_MSurface",v.gridSurface);T("_MPalette",v.gridPalette);cmd.SetComputeIntParam(e.join,"_BodyRay512Enabled",HeadRegion502.Ready&&HeadRegion502.UseAutomaticCurve511&&HeadRegion502.UseBodyRay512?1:0);cmd.SetComputeTextureParam(e.join,k,"_BodyRay512",HeadRegion502.Mask?HeadRegion502.Mask:Texture2D.blackTexture);cmd.SetComputeIntParam(e.join,"_BodyCentre550Enabled",UseCentreBodyRay550&&!HeadRegion502.Enabled&&!HairBoundary491.Enabled&&!e.head.contourReady?1:0);T("_BodyCentre550",e.head.centreMeta[1]);cmd.DispatchCompute(e.join,k,60,34,1);}
 public static void DeferredEyes(CommandBuffer cmd,Full319View335 v){var e=Active;if(!e||!e.headEnabled||!e.headReady||v!=e.main)return;if(!PixelRenderPipelineControl399.EnableEyeComposePass)return;var h=e.head;h.motion=e.headMotion;e.Params(cmd);int k=e.join.FindKernel("MainToHead");void T(string n,RTHandle t)=>cmd.SetComputeTextureParam(e.join,k,n,t.rt);T("_MLine",v.postLine);T("_MReadOwner",v.owner);T("_MReadMeta",v.preparedMeta);T("_MReadUV",v.preparedUV);T("_HBeforeRW",h.before);T("_HColourRW",h.colour);T("_HPostLineRW",h.postLine);T("_HOwnerRW",h.owner);T("_HMetaRW",h.preparedMeta);T("_HUVRW",h.preparedUV);T("_HDomainRW",h.domain);cmd.DispatchCompute(e.join,k,60,34,1);
 var cs=h.eyeMerge;k=cs.FindKernel("Merge");void E(string n,RTHandle t)=>cmd.SetComputeTextureParam(cs,k,n,t.rt);E("_EyeColour",h.eyeOutput);E("_EyeOwner",h.eyeOwner);E("_Intrinsic",h.intrinsic);E("_EyeAudit",h.eyeAudit);E("_Before",h.before);E("_Colour",h.colour);E("_Owner",h.owner);E("_Domain",h.domain);cmd.DispatchCompute(cs,k,60,34,1);if(PixelRenderPipelineControl399.EnableEyeDetail348Pass)EyeRenderer367.Dispatch(e.headEyes,cmd);HeadRegion502.Gate(cmd,h);k=e.join.FindKernel("EyesToMain");e.BindMain(cmd,k);T("_HColour",h.colour);T("_HOwner",h.owner);T("_HMeta",h.preparedMeta);T("_HUV",h.preparedUV);T("_HReadDomain",h.domain);cmd.DispatchCompute(e.join,k,60,34,1);}
 public static void Declare(IRasterRenderGraphBuilder b,RenderGraph g){} // raster stages own their ordinary inputs
 public static void Declare(IUnsafeRenderGraphBuilder b,RenderGraph g,Full319View335 v){var e=Active;if(!e||!e.headEnabled||v!=e.main||!e.head)return;var h=e.head;foreach(var t in new[]{h.prepared,h.preparedOwner,h.gridPalette,h.eyeOutput,h.eyeOwner,h.intrinsic,h.eyeAudit,h.centreMeta[1]})b.UseTexture(g.ImportTexture(t));foreach(var t in new[]{h.before,h.colour,h.owner,h.preparedMeta,h.preparedUV,h.resolvedMeta,h.resolvedUV,h.postLine,h.domain})b.UseTexture(g.ImportTexture(t),AccessFlags.ReadWrite);foreach(var s in h.layers)foreach(var t in new[]{s.rgba,s.meta,s.uv})b.UseTexture(g.ImportTexture(t));if(e.headEyes&&e.headEyes.samples!=null&&PixelRenderPipelineControl399.EnableEyeDetail348Pass){foreach(var s in e.headEyes.samples)foreach(var t in new[]{s.rgba,s.meta,s.point,s.uv,s.shade})b.UseTexture(g.ImportTexture(t));foreach(var t in new[]{e.headEyes.output,e.headEyes.owner,e.headEyes.intrinsic,e.headEyes.visible,e.headEyes.histA,e.headEyes.histB,e.headEyes.surface,e.headEyes.pigment,e.headEyes.audit,e.headEyes.domain,e.headEyes.bary,e.headEyes.supportMeta})b.UseTexture(g.ImportTexture(t),AccessFlags.ReadWrite);}}
 public void EnsureSampleJoin(){if(post.targets==null)return;int w=post.targets[4][0].rt.width,h=post.targets[4][0].rt.height;if(sampleJoin!=null&&sampleJoin[0][0].rt.width==w&&sampleJoin[0][0].rt.height==h)return;if(sampleJoin!=null)foreach(var row in sampleJoin)foreach(var t in row)t.Release();sampleJoin=Enumerable.Range(0,2).Select(_=>Enumerable.Range(0,4).Select(c=>RTHandles.Alloc(w,h,colorFormat:post.targets[4][c].rt.graphicsFormat,enableRandomWrite:true,filterMode:FilterMode.Point)).ToArray()).ToArray();}
 public void JoinSamples(CommandBuffer cmd){if(!headReady||!headEnabled||post.targets==null||headPost.targets==null)return;Params(cmd);cmd.SetComputeIntParams(join,"_MainROI365",post.roi.x,272-post.roi.y-post.roi.height);cmd.SetComputeIntParams(join,"_HeadROI365",headPost.roi.x,272-headPost.roi.y-headPost.roi.height);cmd.SetComputeIntParams(join,"_MainROIShape365",post.roi.width,post.roi.height);cmd.SetComputeIntParams(join,"_HeadROIShape365",headPost.roi.width,headPost.roi.height);int k=join.FindKernel("JoinSamples");for(int g=4;g<6;g++)for(int c=0;c<4;c++){cmd.SetComputeIntParam(join,"_Channel365",c);cmd.SetComputeTextureParam(join,k,"_HSample",headPost.targets[g][c].rt);cmd.SetComputeTextureParam(join,k,"_MSample",sampleJoin[g-4][c].rt);cmd.DispatchCompute(join,k,(post.roi.width*4+7)/8,(post.roi.height*4+7)/8,1);cmd.CopyTexture(sampleJoin[g-4][c].rt,post.targets[g][c].rt);}}
 void LateUpdate(){if(Application.isPlaying&&automatic)RenderFrame();}
#if UNITY_EDITOR
 void EditorTick(){if(this&&enabled&&!Application.isPlaying&&automatic)RenderFrame();}
#endif
 void OnGUI(){if(!showControls||!main)return;GUILayout.BeginArea(new Rect(10,275,740,95),GUI.skin.box);GUILayout.Label("365 exact head-position grid / same pixel pitch / integer copy / joint outline once");bool a=GUILayout.Toggle(headEnabled,"C head-local grid"),b=GUILayout.Toggle(post.candidateEnabled,"B original364 topology");if(a!=headEnabled||b!=post.candidateEnabled){headEnabled=a;post.candidateEnabled=b;main.motion.resetHistory=true;RenderFrame();}GUILayout.BeginHorizontal();if(GUILayout.Button("< pose")){main.motion.playing=false;main.motion.sourceFrame=Mathf.Repeat(main.motion.sourceFrame-2.5f,40);main.motion.resetHistory=true;RenderFrame();}if(GUILayout.Button("> pose")){main.motion.playing=false;main.motion.sourceFrame=Mathf.Repeat(main.motion.sourceFrame+2.5f,40);main.motion.resetHistory=true;RenderFrame();}GUILayout.EndHorizontal();GUILayout.EndArea();}
 void OnDisable(){
 RenderPipelineManager.beginCameraRendering-=OnBeginCameraRendering;RenderPipelineManager.endCameraRendering-=OnEndCameraRendering;
 DisableScheduledNativeLoop();
 if(!ReleaseClothRequestBits())Debug.LogError("Clothing bit buffer release is pending graphics completion",this);
 ClothRegion524.Release();UseCentreBodyRay550=false;
#if UNITY_EDITOR
 EditorApplication.update-=EditorTick;
#endif
 HeadRegion502.Release();if(sampleJoin!=null)foreach(var row in sampleJoin)foreach(var t in row)t.Release();sampleJoin=null;if(Active==this)Active=null;if(head)head.motion=headMotion;if(headMotion&&!headMotion.enabled)typeof(MotionView331).GetMethod("OnDisable",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(headMotion,null);if(head&&!head.enabled)typeof(Full319View335).GetMethod("OnDisable",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(head,null);if(headObject)DestroyImmediate(headObject);if(target){target.Release();DestroyImmediate(target);}if(main&&priorShadow!=null)for(int i=0;i<priorShadow.Length;i++)main.motion.surface.outputs[i].GetComponent<Renderer>().shadowCastingMode=priorShadow[i];if(main){Full319View335.Active=main;MotionView331.Active=main.motion;}if(mainEyes)EyeFeature348.Active=mainEyes;if(post)PostView366.Active=post;ready=false;}
}
