using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Experimental.Rendering;

// Area input only. Original per-cell feature support, rank, pigments and
// compositing stay in EyeFeature348. No pose results or readback are cached.
public sealed class EyeArea587 : IDisposable {
 public const int Density=128;
 public sealed class View {
  public RectInt box;
  public Matrix4x4 projection;
  public RTHandle[] signal,depth;
 }
 public readonly View[] views={new View(),new View()};
 public long textureBytes;
 public int referenceVertexCount;
 public ComputeBuffer partials;
 public Material[] materials;
 public Material skinMaterial;
 int partialCapacity;
 int[][] vertices;
 readonly Vector4[] signature=new Vector4[7];
 bool bound;

 bool Changed(EyeFeature348 e) {
  if(!bound)return true;
  for(int i=0;i<2;i++)if(signature[i]!=e.centres[i]||signature[2+i]!=e.axesX[i]||signature[4+i]!=e.axesY[i])return true;
  return signature[6]!=new Vector4(e.style.upper.x,e.style.upper.y,0,0);
 }
 void Bind(EyeFeature348 e) {
  var rest=new List<Vector3>();e.sampleFace.GetUVs(1,rest);
  var owners=new List<Vector2>();e.sampleFace.GetUVs(7,owners);
  var indices=new List<int>();foreach(int sm in new[]{3,4,1,6})indices.AddRange(e.sampleFace.GetIndices(sm));
  vertices=new int[2][];referenceVertexCount=0;
  for(int eye=0;eye<2;eye++) {
   var selected=new HashSet<int>();var c=(Vector3)e.centres[eye];var ax=e.axesX[eye];var ay=e.axesY[eye];float id=e.centres[eye].w;
   for(int k=0;k<indices.Count;k+=3) {
    float u0=float.PositiveInfinity,u1=float.NegativeInfinity,v0=u0,v1=u1,o0=u0,o1=u1;
    for(int j=0;j<3;j++) {
     int i=indices[k+j];var d=rest[i]-c;float u=Vector3.Dot(d,(Vector3)ax)/ax.w,v=-Vector3.Dot(d,(Vector3)ay)/ay.w;
     u0=Mathf.Min(u0,u);u1=Mathf.Max(u1,u);v0=Mathf.Min(v0,v);v1=Mathf.Max(v1,v);o0=Mathf.Min(o0,owners[i].x);o1=Mathf.Max(o1,owners[i].x);
    }
    float sq0=u0<=0&&u1>=0?0:Mathf.Min(u0*u0,u1*u1),sq1=Mathf.Max(u0*u0,u1*u1);
    float b0=e.style.upper.y*sq0,b1=e.style.upper.y*sq1;
    float g0=v0-e.style.upper.x-Mathf.Max(b0,b1),g1=v1-e.style.upper.x-Mathf.Min(b0,b1);
    if(u1 < -1.08f||u0 > 1.08f||g1 < -.36f||g0 > .22f||o1 < id-.5f||o0 > id+.5f)continue;
    for(int j=0;j<3;j++)selected.Add(indices[k+j]);
   }
   vertices[eye]=new int[selected.Count];selected.CopyTo(vertices[eye]);referenceVertexCount+=selected.Count;
   signature[eye]=e.centres[eye];signature[2+eye]=e.axesX[eye];signature[4+eye]=e.axesY[eye];
  }
  signature[6]=new Vector4(e.style.upper.x,e.style.upper.y,0,0);bound=true;
 }
 public void Prepare(EyeFeature348 e,Vector3[] current) {
  if(Changed(e))Bind(e);
  if(materials==null){materials=new Material[e.materials.Length];for(int i=0;i<materials.Length;i++)materials[i]=new Material(e.materials[i]){hideFlags=HideFlags.DontSave};skinMaterial=new Material(e.skinMaterial){hideFlags=HideFlags.DontSave};}
  for(int i=0;i<materials.Length;i++){materials[i].CopyPropertiesFromMaterial(e.materials[i]);materials[i].EnableKeyword("EYE_AREA_587");}skinMaterial.CopyPropertiesFromMaterial(e.skinMaterial);skinMaterial.EnableKeyword("EYE_AREA_587");
  var mvp=e.full.effectiveProjection*e.full.motion.camera.worldToCameraMatrix*e.full.motion.surface.outputs[1].transform.localToWorldMatrix;
  textureBytes=0;int requiredPartials=1;
  for(int eye=0;eye<2;eye++) {
   var lo=new Vector2(float.PositiveInfinity,float.PositiveInfinity);var hi=new Vector2(float.NegativeInfinity,float.NegativeInfinity);
   foreach(int i in vertices[eye]) {
    var p=current[i];var q=mvp*new Vector4(p.x,p.y,p.z,1);
    if(q.w<=0)throw new InvalidOperationException("587 area reference crosses projection plane");
    var xy=new Vector2((q.x/q.w*.5f+.5f)*480,(.5f-q.y/q.w*.5f)*272);lo=Vector2.Min(lo,xy);hi=Vector2.Max(hi,xy);
   }
   int x0=e.roi.x,y0=e.roi.y,x1=x0+1,y1=y0+1;
   if(vertices[eye].Length>0) {
    x0=Mathf.Clamp(Mathf.FloorToInt(lo.x)-1,e.roi.x,e.roi.xMax-1);y0=Mathf.Clamp(Mathf.FloorToInt(lo.y)-1,e.roi.y,e.roi.yMax-1);
    x1=Mathf.Clamp(Mathf.CeilToInt(hi.x)+1,x0+1,e.roi.xMax);y1=Mathf.Clamp(Mathf.CeilToInt(hi.y)+1,y0+1,e.roi.yMax);
   }
   var box=new RectInt(x0,y0,x1-x0,y1-y0);var v=views[eye];int w=box.width*Density,h=box.height*Density;
   if(w>SystemInfo.maxTextureSize||h>SystemInfo.maxTextureSize)throw new InvalidOperationException("587 area target exceeds GPU texture limit");
   if(v.signal==null||v.box.size!=box.size) {
    Release(v);v.signal=new RTHandle[7];v.depth=new RTHandle[7];
    for(int s=0;s<7;s++) {
     v.signal[s]=RTHandles.Alloc(w,h,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point);
     v.depth[s]=RTHandles.Alloc(w,h,depthBufferBits:DepthBits.Depth32);
    }
   }
   v.box=box;var crop=Matrix4x4.identity;crop[0,0]=480f/box.width;crop[0,3]=(480f-2*box.x-box.width)/box.width;crop[1,1]=272f/box.height;crop[1,3]=(2*box.y+box.height-272f)/box.height;v.projection=crop*e.full.effectiveProjection;
   textureBytes+=(long)w*h*20*7;
   requiredPartials=Mathf.Max(requiredPartials,(w*h+255)/256);
  }
  if(requiredPartials>partialCapacity){partials?.Dispose();partials=new ComputeBuffer(requiredPartials,16);partialCapacity=requiredPartials;}
 }
 static void Release(View v) {
  if(v.signal!=null)foreach(var t in v.signal)t?.Release();if(v.depth!=null)foreach(var t in v.depth)t?.Release();v.signal=null;v.depth=null;
 }
 public void Dispose(){foreach(var v in views)Release(v);partials?.Dispose();partials=null;partialCapacity=0;if(materials!=null)foreach(var m in materials)if(m)UnityEngine.Object.DestroyImmediate(m);if(skinMaterial)UnityEngine.Object.DestroyImmediate(skinMaterial);materials=null;skinMaterial=null;}
}
