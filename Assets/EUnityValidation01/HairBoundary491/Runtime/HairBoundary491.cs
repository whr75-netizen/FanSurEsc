using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;

// R3 prototype: replaces one verified thin UV ribbon at the existing head source draw.
// Disabled by default. No raster-mask, colour, eye or temporal post-processing.
public static class HairBoundary491 {
 public static bool Enabled;
 public static string Status="disabled";
 public static readonly List<Packet> Packets=new();
 public static int Hidden,Unsupported;public static float MaxWidth;
 [Serializable] public class Packet {public int x,y,primitive;public Vector3 barycentric,world;public Vector2 uv,projected;public float depth,centreDistance;}
 struct Point {public Vector2 p;public Vector3 b;public Point(Vector2 p,Vector3 b){this.p=p;this.b=b;}}
 struct Triangle {public Vector3 a,b,c;public Vector2 pa,pb,pc;public float za,zb,zc;}
 static Full319View335 current;static Mesh rest,pixels;static Material material;static ComputeBuffer sides;
 static int[] component,indices;static int[][] rows;static Vector3[] vertices,normals;static Vector4[] tangents;static Vector2[] uvs,projected;static Triangle[] occluders;
 static Mesh source;static readonly List<Vector3> pv=new(),pn=new();static readonly List<Vector4> pt=new(),clip=new();static readonly List<Vector2> pu=new();static readonly List<int> pi=new();
 public static void Release(){Enabled=false;current=null;source=null;component=null;rows=null;if(rest)UnityEngine.Object.DestroyImmediate(rest);if(pixels)UnityEngine.Object.DestroyImmediate(pixels);if(material)UnityEngine.Object.DestroyImmediate(material);sides?.Dispose();rest=pixels=null;material=null;sides=null;Packets.Clear();Status="disabled";}
 static string Key(Vector3 p,Vector2 uv)=>Math.Round(p.x,6)+"/"+Math.Round(p.y,6)+"/"+Math.Round(p.z,6)+"/"+Math.Round(uv.x,6)+"/"+Math.Round(uv.y,6);
 static ulong Edge(int a,int b)=>((ulong)(uint)Math.Min(a,b)<<32)|(uint)Math.Max(a,b);
 static void Topology(Mesh mesh){
  indices=mesh.GetIndices(1);var v=mesh.vertices;var uv=mesh.uv;var weld=new Dictionary<string,int>();var ids=new int[v.Length];var unique=new List<Vector3>();
  for(int i=0;i<v.Length;i++){var key=Key(v[i],uv[i]);if(!weld.TryGetValue(key,out int k)){k=unique.Count;weld[key]=k;unique.Add(v[i]);}ids[i]=k;}
  var edge=new Dictionary<ulong,List<int>>();for(int t=0;t<indices.Length/3;t++)for(int j=0;j<3;j++){ulong k=Edge(ids[indices[t*3+j]],ids[indices[t*3+(j+1)%3]]);if(!edge.ContainsKey(k))edge[k]=new List<int>();edge[k].Add(t);}
  var seen=new HashSet<int>{0};var todo=new Stack<int>();todo.Push(0);while(todo.Count>0){int t=todo.Pop();for(int j=0;j<3;j++)foreach(int n in edge[Edge(ids[indices[t*3+j]],ids[indices[t*3+(j+1)%3]])])if(seen.Add(n))todo.Push(n);}
  component=seen.OrderBy(i=>i).ToArray();var ci=component.SelectMany(t=>new[]{indices[t*3],indices[t*3+1],indices[t*3+2]}).Distinct().ToArray();
  var validation=new Mesh{hideFlags=HideFlags.DontSave};validation.vertices=unique.ToArray();validation.triangles=component.SelectMany(t=>new[]{ids[indices[t*3]],ids[indices[t*3+1]],ids[indices[t*3+2]]}).ToArray();
  var rings=EyeBoundaryBinding348.ClosedRings(validation,0);UnityEngine.Object.DestroyImmediate(validation);if(rings.Length!=1)throw new Exception("Selected component has no unique closed boundary");
  rows=ci.GroupBy(i=>Math.Round(uv[i].y,6)).OrderBy(g=>g.Key).Select(g=>g.OrderBy(i=>uv[i].x).ToArray()).ToArray();if(rows.Length<3||rows.Any(r=>r.Length!=2))throw new Exception("Selected component is not a paired UV ribbon");
  rest=new Mesh{name="491 original ribbon-excluded source; original primitive slots retained",hideFlags=HideFlags.DontSave};pixels=new Mesh{name="491 geometry-authored source cells",hideFlags=HideFlags.DontSave};
  var remaining=(int[])indices.Clone();foreach(int t in component){remaining[t*3+1]=remaining[t*3];remaining[t*3+2]=remaining[t*3];}rest.vertices=v;rest.uv=uv;rest.normals=mesh.normals;rest.tangents=mesh.tangents;rest.triangles=remaining;
  source=mesh;
 }
 static Vector3 Bary(Vector2 p,Vector2 a,Vector2 b,Vector2 c){float det=Cross(b-a,c-a);if(Mathf.Abs(det)<1e-10f)return new Vector3(-1,-1,-1);float v=Cross(p-a,c-a)/det,w=Cross(b-a,p-a)/det;return new Vector3(1-v-w,v,w);}
 static float Cross(Vector2 a,Vector2 b)=>a.x*b.y-a.y*b.x;
 static float Depth(Full319View335 f,Vector3 w)=>-f.motion.camera.worldToCameraMatrix.MultiplyPoint3x4(w).z;
 static List<Point> Clip(List<Point> input,int axis,float value,bool greater){var output=new List<Point>();if(input.Count==0)return output;var a=input[input.Count-1];float da=(axis==0?a.p.x:a.p.y)-value;if(!greater)da=-da;foreach(var b in input){float db=(axis==0?b.p.x:b.p.y)-value;if(!greater)db=-db;bool ai=da>=0,bi=db>=0;if(ai!=bi){float t=da/(da-db);output.Add(new Point(Vector2.LerpUnclamped(a.p,b.p,t),Vector3.LerpUnclamped(a.b,b.b,t)));}if(bi)output.Add(b);a=b;da=db;}return output;}
 static Point Closest(List<Point> poly,Vector2 centre){var best=poly[0];float error=float.PositiveInfinity;for(int j=0;j<poly.Count;j++){var a=poly[j];var b=poly[(j+1)%poly.Count];var d=b.p-a.p;float t=d.sqrMagnitude>0?Mathf.Clamp01(Vector2.Dot(centre-a.p,d)/d.sqrMagnitude):0;var p=new Point(a.p+t*d,Vector3.LerpUnclamped(a.b,b.b,t));float e=(p.p-centre).sqrMagnitude;if(e<error){error=e;best=p;}}return best;}
 static bool Select(Full319View335 f,int x,int y,out Packet packet){
  packet=null;var centre=new Vector2(x+.5f,y+.5f);float best=float.PositiveInfinity;
  foreach(int t in component){int ia=indices[t*3],ib=indices[t*3+1],ic=indices[t*3+2];var a=projected[ia];var b=projected[ib];var c=projected[ic];if(Mathf.Max(a.x,Mathf.Max(b.x,c.x))<x||Mathf.Min(a.x,Mathf.Min(b.x,c.x))>x+1||Mathf.Max(a.y,Mathf.Max(b.y,c.y))<y||Mathf.Min(a.y,Mathf.Min(b.y,c.y))>y+1)continue;
   var poly=new List<Point>{new Point(a,Vector3.right),new Point(b,Vector3.up),new Point(c,Vector3.forward)};poly=Clip(poly,0,x,true);poly=Clip(poly,0,x+1,false);poly=Clip(poly,1,y,true);poly=Clip(poly,1,y+1,false);if(poly.Count<3)continue;
   Vector3 bary=Bary(centre,a,b,c);Point q=bary.x>=0&&bary.y>=0&&bary.z>=0?new Point(centre,bary):Closest(poly,centre);
   // Keep the sample strictly inside its original triangle, not a borrowed neighbour.
   q.b=Vector3.Lerp(q.b,new Vector3(1f/3,1f/3,1f/3),.00001f);q.p=a*q.b.x+b*q.b.y+c*q.b.z;
   float error=(q.p-centre).sqrMagnitude;var local=vertices[ia]*q.b.x+vertices[ib]*q.b.y+vertices[ic]*q.b.z;var world=f.motion.surface.outputs[2].transform.TransformPoint(local);float z=Depth(f,world);
   if(error>best+1e-8f||(Mathf.Abs(error-best)<1e-8f&&packet!=null&&z>=packet.depth))continue;
   best=error;packet=new Packet{x=x,y=y,primitive=t,barycentric=q.b,world=world,uv=uvs[ia]*q.b.x+uvs[ib]*q.b.y+uvs[ic]*q.b.z,projected=q.p,depth=z,centreDistance=Mathf.Sqrt(error)};
  }
  return packet!=null&&packet.centreDistance<=Mathf.Sqrt(.5f)+.00001f;
 }
 static void Simplify(List<Vector2> p,int a,int b,HashSet<int> keep){if(b<=a+1)return;float far=0;int at=-1;var d=p[b]-p[a];for(int i=a+1;i<b;i++){float t=d.sqrMagnitude>0?Mathf.Clamp01(Vector2.Dot(p[i]-p[a],d)/d.sqrMagnitude):0;float e=(p[i]-(p[a]+t*d)).sqrMagnitude;if(e>far){far=e;at=i;}}if(far>.25f*.25f){keep.Add(at);Simplify(p,a,at,keep);Simplify(p,at,b,keep);}}
 // Keep the continuous segment's fractional phase. Flooring both anchors before
 // line stepping changes the slope/intercept and can pick cells outside the ribbon.
 static void Line(Vector2 a,Vector2 b,List<Vector2Int> cells){
  Vector2 d=b-a;int axis=Mathf.Abs(d.x)>=Mathf.Abs(d.y)?0:1;
  int start=Mathf.FloorToInt(a[axis]),end=Mathf.FloorToInt(b[axis]),step=start<=end?1:-1;
  for(int z=start;;z+=step){
   float t=Mathf.Abs(d[axis])>1e-10f?Mathf.Clamp01((z+.5f-a[axis])/d[axis]):0;
   Vector2 p=a+t*d;var cell=new Vector2Int(Mathf.FloorToInt(p.x),Mathf.FloorToInt(p.y));
   if(cells.Count==0||cells[cells.Count-1]!=cell)cells.Add(cell);
   if(z==end)break;
  }
 }

 static void BuildOccluders(Full319View335 f){var all=new List<Triangle>();for(int r=0;r<3;r++){var mf=f.motion.surface.outputs[r];var mesh=mf.sharedMesh;var v=mesh.vertices;var world=v.Select(p=>mf.transform.TransformPoint(p)).ToArray();var screen=world.Select(f.Project).ToArray();var z=world.Select(p=>Depth(f,p)).ToArray();for(int sm=0;sm<mesh.subMeshCount;sm++){var ix=mesh.GetIndices(sm);for(int t=0;t<ix.Length;t+=3){int a=ix[t],b=ix[t+1],c=ix[t+2];all.Add(new Triangle{a=world[a],b=world[b],c=world[c],pa=screen[a],pb=screen[b],pc=screen[c],za=z[a],zb=z[b],zc=z[c]});}}}occluders=all.ToArray();}
 static bool Visible(Packet p){foreach(var t in occluders){if(p.projected.x<Mathf.Min(t.pa.x,Mathf.Min(t.pb.x,t.pc.x))||p.projected.x>Mathf.Max(t.pa.x,Mathf.Max(t.pb.x,t.pc.x))||p.projected.y<Mathf.Min(t.pa.y,Mathf.Min(t.pb.y,t.pc.y))||p.projected.y>Mathf.Max(t.pa.y,Mathf.Max(t.pb.y,t.pc.y)))continue;var b=Bary(p.projected,t.pa,t.pb,t.pc);if(b.x>=-.00001f&&b.y>=-.00001f&&b.z>=-.00001f&&b.x*t.za+b.y*t.zb+b.z*t.zc<p.depth-.0001f)return false;}return true;}
 static void Quad(Full319View335 f,Packet p,float flip){int a=indices[p.primitive*3],b=indices[p.primitive*3+1],c=indices[p.primitive*3+2];var w=p.barycentric;var local=vertices[a]*w.x+vertices[b]*w.y+vertices[c]*w.z;var normal=(normals[a]*w.x+normals[b]*w.y+normals[c]*w.z).normalized;var tangent=tangents[a]*w.x+tangents[b]*w.y+tangents[c]*w.z;int start=pv.Count;foreach(var corner in new[]{new Vector2(p.x,p.y),new Vector2(p.x+1,p.y),new Vector2(p.x+1,p.y+1),new Vector2(p.x,p.y+1)}){pv.Add(local);pn.Add(normal);pt.Add(tangent);pu.Add(p.uv);clip.Add(new Vector4(corner.x/240-1,(1-corner.y/136)*flip,p.primitive,0));}bool forward=Cross(projected[b]-projected[a],projected[c]-projected[a])>0;foreach(int i in forward?new[]{0,1,2,0,2,3}:new[]{0,2,1,0,3,2})pi.Add(start+i);}
 public static void Prepare(Full319View335 f){
  if(!Enabled||!HeadLocal367.IsHead(f))return;current=null;Packets.Clear();Hidden=Unsupported=0;MaxWidth=0;
  try{var mf=f.motion.surface.outputs[2];var mesh=mf.sharedMesh;if(source!=mesh)Topology(mesh);vertices=mesh.vertices;uvs=mesh.uv;normals=mesh.normals;tangents=mesh.tangents;projected=vertices.Select(v=>f.Project(mf.transform.TransformPoint(v))).ToArray();rest.vertices=vertices;rest.normals=normals;rest.tangents=tangents;rest.bounds=mesh.bounds;
   var centre=new List<Vector2>();foreach(var row in rows){var a=projected[row[0]];var b=projected[row[1]];MaxWidth=Mathf.Max(MaxWidth,Vector2.Distance(a,b));centre.Add((a+b)*.5f);}if(MaxWidth>1)throw new Exception("Projected ribbon width exceeds1cell");
   var keep=new HashSet<int>{0,centre.Count-1};Simplify(centre,0,centre.Count-1,keep);var line=keep.OrderBy(i=>i).Select(i=>centre[i]).ToArray();var cells=new List<Vector2Int>();for(int i=1;i<line.Length;i++)Line(line[i-1],line[i],cells);BuildOccluders(f);pv.Clear();pn.Clear();pt.Clear();pu.Clear();clip.Clear();pi.Clear();var written=new HashSet<Vector2Int>();float flip=GL.GetGPUProjectionMatrix(f.effectiveProjection,true)[1,1]/f.effectiveProjection[1,1];
   foreach(var cell in cells){if(!written.Add(cell)||cell.x<0||cell.y<0||cell.x>=480||cell.y>=272)continue;if(!Select(f,cell.x,cell.y,out var p)){Unsupported++;continue;}if(!Visible(p)){Hidden++;continue;}Packets.Add(p);Quad(f,p,flip);}
   pixels.Clear();pixels.SetVertices(pv);pixels.SetNormals(pn);pixels.SetTangents(pt);pixels.SetUVs(0,pu);pixels.SetUVs(3,clip);pixels.SetTriangles(pi,0);pixels.bounds=mesh.bounds;
   if(!material){var shader=Shader.Find("EValidation/HairBoundary491Probe");if(!shader)throw new Exception("491 shader missing");material=new Material(f.motion.materials[12]){shader=shader,hideFlags=HideFlags.DontSave};material.shaderKeywords=f.motion.materials[12].shaderKeywords;sides=new ComputeBuffer(indices.Length/3,4);sides.SetData(new float[indices.Length/3]);material.SetBuffer("_Instance331",sides);}
   current=f;Status="ready";
  }catch(Exception e){Status="unsupported: "+e.Message;}
 }
 public static bool TryGet(Full319View335 f,int renderer,int submesh,out Mesh remaining,out Mesh cells,out Material shader){remaining=rest;cells=pixels;shader=material;return Enabled&&f==current&&renderer==2&&submesh==1;}
}
