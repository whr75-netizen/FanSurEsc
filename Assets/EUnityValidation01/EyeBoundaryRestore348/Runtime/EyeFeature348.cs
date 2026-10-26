using System;using System.Linq;using System.Collections.Generic;using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Experimental.Rendering;
[ExecuteAlways]public sealed class EyeFeature348:MonoBehaviour{
 [Serializable]public class ModelEye{public int stableId;public Vector3 centre,axisX,axisY,normal;public Vector2 measuredRadii;public int[]closedBoundary;public bool boundaryClosed;}
 [Serializable]public class Style{public string version="V11_CURVES_CURRENT_PIGMENT_348_02";public Vector2 upper=new Vector2(-.82f,.35f),lower=new Vector2(.72f,-.26f),irisRadii=new Vector2(.55f,.84f),catchU=new Vector2(-.46f,-.08f),catchV=new Vector2(-.55f,-.08f);public float irisOffset=.05f,irisPower=3;public Vector2 referenceSocketMetres=new Vector2(.0195f,.0145f);public Vector2[]radiusScale;public bool newCatchPigment=false,whiteNeighbourSupport=false;}
 public string modelTopologySHA256;public Full319View335 full;public Shader sampleShader,skinShader;public ComputeShader candidateShader;public bool candidateEnabled=true,showControls=true;public ModelEye[]modelEyes;public Style style=new Style();public Vector4 faceLidShadeEndpoint;public string lidPigmentProvenance="Existing335.skinShade style endpoint";public static EyeFeature348 Active;public static bool UseIrisSurface582,UseLashRegion583;public static bool UseClosedLash590=true;
 public sealed class Layer{public RTHandle rgba,meta,point,uv,depth;}
 [NonSerialized]public Layer[]samples;[NonSerialized]public RTHandle output,owner,intrinsic,visible,histA,histB,surface,pigment,audit,domain,bary,supportMeta;
 [NonSerialized]public ComputeBuffer restTriangles,records;[NonSerialized]public Vector4[]triangleRanges=new Vector4[16];public bool samplesOnly;
 [NonSerialized]public ComputeBuffer lashGeometry590;Vector3[]lashRest590;int[][]lashArcs590;
 [NonSerialized]public Material[]materials;[NonSerialized]public Material skinMaterial;[NonSerialized]public RectInt roi;[NonSerialized]public Matrix4x4 cropProjection,headMatrix;[NonSerialized]public Vector4[]centres,axesX,axesY,normals;[NonSerialized]public Mesh sampleFace;[NonSerialized]public Matrix4x4 sourceToRestHead;[NonSerialized]public int headBoneIndex;bool ready;
 void OnEnable(){Active=this;}
 RTHandle T(int w,int h,bool rw=true)=>RTHandles.Alloc(w,h,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:rw,filterMode:FilterMode.Point);
 public void Initialise(){if(ready||!full)return;Active=this;full.Initialise();full.PrepareCurrent();var src=full.motion.surface.source[1];var original=src.sharedMesh;var hash348=EyeBoundaryBinding348.Hash(original);if(!string.IsNullOrEmpty(modelTopologySHA256)&&modelTopologySHA256!=hash348)throw new Exception("348 MODEL_BINDING_MISMATCH_REGENERATE_ADAPTER");modelTopologySHA256=hash348;headBoneIndex=Array.IndexOf(src.bones,full.motion.animation.target.GetBoneTransform(HumanBodyBones.Head));if(headBoneIndex<0)throw new Exception("348 Head bindpose unavailable");sourceToRestHead=original.bindposes[headBoneIndex];var rest=original.vertices.Select(p=>sourceToRestHead.MultiplyPoint3x4(p)).ToArray();if(modelEyes==null||modelEyes.Length!=2){var ix=original.GetIndices(4).Distinct().ToArray();var local=ix.Select(i=>rest[i]).ToArray();var rings348=EyeBoundaryBinding348.ClosedRings(original,3);if(rings348.Length<2)throw new Exception("348 NO_CLOSED_NATIVE_EYE_BOUNDARY");modelEyes=new ModelEye[2];style.radiusScale=new Vector2[2];for(int e=0;e<2;e++){var spec=full.eyes[e];var n=spec.whiteNormalHead.normalized;var y=Vector3.up;var x=Vector3.Cross(y,n).normalized;y=Vector3.Cross(n,x).normalized;var c=spec.whiteCentreHead;var ring348=rings348.OrderBy(ring=>{var mean=ring.Select(i=>rest[i]).Aggregate(Vector3.zero,(a,b)=>a+b)/ring.Length;return (mean-c).sqrMagnitude;}).First();var ringMean348=ring348.Select(i=>rest[i]).Aggregate(Vector3.zero,(a,b)=>a+b)/ring348.Length;float separation348=(full.eyes[0].whiteCentreHead-full.eyes[1].whiteCentreHead).magnitude;if((ringMean348-c).magnitude>separation348*.25f)throw new Exception("348 EYE_BOUNDARY_BINDING_DISTANCE");var own=ring348.Select(i=>rest[i]).ToArray();var radii=new Vector2(own.Max(p=>Mathf.Abs(Vector3.Dot(p-c,x))),own.Max(p=>Mathf.Abs(Vector3.Dot(p-c,y))));if(radii.x<=0||radii.y<=0)throw new Exception("348 no native eye radius support");modelEyes[e]=new ModelEye{stableId=e==0?2:1,centre=c,axisX=x,axisY=y,normal=n,measuredRadii=radii,closedBoundary=ring348,boundaryClosed=true};style.radiusScale[e]=new Vector2(style.referenceSocketMetres.x/radii.x,style.referenceSocketMetres.y/radii.y);}}
  sampleFace=Instantiate(original);sampleFace.name="348 native source current surface + original Head-bind rest attribute";sampleFace.hideFlags=HideFlags.DontSave;sampleFace.SetUVs(1,rest.ToList());sampleFace.SetUVs(7,rest.Select(p=>new Vector2((p-modelEyes[0].centre).sqrMagnitude<=(p-modelEyes[1].centre).sqrMagnitude?modelEyes[0].stableId:modelEyes[1].stableId,0)).ToList());if(faceLidShadeEndpoint.w<=0)faceLidShadeEndpoint=full.skinShade;var triangles=new List<Vector4>();for(int sm=0;sm<7;sm++){var ix=original.GetIndices(sm);triangleRanges[sm]=new Vector4(triangles.Count,ix.Length/3,0,0);foreach(int i in ix)triangles.Add(rest[i]);}restTriangles=new ComputeBuffer(triangles.Count,16);restTriangles.SetData(triangles);
  materials=full.independentMats.Select(m=>new Material(m){shader=sampleShader,hideFlags=HideFlags.DontSave}).ToArray();skinMaterial=new Material(full.legacyProviderMat){shader=skinShader,hideFlags=HideFlags.DontSave};
  records=new ComputeBuffer(480*272,16*16);output=T(480,272);owner=T(480,272);intrinsic=T(480,272);visible=T(480,272);histA=T(480,272);histB=T(480,272);surface=T(480,272);pigment=T(480,272);audit=T(480,272);domain=T(480,272);bary=T(480,272);supportMeta=T(480,272);ready=true;
 }
 public void Prepare(){Initialise();var ph=full.phases[full.phaseIndex];headMatrix=full.providerMatrix*ph.head;centres=new Vector4[2];axesX=new Vector4[2];axesY=new Vector4[2];normals=new Vector4[2];var min=new Vector2(float.PositiveInfinity,float.PositiveInfinity);var max=new Vector2(float.NegativeInfinity,float.NegativeInfinity);for(int e=0;e<2;e++){var m=modelEyes[e];var r=Vector2.Scale(m.measuredRadii,style.radiusScale[e]);centres[e]=new Vector4(m.centre.x,m.centre.y,m.centre.z,m.stableId);axesX[e]=new Vector4(m.axisX.x,m.axisX.y,m.axisX.z,r.x);axesY[e]=new Vector4(m.axisY.x,m.axisY.y,m.axisY.z,r.y);normals[e]=new Vector4(m.normal.x,m.normal.y,m.normal.z,0);foreach(float u in new[]{-1.4f,1.4f})foreach(float v in new[]{-1.4f,1.4f}){var s=full.Project(headMatrix.MultiplyPoint3x4(m.centre+m.axisX*(u*r.x)+m.axisY*(v*r.y)));min=Vector2.Min(min,s);max=Vector2.Max(max,s);}}
  var current=full.motion.surface.outputs[1].sharedMesh;if(current.vertexCount!=sampleFace.vertexCount)throw new Exception("348 native topology changed");var currentVertices590=current.vertices;sampleFace.vertices=currentVertices590;sampleFace.normals=current.normals;sampleFace.tangents=current.tangents;sampleFace.bounds=current.bounds;
  List<LashRegion590.V[]>[]lashCurves590=null;if(UseLashRegion583&&UseClosedLash590){lashCurves590=BuildLashCurves590(currentVertices590);foreach(var eye in lashCurves590)foreach(var quad in eye)foreach(var p in quad){var xy=new Vector2((float)p.x,(float)p.y);min=Vector2.Min(min,xy);max=Vector2.Max(max,xy);}}
  int x0=Mathf.Clamp(Mathf.FloorToInt(min.x)-1,0,479),y0=Mathf.Clamp(Mathf.FloorToInt(min.y)-1,0,271),x1=Mathf.Clamp(Mathf.CeilToInt(max.x)+1,x0+1,480),y1=Mathf.Clamp(Mathf.CeilToInt(max.y)+1,y0+1,272);var next=new RectInt(x0,y0,x1-x0,y1-y0);if(samples==null||next.width!=roi.width||next.height!=roi.height){if(samples!=null)foreach(var l in samples)foreach(var t in new[]{l.rgba,l.meta,l.point,l.uv,l.depth})t.Release();samples=Enumerable.Range(0,7).Select(_=>new Layer{rgba=T(next.width*4,next.height*4,false),meta=T(next.width*4,next.height*4,false),point=T(next.width*4,next.height*4,false),uv=T(next.width*4,next.height*4,false),depth=RTHandles.Alloc(next.width*4,next.height*4,depthBufferBits:DepthBits.Depth32)}).ToArray();}roi=next;var crop=Matrix4x4.identity;crop[0,0]=480f/roi.width;crop[0,3]=(480f-2*roi.x-roi.width)/roi.width;crop[1,1]=272f/roi.height;crop[1,3]=(2*roi.y+roi.height-272f)/roi.height;cropProjection=crop*full.effectiveProjection;
  if(lashGeometry590==null)lashGeometry590=new ComputeBuffer(1,16);
  if(UseLashRegion583&&UseClosedLash590){int count=roi.width*roi.height*16;var data=new LashRegion590.Sample[count*2];for(int eye=0;eye<2;eye++){var a=LashRegion590.Rasterise(lashCurves590[eye],roi.x,roi.y,roi.width,roi.height);Array.Copy(a,0,data,eye*count,count);}if(lashGeometry590.count!=data.Length){lashGeometry590.Dispose();lashGeometry590=new ComputeBuffer(data.Length,16);}lashGeometry590.SetData(data);}
 }
 // Native open-eye boundary determines the region before source pigment or
 // raster alpha is consulted. Thickness retains the existing design constants.
 List<LashRegion590.V[]>[] BuildLashCurves590(Vector3[]current)
 {
  if(lashRest590==null){lashRest590=full.motion.surface.source[1].sharedMesh.vertices.Select(p=>sourceToRestHead.MultiplyPoint3x4(p)).ToArray();lashArcs590=new int[2][];for(int eye=0;eye<2;eye++){var m=modelEyes[eye];if(!m.boundaryClosed||m.closedBoundary==null)throw new Exception("590 requires closed native eye boundary");var u=new double[lashRest590.Length];var v=new double[u.Length];for(int i=0;i<u.Length;i++){var d=lashRest590[i]-m.centre;u[i]=Vector3.Dot(d,m.axisX)/axesX[eye].w;v[i]=-Vector3.Dot(d,m.axisY)/axesY[eye].w;}lashArcs590[eye]=LashRegion590.UpperArc(m.closedBoundary,u,v);}}
  var output=new List<LashRegion590.V[]>[2];var transform=full.motion.surface.outputs[1].transform.localToWorldMatrix;var view=full.motion.camera.worldToCameraMatrix;
  for(int eye=0;eye<2;eye++)
  {
   output[eye]=new List<LashRegion590.V[]>();var m=modelEyes[eye];var ring=m.closedBoundary;var origin=transform.MultiplyPoint3x4(current[ring[0]]);Vector3 restNormal=Vector3.zero,currentNormal=Vector3.zero;for(int i=0;i<ring.Length;i++){int a=ring[i],b=ring[(i+1)%ring.Length];restNormal+=Vector3.Cross(lashRest590[a]-m.centre,lashRest590[b]-m.centre);currentNormal+=Vector3.Cross(transform.MultiplyPoint3x4(current[a])-origin,transform.MultiplyPoint3x4(current[b])-origin);}
   // Correct native ring winding once with the model's outward eye normal.
   if(Vector3.Dot(restNormal,m.normal)<0)currentNormal=-currentNormal;if(Vector3.Dot(currentNormal,full.rayDepth)>=0)continue;
   var up=headMatrix.MultiplyVector(m.axisY*axesY[eye].w);
   LashRegion590.V Vertex(int id,float offset){var world=transform.MultiplyPoint3x4(current[id])+up*offset;var xy=full.Project(world);var d=lashRest590[id]-m.centre;return new LashRegion590.V(xy.x,xy.y,-view.MultiplyPoint3x4(world).z,Vector3.Dot(d,m.axisX)/axesX[eye].w,-Vector3.Dot(d,m.axisY)/axesY[eye].w-offset);}
   var arc=lashArcs590[eye];for(int i=1;i<arc.Length;i++)output[eye].Add(new[]{Vertex(arc[i-1],.36f),Vertex(arc[i],.36f),Vertex(arc[i],-.22f),Vertex(arc[i-1],-.22f)});
  }
  return output;
 }
 void OnGUI(){if(!showControls||!full)return;GUILayout.BeginArea(new Rect(10,165,730,98),GUI.skin.box);bool next=GUILayout.Toggle(candidateEnabled,"348 independent V11 eye feature curves / actual16samples / source pigments /343 registration");if(next!=candidateEnabled){candidateEnabled=next;full.motion.resetHistory=true;full.RenderFrame();}GUILayout.Label("Same main camera/grid. Strict all-hair/body depth. No screen-painted line, new texture or hair deletion.");GUILayout.EndArea();}
 void OnDisable(){if(Active==this)Active=null;if(materials!=null)foreach(var m in materials)if(m)DestroyImmediate(m);if(skinMaterial)DestroyImmediate(skinMaterial);if(sampleFace)DestroyImmediate(sampleFace);restTriangles?.Dispose();records?.Dispose();lashGeometry590?.Dispose();lashGeometry590=null;lashRest590=null;lashArcs590=null;if(samples!=null)foreach(var l in samples)foreach(var t in new[]{l.rgba,l.meta,l.point,l.uv,l.depth})t?.Release();foreach(var t in new[]{output,owner,intrinsic,visible,histA,histB,surface,pigment,audit,domain,bary,supportMeta})t?.Release();ready=false;}
}

// The shape input is a closed, currently deformed ribbon, never source alpha.
// Uses the existing continuous positive-winding curve area implementation.
public static class LashRegion590
{
 public struct V {public double x,y,z,u,v;public V(double x,double y,double z,double u,double v){this.x=x;this.y=y;this.z=z;this.u=u;this.v=v;}}
 public struct Sample {public float area,depth,u,v;}
 static double Cross(V a,V b,V c)=>(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
 public static int[] UpperArc(int[] ring,double[] u,double[] v)
 {
  int n=ring.Length;if(n>1&&ring[0]==ring[n-1])n--;if(n<3)throw new System.InvalidOperationException("590 eye boundary is not closed");
  int left=0,right=0;for(int i=1;i<n;i++){if(u[ring[i]]<u[ring[left]])left=i;if(u[ring[i]]>u[ring[right]])right=i;}
  if(left==right)throw new System.InvalidOperationException("590 eye boundary has no horizontal span");
  int[] Chain(int direction){var a=new System.Collections.Generic.List<int>();int at=left;for(int k=0;k<=n;k++){a.Add(ring[at]);if(at==right)return a.ToArray();at=(at+direction+n)%n;}throw new System.InvalidOperationException("590 open eye boundary");}
  double Mean(int[] chain){double weighted=0,length=0;for(int i=1;i<chain.Length;i++){int a=chain[i-1],b=chain[i];double du=u[b]-u[a],dv=v[b]-v[a],w=System.Math.Sqrt(du*du+dv*dv);weighted+=w*(v[a]+v[b])*.5;length+=w;}return weighted/length;}
  var forward=Chain(1);var backward=Chain(-1);return Mean(forward)<=Mean(backward)?forward:backward;
 }
 static System.Collections.Generic.List<V> Clip(System.Collections.Generic.List<V> input,int axis,double edge,bool greater)
 {
  var output=new System.Collections.Generic.List<V>();if(input.Count==0)return output;
  double D(V p)=>((axis==0?p.x:p.y)-edge)*(greater?1:-1);
  var a=input[input.Count-1];double da=D(a);foreach(var b in input){double db=D(b);if((da>=0)!=(db>=0)){double t=da/(da-db);output.Add(new V(a.x+t*(b.x-a.x),a.y+t*(b.y-a.y),a.z+t*(b.z-a.z),a.u+t*(b.u-a.u),a.v+t*(b.v-a.v)));}if(db>=0)output.Add(b);a=b;da=db;}return output;
 }
 static double Area(System.Collections.Generic.List<V> p){double a=0;for(int i=0;i<p.Count;i++){var b=p[(i+1)%p.Count];a+=p[i].x*b.y-b.x*p[i].y;}return System.Math.Abs(a)*.5;}
 static double At(V a,V b,V c,double x,double y,int field)
 {
  double den=Cross(a,b,c),s=((x-a.x)*(c.y-a.y)-(y-a.y)*(c.x-a.x))/den,t=((b.x-a.x)*(y-a.y)-(b.y-a.y)*(x-a.x))/den;
  double Get(V p)=>field==0?p.z:field==1?p.u:p.v;return Get(a)+s*(Get(b)-Get(a))+t*(Get(c)-Get(a));
 }
 // Result is top-left ordered at 4x the logical ROI. Each packet contains
 // exact polygon/subcell area and same-sample-ray geometric depth/rest u/v.
 // Occlusion still uses the existing sampled hair, brow and body inputs.
 public static Sample[] Rasterise(System.Collections.Generic.IList<V[]> quads,int x0,int y0,int width,int height)
 {
  int w=width*4,h=height*4;var rings=new System.Collections.Generic.List<CurveArea511.P[]>();
  foreach(var quad in quads){var p=new CurveArea511.P[quad.Length];double signed=0;for(int i=0;i<quad.Length;i++){p[i]=new CurveArea511.P(quad[i].x*4,quad[i].y*4);var b=quad[(i+1)%quad.Length];signed+=quad[i].x*b.y-b.x*quad[i].y;}if(signed<0)System.Array.Reverse(p);if(signed!=0)rings.Add(p);}
  var area=CurveArea511.Compute(rings,x0*4,y0*4,w,h);var output=new Sample[w*h];
  foreach(var quad in quads)
  {
   if(quad.Length<3||System.Math.Abs(Cross(quad[0],quad[1],quad[2]))<1e-15)continue;
   double minX=double.PositiveInfinity,minY=minX,maxX=double.NegativeInfinity,maxY=maxX;foreach(var p in quad){minX=System.Math.Min(minX,p.x);maxX=System.Math.Max(maxX,p.x);minY=System.Math.Min(minY,p.y);maxY=System.Math.Max(maxY,p.y);}
   int xa=System.Math.Max(x0*4,(int)System.Math.Floor(minX*4)),xb=System.Math.Min((x0+width)*4-1,(int)System.Math.Floor(maxX*4));
   int ya=System.Math.Max(y0*4,(int)System.Math.Floor(minY*4)),yb=System.Math.Min((y0+height)*4-1,(int)System.Math.Floor(maxY*4));
   for(int y=ya;y<=yb;y++)for(int x=xa;x<=xb;x++)
   {
    int index=(y-y0*4)*w+x-x0*4;if(area[index]<=0)continue;
    var clipped=new System.Collections.Generic.List<V>(quad);clipped=Clip(clipped,0,x*.25,true);clipped=Clip(clipped,0,(x+1)*.25,false);clipped=Clip(clipped,1,y*.25,true);clipped=Clip(clipped,1,(y+1)*.25,false);if(Area(clipped)<=1e-15)continue;
    double sx=(x+.5)*.25,sy=(y+.5)*.25,z=At(quad[0],quad[1],quad[2],sx,sy,0);if(z<=0||double.IsNaN(z)||double.IsInfinity(z))continue;
    if(output[index].depth>0&&output[index].depth<=z)continue;
    output[index]=new Sample{area=area[index],depth=(float)z,u=(float)At(quad[0],quad[1],quad[2],sx,sy,1),v=(float)At(quad[0],quad[1],quad[2],sx,sy,2)};
   }
  }
  return output;
 }
}
