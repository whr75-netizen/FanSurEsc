// Owns only cloned materials and offscreen targets; no borrowed state mutation.
public sealed class SourceOutline29 : ScriptableRenderPass,IDisposable {
 readonly EyeFeature348 eye;readonly Material[][]depthMats;readonly Material ink,pigmentMat;readonly ComputeShader classifier;
 readonly int renderer,submesh,pigmentRenderer,pigmentSubmesh;readonly float width;readonly Vector4 sourceInk;readonly string sourceSHA,pigmentSHA;
 Exception failure;int classifierKernel;readonly Material[][]sourceMats;readonly string topology;
 RTHandle depth;public RTHandle[]Fields{get;private set;}public RTHandle Classification{get;private set;}public RectInt ROI{get;private set;}
 public int RenderedFrame{get;private set;}=-1;public bool Disposed{get;private set;}
 public Obj58 Info{get;private set;}int tw,th;
 sealed class Data{public SourceOutline29 owner;public bool hair;}
 public SourceOutline29(EyeFeature348 e,string bindingPath,string registryPath){
  eye=e;topology=e.modelTopologySHA256;sourceMats=e.full.motion.surface.source.Select(r=>r.sharedMaterials).ToArray();var input=Json58.Parse(File.ReadAllText(bindingPath));var b=input["nativeBinding"];
  renderer=(int)b["rendererOrdinal"];submesh=(int)b["subMesh"];
  sourceSHA=(string)b["imageSHA256"];
  // Native role6 is the existing verified pigment material domain of this
  // pipeline, not skin assigned by nearest-eye or canonical bank location.
  var registry=Json58.Parse(File.ReadAllText(registryPath));if((string)registry["modelSHA256"]!=(string)input["modelSHA256"])throw new InvalidOperationException("29 source model identity changed");
  var pigment=registry["bindings"].Where(row=>(int)row["rendererOrdinal"]==renderer&&(int)row["gltfPrimitive"]==6).ToArray();if(pigment.Length!=1)throw new InvalidOperationException("29 unique registered native pigment binding required");
  pigmentRenderer=(int)pigment[0]["rendererOrdinal"];pigmentSubmesh=(int)pigment[0]["subMesh"];pigmentSHA=(string)pigment[0]["imageSHA256"];
  var outline=input["finiteOutlineColourInput"];if((string)outline["widthMode"]!="worldCoordinates"||(double)outline["lightingMix"]!=0)throw new InvalidOperationException("29 requires verified world outline with unmixed source colour");
  width=(float)(double)outline["widthMetres"];var rgb=outline["linearRGB"].Values<float>().ToArray();sourceInk=new Vector4(rgb[0],rgb[1],rgb[2],1);
  var shader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary29/SourceOutline29.shader");if(!shader||!shader.isSupported)throw new InvalidOperationException("29 outline shader unavailable");
  depthMats=new Material[e.full.motion.surface.source.Length][];
  try{
   var compute=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/SourceBoundary29/LineClass29.compute");if(!compute)throw new InvalidOperationException("29 classifier unavailable");classifier=UnityEngine.Object.Instantiate(compute);classifier.name="29 owned source classifier";classifierKernel=classifier.FindKernel("Classify29");
   for(int r=0;r<depthMats.Length;r++)depthMats[r]=sourceMats[r].Select(m=>new Material(m){shader=shader,hideFlags=HideFlags.DontSave,name="29 owned source depth"}).ToArray();
   ink=new Material(depthMats[renderer][submesh]){hideFlags=HideFlags.DontSave,name="29 owned native outline"};ink.SetFloat("_OutlineWidth",width);ink.SetVector("_SourceOutline29",sourceInk);
   pigmentMat=new Material(depthMats[pigmentRenderer][pigmentSubmesh]){hideFlags=HideFlags.DontSave,name="29 owned physical native pigment"};if(pigmentMat.FindPass("SourcePigment29")!=2)throw new InvalidOperationException("29 proposed physical shader not applied; stop before graph registration");
  }catch{Dispose();throw;}
 }
 void Targets(){
  var f=eye.full;var mf=f.motion.surface.outputs[renderer];var mesh=mf.sharedMesh;
  var vertices=mesh.vertices;var normals=mesh.normals;var indices=mesh.GetIndices(submesh);var m=mf.transform.localToWorldMatrix;var n=m.inverse.transpose;
  if(normals.Length!=vertices.Length||indices.Length==0)throw new InvalidOperationException("29 native source vertex/normal/index input missing");
  float x0=1e20f,y0=1e20f,x1=-1e20f,y1=-1e20f;
  indices=indices.Concat(mesh.GetIndices(pigmentSubmesh)).Distinct().ToArray();
  foreach(int ix in indices){if(ix<0||ix>=vertices.Length)throw new InvalidOperationException("29 source index range");var p=m.MultiplyPoint3x4(vertices[ix]);var normal=n.MultiplyVector(normals[ix]).normalized;
   foreach(var world in new[]{p,p+normal*width}){var q=f.Project(world);if(!float.IsFinite(q.x)||!float.IsFinite(q.y))throw new InvalidOperationException("29 nonfinite source projection");x0=Math.Min(x0,q.x);x1=Math.Max(x1,q.x);y0=Math.Min(y0,q.y);y1=Math.Max(y1,q.y);}}
  int left=Math.Max(0,(int)Math.Floor(x0)-1),top=Math.Max(0,(int)Math.Floor(y0)-1),right=Math.Min(480,(int)Math.Ceiling(x1)+1),bottom=Math.Min(272,(int)Math.Ceiling(y1)+1);
  ROI=new RectInt(left,top,right-left,bottom-top);int w=ROI.width*8,h=ROI.height*8;
  if(w<=0||h<=0||(long)w*h>262144)throw new InvalidOperationException("29 projected native face ROI exceeds262144 subsamples; no truncation");
  if(Fields!=null&&w==tw&&h==th)return;Release();tw=w;th=h;
  try{Fields=Enumerable.Range(0,8).Select(_=>RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:"29 owned source-outline channel")).ToArray();depth=RTHandles.Alloc(w,h,depthBufferBits:DepthBits.Depth32,name:"29 owned source depth");Classification=RTHandles.Alloc(ROI.width,ROI.height,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"29 owned source classes");}catch{Release();throw;}
 }
 public void Record(RenderGraph graph,UniversalResourceData unused){
  if(Disposed||failure!=null)return;try{RecordChecked(graph,unused);}catch(Exception e){failure=e;}
 }
 void RecordChecked(RenderGraph graph,UniversalResourceData unused){
  var f=eye.full;if(eye.modelTopologySHA256!=topology)throw new InvalidOperationException("29 source topology cache invalidated");for(int r=0;r<depthMats.Length;r++){var mf=f.motion.surface.outputs[r];if(!mf||!mf.sharedMesh||mf.sharedMesh.subMeshCount!=depthMats[r].Length||!f.motion.surface.source[r].sharedMaterials.SequenceEqual(sourceMats[r]))throw new InvalidOperationException("29 native source graph/material cache changed before recording");}
  if(renderer!=pigmentRenderer)throw new InvalidOperationException("29 separate pigment transform requires explicit union implementation");
  Targets();var vp=GL.GetGPUProjectionMatrix(OutputSupport26.Crop(ROI,f.effectiveProjection),true)*f.motion.camera.worldToCameraMatrix;
  foreach(var mat in depthMats.SelectMany(row=>row).Concat(new[]{ink,pigmentMat})){mat.SetMatrix("_ProbeGPUVP29",vp);mat.SetMatrix("_ProbeView29",f.motion.camera.worldToCameraMatrix);}
  foreach(bool hair in new[]{true,false}){using(var b=graph.AddUnsafePass<Data>("29 native outline source and real geometry occlusion",out var d)){d.owner=this;d.hair=hair;int start=hair?0:4;for(int i=start;i<start+4;i++)b.UseTexture(graph.ImportTexture(Fields[i]),AccessFlags.Write);b.UseTexture(graph.ImportTexture(depth),AccessFlags.Write);b.AllowPassCulling(false);b.SetRenderFunc(static(Data data,UnsafeGraphContext context)=>{if(data.owner.failure!=null)return;try{data.owner.Draw(context,data.hair);}catch(Exception e){data.owner.failure=e;}});}}
  using(var b=graph.AddUnsafePass<Data>("29 typed source silhouette/pigment/Q inputs",out var data)){data.owner=this;foreach(var t in new[]{Fields[0],Fields[2],f.style480[3],f.native[5]})b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);b.UseTexture(graph.ImportTexture(Classification),AccessFlags.Write);b.AllowPassCulling(false);b.SetRenderFunc(static(Data d,UnsafeGraphContext context)=>{if(d.owner.failure!=null)return;try{d.owner.Classify(context);}catch(Exception e){d.owner.failure=e;}});}
  Info=new Obj58{["frame"]=Time.frameCount,["sourceGeometry"]= "current evaluated surface.outputs; source material binding; no authored bank plane",["renderer"]=renderer,["submesh"]=submesh,["pigmentRenderer"]=pigmentRenderer,["pigmentSubmesh"]=pigmentSubmesh,["pigmentImageSHA"]=pigmentSHA,["worldWidth"]=width,["linearInk"]=new Arr58(sourceInk.x,sourceInk.y,sourceInk.z),["sourceImageSHA"]=sourceSHA,["ROI_topLeft"]=new Arr58(ROI.x,ROI.y,ROI.width,ROI.height),["pigmentROI_topLeft"]=new Arr58(ROI.x,ROI.y,ROI.width,ROI.height),["sampleScale"]=8,["maxSubsamples"]=262144,["colourPolicy"]="original source outline slot direct; no light multiplication or RGB classification",["hairOffMeaning"]="only owned depth draw omits renderer2; original renderer remains unchanged",["visibilityLimit"]="Original material discard/depth-write policy; fractional transmittance through non-depth-writing blend materials is not reconstructed",["originalMaterialAlphaModes"]=new Arr58(sourceMats.SelectMany(row=>row).Select(m=>m.HasProperty("_AlphaMode")?m.GetFloat("_AlphaMode"):-1))};
 }
 void Classify(UnsafeGraphContext context){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);int k=classifierKernel;var f=eye.full;
  cmd.SetComputeTextureParam(classifier,k,"_Outline29",Fields[0].rt);cmd.SetComputeTextureParam(classifier,k,"_Pigment29",Fields[2].rt);cmd.SetComputeTextureParam(classifier,k,"_Q29",f.style480[3].rt);cmd.SetComputeTextureParam(classifier,k,"_NativeMeta29",f.native[5].rt);cmd.SetComputeTextureParam(classifier,k,"_Class29",Classification.rt);
  cmd.SetComputeIntParams(classifier,"_Rect29",ROI.x,ROI.y,ROI.width,ROI.height);cmd.SetComputeIntParams(classifier,"_PigmentRect29",ROI.x,ROI.y,ROI.width,ROI.height);cmd.DispatchCompute(classifier,k,(ROI.width+7)/8,(ROI.height+7)/8,1);
  Info["classifierDispatches"]=1;Info["classifierThreads"]=(ROI.width+7)/8*((ROI.height+7)/8)*64;Info["classificationContract"]="R native world-outline alpha; G physical native pigment alpha after original material discard/depth; B independent Q transition; A face/pigment-domain/Q-valid/provenance flags. Classes may overlap. This is source evidence, not final label/outline placement or full translucent visibility.";
 }
 void Draw(UnsafeGraphContext context,bool hair){
  var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);int start=hair?0:4;cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[start].rt),new RenderTargetIdentifier(Fields[start+1].rt)},depth.rt);cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);cmd.SetViewport(new Rect(0,0,tw,th));
  var output=eye.full.motion.surface.outputs;int draws=0;
  for(int r=0;r<output.Length;r++){if(!hair&&r==2)continue;var mf=output[r];if(!mf||!mf.sharedMesh||mf.sharedMesh.subMeshCount!=depthMats[r].Length)throw new InvalidOperationException("29 source graph changed during frame");for(int sm=0;sm<depthMats[r].Length;sm++){cmd.DrawMesh(mf.sharedMesh,mf.transform.localToWorldMatrix,depthMats[r][sm],sm,0);draws++;}}
  var pigment=output[pigmentRenderer];cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[start+2].rt),new RenderTargetIdentifier(Fields[start+3].rt)},depth.rt);cmd.ClearRenderTarget(RTClearFlags.Color,Color.clear,1,0);cmd.DrawMesh(pigment.sharedMesh,pigment.transform.localToWorldMatrix,pigmentMat,pigmentSubmesh,2);
  var face=output[renderer];cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[start].rt),new RenderTargetIdentifier(Fields[start+1].rt)},depth.rt);cmd.DrawMesh(face.sharedMesh,face.transform.localToWorldMatrix,ink,submesh,1);RenderedFrame=Time.frameCount;Info[hair?"depthDrawsHairOn":"depthDrawsHairOff"]=draws;
 }
 public void CheckFailure(){if(failure!=null)throw new InvalidOperationException("29 deferred source failure outside RenderGraph",failure);}
 public void AssertRendered(){CheckFailure();if(Disposed||RenderedFrame!=Time.frameCount)throw new InvalidOperationException("29 no matching native-outline frame");}
 void Release(){if(Fields!=null)foreach(var t in Fields)t?.Release();depth?.Release();Classification?.Release();Classification=null;Fields=null;depth=null;}
 public void Dispose(){if(Disposed)return;Disposed=true;Release();if(depthMats!=null)foreach(var row in depthMats)if(row!=null)foreach(var m in row)if(m)UnityEngine.Object.DestroyImmediate(m);if(ink)UnityEngine.Object.DestroyImmediate(ink);if(pigmentMat)UnityEngine.Object.DestroyImmediate(pigmentMat);if(classifier)UnityEngine.Object.DestroyImmediate(classifier);}
}
