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
 struct Triangle {public int renderer,submesh,primitive;public Vector3 a,b,c;public Vector2 pa,pb,pc;public float za,zb,zc;}
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
 static void Simplify(IList<Vector2> p,int a,int b,HashSet<int> keep){if(b<=a+1)return;float far=0;int at=-1;var d=p[b]-p[a];for(int i=a+1;i<b;i++){float t=d.sqrMagnitude>0?Mathf.Clamp01(Vector2.Dot(p[i]-p[a],d)/d.sqrMagnitude):0;float e=(p[i]-(p[a]+t*d)).sqrMagnitude;if(e>far){far=e;at=i;}}if(far>.25f*.25f){keep.Add(at);Simplify(p,a,at,keep);Simplify(p,at,b,keep);}}
 struct CurveSample {public Vector2 p;public double at;public CurveSample(Vector2 p,double at){this.p=p;this.at=at;}}
 // RDP supplies directional spans, never the selected positions. Positions and
 // connector candidates both come from the same UV-ordered dense source curve.
 static void CurveSamples(Vector2[] curve,int first,int last,List<CurveSample> samples){
  Vector2 a=curve[first],b=curve[last],d=b-a;int axis=Mathf.Abs(d.x)>=Mathf.Abs(d.y)?0:1;
  int step=a[axis]<=b[axis]?1:-1;int low=Mathf.CeilToInt(Mathf.Min(a[axis],b[axis])-.5f),high=Mathf.FloorToInt(Mathf.Max(a[axis],b[axis])-.5f);
  for(int i=first;i<last;i++)if((curve[i+1][axis]-curve[i][axis])*step<0)throw new Exception("Original curve reverses within a directional span");
  if(low>high)return;int start=step>0?low:high,end=step>0?high:low;
  for(int z=start;;z+=step){
   float target=z+.5f;bool found=false;
   for(int i=first;i<last;i++){var u=curve[i];var v=curve[i+1];if(target<Mathf.Min(u[axis],v[axis])||target>Mathf.Max(u[axis],v[axis]))continue;float delta=v[axis]-u[axis];float t=Mathf.Abs(delta)>1e-10f?(target-u[axis])/delta:0;samples.Add(new CurveSample(Vector2.LerpUnclamped(u,v,t),i+(double)t));found=true;break;}
   if(!found)throw new Exception("No original curve crossing for selected slice");
   if(z==end)break;
  }
 }
 static bool Neighbours(Vector2Int a,Vector2Int b)=>Mathf.Max(Mathf.Abs(a.x-b.x),Mathf.Abs(a.y-b.y))<=1;
 static void AddCell(List<Vector2Int> cells,Vector2Int cell){if(cells.Count==0||cells[cells.Count-1]!=cell)cells.Add(cell);}
 // Traverse the actual segment across grid boundaries. A corner crossing moves
 // both axes at once; no cell is borrowed from a raster neighbourhood.
 static void TraceGrid(Vector2 a,Vector2 b,List<Vector2Int> cells){
  var cell=Vector2Int.FloorToInt(a);var end=Vector2Int.FloorToInt(b);AddCell(cells,cell);
  double dx=(double)b.x-a.x,dy=(double)b.y-a.y;int sx=Math.Sign(dx),sy=Math.Sign(dy);
  double tx=sx==0?double.PositiveInfinity:((sx>0?cell.x+1:cell.x)-(double)a.x)/dx;
  double ty=sy==0?double.PositiveInfinity:((sy>0?cell.y+1:cell.y)-(double)a.y)/dy;
  double ux=sx==0?double.PositiveInfinity:1/Math.Abs(dx),uy=sy==0?double.PositiveInfinity:1/Math.Abs(dy);
  long limit=Math.Abs((long)end.x-cell.x)+Math.Abs((long)end.y-cell.y)+1,steps=0;
  while(cell!=end){if(++steps>limit)throw new Exception("Original segment traversal did not reach its end");double nextX=cell.x==end.x?double.PositiveInfinity:tx,nextY=cell.y==end.y?double.PositiveInfinity:ty;if(nextX<nextY){cell.x+=sx;tx+=ux;}else if(nextY<nextX){cell.y+=sy;ty+=uy;}else{cell.x+=sx;cell.y+=sy;tx+=ux;ty+=uy;}AddCell(cells,cell);}
 }
 static double Distance2(Vector2Int cell,List<Vector2> curve){double px=cell.x+.5,py=cell.y+.5,best=double.PositiveInfinity;for(int i=1;i<curve.Count;i++){double ax=curve[i-1].x,ay=curve[i-1].y,dx=(double)curve[i].x-ax,dy=(double)curve[i].y-ay,den=dx*dx+dy*dy,t=den>0?Math.Max(0,Math.Min(1,((px-ax)*dx+(py-ay)*dy)/den)):0;double x=px-ax-t*dx,y=py-ay-t*dy;best=Math.Min(best,x*x+y*y);}return best;}
 static void JoinCurve(Vector2[] curve,CurveSample a,CurveSample b,List<Vector2Int> output){
  if(b.at<a.at)throw new Exception("Source curve samples are not in UV order");
  var interval=new List<Vector2>{a.p};for(int i=(int)Math.Floor(a.at)+1;i<(int)Math.Ceiling(b.at);i++)interval.Add(curve[i]);interval.Add(b.p);
  var corridor=new List<Vector2Int>();for(int i=1;i<interval.Count;i++)TraceGrid(interval[i-1],interval[i],corridor);
  if(corridor.Count==0||corridor[0]!=output[output.Count-1])throw new Exception("Source corridor start mismatch");
  int n=corridor.Count;var count=new int[n];var parent=new int[n];var error=new double[n];for(int j=0;j<n;j++){count[j]=int.MaxValue;parent[j]=-1;error[j]=double.PositiveInfinity;}count[0]=0;error[0]=0;
  // Ordered shortest8path: preserve a thin line; among equally short paths,
  // prefer cell centres closest to the original interval. Exact ties keep UV order.
  for(int j=1;j<n;j++){double penalty=Distance2(corridor[j],interval);for(int i=0;i<j;i++){if(count[i]==int.MaxValue||!Neighbours(corridor[i],corridor[j]))continue;int steps=count[i]+1;double cost=error[i]+penalty;if(steps<count[j]||(steps==count[j]&&cost<error[j])){count[j]=steps;error[j]=cost;parent[j]=i;}}}
  if(parent[n-1]<0)throw new Exception("No connected path through original curve corridor");
  var path=new List<Vector2Int>();for(int i=n-1;i>=0;i=parent[i])path.Add(corridor[i]);path.Reverse();for(int i=1;i<path.Count;i++)AddCell(output,path[i]);
 }
 // Pure selection entry point also exercises saved deformed-curve fixtures.
 public static Vector2Int[] SelectCurveCells(Vector2[] curve){
  if(curve==null||curve.Length<2)throw new ArgumentException("Curve requires two endpoints");foreach(var p in curve)if(float.IsNaN(p.x)||float.IsNaN(p.y)||float.IsInfinity(p.x)||float.IsInfinity(p.y))throw new ArgumentException("Curve coordinates must be finite");
  var keep=new HashSet<int>{0,curve.Length-1};Simplify(curve,0,curve.Length-1,keep);var spans=keep.OrderBy(i=>i).ToArray();var samples=new List<CurveSample>{new CurveSample(curve[0],0)};for(int i=1;i<spans.Length;i++)CurveSamples(curve,spans[i-1],spans[i],samples);samples.Add(new CurveSample(curve[curve.Length-1],curve.Length-1));
  var cells=new List<Vector2Int>{Vector2Int.FloorToInt(samples[0].p)};var previous=samples[0];for(int i=1;i<samples.Count;i++){var next=samples[i];var cell=Vector2Int.FloorToInt(next.p);if(cell!=cells[cells.Count-1]){if(Neighbours(cells[cells.Count-1],cell))cells.Add(cell);else JoinCurve(curve,previous,next,cells);}previous=next;}
  for(int i=1;i<cells.Count;i++)if(!Neighbours(cells[i-1],cells[i]))throw new Exception("Selected original curve path is not8connected");return cells.ToArray();
 }

 static void BuildOccluders(Full319View335 f){var all=new List<Triangle>();for(int r=0;r<3;r++){var mf=f.motion.surface.outputs[r];var mesh=mf.sharedMesh;var v=mesh.vertices;var world=v.Select(p=>mf.transform.TransformPoint(p)).ToArray();var screen=world.Select(f.Project).ToArray();var z=world.Select(p=>Depth(f,p)).ToArray();for(int sm=0;sm<mesh.subMeshCount;sm++){var ix=mesh.GetIndices(sm);for(int t=0;t<ix.Length;t+=3){int a=ix[t],b=ix[t+1],c=ix[t+2];all.Add(new Triangle{renderer=r,submesh=sm,primitive=t/3,a=world[a],b=world[b],c=world[c],pa=screen[a],pb=screen[b],pc=screen[c],za=z[a],zb=z[b],zc=z[c]});}}}occluders=all.ToArray();}
 static bool Visible(Packet p){foreach(var t in occluders){
  // A packet lies on this exact original triangle by construction. Reprojecting
  // its near-edge-on triangle and solving float barycentrics can invent a nearer
  // intersection on itself. No other triangle, strand or owner is exempted.
  if(t.renderer==2&&t.submesh==1&&t.primitive==p.primitive)continue;
  if(p.projected.x<Mathf.Min(t.pa.x,Mathf.Min(t.pb.x,t.pc.x))||p.projected.x>Mathf.Max(t.pa.x,Mathf.Max(t.pb.x,t.pc.x))||p.projected.y<Mathf.Min(t.pa.y,Mathf.Min(t.pb.y,t.pc.y))||p.projected.y>Mathf.Max(t.pa.y,Mathf.Max(t.pb.y,t.pc.y)))continue;
  double ax=t.pa.x,ay=t.pa.y,bx=t.pb.x-ax,by=t.pb.y-ay,cx=t.pc.x-ax,cy=t.pc.y-ay,px=p.projected.x-ax,py=p.projected.y-ay;
  double det=bx*cy-by*cx;if(Math.Abs(det)<1e-20)continue;
  double v=(px*cy-py*cx)/det,w=(bx*py-by*px)/det,u=1-v-w;
  if(u>=-.00001&&v>=-.00001&&w>=-.00001&&u*t.za+v*t.zb+w*t.zc<p.depth-.0001f)return false;
 }return true;}
 static void Quad(Full319View335 f,Packet p,float flip){int a=indices[p.primitive*3],b=indices[p.primitive*3+1],c=indices[p.primitive*3+2];var w=p.barycentric;var local=vertices[a]*w.x+vertices[b]*w.y+vertices[c]*w.z;var normal=(normals[a]*w.x+normals[b]*w.y+normals[c]*w.z).normalized;var tangent=tangents[a]*w.x+tangents[b]*w.y+tangents[c]*w.z;int start=pv.Count;foreach(var corner in new[]{new Vector2(p.x,p.y),new Vector2(p.x+1,p.y),new Vector2(p.x+1,p.y+1),new Vector2(p.x,p.y+1)}){pv.Add(local);pn.Add(normal);pt.Add(tangent);pu.Add(p.uv);clip.Add(new Vector4(corner.x/240-1,(1-corner.y/136)*flip,p.primitive,0));}bool forward=Cross(projected[b]-projected[a],projected[c]-projected[a])>0;foreach(int i in forward?new[]{0,1,2,0,2,3}:new[]{0,2,1,0,3,2})pi.Add(start+i);}
 public static void Prepare(Full319View335 f){
  if(!Enabled||!HeadLocal367.IsHead(f))return;current=null;Packets.Clear();Hidden=Unsupported=0;MaxWidth=0;
  try{var mf=f.motion.surface.outputs[2];var mesh=mf.sharedMesh;if(source!=mesh)Topology(mesh);vertices=mesh.vertices;uvs=mesh.uv;normals=mesh.normals;tangents=mesh.tangents;projected=vertices.Select(v=>f.Project(mf.transform.TransformPoint(v))).ToArray();rest.vertices=vertices;rest.normals=normals;rest.tangents=tangents;rest.bounds=mesh.bounds;
   var centre=new List<Vector2>();foreach(var row in rows){var a=projected[row[0]];var b=projected[row[1]];MaxWidth=Mathf.Max(MaxWidth,Vector2.Distance(a,b));centre.Add((a+b)*.5f);}if(MaxWidth>1)throw new Exception("Projected ribbon width exceeds1cell");
   var cells=SelectCurveCells(centre.ToArray());BuildOccluders(f);pv.Clear();pn.Clear();pt.Clear();pu.Clear();clip.Clear();pi.Clear();var written=new HashSet<Vector2Int>();float flip=GL.GetGPUProjectionMatrix(f.effectiveProjection,true)[1,1]/f.effectiveProjection[1,1];
   foreach(var cell in cells){if(!written.Add(cell)||cell.x<0||cell.y<0||cell.x>=480||cell.y>=272)continue;if(!Select(f,cell.x,cell.y,out var p)){Unsupported++;continue;}if(!Visible(p)){Hidden++;continue;}Packets.Add(p);Quad(f,p,flip);}
   if(Unsupported>0)throw new Exception("Selected curve cell has no original triangle packet");
   pixels.Clear();pixels.SetVertices(pv);pixels.SetNormals(pn);pixels.SetTangents(pt);pixels.SetUVs(0,pu);pixels.SetUVs(3,clip);pixels.SetTriangles(pi,0);pixels.bounds=mesh.bounds;
   if(!material){var shader=Shader.Find("EValidation/HairBoundary491Probe");if(!shader)throw new Exception("491 shader missing");material=new Material(f.motion.materials[12]){shader=shader,hideFlags=HideFlags.DontSave};material.shaderKeywords=f.motion.materials[12].shaderKeywords;sides=new ComputeBuffer(indices.Length/3,4);sides.SetData(new float[indices.Length/3]);material.SetBuffer("_Instance331",sides);}
   current=f;Status="ready";
  }catch(Exception e){Status="unsupported: "+e.Message;}
 }
 public static bool TryGet(Full319View335 f,int renderer,int submesh,out Mesh remaining,out Mesh cells,out Material shader){remaining=rest;cells=pixels;shader=material;return Enabled&&f==current&&renderer==2&&submesh==1;}
}
