using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
#if UNITY_EDITOR
using UnityEditor;
#endif

[ExecuteAlways,DefaultExecutionOrder(110)]public sealed class MotionView331:MonoBehaviour
{
 public Source329WalkView animation;public CurrentSurface330 surface;public Camera camera;
 [Range(0,2)]public int mode;public int poseBins=16;public bool playing=true,showControls=true;public float sourceFrame,speed=1;
 public bool commonDepth=true;public bool resetHistory=true;
 public bool actorLocalGrid=true;public float uvToleranceTexels=.5f;
 public static MotionView331 Active;
 [NonSerialized]public Material[]materials;public ComputeShader compose;
 [NonSerialized]public float evaluatedFrame;
 [NonSerialized]public RTHandle[]raw;[NonSerialized]public RTHandle depth,output,audit,owner,historyColour,historyMeta,historyUV,worldInfo;
 [NonSerialized]public int probeRole,probeSide;
 [NonSerialized]public Vector4 clipShift;[NonSerialized]public Vector2 composeDelta;[NonSerialized]public bool captureNow;[NonSerialized]public Vector4[]texelSizes=new Vector4[16];
 public Vector2 capturePivot;public int captures,historyEpoch;
 readonly List<ComputeBuffer>buffers=new();double last;int previousMode=-1,previousBins=-1,lightingHash,gridMode=-1;float previousBin=-1,gridSize,gridAspect;Quaternion previousCameraRotation,gridRotation;Vector4 previousLight;bool ready,gridReady;Vector2 fixedGridPivot;
 void OnEnable(){Active=this;last=Time.realtimeSinceStartupAsDouble;
#if UNITY_EDITOR
 EditorApplication.update+=EditorTick;
#endif
 }
 public void Initialise(){if(ready||!animation||!surface||!camera||!compose)return;Active=this;animation.playing=false;animation.showControls=false;
  var shader=Shader.Find("EValidation/VisibilityMotion331Probe");if(!shader)throw new Exception("331 probe shader missing");
  var mats=new List<Material>();for(int i=0;i<surface.source.Length;i++)for(int sm=0;sm<surface.source[i].sharedMaterials.Length;sm++){
   var src=surface.source[i].sharedMaterials[sm];var m=new Material(src){shader=shader,hideFlags=HideFlags.DontSave};m.CopyPropertiesFromMaterial(src);m.shaderKeywords=src.shaderKeywords;int role=i==0?new[]{7,8,9,10}[sm]:i==1?new[]{0,1,2,3,4,5,6}[sm]:new[]{11,12,13,14}[sm];var tx=src.GetTexture("_MainTex");texelSizes[role]=new Vector4(tx?1f/tx.width:1,tx?1f/tx.height:1,0,0);
   var mesh=surface.source[i].sharedMesh;var indices=mesh.GetIndices(sm);var ids=new float[indices.Length/3];
   if(i==0){var skin=surface.source[i];var weights=mesh.boneWeights;var left=animation.target.GetBoneTransform(HumanBodyBones.LeftUpperLeg);var right=animation.target.GetBoneTransform(HumanBodyBones.RightUpperLeg);var side=skin.bones.Select(b=>b==left||b.IsChildOf(left)?1:b==right||b.IsChildOf(right)?2:0).ToArray();
    for(int t=0;t<ids.Length;t++){float l=0,r=0;for(int j=0;j<3;j++){var b=weights[indices[3*t+j]];var ix=new[]{b.boneIndex0,b.boneIndex1,b.boneIndex2,b.boneIndex3};var wt=new[]{b.weight0,b.weight1,b.weight2,b.weight3};for(int k=0;k<4;k++){if(side[ix[k]]==1)l+=wt[k];if(side[ix[k]]==2)r+=wt[k];}}ids[t]=Mathf.Max(l,r)>1.5f?(l>=r?1:2):0;}}
   var cb=new ComputeBuffer(Math.Max(1,ids.Length),4);cb.SetData(ids.Length>0?ids:new float[1]);buffers.Add(cb);m.SetBuffer("_Instance331",cb);mats.Add(m);
  }materials=mats.ToArray();
  RTHandle T(bool rw=true)=>RTHandles.Alloc(480,272,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:rw,filterMode:FilterMode.Point);
  raw=Enumerable.Range(0,7).Select(_=>T(false)).ToArray();depth=RTHandles.Alloc(480,272,depthBufferBits:DepthBits.Depth32);output=T();audit=T();owner=T();historyColour=T();historyMeta=T();historyUV=T();worldInfo=T();
  foreach(var f in surface.outputs)f.GetComponent<Renderer>().shadowCastingMode=ShadowCastingMode.ShadowsOnly;
  previousCameraRotation=camera.transform.rotation;ready=true;resetHistory=true;Evaluate();
 }
 public Vector2 Pivot(){var q=camera.WorldToViewportPoint(animation.target.transform.position);return new Vector2(q.x*480,q.y*272);}
 int LightingHash(){unchecked{int h=17;void A(int x){h=h*31+x;}foreach(var l in FindObjectsByType<Light>(FindObjectsSortMode.None).OrderBy(x=>x.GetEntityId().GetHashCode())){A(l.GetEntityId().GetHashCode());A(l.isActiveAndEnabled?1:0);A(l.transform.position.GetHashCode());A(l.transform.rotation.GetHashCode());A(l.color.GetHashCode());A(l.intensity.GetHashCode());A(l.range.GetHashCode());A(l.shadowStrength.GetHashCode());}foreach(var l in FindObjectsByType<FantasySurvival.WorldLighting.SteppedLocalLight>(FindObjectsSortMode.None).OrderBy(x=>x.GetEntityId().GetHashCode())){A(l.transform.position.GetHashCode());A(l.Color.GetHashCode());A(l.Intensity.GetHashCode());A(l.Radius.GetHashCode());}A(RenderSettings.ambientLight.GetHashCode());A(animation.shadeProfile.GetHashCode());return h;}}
 public bool NeedCapture(){if(mode!=2)return true;var sun=RenderSettings.sun;var light=sun?new Vector4(sun.transform.forward.x,sun.transform.forward.y,sun.transform.forward.z,sun.intensity):Vector4.zero;int hash=LightingHash();bool changed=resetHistory||previousMode!=mode||previousBins!=poseBins||previousBin!=evaluatedFrame||Quaternion.Angle(previousCameraRotation,camera.transform.rotation)>.00001f||light!=previousLight||hash!=lightingHash;if(changed){capturePivot=Pivot();captures++;historyEpoch++;previousMode=mode;previousBins=poseBins;previousBin=evaluatedFrame;previousCameraRotation=camera.transform.rotation;previousLight=light;lightingHash=hash;resetHistory=false;}return changed;}
 public void PrepareCapture(){var pivot=Pivot();var rotation=Quaternion.Inverse(animation.target.transform.rotation)*camera.transform.rotation;if(mode==2&&actorLocalGrid){if(!gridReady||gridMode!=2||Quaternion.Angle(rotation,gridRotation)>.00001f||gridSize!=camera.orthographicSize||gridAspect!=camera.aspect){fixedGridPivot=pivot;gridReady=true;gridRotation=rotation;gridSize=camera.orthographicSize;gridAspect=camera.aspect;resetHistory=true;}var gpu=GL.GetGPUProjectionMatrix(camera.projectionMatrix,true);var delta=fixedGridPivot-pivot;clipShift=new Vector4(2*delta.x/480,2*delta.y/272*(gpu[1,1]/camera.projectionMatrix[1,1]),0,0);composeDelta=pivot-fixedGridPivot;}else{clipShift=Vector4.zero;composeDelta=mode==2?pivot-capturePivot:Vector2.zero;}gridMode=mode;captureNow=NeedCapture();}
 public void Evaluate(){if(!animation||!surface)return;animation.playing=false;float step=40f/Mathf.Max(1,poseBins);evaluatedFrame=mode==0?sourceFrame:Mathf.Floor(sourceFrame/step)*step;animation.Sample(evaluatedFrame);surface.Evaluate();}
 void Advance(){double now=Time.realtimeSinceStartupAsDouble;float dt=(float)Math.Min(now-last,.1);last=now;if(playing&&animation&&animation.clip)sourceFrame=Mathf.Repeat(sourceFrame+dt*40/animation.clip.length*speed,40);Evaluate();}
 void Update(){Initialise();if(Application.isPlaying)Advance();}
#if UNITY_EDITOR
 void EditorTick(){if(!Application.isPlaying&&animation&&surface){Initialise();Advance();if(playing)EditorApplication.QueuePlayerLoopUpdate();}}
#endif
 void OnDisable(){
#if UNITY_EDITOR
 EditorApplication.update-=EditorTick;
#endif
  if(Active==this)Active=null;foreach(var f in surface?surface.outputs:Array.Empty<MeshFilter>())if(f)f.GetComponent<Renderer>().shadowCastingMode=ShadowCastingMode.On;
  if(materials!=null)foreach(var m in materials)if(m)DestroyImmediate(m);foreach(var b in buffers)b.Dispose();buffers.Clear();if(raw!=null)foreach(var t in raw)t.Release();foreach(var t in new[]{depth,output,audit,owner,historyColour,historyMeta,historyUV,worldInfo})t?.Release();ready=false;gridReady=false;
 }
 void OnGUI(){if(!showControls||!animation)return;GUILayout.BeginArea(new Rect(10,10,760,130),GUI.skin.box);GUILayout.Label("331 GameMap1 | R0 continuous / R1 pose hold / R2 colour hold + CURRENT visibility");GUILayout.BeginHorizontal();
  if(GUILayout.Button(playing?"Pause":"Play"))playing=!playing;if(GUILayout.Button("0.25x / 1x"))speed=speed<.5?1:.25f;
  if(GUILayout.Button("<")){playing=false;sourceFrame=Mathf.Max(0,Mathf.Round(sourceFrame)-1);resetHistory=true;}
  if(GUILayout.Button(">")){playing=false;sourceFrame=Mathf.Min(40,Mathf.Round(sourceFrame)+1);resetHistory=true;}
  int selected=GUILayout.SelectionGrid(mode,new[]{"R0 continuous","R1 pose only","R2 held colour"},3);if(selected!=mode){mode=selected;resetHistory=true;}
  if(GUILayout.Button(poseBins+" bins")){poseBins=poseBins==16?8:16;resetHistory=true;}
  GUILayout.EndHorizontal();float f=GUILayout.HorizontalSlider(sourceFrame,0,40);if(Mathf.Abs(f-sourceFrame)>.01){playing=false;sourceFrame=f;resetHistory=true;}
  GUILayout.Label("time "+sourceFrame.ToString("F2")+" -> evaluated "+evaluatedFrame.ToString("F2")+" | R2 fixed actor capture grid + current per-pixel depth/coverage | no global RGB accumulation");GUILayout.EndArea();}
}
