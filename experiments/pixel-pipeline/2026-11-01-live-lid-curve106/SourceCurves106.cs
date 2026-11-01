using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

// One renderer/view owns its current evaluated source curve buffer. Static
// registration/topology is cached; every Record uses current native vertices,
// source->head transform and the SAME public homography as NativeRetarget96.
// No pixel-budget target, GPU readback, global writes or source-mesh mutation.
public sealed class SourceCurves106:IDisposable{
 public struct Segment{public Vector4 a,b;public Segment(Vector4 x,Vector4 y){a=x;b=y;}}
 readonly EyeFeature348 eye;readonly Full319View335 view;readonly Camera camera;readonly UnityEngine.Mesh mesh;
 readonly string topology;readonly int[] eyeIds;readonly int[][] arcs;readonly Vector4[] projectionX,projectionY;
 readonly List<Vector3> vertices;public Segment[] Segments{get;private set;}
 public GraphicsBuffer Buffer{get;private set;}public bool Disposed{get;private set;}public int UpdatedFrame{get;private set;}=-1;
 public string Scope{get;private set;}public int Count=>Segments==null?0:Segments.Length;
 public int EyeId(int index)=>eyeIds[index];
 public long OwnedBytes=>Buffer==null?0:(long)Buffer.count*Buffer.stride;
 public Obj58 Info=>new Obj58{["scope"]=Scope,["segments"]=Count,["ownedBytes"]=OwnedBytes,["updatedFrame"]=UpdatedFrame,["readbacksInRuntime"]=0,["source"]="registered native skin-ring upper chain; actual current deformed mesh; not authored lash-pigment boundary",["poseGate"]=false,["pixelBudget"]=false};
 static float F(Json58 v)=>(float)(double)v;
 static Matrix4x4 Forward(Matrix4x4 inverse){inverse.m33=1;if(Mathf.Abs(inverse.determinant)<1e-12f)throw new InvalidOperationException("106 homography singular");return inverse.inverse;}
 static int[] Upper(Json58 row){var q=row["authoredParent"];int n=q.Count,left=0,right=0;
  for(int i=1;i<n;i++){if(F(q[i][0])<F(q[left][0]))left=i;if(F(q[i][0])>F(q[right][0]))right=i;}
  if(n<3||left==right)throw new InvalidOperationException("106 registered ring has no span");
  int[] Chain(int direction){var a=new List<int>();int i=left;for(int k=0;k<=n;k++){a.Add(i);if(i==right)return a.ToArray();i=(i+direction+n)%n;}throw new InvalidOperationException("106 ring open");}
  double Mean(int[] a){double weighted=0,length=0;for(int i=1;i<a.Length;i++){double dx=(double)q[a[i]][0]-(double)q[a[i-1]][0],dy=(double)q[a[i]][1]-(double)q[a[i-1]][1];double w=Math.Sqrt(dx*dx+dy*dy);weighted+=w*((double)q[a[i]][1]+(double)q[a[i-1]][1])*.5;length+=w;}return weighted/length;}
  var a=Chain(1);var b=Chain(-1);return(Mean(a)<=Mean(b)?a:b).Select(i=>(int)row["nativeRingVertexIds"][i]).ToArray();
 }
 public SourceCurves106(EyeFeature348 e,Json58 registration){eye=e;view=e.full;camera=view.motion.camera;mesh=e.sampleFace;topology=e.modelTopologySHA256;
  if(!eye||!view||!camera||!mesh)throw new InvalidOperationException("106 live source missing");
  var rows=registration["eyes"].OrderBy(r=>(int)r["eye"]).ToArray();if(rows.Length!=2)throw new NotSupportedException("106 current two-eye source contract required");eyeIds=rows.Select(r=>(int)r["eye"]).ToArray();arcs=rows.Select(Upper).ToArray();projectionX=new Vector4[rows.Length];projectionY=new Vector4[rows.Length];
  for(int i=0;i<rows.Length;i++){if(arcs[i].Any(v=>v<0||v>=mesh.vertexCount)||!e.centres.Any(c=>Mathf.RoundToInt(c.w)==eyeIds[i]))throw new InvalidOperationException("106 source registration/eye mismatch");for(int c=0;c<4;c++){projectionX[i][c]=F(rows[i]["nativeToAuthoredProjection"][c][0]);projectionY[i][c]=F(rows[i]["nativeToAuthoredProjection"][c][1]);}}
  int count=arcs.Sum(a=>a.Length-1);if(count<1||count>256)throw new InvalidOperationException("106 source segment bound exceeded, no reduction");
  vertices=new List<Vector3>(mesh.vertexCount);Segments=new Segment[count];Scope=e.GetEntityId()+"/"+camera.GetEntityId()+"/"+mesh.GetEntityId()+"/"+topology;
  try{Buffer=new GraphicsBuffer(GraphicsBuffer.Target.Structured,count,32);}catch{Dispose();throw;}
 }
 public void Update(Vector2 anchor,Vector4 bounds){if(Disposed)throw new ObjectDisposedException(nameof(SourceCurves106));
  if(!eye||eye.full!=view||view.motion.camera!=camera||eye.sampleFace!=mesh||eye.modelTopologySHA256!=topology||view.motion.surface.outputs[1].sharedMesh.vertexCount!=mesh.vertexCount)throw new InvalidOperationException("106 model/view/source lifetime changed; recreate explicit owner");
  mesh.GetVertices(vertices);var model=view.motion.surface.outputs[1].transform.localToWorldMatrix;var head=eye.headMatrix.inverse;var physicalView=camera.worldToCameraMatrix;int at=0;
  for(int eyeIndex=0;eyeIndex<eyeIds.Length;eyeIndex++){
   int owner=eyeIds[eyeIndex],slot=Array.FindIndex(eye.centres,c=>Mathf.RoundToInt(c.w)==owner);if(slot<0)throw new InvalidOperationException("106 source eye removed");var forward=Forward(view.eyeInverse[slot]);
   Vector4 Point(int id){var world=model.MultiplyPoint3x4(vertices[id]);var r=head.MultiplyPoint3x4(world);var q=new Vector4(r.x,r.y,r.z,1);var p=forward*new Vector4(Vector4.Dot(q,projectionX[eyeIndex]),Vector4.Dot(q,projectionY[eyeIndex]),1,0);
    if(Mathf.Abs(p.z)<1e-12f)throw new InvalidOperationException("106 curve projection singular");float x=p.x/p.z-anchor.x-bounds.x,y=p.y/p.z-anchor.y-bounds.y,z=-physicalView.MultiplyPoint3x4(world).z;
    if(float.IsNaN(x)||float.IsNaN(y)||float.IsInfinity(x)||float.IsInfinity(y)||z<=0)throw new InvalidOperationException("106 projected curve outside valid view");return new Vector4(x,y,z,owner);}
   var arc=arcs[eyeIndex];var a=Point(arc[0]);for(int i=1;i<arc.Length;i++){var b=Point(arc[i]);Segments[at++]=new Segment(a,b);a=b;}
  }
  UpdatedFrame=Time.frameCount;
 }
 public void Upload(CommandBuffer cmd){if(Disposed||UpdatedFrame!=Time.frameCount)throw new InvalidOperationException("106 same-frame source curve missing");cmd.SetBufferData(Buffer,Segments);}
 public void Dispose(){if(Disposed)return;Disposed=true;Buffer?.Dispose();Buffer=null;Segments=null;vertices?.Clear();}
}
