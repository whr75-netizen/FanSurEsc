using System;using System.IO;using UnityEngine;using UnityEngine.Rendering;
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
// Deliberate test fixture, not a model feature or final art. Attach before
// Gameplay397 renders the original gameCamera; a late head-pass relocation
// cannot validate the already captured Native395 world depth.
public sealed class WorldOccluder42:IDisposable {
 readonly Camera camera;readonly string cameraIdentity;readonly Transform head;readonly int layer;readonly float cell;GameObject go;UnityEngine.Mesh mesh;Material material;bool disposed;int updates;
 public WorldOccluder42(NativePlayer395 native){
  camera=native.gameCamera;head=native.host.main.motion.animation.target.GetBoneTransform(HumanBodyBones.Head);if(!head||camera.cullingMask==0)throw new InvalidOperationException("41 fixture requires actual world camera/layer/head");
  cameraIdentity=camera.GetEntityId().ToString();layer=0;while((camera.cullingMask&(1<<layer))==0)layer++;cell=2*native.host.main.motion.camera.orthographicSize/272;
  var shader=Shader.Find("Universal Render Pipeline/Unlit");if(!shader||!shader.isSupported)throw new InvalidOperationException("41 test world shader unavailable; no fallback");
  try{
   material=new Material(shader){hideFlags=HideFlags.DontSave};var j=Json40.Parse(File.ReadAllText(@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\resume-20261111\producer\support\surface27\FACE_INPUT27.json"));var c=j["finiteOutlineColourInput"]["linearRGB"].Values<float>();var rgb=System.Linq.Enumerable.ToArray(c);material.SetColor("_BaseColor",new Color(rgb[0],rgb[1],rgb[2],1));material.SetFloat("_Cull",0);material.SetFloat("_ZWrite",1);
   float x=6*cell,y=14*cell;mesh=new UnityEngine.Mesh{hideFlags=HideFlags.DontSave,name="41 owned world occluder mesh",vertices=new[]{new Vector3(-x,-y,0),new Vector3(x,-y,0),new Vector3(x,y,0),new Vector3(-x,y,0)},triangles=new[]{0,2,1,0,3,2},uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up}};mesh.RecalculateBounds();
   go=new GameObject("41 owned world-depth fixture"){hideFlags=HideFlags.DontSave,layer=layer};go.AddComponent<MeshFilter>().sharedMesh=mesh;var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterial=material;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;go.transform.SetPositionAndRotation(head.position+camera.transform.right*(4*cell)-camera.transform.forward*(32*cell),camera.transform.rotation);go.transform.SetParent(head,true);
  }catch{Dispose();throw;}
 }
 public void Update(){if(disposed||!go||!head||!camera)throw new InvalidOperationException("42 fixture lifetime invalidated");updates++;}

 public Obj40 Snapshot(){var p=go?go.transform.position:Vector3.zero;return new Obj40{["temporaryWorldFixture"]=true,["frame"]=Time.frameCount,["updates"]=updates,["layer"]=layer,["camera"]=cameraIdentity,["position"]=new Arr40(p.x,p.y,p.z),["sizeWorld"]=new Arr40(12*cell,28*cell),["disposed"]=disposed,["ownedGoAlive"]=(bool)go,["ownedMeshAlive"]=(bool)mesh,["ownedMaterialAlive"]=(bool)material,["poseHookChanged"]=false,["attachedToHeadBeforeWorldCapture"]=true,["testColourSource"]="original face outline RGB; not a newly authored character palette"};}
 public void Dispose(){if(disposed)return;disposed=true;if(go)UnityEngine.Object.DestroyImmediate(go);if(material)UnityEngine.Object.DestroyImmediate(material);if(mesh)UnityEngine.Object.DestroyImmediate(mesh);}
}
}
