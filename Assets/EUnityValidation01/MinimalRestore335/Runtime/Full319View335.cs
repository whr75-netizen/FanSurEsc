using System;using System.IO;using System.Linq;using System.Collections.Generic;using Unity.Collections;using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Experimental.Rendering;
#if UNITY_EDITOR
using UnityEditor;
#endif

[ExecuteAlways,DefaultExecutionOrder(200)]public sealed class Full319View335:MonoBehaviour
{
 [Serializable]public class Endpoint{public int a,b;public float t;}
 [Serializable]public class Phase{public Matrix4x4 head,nativeFaceMatrix;public Vector3[]anchors;public Mesh face,backing,nativeFace;public Endpoint first,last;}
 public MotionView331 motion;public Phase[]phases;public Socket216View.Eye[]eyes;public Projected262Calibration calibration;public Contour295Input contours;public Texture2D templateRGBA,templateRole,triangleVertices;public TextAsset bodyParts;public Material[]metadata;
 public Texture2D creamMember,stockMember,skinMember;public ComputeShader canonical;[NonSerialized]public ComputeBuffer sourceTags;[NonSerialized]public Vector4[]roleRanges=new Vector4[16];public Shader nativeShader,independentShader;public ComputeShader prepare,lines,eyeCompose,eyeMerge,compose;public bool integrated=true,automatic=true;public float lineTone;public bool usePalette;public Vector4 deepCream,deepSkin;
 public bool layeredSurface=true,shadeLayer=true;
 public bool shadeCurvature=true,faceShadeTint=true;
 // Linear shadow factors (.86,.686,.60) at the existing .72 floor, not skin albedo.
 public Vector3 faceShadeChromaticity=new Vector3(.86f/.72f,.686f/.72f,.60f/.72f);public int faceShadeSteps=3,surfaceShadeSteps=2;[NonSerialized]public int surfaceLayerView;
 public bool styleEnabled=true;[Range(0,3)]public int stockMode=3;public bool faceMain=true,faceProvider=false;
 public Shader legacySignalsShader,legacyProviderShader;public ComputeShader restoreStyle;public Material legacyRole3,legacyRole7;public Vector4 stockLit,stockShade,creamShade,skinShade,role3Reflectance,role7Reflectance;
 [NonSerialized]public RTHandle[]style480,style960;[NonSerialized]public RTHandle shadeMask480,shadeMask960;[NonSerialized]public RTHandle styleDepth480,styleDepth960,beforeStyle;
 [NonSerialized]public Material[]legacySignalsMats;[NonSerialized]public Material legacyProviderMat;int priorStyleKey=-1;
 [NonSerialized]public int renderedSerial335;[NonSerialized]public float renderedSource335,renderedFrame335;
 public static Full319View335 Active;
 public bool showReviewUI=false;
 [NonSerialized]public RTHandle[]native,meta,normal;[NonSerialized]public RTHandle[]centreMeta,centreNormal;[NonSerialized]public RTHandle centreFamily;[NonSerialized]public RTHandle family,nativeDepth,colourNative,before,colour,owner,audit,gridSurface,gridPalette,paletteAudit,prepared,preparedOwner,postLine,preparedUV,preparedMeta,resolvedMeta,resolvedUV,eyeOutput,eyeOwner,intrinsic,eyeAudit,domain;
 [NonSerialized]public RTHandle edgeMetaSnap,edgeUVSnap;[NonSerialized]public RTHandle[]edgeHistory;[NonSerialized]public ComputeShader edgeStabilize;
 [NonSerialized]public bool isGenericModel;[NonSerialized]public int[][]submeshRoles;
 Material[]originalMetadataAssets,dynamicMetadataMats;
 int edgeHistoryWriteIdx;bool hasPrevEdgePivot;Vector2Int prevEdgePivot;Quaternion prevEdgeActorRot,prevEdgeCamRot;float prevEdgeOrtho;
 public sealed class Layer{public RTHandle rgba,meta,uv,depth;}
 [NonSerialized]public Layer[]layers;[NonSerialized]public RTHandle[]flood;[NonSerialized]public Material[]nativeMats,worldMats,independentMats;[NonSerialized]public Mesh bodyProxy,registeredHair,otherHair;
 [NonSerialized]public Texture2D actionMap;[NonSerialized]public Matrix4x4 providerMatrix,effectiveProjection;[NonSerialized]public Vector4 nativeShift;[NonSerialized]public Vector2[]projectedPivots,projectedAnchors;[NonSerialized]public int phaseIndex,y0,y1;[NonSerialized]public bool contourReady,capturePending;[NonSerialized]public ContourSelect333.Receipt receipt;
 [NonSerialized]public Matrix4x4[]eyeInverse;[NonSerialized]public Vector4[]eyePlanes;[NonSerialized]public Vector3 rayBase,rayX,rayY,rayDepth;
 [NonSerialized]public Action validateRender;Camera geometryCamera;bool ready,rendering;int priorIntegrated=-1;int[]proxyIndices;Vector4[]proxyInfo;Vector2[]proxyUV;int[][]proxyGroups;
 Vector3[]proxyVertsBuf,proxyNormsBuf;bool proxyTopologyUploaded,actionMapDirty;readonly Vector3[]eyeWorldBuf=new Vector3[4];readonly Vector2[]eyePtsBuf=new Vector2[4],eyeToPtsBuf=new Vector2[4];
 static Color[]emptyActionMapColors;
 void OnEnable(){Active=this;
#if UNITY_EDITOR
 EditorApplication.update+=EditorTick;
#endif
 }
 public void Initialise(){if(ready||!motion||phases==null||phases.Length!=16)return;Active=this;motion.Initialise();motion.mode=2;motion.poseBins=16;motion.camera.enabled=false;
  RTHandle T(int w=480,int h=272,bool rw=true)=>RTHandles.Alloc(w,h,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:rw,filterMode:FilterMode.Point);
  centreMeta=Enumerable.Range(0,3).Select(_=>T(480,272,true)).ToArray();centreNormal=Enumerable.Range(0,3).Select(_=>T(480,272,true)).ToArray();centreFamily=T(480,272,true);
  before=T();colour=T();owner=T();audit=T();gridSurface=T(960,544);gridPalette=T(960,544);paletteAudit=T();prepared=T();preparedOwner=T();postLine=T();preparedUV=T();preparedMeta=T();resolvedMeta=T();resolvedUV=T();eyeOutput=T();eyeOwner=T();intrinsic=T();eyeAudit=T();domain=T();
  edgeMetaSnap=T();edgeUVSnap=T();edgeHistory=new[]{T(),T()};edgeStabilize=Resources.Load<ComputeShader>("EdgeStabilize399");hasPrevEdgePivot=false;edgeHistoryWriteIdx=0;
  flood=new[]{RTHandles.Alloc(480,272,colorFormat:GraphicsFormat.R32_UInt,enableRandomWrite:true),RTHandles.Alloc(480,272,colorFormat:GraphicsFormat.R32_UInt,enableRandomWrite:true)};
  if(!legacySignalsShader||!legacyProviderShader||!restoreStyle||!legacyRole3||!legacyRole7)throw new Exception("335 explicit legacy policy inputs missing");
  style480=Enumerable.Range(0,4).Select(_=>T(480,272,true)).ToArray();shadeMask480=T(480,272,true);styleDepth480=RTHandles.Alloc(480,272,depthBufferBits:DepthBits.Depth32);beforeStyle=T();
  if(PixelRenderPipelineControl399.NeedsNative960)EnsureNative960();
  actionMap=new Texture2D(480,272,TextureFormat.RGBAFloat,false,true){filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp,hideFlags=HideFlags.DontSave};emptyActionMapColors??=new Color[480*272];actionMap.SetPixels(emptyActionMapColors);actionMap.Apply();actionMapDirty=false;
  geometryCamera=new GameObject("333 CPU effective capture projection"){hideFlags=HideFlags.HideAndDontSave}.AddComponent<Camera>();geometryCamera.enabled=false;geometryCamera.orthographic=true;
  if(!creamMember||!stockMember||!skinMember||!canonical)throw new Exception("333 original319 membership/canonical input must be explicitly bound");ContourSelect333.TagBytes=bodyParts.bytes;
  if(originalMetadataAssets==null&&metadata!=null)originalMetadataAssets=(Material[])metadata.Clone();
  RebuildModelMaterialsAndProxy(isGenericModel,submeshRoles);
  ready=true;motion.showControls=false;motion.animation.showControls=false;
 }
 public void EnsureNative960(){
  if(native!=null)return;
  RTHandle T(int w,int h,bool rw=true)=>RTHandles.Alloc(w,h,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:rw,filterMode:FilterMode.Point);
  RTHandle Z()=>RTHandles.Alloc(960,544,depthBufferBits:DepthBits.Depth32);
  native=Enumerable.Range(0,8).Select(_=>T(960,544,false)).ToArray();
  meta=Enumerable.Range(0,3).Select(_=>T(960,544,true)).ToArray();
  normal=Enumerable.Range(0,3).Select(_=>T(960,544,true)).ToArray();
  family=T(960,544,true);nativeDepth=Z();colourNative=T(960,544,true);
  style960=Enumerable.Range(0,4).Select(_=>T(960,544,true)).ToArray();
  shadeMask960=T(960,544,true);styleDepth960=Z();
 }
 public void EnsureEyeLayers(){
  if(layers!=null)return;
  RTHandle T(int w,int h,bool rw=true)=>RTHandles.Alloc(w,h,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:rw,filterMode:FilterMode.Point);
  layers=Enumerable.Range(0,13).Select(_=>new Layer{rgba=T(480,272,false),meta=T(480,272,false),uv=T(480,272,false),depth=RTHandles.Alloc(480,272,depthBufferBits:DepthBits.Depth32)}).ToArray();
 }
 public int RoleFor(int r,int sm){
  if(submeshRoles!=null&&r>=0&&r<submeshRoles.Length&&submeshRoles[r]!=null&&sm>=0&&sm<submeshRoles[r].Length)return submeshRoles[r][sm];
  return r==0?(sm<4?new[]{7,8,9,10}[sm]:10):r==1?Mathf.Clamp(sm,0,6):(11+(sm%4));
 }
 public void RebuildForModel(bool generic,int[][]roles){
  isGenericModel=generic;submeshRoles=roles;hasPrevEdgePivot=false;
  if(!ready)return;
  RebuildModelMaterialsAndProxy(generic,roles);
 }
 void DestroyMatArray(Material[]arr){if(arr!=null)foreach(var m in arr)if(m)DestroyImmediate(m);}
 void RebuildModelMaterialsAndProxy(bool generic,int[][]roles){
  DestroyMatArray(nativeMats);DestroyMatArray(worldMats);DestroyMatArray(independentMats);DestroyMatArray(legacySignalsMats);
  if(legacyProviderMat)DestroyImmediate(legacyProviderMat);
  DestroyMatArray(dynamicMetadataMats);dynamicMetadataMats=null;
  if(bodyProxy)DestroyImmediate(bodyProxy);bodyProxy=null;
  if(registeredHair)DestroyImmediate(registeredHair);registeredHair=null;
  if(otherHair)DestroyImmediate(otherHair);otherHair=null;
  sourceTags?.Dispose();sourceTags=null;

  nativeMats=motion.materials.Select(m=>new Material(m){shader=nativeShader,hideFlags=HideFlags.DontSave}).ToArray();
  worldMats=nativeMats.Select(m=>new Material(m){shader=Shader.Find("EValidation/GameMap333World"),hideFlags=HideFlags.DontSave}).ToArray();
  var indList=new List<Material>();
  var legList=new List<Material>();
  var metaList=new List<Material>();
  var metaTemplate=originalMetadataAssets!=null&&originalMetadataAssets.Length>0?originalMetadataAssets[0]:(metadata!=null&&metadata.Length>0?metadata[0]:null);
  var metaShader=metaTemplate?metaTemplate.shader:Shader.Find("EValidation/GameMap333Metadata");
  int flatIdx=0;
  for(int r=0;r<3;r++){
   var skin=motion.surface.source[r];if(!skin||!skin.sharedMesh)continue;
   var srcMats=skin.sharedMaterials;
   int subCount=Math.Min(skin.sharedMesh.subMeshCount,srcMats.Length);
   for(int sm=0;sm<subCount;sm++){
    var src=srcMats[sm];
    int role=RoleFor(r,sm);
    var im=new Material(src){shader=independentShader,hideFlags=HideFlags.DontSave};im.SetFloat("_Auto245Role",role);indList.Add(im);
    var probeMat=flatIdx<motion.materials.Length?motion.materials[flatIdx]:src;
    var lm=new Material(probeMat){shader=legacySignalsShader,hideFlags=HideFlags.DontSave};lm.SetFloat("_Auto245Role",role);
    if(!generic&&(role==3||role==7))LegacyClass(lm,role==3?role3Reflectance:role7Reflectance);
    legList.Add(lm);
    if(generic&&metaShader){
     var mm=new Material(metaShader){hideFlags=HideFlags.DontSave};
     if(src.HasProperty("_MainTex"))mm.SetTexture("_MainTex",src.GetTexture("_MainTex"));
     if(src.HasProperty("_Color"))mm.SetColor("_Color",src.GetColor("_Color"));
     if(src.HasProperty("_Cutoff"))mm.SetFloat("_Cutoff",src.GetFloat("_Cutoff"));
     if(src.HasProperty("_M_CullMode"))mm.SetFloat("_M_CullMode",src.GetFloat("_M_CullMode"));
     mm.SetFloat("_Auto245Role",role);
     mm.SetFloat("_Surface252DefaultPart",r==0?0:(r==1?6:7));
     foreach(var kw in src.shaderKeywords)if(kw=="_ALPHATEST_ON"||kw=="_ALPHABLEND_ON")mm.EnableKeyword(kw);
     metaList.Add(mm);
    }
    flatIdx++;
   }
  }
  independentMats=indList.ToArray();
  legacySignalsMats=legList.ToArray();
  if(generic){dynamicMetadataMats=metaList.ToArray();metadata=dynamicMetadataMats;}
  else if(originalMetadataAssets!=null){metadata=originalMetadataAssets;}
  if(!generic&&independentMats.Length>7){legacyProviderMat=new Material(independentMats[7]){shader=legacyProviderShader,hideFlags=HideFlags.DontSave};legacyProviderMat.SetFloat("_Auto245Role",3);LegacyClass(legacyProviderMat,role3Reflectance);}
  if(!generic)BuildProxy();
  else BuildGenericProxy();
 }
 void BuildGenericProxy(){
  var skin=motion.surface.source[0];var mesh=motion.surface.outputs[0].sharedMesh;
  var target=motion.animation?motion.animation.target:null;
  var lArm=target?target.GetBoneTransform(HumanBodyBones.LeftUpperArm):null;
  var rArm=target?target.GetBoneTransform(HumanBodyBones.RightUpperArm):null;
  var lLeg=target?target.GetBoneTransform(HumanBodyBones.LeftUpperLeg):null;
  var rLeg=target?target.GetBoneTransform(HumanBodyBones.RightUpperLeg):null;
  var bonePart=skin&&skin.bones!=null?skin.bones.Select(b=>!b?1:(lArm&&(b==lArm||b.IsChildOf(lArm)))?2:(rArm&&(b==rArm||b.IsChildOf(rArm)))?3:(lLeg&&(b==lLeg||b.IsChildOf(lLeg)))?4:(rLeg&&(b==rLeg||b.IsChildOf(rLeg)))?5:1).ToArray():Array.Empty<int>();
  var weights=skin&&skin.sharedMesh?skin.sharedMesh.boneWeights:Array.Empty<BoneWeight>();
  int ns=mesh.subMeshCount;var ids=new List<int>();var info=new List<Vector4>();var uv=new List<Vector2>();proxyGroups=new int[ns][];
  int globalTri=1;
  for(int sm=0;sm<ns;sm++){
   var ix=mesh.GetIndices(sm);int nt=ix.Length/3;int start=ids.Count;
   for(int t=0;t<nt;t++){
    float w1=0,w2=0,w3=0,w4=0,w5=0;
    if(weights.Length>0&&bonePart.Length>0){
     for(int j=0;j<3;j++){
      var b=weights[ix[3*t+j]];int[]bi={b.boneIndex0,b.boneIndex1,b.boneIndex2,b.boneIndex3};float[]wt={b.weight0,b.weight1,b.weight2,b.weight3};
      for(int k=0;k<4;k++){int idxB=bi[k];if(idxB<0||idxB>=bonePart.Length)continue;int p=bonePart[idxB];float w=wt[k];if(p==2)w2+=w;else if(p==3)w3+=w;else if(p==4)w4+=w;else if(p==5)w5+=w;else w1+=w;}
     }
    }
    int bestP=1;float bestW=w1;if(w2>bestW){bestW=w2;bestP=2;}if(w3>bestW){bestW=w3;bestP=3;}if(w4>bestW){bestW=w4;bestP=4;}if(w5>bestW){bestW=w5;bestP=5;}
    var tag=new Vector4(bestP,0,globalTri++,1);
    for(int z=0;z<3;z++){int vi=ix[3*t+z];ids.Add(vi);info.Add(tag);uv.Add(vi<mesh.uv.Length?mesh.uv[vi]:Vector2.zero);}
   }
   proxyGroups[sm]=Enumerable.Range(start,ix.Length).ToArray();
  }
  for(int role=0;role<16;role++)roleRanges[role]=new Vector4(role<7?6:(role>=11?7:1),0,0,0);
  sourceTags=new ComputeBuffer(Math.Max(1,info.Count/3),16);
  if(info.Count>=3)sourceTags.SetData(info.Where((v,i)=>i%3==0).ToArray());else sourceTags.SetData(new[]{new Vector4(1,0,1,1)});
  proxyIndices=ids.ToArray();proxyInfo=info.ToArray();proxyUV=uv.ToArray();proxyVertsBuf=new Vector3[proxyIndices.Length];proxyNormsBuf=new Vector3[proxyIndices.Length];proxyTopologyUploaded=false;
  bodyProxy=new Mesh{name="399 generic body metadata proxy",indexFormat=UnityEngine.Rendering.IndexFormat.UInt32,hideFlags=HideFlags.DontSave};bodyProxy.MarkDynamic();
 }
 void BuildProxy(){var mesh=motion.surface.outputs[0].sharedMesh;using var b=new BinaryReader(new MemoryStream(bodyParts.bytes));b.ReadInt32();int ns=b.ReadInt32();var ids=new List<int>();var info=new List<Vector4>();var uv=new List<Vector2>();proxyGroups=new int[ns][];
  for(int sm=0;sm<ns;sm++){b.ReadInt32();int nt=b.ReadInt32();var ix=new int[nt*3];for(int i=0;i<ix.Length;i++)ix[i]=b.ReadInt32();if(!ix.SequenceEqual(mesh.GetIndices(sm)))throw new Exception("333 source body topology differs from original319 tags");int start=ids.Count;for(int t=0;t<nt;t++){var tag=new Vector4(b.ReadInt32(),b.ReadInt32(),b.ReadInt32(),1);for(int z=0;z<3;z++){ids.Add(ix[3*t+z]);info.Add(tag);uv.Add(mesh.uv[ix[3*t+z]]);}}proxyGroups[sm]=Enumerable.Range(start,ix.Length).ToArray();}
  int tagOffset=0;for(int sm=0;sm<ns;sm++){roleRanges[new[]{7,8,9,10}[sm]]=new Vector4(0,tagOffset,0,0);tagOffset+=proxyGroups[sm].Length/3;}for(int role=0;role<16;role++)if(role<7||role>10)roleRanges[role]=new Vector4(role<7?6:7,0,0,0);sourceTags=new ComputeBuffer(info.Count/3,16);sourceTags.SetData(info.Where((v,i)=>i%3==0).ToArray());proxyIndices=ids.ToArray();proxyInfo=info.ToArray();proxyUV=uv.ToArray();proxyVertsBuf=new Vector3[proxyIndices.Length];proxyNormsBuf=new Vector3[proxyIndices.Length];proxyTopologyUploaded=false;bodyProxy=new Mesh{name="333 current source body metadata",indexFormat=UnityEngine.Rendering.IndexFormat.UInt32,hideFlags=HideFlags.DontSave};bodyProxy.MarkDynamic();
  var hair=motion.surface.outputs[2].sharedMesh;registeredHair=Instantiate(hair);registeredHair.hideFlags=HideFlags.DontSave;registeredHair.subMeshCount=1;registeredHair.SetTriangles(hair.GetIndices(0).Skip(574*3).Take(284*3).ToArray(),0);otherHair=Instantiate(hair);otherHair.hideFlags=HideFlags.DontSave;otherHair.SetTriangles(hair.GetIndices(0).Take(574*3).Concat(hair.GetIndices(0).Skip(858*3)).ToArray(),0);
 }
 internal void ClearActionMapIfNeeded(){if(!actionMapDirty||!actionMap)return;emptyActionMapColors??=new Color[480*272];actionMap.SetPixels(emptyActionMapColors);actionMap.Apply();actionMapDirty=false;}
 internal void ComputeEdgeHistoryParams(out Vector2Int pivotDelta,out bool resetHistory,out int readIdx,out int writeIdx){
  Vector2 renderedRoot=motion.actorLocalGrid&&motion.mode==2?(motion.Pivot()-motion.composeDelta):motion.Pivot();
  Vector2Int curPivot=new Vector2Int(Mathf.RoundToInt(renderedRoot.x),Mathf.RoundToInt(renderedRoot.y));
  Quaternion actorRot=motion.animation&&motion.animation.target?motion.animation.target.transform.rotation:Quaternion.identity;
  Quaternion camRot=motion.camera?motion.camera.transform.rotation:Quaternion.identity;
  float ortho=motion.camera?motion.camera.orthographicSize:1f;
  resetHistory=!hasPrevEdgePivot||motion.resetHistory||Quaternion.Angle(actorRot,prevEdgeActorRot)>1.5f||Quaternion.Angle(camRot,prevEdgeCamRot)>0.5f||Mathf.Abs(ortho-prevEdgeOrtho)>0.001f;
  pivotDelta=resetHistory?Vector2Int.zero:(curPivot-prevEdgePivot);
  if(Mathf.Abs(pivotDelta.x)>12||Mathf.Abs(pivotDelta.y)>12){resetHistory=true;pivotDelta=Vector2Int.zero;}
  hasPrevEdgePivot=true;prevEdgePivot=curPivot;prevEdgeActorRot=actorRot;prevEdgeCamRot=camRot;prevEdgeOrtho=ortho;
  readIdx=1-edgeHistoryWriteIdx;writeIdx=edgeHistoryWriteIdx;edgeHistoryWriteIdx=1-edgeHistoryWriteIdx;
 }
 internal void SetActionMap(Color[]map){if(!actionMap||map==null)return;actionMap.SetPixels(map);actionMap.Apply();actionMapDirty=true;}
 internal void UpdateProxyMeshes(){var mesh=motion.surface.outputs[0].sharedMesh;if(mesh&&bodyProxy&&proxyIndices!=null){var vp=mesh.vertices;var vn=mesh.normals;if(proxyVertsBuf==null||proxyVertsBuf.Length!=proxyIndices.Length){proxyVertsBuf=new Vector3[proxyIndices.Length];proxyNormsBuf=new Vector3[proxyIndices.Length];}for(int i=0;i<proxyIndices.Length;i++){int idx=proxyIndices[i];proxyVertsBuf[i]=vp[idx];proxyNormsBuf[i]=vn[idx];}bodyProxy.vertices=proxyVertsBuf;bodyProxy.normals=proxyNormsBuf;if(!proxyTopologyUploaded){bodyProxy.uv=proxyUV;bodyProxy.SetUVs(3,proxyInfo);bodyProxy.subMeshCount=proxyGroups.Length;for(int i=0;i<proxyGroups.Length;i++)bodyProxy.SetTriangles(proxyGroups[i],i,false);proxyTopologyUploaded=true;}bodyProxy.bounds=mesh.bounds;}if(!isGenericModel&&registeredHair&&otherHair){var hm=motion.surface.outputs[2].sharedMesh;if(hm){var hv=hm.vertices;var hn=hm.normals;var ht=hm.tangents;var hb=hm.bounds;registeredHair.vertices=hv;registeredHair.normals=hn;registeredHair.tangents=ht;registeredHair.bounds=hb;otherHair.vertices=hv;otherHair.normals=hn;otherHair.tangents=ht;otherHair.bounds=hb;}}}
 static void LegacyClass(Material target,Vector4 reference){target.SetFloat("_ShadingShiftFactor",reference.x);target.SetFloat("_ShadingToonyFactor",reference.y);target.SetFloat("_ShadingShiftTexScale",reference.z);}
 public void PrepareCurrent(){Initialise();Shader.SetGlobalTexture("_Auto245StockMember",isGenericModel?Texture2D.blackTexture:stockMember);Shader.SetGlobalTexture("_Auto245BodySkinMember",isGenericModel?Texture2D.blackTexture:skinMember);Shader.SetGlobalTexture("_Auto245CreamMember",isGenericModel?Texture2D.blackTexture:creamMember);int styleKey=styleEnabled?(stockMode+8*(faceMain?1:0)+16*(faceProvider?1:0)+(isGenericModel?32:0)):0;if(styleKey!=priorStyleKey){motion.resetHistory=true;priorStyleKey=styleKey;}var actorPosition=motion.animation.target.transform.position;var actorRotation=motion.animation.target.transform.rotation;motion.Evaluate();motion.animation.target.transform.SetPositionAndRotation(actorPosition,actorRotation);motion.surface.Evaluate();motion.PrepareCapture();capturePending|=motion.captureNow;if(priorIntegrated!=(integrated?1:0)){capturePending=true;priorIntegrated=integrated?1:0;}
  var cam=motion.camera;var gpu=GL.GetGPUProjectionMatrix(cam.projectionMatrix,true);float flip=gpu[1,1]/cam.projectionMatrix[1,1];nativeShift=motion.clipShift+new Vector4(.5f/480,.5f/272*flip,0,0);
  effectiveProjection=cam.projectionMatrix;effectiveProjection.SetRow(0,effectiveProjection.GetRow(0)+motion.clipShift.x*effectiveProjection.GetRow(3));effectiveProjection.SetRow(1,effectiveProjection.GetRow(1)+motion.clipShift.y/flip*effectiveProjection.GetRow(3));geometryCamera.worldToCameraMatrix=cam.worldToCameraMatrix;geometryCamera.projectionMatrix=effectiveProjection;geometryCamera.orthographicSize=cam.orthographicSize;
  phaseIndex=Mathf.RoundToInt(motion.evaluatedFrame/2.5f)%16;var p=phases[phaseIndex];var headBone=motion.animation.target.GetBoneTransform(HumanBodyBones.Head);providerMatrix=headBone?(headBone.localToWorldMatrix*p.head.inverse):Matrix4x4.identity;
  UpdateProxyMeshes();
  if(!isGenericModel){
   var mesh=motion.surface.outputs[0].sharedMesh;var vp=mesh.vertices;
   Vector3 E(Endpoint e)=>motion.surface.outputs[0].transform.TransformPoint(Vector3.LerpUnclamped(vp[e.a],vp[e.b],e.t));var a=Project(E(p.first));var z=Project(E(p.last));y0=Mathf.Clamp(Mathf.FloorToInt(Mathf.Min(a.y,z.y)),1,270);y1=Mathf.Clamp(Mathf.CeilToInt(Mathf.Max(a.y,z.y))-1,y0+1,270);
   BindEyes();
  }
 }
 public Vector2 Project(Vector3 world){var q=effectiveProjection*motion.camera.worldToCameraMatrix*new Vector4(world.x,world.y,world.z,1);return new Vector2((q.x/q.w*.5f+.5f)*480,(.5f-q.y/q.w*.5f)*272);}
 internal void BindEyes(){var p=phases[phaseIndex];if(eyeInverse==null||eyeInverse.Length!=2)eyeInverse=new Matrix4x4[2];if(eyePlanes==null||eyePlanes.Length!=2)eyePlanes=new Vector4[2];if(projectedPivots==null||projectedPivots.Length!=2)projectedPivots=new Vector2[2];if(projectedAnchors==null||projectedAnchors.Length!=2)projectedAnchors=new Vector2[2];var head=providerMatrix*p.head;var headInvT=head.inverse.transpose;
  for(int i=0;i<2;i++){var spec=calibration.eyes[i];var displacement=p.anchors[i]-p.head.MultiplyPoint3x4(eyes[i].expectedRestChildHead)-p.head.MultiplyVector(spec.referenceChildOffsetHead);for(int c=0;c<4;c++){eyeWorldBuf[c]=providerMatrix.MultiplyPoint3x4(p.head.MultiplyPoint3x4(spec.cornersHead[c])+displacement);eyePtsBuf[c]=Project(eyeWorldBuf[c]);}var b=spec.referenceBounds;eyeToPtsBuf[0]=new Vector2(b.x,b.y);eyeToPtsBuf[1]=new Vector2(b.z,b.y);eyeToPtsBuf[2]=new Vector2(b.x,b.w);eyeToPtsBuf[3]=new Vector2(b.z,b.w);eyeInverse[i]=Homography335.Solve(eyePtsBuf,eyeToPtsBuf);var n=headInvT.MultiplyVector(eyes[i].whiteNormalHead).normalized;eyePlanes[i]=new Vector4(n.x,n.y,n.z,-Vector3.Dot(n,eyeWorldBuf[0]));projectedPivots[i]=Project(head.MultiplyPoint3x4(eyes[i].whiteCentreHead));projectedAnchors[i]=Project(providerMatrix.MultiplyPoint3x4(p.anchors[i]));}
  var view=motion.camera.worldToCameraMatrix;var pv=effectiveProjection*view;var l=Matrix4x4.identity;l.SetRow(0,pv.GetRow(0)*240);l.SetRow(1,pv.GetRow(1)*-136);l.SetRow(2,-view.GetRow(2));l[0,3]=l[1,3]=l[2,3]=0;var inv=l.inverse;var off=new Vector3(240+240*pv[0,3],136-136*pv[1,3],-view[2,3]);rayBase=-inv.MultiplyVector(off);rayX=inv.MultiplyVector(Vector3.right);rayY=inv.MultiplyVector(Vector3.up);rayDepth=inv.MultiplyVector(Vector3.forward);
 }
 public static Color[]Read(RTHandle t){var data=new NativeArray<Color>(t.rt.width*t.rt.height,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);try{var r=AsyncGPUReadback.RequestIntoNativeArray(ref data,t.rt,0,TextureFormat.RGBAFloat);r.WaitForCompletion();if(r.hasError)throw new Exception("333 GPU readback");return data.ToArray();}finally{data.Dispose();}}
 public void RenderFrame(){if(rendering)return;Initialise();if(!ready)return;EnsureNative960();EnsureEyeLayers();rendering=true;try{PrepareCurrent();contourReady=false;motion.camera.Render();validateRender?.Invoke();var src=Read(meta[0]);var pal=Read(family);var raw=Read(native[0]);var phys=Read(native[3]);var uv=Read(native[6]);var world=Read(native[7]);var key=Read(native[5]);var own=Read(colourNative);var corr0=new Color[960*544];for(int i=0;i<corr0.Length;i++)corr0[i]=new Color(uv[i].r,uv[i].g,key[i].g,key[i].a);var sig=new Color[7][];sig[2]=phys;sig[3]=raw;sig[5]=raw;sig[6]=key;
   var selected=ContourSelect333.Build(new ContourSelect333.Input{phase=phaseIndex,y0=y0,y1=y1,underlayAvailable=true,camera=geometryCamera,renderers=motion.surface.outputs.Select(x=>x.GetComponent<Renderer>()).ToArray(),surface=src,palette=pal,centreSurface=Read(centreMeta[0]),centrePalette=Read(centreFamily),line=Read(audit),signals=sig,corr=new[]{corr0,world,own,own},worldCell=motion.camera.orthographicSize*2/272,backgroundUniform=false});receipt=selected.receipt;actionMap.SetPixels(selected.map);actionMap.Apply();contourReady=true;motion.camera.Render();validateRender?.Invoke();capturePending=false;renderedSerial335++;renderedSource335=motion.sourceFrame;renderedFrame335=motion.evaluatedFrame;
  }finally{rendering=false;}}
 void LateUpdate(){if(Application.isPlaying&&automatic)RenderFrame();}
#if UNITY_EDITOR
 void EditorTick(){if(this&&enabled&&!Application.isPlaying&&automatic&&motion&&motion.playing)RenderFrame();}
#endif
 void OnGUI(){if(!showReviewUI)return;if(!motion)return;GUILayout.BeginArea(new Rect(10,10,720,142),GUI.skin.box);GUILayout.Label(styleEnabled?"335 GameMap1 / original stock+face colour policy / same16 source poses":"333 same-scene control / same16 source poses");GUILayout.BeginHorizontal();if(GUILayout.Button(motion.playing?"Pause":"Play"))motion.playing=!motion.playing;if(GUILayout.Button("0.25x / 1x"))motion.speed=motion.speed<.5f?1:.25f;if(GUILayout.Button("<")){motion.playing=false;motion.sourceFrame=Mathf.Max(0,motion.sourceFrame-1);motion.resetHistory=true;RenderFrame();}if(GUILayout.Button(">")){motion.playing=false;motion.sourceFrame=Mathf.Min(40,motion.sourceFrame+1);motion.resetHistory=true;RenderFrame();}if(GUILayout.Button(styleEnabled?"Show333 control":"Show335 restored policy")){styleEnabled=!styleEnabled;motion.resetHistory=true;RenderFrame();}GUILayout.EndHorizontal();float f=GUILayout.HorizontalSlider(motion.sourceFrame,0,40);if(Mathf.Abs(f-motion.sourceFrame)>.01){motion.playing=false;motion.sourceFrame=f;motion.resetHistory=true;RenderFrame();}GUILayout.Label("source "+motion.sourceFrame.ToString("F2")+" -> pose "+motion.evaluatedFrame.ToString("F2")+" / 16 | current world visibility");GUILayout.EndArea();}
 void OnDisable(){
#if UNITY_EDITOR
 EditorApplication.update-=EditorTick;
#endif
  ClothRegion524.ReleaseScope551(this); // also runs after incomplete Initialise / cancelled capture
  if(Active==this)Active=null;if(!ready)return;DestroyMatArray(legacySignalsMats);if(legacyProviderMat)DestroyImmediate(legacyProviderMat);DestroyMatArray(dynamicMetadataMats);dynamicMetadataMats=null;if(originalMetadataAssets!=null)metadata=originalMetadataAssets;if(style480!=null)foreach(var t in style480)t?.Release();if(style960!=null)foreach(var t in style960)t?.Release();shadeMask480?.Release();shadeMask960?.Release();styleDepth480?.Release();styleDepth960?.Release();beforeStyle?.Release();sourceTags?.Dispose();DestroyMatArray(nativeMats);DestroyMatArray(worldMats);DestroyMatArray(independentMats);foreach(var m in new[]{bodyProxy,registeredHair,otherHair})if(m)DestroyImmediate(m);if(geometryCamera)DestroyImmediate(geometryCamera.gameObject);if(actionMap)DestroyImmediate(actionMap);var all=new List<RTHandle>();if(native!=null)all.AddRange(native);if(meta!=null)all.AddRange(meta);if(normal!=null)all.AddRange(normal);if(centreMeta!=null)all.AddRange(centreMeta);if(centreNormal!=null)all.AddRange(centreNormal);all.Add(centreFamily);if(flood!=null)all.AddRange(flood);if(layers!=null)foreach(var s in layers)all.AddRange(new[]{s.rgba,s.meta,s.uv,s.depth});all.AddRange(new[]{family,nativeDepth,colourNative,before,colour,owner,audit,gridSurface,gridPalette,paletteAudit,prepared,preparedOwner,postLine,preparedUV,preparedMeta,resolvedMeta,resolvedUV,eyeOutput,eyeOwner,intrinsic,eyeAudit,domain,edgeMetaSnap,edgeUVSnap});if(edgeHistory!=null)all.AddRange(edgeHistory);foreach(var t in all)t?.Release();native=meta=normal=style960=null;layers=null;family=nativeDepth=colourNative=shadeMask960=styleDepth960=null;edgeHistory=null;edgeMetaSnap=edgeUVSnap=null;hasPrevEdgePivot=false;ready=false;}
}
public static class Homography335{public static Matrix4x4 Solve(Vector2[]from,Vector2[]to){double[,]a=new double[8,9];for(int k=0;k<4;k++){double x=from[k].x,y=from[k].y,u=to[k].x,v=to[k].y;int i=k*2;a[i,0]=x;a[i,1]=y;a[i,2]=1;a[i,6]=-u*x;a[i,7]=-u*y;a[i,8]=u;a[i+1,3]=x;a[i+1,4]=y;a[i+1,5]=1;a[i+1,6]=-v*x;a[i+1,7]=-v*y;a[i+1,8]=v;}for(int col=0;col<8;col++){int pivot=col;for(int k=col+1;k<8;k++)if(Math.Abs(a[k,col])>Math.Abs(a[pivot,col]))pivot=k;if(Math.Abs(a[pivot,col])<1e-10)throw new Exception("Unsupported edge-on original eye basis");for(int k=col;k<9;k++)(a[col,k],a[pivot,k])=(a[pivot,k],a[col,k]);double value=a[col,col];for(int k=col;k<9;k++)a[col,k]/=value;for(int row=0;row<8;row++)if(row!=col){value=a[row,col];for(int k=col;k<9;k++)a[row,k]-=a[col,k]*value;}}var m=Matrix4x4.zero;m.SetRow(0,new Vector4((float)a[0,8],(float)a[1,8],(float)a[2,8],0));m.SetRow(1,new Vector4((float)a[3,8],(float)a[4,8],(float)a[5,8],0));m.SetRow(2,new Vector4((float)a[6,8],(float)a[7,8],1,0));return m;}}
