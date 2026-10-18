using System;using System.Linq;using UnityEngine;using UnityEngine.Rendering;
[ExecuteAlways]public sealed class CurrentSurface330:MonoBehaviour{
 public Camera targetCamera;public SkinnedMeshRenderer[]source;public MeshFilter[]outputs;Mesh[]meshes;bool[]priorEnabled;
 void OnEnable(){RenderPipelineManager.beginCameraRendering+=BeforeCamera;Initialise();}
 public void Initialise(){if(source==null||outputs==null||source.Length!=outputs.Length)return;meshes=new Mesh[source.Length];priorEnabled=source.Select(s=>s.enabled).ToArray();for(int i=0;i<source.Length;i++){meshes[i]=new Mesh{name="330 current evaluated surface "+i,hideFlags=HideFlags.DontSave};meshes[i].MarkDynamic();source[i].forceMatrixRecalculationPerRender=true;source[i].updateWhenOffscreen=true;source[i].enabled=false;}Evaluate();}
 void BeforeCamera(ScriptableRenderContext context,Camera camera){if(camera==targetCamera)Evaluate();}
 public void Evaluate(){if(meshes==null)return;for(int i=0;i<source.Length;i++){var m=meshes[i];source[i].BakeMesh(m);var matrix=outputs[i].transform.worldToLocalMatrix*source[i].localToWorldMatrix;var normal=matrix.inverse.transpose;m.vertices=m.vertices.Select(p=>matrix.MultiplyPoint3x4(p)).ToArray();m.normals=m.normals.Select(n=>normal.MultiplyVector(n).normalized).ToArray();m.tangents=m.tangents.Select(t=>{var p=matrix.MultiplyVector(t);return new Vector4(p.x,p.y,p.z,t.w);}).ToArray();m.RecalculateBounds();outputs[i].sharedMesh=m;}}
 public void ClearTransientReferences(){if(outputs!=null)foreach(var f in outputs)if(f)f.sharedMesh=null;}
 void OnDisable(){RenderPipelineManager.beginCameraRendering-=BeforeCamera;if(source!=null&&priorEnabled!=null)for(int i=0;i<source.Length;i++)if(source[i])source[i].enabled=priorEnabled[i];if(meshes!=null)foreach(var m in meshes)if(m){if(Application.isPlaying)Destroy(m);else DestroyImmediate(m);}meshes=null;}
}
