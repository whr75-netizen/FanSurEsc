using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.Experimental.Rendering;
using FantasySurvival.CharacterPresentation;

// Presentation glue: original native world grid, existing480 E cells, one final native sample.
[DefaultExecutionOrder(475)]public sealed class NativePlayer395:MonoBehaviour
{
 public static NativePlayer395 Active;
 public bool showReviewUI = false;
 public HeadLocal367 host;public RenderPipelineAsset pipeline;public ComputeShader compute;public Shader exactGUI;
 public Camera baselineCamera,gameCamera,localCamera;public bool ready,automatic,showCharacter=true,showBones;public string failure;
 [NonSerialized]internal RenderTexture worldRenderTarget,localRenderTarget;
 [NonSerialized]internal float originalGameCameraDepth;
 public Transform player,avatar,feet;public Quaternion avatarRotation;public ScaleBake378 bake;
 public RTHandle world,worldDepth,output,owner,cellID,depthAudit;
 public Matrix4x4 worldView,worldProjection;public int worldSerial,presentSerial,warmup=90;
 public Vector2 deliveredDelta;public Vector2Int origin=new(0,0);public int nativePixelsPerCell=2;
 public bool reviewFreeze=true;float priorTimeScale=1;bool frozen;
 public float bodyHeight=1.65f,sourceHeight=1.5270981788635254f;
 public float pixelPitch;public bool manualDelta;public Vector2 delta;
 static readonly string interactiveScope="InteractiveReview395_"+DateTime.UtcNow.ToString("yyyyMMdd_HHmmss_fff");
 public static string RunName {get{var args=Environment.GetCommandLineArgs();int at=Array.IndexOf(args,"-native395Run");return at>=0?args[at+1]:interactiveScope;}}
 public static string Out=>Path.GetFullPath(Path.Combine(Application.dataPath,"..","LocalOnly","Runtime399","Native395",RunName))+Path.DirectorySeparatorChar;
 Material gui;int setupWait,lastZoomTrace=-1;
 void Awake(){if(host&&host.main&&host.main.motion.surface.outputs!=null)foreach(var item in host.main.motion.surface.outputs)if(item)item.GetComponent<Renderer>().enabled=false;}
 void OnEnable(){Active=this;if(Application.isPlaying&&pipeline){GraphicsSettings.defaultRenderPipeline=pipeline;QualitySettings.renderPipeline=pipeline;}}
 void OnDisable(){if(frozen)Time.timeScale=priorTimeScale;if(Active==this)Active=null;}
 // Gameplay397 disables this driver while continuing to use its buffers.
 // Only destruction ends ownership of the six handles allocated by EnsureWorld.
 void OnDestroy(){
  if(Active==this)Active=null;
  if(gameCamera){
   if(worldRenderTarget&&gameCamera.targetTexture==worldRenderTarget)gameCamera.targetTexture=null;
   gameCamera.depth=originalGameCameraDepth;
  }
  if(localCamera){localCamera.enabled=false;localCamera.targetTexture=null;}
  if(worldRenderTarget){worldRenderTarget.Release();DestroyImmediate(worldRenderTarget);worldRenderTarget=null;}
  if(localRenderTarget){localRenderTarget.Release();DestroyImmediate(localRenderTarget);localRenderTarget=null;}
  world?.Release();world=null;
  worldDepth?.Release();worldDepth=null;
  output?.Release();output=null;
  owner?.Release();owner=null;
  cellID?.Release();cellID=null;
  depthAudit?.Release();depthAudit=null;
 }
 internal static void ConfigureCharacterOffscreenCamera(Camera cam,Camera referenceWorldCamera){
  if(!cam)return;
  bool cullWorld=PixelRenderPipelineControl399.CullWorldOnCharacterCameras;
  cam.cullingMask=cullWorld?0:(referenceWorldCamera?referenceWorldCamera.cullingMask:~0);
  cam.clearFlags=cullWorld?CameraClearFlags.Nothing:(referenceWorldCamera?referenceWorldCamera.clearFlags:CameraClearFlags.SolidColor);
  cam.allowHDR=false;cam.allowMSAA=false;cam.useOcclusionCulling=false;
  var urp=cam.GetUniversalAdditionalCameraData();
  if(urp!=null){
   urp.renderPostProcessing=false;
   urp.renderShadows=!cullWorld;
   urp.requiresDepthOption=CameraOverrideOption.Off;
   urp.requiresColorOption=CameraOverrideOption.Off;
   urp.antialiasing=AntialiasingMode.None;
   urp.stopNaN=false;
   urp.dithering=false;
  }
 }
 public void EnsureWorld(){if(world!=null)return;world=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"395 unchanged native960 world linear values");worldDepth=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"395 native960 world device depth");output=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"395 native final pixel samples");owner=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point);cellID=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point);depthAudit=RTHandles.Alloc(960,544,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point);}
 void LateUpdate(){if(!Application.isPlaying||!string.IsNullOrEmpty(failure))return;try{TraceZoom();if(!ready){Initialise();return;}if(automatic)RenderPose(host.main.motion.sourceFrame,false);}catch(Exception e){FailPresentation(e);Debug.LogException(e);}}
 public void FailPresentation(Exception error){
  failure=error.ToString();ready=false;automatic=false;showCharacter=false;
  if(host)host.DisableScheduledNativeLoop();
  if(localCamera)localCamera.enabled=false;
  if(gameCamera&&worldRenderTarget&&gameCamera.targetTexture==worldRenderTarget){gameCamera.targetTexture=null;gameCamera.depth=originalGameCameraDepth;}
  if(frozen){Time.timeScale=priorTimeScale;frozen=false;}
  if(host&&host.main&&host.main.motion&&host.main.motion.surface.outputs!=null)foreach(var item in host.main.motion.surface.outputs)if(item)item.GetComponent<Renderer>().enabled=false;
  Directory.CreateDirectory(Out);File.WriteAllText(Out+"FIRST_RUNTIME_FAILURE395.txt",failure);
 }
 void TraceZoom(){if((!reviewFreeze&&!showReviewUI)||Time.frameCount>105||lastZoomTrace==Time.frameCount)return;lastZoomTrace=Time.frameCount;var cam=Camera.main;if(!cam)return;var z=cam.GetComponent<CameraZoomController>();if(!z)return;Directory.CreateDirectory(Out);string file=Out+"NATIVE_ZOOM_STARTUP_TRACE395.csv";if(!File.Exists(file))File.WriteAllText(file,"frame,nativeGrid,ppu,nativeIntegerScale,pixelHeight,scaledPixelHeight,screenHeight,heightScale,ortho,targetHeight\n");File.AppendAllText(file,Time.frameCount+","+z.NativePixelGridEnabled+","+z.NativePixelsPerUnit.ToString("R")+","+z.NativeIntegerScale+","+cam.pixelHeight+","+cam.scaledPixelHeight+","+Screen.height+","+ScalableBufferManager.heightScaleFactor.ToString("R")+","+cam.orthographicSize.ToString("R")+","+(cam.targetTexture?cam.targetTexture.height:0)+"\n");}
 void Initialise(){
  PixelRenderPipelineControl399.Ensure(this);
  bool fast=PixelRenderPipelineControl399.FastStartup&&!reviewFreeze;
  if(!fast&&Time.frameCount<warmup)return;
  var m=host.main.motion;
  if(!gameCamera){
   var cam=Camera.main;var old=FindObjectsByType<CharacterSilhouetteSubject>(FindObjectsInactive.Include).FirstOrDefault(s=>s.name=="CharacterSilhouettePlayerVisual");if(!cam||!old)return;
   gameCamera=cam;originalGameCameraDepth=gameCamera.depth;if(reviewFreeze){priorTimeScale=Time.timeScale;Time.timeScale=0;frozen=true;}player=old.transform.parent;var cc=player.GetComponent<CharacterController>();if(!cc)throw new Exception("395 actual Player controller missing");
   if(UniversalRenderPipeline.asset.renderScale!=1)throw new Exception("395 original PC renderScale must remain1");
   if(!gameCamera.targetTexture){worldRenderTarget=new RenderTexture(960,544,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB){name="395 original native gameplay960",filterMode=FilterMode.Point,antiAliasing=1};worldRenderTarget.Create();gameCamera.targetTexture=worldRenderTarget;}else worldRenderTarget=gameCamera.targetTexture;
   gameCamera.depth=-2f;
   foreach(var item in m.surface.outputs)if(item)item.GetComponent<Renderer>().enabled=true;
   // Keep the original camera enabled: Camera.main and gameplay/native registration continue to work.
   var anchor=new GameObject("E395_Visual_165cm_Trial");anchor.transform.SetParent(player,false);anchor.transform.localPosition=cc.center-Vector3.up*(cc.height*.5f);feet=anchor.transform;
   avatar=m.animation.target.transform;avatarRotation=avatar.rotation;avatar.SetParent(feet,true);avatar.localScale=Vector3.one*(bodyHeight/sourceHeight);Follow();
   foreach(var r in old.GetComponentsInChildren<Renderer>(true))r.enabled=false;old.enabled=false;
   localCamera=new GameObject("395 E local480 cells at native world pitch").AddComponent<Camera>();localCamera.transform.SetParent(transform,false);localCamera.CopyFrom(gameCamera);localCamera.tag="Untagged";localCamera.depth=0f;localCamera.enabled=false;
   ConfigureCharacterOffscreenCamera(localCamera,gameCamera);
   localRenderTarget=new RenderTexture(960,544,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB){name="395 E composite native960",filterMode=FilterMode.Point,antiAliasing=1};localRenderTarget.Create();localCamera.targetTexture=localRenderTarget;
   m.camera=localCamera;m.animation.viewCamera=localCamera;m.surface.targetCamera=localCamera;m.animation.previewPipeline=pipeline;
   host.automatic=host.main.automatic=false;host.headEnabled=PixelRenderPipelineControl399.EnableHeadLocalGrid;host.post.candidateEnabled=PixelRenderPipelineControl399.EnablePost366Candidate;host.showControls=host.mainEyes.showControls=host.post.showControls=m.showControls=m.animation.showControls=false;
   EnsureWorld();
  }
  if(++setupWait<(fast?1:5))return;
  Follow();gameCamera.Render();SetLocalCamera();
  m.animation.Initialise();m.Initialise();m.surface.Initialise();
  bake=gameObject.AddComponent<ScaleBake378>();bake.host=host;bake.original=m.surface;bake.Initialise();
  m.sourceFrame=0;PreBake();host.Initialise();m.playing=false;m.speed=.25f;m.resetHistory=true;automatic=false;ready=true;
  pixelPitch=2*localCamera.orthographicSize/272;
  Directory.CreateDirectory(Out);WriteBinding();
 }
 public void Follow(){if(avatar&&feet){avatar.position=feet.position;avatar.rotation=player.rotation*avatarRotation;avatar.localScale=Vector3.one*(bodyHeight/sourceHeight);}}
 void PreBake(){host.main.motion.Evaluate();Follow();bake.Evaluate(true);}
 internal void SetLocalCamera(){
  if(worldSerial==0)throw new Exception("395 native world capture did not execute");
  var inverse=worldView.inverse;localCamera.transform.SetPositionAndRotation(inverse.GetColumn(3),gameCamera.transform.rotation);
  localCamera.orthographicSize=gameCamera.orthographicSize*nativePixelsPerCell*.5f;localCamera.aspect=gameCamera.aspect;localCamera.nearClipPlane=gameCamera.nearClipPlane;localCamera.farClipPlane=gameCamera.farClipPlane;
  localCamera.ResetWorldToCameraMatrix();var projection=worldProjection;float factor=2f/nativePixelsPerCell;projection.SetRow(0,projection.GetRow(0)*factor+(960-480*nativePixelsPerCell-2*origin.x)/(480f*nativePixelsPerCell)*worldProjection.GetRow(3));projection.SetRow(1,projection.GetRow(1)*factor+(544-272*nativePixelsPerCell-2*origin.y)/(272f*nativePixelsPerCell)*worldProjection.GetRow(3));localCamera.projectionMatrix=projection;
 }
 public void RenderPose(float frame,bool forceCapture=true){var m=host.main.motion;m.sourceFrame=frame;if(forceCapture)m.resetHistory=true;PreBake();gameCamera.Render();SetLocalCamera();host.RenderFrame();}
 [Serializable]class Binding{public string player,avatar,worldCamera,localCamera,pipeline;public bool originalCameraEnabled,headLocal,wholeBody364,T0;public float bodyHeight,scale,worldOrtho,localOrtho,worldPixelPitch,localPixelPitch;public int warmupFrame,worldSerial,nativePixelsPerCell;public float authoredArtWorldPitch;public Vector2Int origin;public Matrix4x4 worldView,worldProjection;}
 void WriteBinding(){var b=new Binding{player=ActualPlayerAudit391.PathOf(player),avatar=ActualPlayerAudit391.PathOf(avatar),worldCamera=ActualPlayerAudit391.PathOf(gameCamera.transform),localCamera=localCamera.name,pipeline=pipeline.name,originalCameraEnabled=gameCamera.enabled,headLocal=true,wholeBody364=false,T0=false,bodyHeight=sourceHeight*avatar.lossyScale.y,scale=avatar.lossyScale.y,worldOrtho=gameCamera.orthographicSize,localOrtho=localCamera.orthographicSize,worldPixelPitch=2*gameCamera.orthographicSize/544,localPixelPitch=2*localCamera.orthographicSize/272,warmupFrame=Time.frameCount,worldSerial=worldSerial,nativePixelsPerCell=nativePixelsPerCell,authoredArtWorldPitch=1/gameCamera.GetComponent<CameraZoomController>().NativePixelsPerUnit,origin=origin,worldView=worldView,worldProjection=worldProjection};File.WriteAllText(Out+"RUNTIME_BINDING395.json",JsonUtility.ToJson(b,true));}
 void OnGUI(){if(!showReviewUI)return;if(!ready)return;GUI.depth=-20000;GUI.color=new Color(.06f,.07f,.09f,1);GUI.DrawTexture(new Rect(0,0,Screen.width,172),Texture2D.whiteTexture);GUI.color=Color.white;GUILayout.BeginArea(new Rect(12,10,1120,150),GUI.skin.box);GUILayout.Label("E / actual Player / original world pixels / 1.65m trial");GUILayout.BeginHorizontal();if(GUILayout.Button(automatic?"Pause":"Walk")){automatic=!automatic;host.main.motion.playing=automatic;}if(GUILayout.Button("0.25x"))host.main.motion.speed=.25f;if(GUILayout.Button("1x"))host.main.motion.speed=1;if(GUILayout.Button("< frame")){automatic=false;host.main.motion.playing=false;RenderPose(Mathf.Repeat(host.main.motion.sourceFrame-2.5f,40));}if(GUILayout.Button("frame >")){automatic=false;host.main.motion.playing=false;RenderPose(Mathf.Repeat(host.main.motion.sourceFrame+2.5f,40));}showBones=GUILayout.Toggle(showBones,"Bones");GUILayout.EndHorizontal();GUILayout.Label("Frame "+host.main.renderedFrame335.ToString("F2")+" / E native-art grid "+pixelPitch.ToString("F8")+"m / unadopted review");GUILayout.EndArea();if(Event.current.type==EventType.Repaint){if(!gui)gui=new Material(exactGUI);bool old=GL.sRGBWrite;GL.sRGBWrite=false;Graphics.DrawTexture(new Rect(16,176,960,544),localCamera.targetTexture,gui);GL.sRGBWrite=old;}if(showBones){foreach(HumanBodyBones bone in Enum.GetValues(typeof(HumanBodyBones))){if(bone==HumanBodyBones.LastBone)continue;var t=host.main.motion.animation.target.GetBoneTransform(bone);if(!t)continue;var q=worldProjection*worldView*new Vector4(t.position.x,t.position.y,t.position.z,1);GUI.color=Color.cyan;GUI.DrawTexture(new Rect(16+(q.x/q.w*.5f+.5f)*960-1,176+(.5f-q.y/q.w*.5f)*544-1,3,3),Texture2D.whiteTexture);}GUI.color=Color.white;}}
}
