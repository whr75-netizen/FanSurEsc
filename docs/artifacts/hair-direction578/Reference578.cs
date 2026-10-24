using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using FantasySurvival.WorldLighting;

// Diagnostic only: reuse the actual-Walk lifecycle; retain a small hand ROI.
public static class Reference578
{
 static string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairDirections578/Reference170/";static bool geometryOnly,oldNegative,oldBranch,oldOrder; static int[] Targets=new[]{8,9,10,16,20,21,22,23,24,25,40,41,42,43,44,45,46,47,48,49,51,62,71,72,73,77};static bool oldCentre,oldScope,oldAutoHair,oldRayHair,oldVisibleHair;
 static Gameplay397 g;static HeadLocal367 h;static Full319View335 f;static Animator a;static PlayerMovement move;static SkyLightingCycleController sky;
 static Action prior;static int count,state,bits;static bool queued,oldMove,oldAnim,oldAuto,oldBg,oldPaused,oldIndex,oldOpacity,oldArea,oldWhole,oldSpans,oldCompact,oldReference;
 static float oldLoc,oldSpeed,oldCapture,oldPhase,oldHour;static Quaternion oldRotation;static double deadline;
 static readonly RectInt Roi=new RectInt(195,25,55,45);
 static Color[] Read(RenderTexture rt){var old=RenderTexture.active;Texture2D t=null;try{RenderTexture.active=rt;t=new Texture2D(rt.width,rt.height,TextureFormat.RGBAFloat,false,true);t.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0,false);t.Apply(false,false);return t.GetPixels();}finally{RenderTexture.active=old;if(t)UnityEngine.Object.DestroyImmediate(t);}}
 static void Write(string path,Color[] data,int width,int height,RectInt r){using(var b=new BinaryWriter(File.Create(path+".bin"))){b.Write(r.width);b.Write(r.height);b.Write(r.x);b.Write(r.y);for(int y=r.y;y<r.yMax;y++)for(int x=r.x;x<r.xMax;x++){var c=data[(height-1-y)*width+x];b.Write(c.r);b.Write(c.g);b.Write(c.b);b.Write(c.a);}}}
 static void Crop(string path,RenderTexture rt,RectInt r)=>Write(path,Read(rt),rt.width,rt.height,r);
 static ulong bindingHash;
 static void HashInt(int n){unchecked{for(int i=0;i<4;i++){bindingHash^=(byte)(n>>(8*i));bindingHash*=1099511628211UL;}}}
 static void HashFloat(float n)=>HashInt(BitConverter.SingleToInt32Bits(n));
 static void Geometry(int frame,float phase)
 {
  var fhead=h.head;var mf=fhead.motion.surface.outputs[2];var mesh=mf.sharedMesh;var vertices=mesh.vertices;var uv=mesh.uv;
  using(var b=new BinaryWriter(File.Create(Root+"REFERENCE576.mesh"))){b.Write(1);b.Write(frame);b.Write(phase);for(int i=0;i<16;i++)b.Write(fhead.effectiveProjection[i]);b.Write(480);b.Write(272);b.Write(mesh.vertexCount);b.Write(mesh.subMeshCount);for(int i=0;i<vertices.Length;i++){var world=mf.transform.TransformPoint(vertices[i]);var screen=fhead.Project(world);b.Write(world.x);b.Write(world.y);b.Write(world.z);b.Write(uv[i].x);b.Write(uv[i].y);b.Write(screen.x);b.Write(screen.y);b.Write(-fhead.motion.camera.worldToCameraMatrix.MultiplyPoint3x4(world).z);}for(int sm=0;sm<mesh.subMeshCount;sm++){var ids=mesh.GetIndices(sm);b.Write(ids.Length);foreach(int v in ids)b.Write(v);}}
  var original=fhead.motion.surface.source[2].sharedMesh;bindingHash=14695981039346656037UL;HashInt(original.vertexCount);HashInt(original.subMeshCount);foreach(var p in original.vertices){HashFloat(p.x);HashFloat(p.y);HashFloat(p.z);}foreach(var p in original.uv){HashFloat(p.x);HashFloat(p.y);}for(int sm=0;sm<original.subMeshCount;sm++){var ids=original.GetIndices(sm);HashInt(ids.Length);foreach(int i in ids)HashInt(i);}foreach(var matrix in original.bindposes)for(int i=0;i<16;i++)HashFloat(matrix[i]);
  File.WriteAllText(Root+"BINDING576.json","{\"semanticPart\":\"Hair\",\"adapterPart\":2,\"containerPart\":0,\"vertices\":"+original.vertexCount+",\"submeshes\":"+original.subMeshCount+",\"bindSignature\":\""+bindingHash.ToString("X16")+"\",\"semanticIntentMetadata\":false}");
 }
 static Camera fheadCamera()=>h.head.motion.camera;
 static void Capture()
 {
  try{
   int frame=Targets[count];var info=a.GetCurrentAnimatorClipInfo(0);if(info.Length==0||info[0].clip.name!="Rig|Walk_Loop")throw new Exception("Actual Walk required");
   ClothRegion524.Enabled=true;ClothRegion524.PartBits540=14;ClothRegion524.UseSpans543=ClothRegion524.UseCompact544=ClothRegion524.UseOpacityCurves527=ClothRegion524.UseWholeRegions539=true;ClothRegion524.UseSimplifiedSpanReference546=false;ClothRegion524.UseAreaCurves532=false;ClosedRegion524.UseSpatialIndex526=true;
   HeadRegion502.Enabled=false;HeadLocal367.UseCentreBodyRay550=true;ClothRegion524.UseBodyScope551=false;h.RenderFrame();string p=Root+frame.ToString("D3")+"_NATIVE";
   Crop(p+"_FINAL",f.colour.rt,Roi);Crop(p+"_META",f.resolvedMeta.rt,Roi);Crop(p+"_EYE_VISIBLE",h.headEyes.visible.rt,new RectInt(205,35,30,28));
   float phase=Mathf.Repeat(a.GetCurrentAnimatorStateInfo(0).normalizedTime,1);if(count==0)Geometry(frame,phase);
   File.WriteAllText(p+"_PARAMS.json","{\"frame\":"+frame+",\"phase\":"+phase.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+",\"yaw\":"+a.transform.eulerAngles.y.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+",\"offsetX\":"+h.offset.x+",\"offsetY\":"+h.offset.y+",\"sky\":"+sky.CurrentHour.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+"}");
   var png=new Texture2D(960,544,TextureFormat.RGBA32,false);try{var shot=Read(g.player.output.rt);var pixels=new Color[shot.Length];for(int i=0;i<shot.Length;i++){var z=shot[i];pixels[i]=new Color(Mathf.LinearToGammaSpace(z.r),Mathf.LinearToGammaSpace(z.g),Mathf.LinearToGammaSpace(z.b),1);}png.SetPixels(pixels);png.Apply();File.WriteAllBytes(p+".png",png.EncodeToPNG());}finally{UnityEngine.Object.DestroyImmediate(png);}
   var cam=fheadCamera();var forward=a.transform.forward;var toward=(cam.transform.position-a.transform.position).normalized;
   File.WriteAllText(Root+"VIEW578.json","{\"yaw\":"+a.transform.eulerAngles.y+",\"modelForward\":["+forward.x+","+forward.y+","+forward.z+"],\"cameraPosition\":["+cam.transform.position.x+","+cam.transform.position.y+","+cam.transform.position.z+"],\"cameraForward\":["+cam.transform.forward.x+","+cam.transform.forward.y+","+cam.transform.forward.z+"],\"forwardTowardCameraDot\":"+Vector3.Dot(forward,toward)+"}");
   count++;File.WriteAllText(Root+"progress.json","{\"poses\":"+count+",\"last\":"+frame+"}");ClothRegion524.Enabled=false;HeadLocal367.UseCentreBodyRay550=false;
   if(count==Targets.Length){End("CAPTURED");return;}queued=false;f.validateRender=OnFinal;EditorApplication.isPaused=false;
  }catch(Exception e){End("FAILED",e.ToString());}
 }
 static void OnFinal(){prior?.Invoke();if(!f.contourReady||queued)return;queued=true;f.validateRender=prior;EditorApplication.isPaused=true;EditorApplication.delayCall+=Capture;}
 static void Tick(){if(!EditorApplication.isPlaying||EditorApplication.timeSinceStartup>deadline){End("FAILED","Play ended or 900s deadline");return;}EditorApplication.QueuePlayerLoopUpdate();}
 static void End(string status,string error="")
 {
  EditorApplication.update-=Tick;EditorApplication.delayCall-=Capture;if(f)f.validateRender=prior;
  HeadRegion502.Enabled=false;HeadRegion502.UseNegativeRegions563=oldNegative;HeadRegion502.UseNegativeBranches566=oldBranch;HeadRegion502.UseRegionFamilies574=oldOrder;HeadRegion502.UseAutomaticCurve511=oldAutoHair;HeadRegion502.UseBodyRay512=oldRayHair;HeadRegion502.UseVisibleArea505=oldVisibleHair;HeadLocal367.UseCentreBodyRay550=oldCentre;ClothRegion524.UseBodyScope551=oldScope;ClothRegion524.Enabled=false;ClothRegion524.UseSpans543=oldSpans;ClothRegion524.UseCompact544=oldCompact;ClothRegion524.UseSimplifiedSpanReference546=oldReference;ClothRegion524.UseOpacityCurves527=oldOpacity;ClothRegion524.UseAreaCurves532=oldArea;ClothRegion524.UseWholeRegions539=oldWhole;ClothRegion524.PartBits540=bits;ClosedRegion524.UseSpatialIndex526=oldIndex;Shader.SetGlobalInt("_Cloth524Enabled",0);
  if(sky){sky.SetTimeHours(oldHour);sky.SetAutomaticAdvance(oldAuto);}if(a){a.transform.rotation=oldRotation;a.SetFloat("LocomotionSpeed",oldLoc);a.speed=oldSpeed;a.Play(state,0,oldPhase);a.Update(0);a.enabled=oldAnim;}if(move)move.enabled=oldMove;Time.captureDeltaTime=oldCapture;Application.runInBackground=oldBg;EditorApplication.isPaused=oldPaused;
  File.WriteAllText(Root+"status.json","{\"status\":\""+status+"\",\"poses\":"+count+",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\r"," ").Replace("\n"," ")+"\",\"inputRestored\":"+(move&&move.enabled==oldMove?"true":"false")+",\"animatorRestored\":"+(a&&a.enabled==oldAnim&&a.speed==oldSpeed?"true":"false")+",\"clockRestored\":"+(sky&&sky.IsAdvancingAutomatically==oldAuto&&Mathf.Abs(sky.CurrentHour-oldHour)<.00001f?"true":"false")+"}");if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;
 }
 public static void Start(float yaw)
 {
  Targets=new[]{70};
  geometryOnly=false;oldNegative=HeadRegion502.UseNegativeRegions563;oldBranch=HeadRegion502.UseNegativeBranches566;oldOrder=HeadRegion502.UseRegionFamilies574;oldCentre=HeadLocal367.UseCentreBodyRay550;oldScope=ClothRegion524.UseBodyScope551;oldAutoHair=HeadRegion502.UseAutomaticCurve511;oldRayHair=HeadRegion502.UseBodyRay512;oldVisibleHair=HeadRegion502.UseVisibleArea505;
  if(!EditorApplication.isPlaying||EditorApplication.isPaused||ClothRegion524.Enabled||Directory.Exists(Root))throw new Exception("Ready Play/OFF and new output required");g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected)throw new Exception("Runtime not ready");h=g.player.host;f=h.main;a=f.motion.animation.target;move=g.player.player.GetComponent<PlayerMovement>();sky=UnityEngine.Object.FindFirstObjectByType<SkyLightingCycleController>();
  if(HeadRegion502.Enabled||h.post.candidateEnabled)throw new Exception("Other trial active");prior=f.validateRender;if(prior!=null&&prior.GetInvocationList().Any(x=>!(x.Target is PostView366)))throw new Exception("Other capture hook active");
  oldMove=move.enabled;oldAnim=a.enabled;oldAuto=sky.IsAdvancingAutomatically;oldHour=sky.CurrentHour;oldBg=Application.runInBackground;string startup="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/HairDirections578/StartupReference/WARMUP_INITIAL540.json";if(File.Exists(startup))oldBg=File.ReadAllText(startup).Contains("\"oldBackground\":true");oldPaused=EditorApplication.isPaused;oldLoc=a.GetFloat("LocomotionSpeed");oldSpeed=a.speed;oldCapture=Time.captureDeltaTime;oldRotation=a.transform.rotation;var s=a.GetCurrentAnimatorStateInfo(0);state=s.fullPathHash;oldPhase=s.normalizedTime;oldSpans=ClothRegion524.UseSpans543;oldCompact=ClothRegion524.UseCompact544;oldReference=ClothRegion524.UseSimplifiedSpanReference546;oldOpacity=ClothRegion524.UseOpacityCurves527;oldArea=ClothRegion524.UseAreaCurves532;oldWhole=ClothRegion524.UseWholeRegions539;oldIndex=ClosedRegion524.UseSpatialIndex526;bits=ClothRegion524.PartBits540;
  Directory.CreateDirectory(Root);File.WriteAllText(Root+"CROP.json","{\"sourceWidth\":960,\"sourceHeight\":544,\"x\":0,\"y\":0,\"width\":960,\"height\":544,\"sampling\":\"original full viewport, no crop or rescale\"}");sky.SetAutomaticAdvance(false);sky.SetTimeHours(3.1476202011f);move.enabled=false;a.enabled=true;a.speed=1;a.SetFloat("LocomotionSpeed",1);a.transform.rotation=Quaternion.Euler(0,yaw,0);a.Play(state,0,1f+(Targets[0]-1)/80f+.00000248f);a.Update(0);Time.captureDeltaTime=1f/60;Application.runInBackground=true;count=0;queued=false;deadline=EditorApplication.timeSinceStartup+900;f.validateRender=OnFinal;EditorApplication.update+=Tick;File.WriteAllText(Root+"status.json","{\"status\":\"STARTED\"}");
 }
}
