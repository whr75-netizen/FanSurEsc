using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

// Supplies only genuinely empty designed clothing cells between the two existing
// renders. The packet is shaded at an actual visible source point, then carried
// into the selected destination cell. No RGB donor search or extra render target.
public static class ClothSurface525
{
    [Serializable] public sealed class Packet
    {
        public int x,y,primitive,submesh;
        public Vector2 sourceProjection,uv;
        public Vector3 barycentric,world;
        public float depth,distance;
    }
    sealed class Triangle
    {
        public int renderer,submesh,primitive,material,a,b,c;
        public Vector2 pa,pb,pc,ua,ub,uc;
        public Vector3 wa,wb,wc;
        public double za,zb,zc;
        public float minX,minY,maxX,maxY;
    }
    public static readonly List<Packet> Packets=new();
    public static int Requested,Unsupported,OccludedCandidates,UncertainCandidates;
    public static double BuildMs;
    static Full319View335 current;
    static Mesh quads;
    static readonly Dictionary<(Material,int),Material> materials=new();
    static readonly List<Triangle> triangles=new();
    static float Cross(Vector2 a,Vector2 b)=>a.x*b.y-a.y*b.x;
    static double CrossD(Vector2 a,Vector2 b)=>(double)a.x*b.y-(double)a.y*b.x;
    static Vector3 Bary(Vector2 p,Triangle t)
    {
        double den=CrossD(t.pb-t.pa,t.pc-t.pa);if(Math.Abs(den)<1e-14)return new Vector3(-1,-1,-1);
        double v=CrossD(p-t.pa,t.pc-t.pa)/den,w=CrossD(t.pb-t.pa,p-t.pa)/den;return new Vector3((float)(1-v-w),(float)v,(float)w);
    }
    static Vector2 Closest(Vector2 p,Triangle t)
    {
        var b=Bary(p,t);if(b.x>=0&&b.y>=0&&b.z>=0)return p;
        Vector2 best=default;float error=float.PositiveInfinity;
        var points=new[]{t.pa,t.pb,t.pc};for(int e=0;e<3;e++){var a=points[e];var d=points[(e+1)%3]-a;var q=a+d*Mathf.Clamp01(Vector2.Dot(p-a,d)/d.sqrMagnitude);float v=(q-p).sqrMagnitude;if(v<error){best=q;error=v;}}
        return best;
    }
    static List<Vector2> Clip(List<Vector2> polygon,int axis,float value,bool greater)
    {
        var result=new List<Vector2>();if(polygon.Count==0)return result;var a=polygon[polygon.Count-1];float da=(a[axis]-value)*(greater?1:-1);
        foreach(var b in polygon){float db=(b[axis]-value)*(greater?1:-1);if((da>=0)!=(db>=0))result.Add(a+(b-a)*(da/(da-db)));if(db>=0)result.Add(b);a=b;da=db;}return result;
    }
    static void Geometry(Full319View335 f)
    {
        triangles.Clear();int material=0;var view=f.motion.camera.worldToCameraMatrix;
        for(int r=0;r<3;r++)
        {
            var output=f.motion.surface.outputs[r];var mesh=output.sharedMesh;var v=mesh.vertices;var uv=mesh.uv;var world=v.Select(output.transform.TransformPoint).ToArray();var p=world.Select(f.Project).ToArray();var z=world.Select(q=>-(double)view.MultiplyPoint3x4(q).z).ToArray();
            for(int sm=0;sm<mesh.subMeshCount;sm++,material++){var ids=mesh.GetIndices(sm);for(int pr=0;pr<ids.Length/3;pr++){int a=ids[pr*3],b=ids[pr*3+1],c=ids[pr*3+2];triangles.Add(new Triangle{renderer=r,submesh=sm,primitive=pr,material=material,a=a,b=b,c=c,pa=p[a],pb=p[b],pc=p[c],wa=world[a],wb=world[b],wc=world[c],za=z[a],zb=z[b],zc=z[c],ua=uv[a],ub=uv[b],uc=uv[c],minX=Mathf.Min(p[a].x,Mathf.Min(p[b].x,p[c].x)),minY=Mathf.Min(p[a].y,Mathf.Min(p[b].y,p[c].y)),maxX=Mathf.Max(p[a].x,Mathf.Max(p[b].x,p[c].x)),maxY=Mathf.Max(p[a].y,Mathf.Max(p[b].y,p[c].y))});}}
        }
    }
    static bool Visible(Full319View335 f,Vector2 point,out Triangle front,out Vector3 weights)
    {
        front=null;weights=default;double nearest=double.PositiveInfinity,uncertain=double.PositiveInfinity;
        foreach(var t in triangles)
        {
            if(point.x<t.minX||point.x>t.maxX||point.y<t.minY||point.y>t.maxY)continue;
            var m=f.motion.materials[t.material];int cull=(int)m.GetFloat("_M_CullMode");double det=CrossD(t.pb-t.pa,t.pc-t.pa);if(cull==2&&det<=0||cull==1&&det>=0)continue;
            var b=Bary(point,t);if(b.x<0||b.y<0||b.z<0)continue;double depth=t.za*b.x+t.zb*b.y+t.zc*b.z;if(depth<=0||depth>nearest)continue;
            var uv=t.ua*b.x+t.ub*b.y+t.uc*b.z;var texture=m.mainTexture as Texture2D;
            if(!texture||texture.mipmapCount!=1||texture.wrapMode!=TextureWrapMode.Repeat||m.GetFloat("_UvAnimScrollXSpeed")!=0||m.GetFloat("_UvAnimScrollYSpeed")!=0||m.GetFloat("_UvAnimRotationSpeed")!=0){uncertain=Math.Min(uncertain,depth);continue;}
            var st=m.GetVector("_MainTex_ST");uv=uv*new Vector2(st.x,st.y)+new Vector2(st.z,st.w);int mode=(int)m.GetFloat("_AlphaMode");float cutoff=mode==1?m.GetFloat("_Cutoff"):mode==2?6.103515625e-5f:0;
            var range=HeadArea505.SourceAlphaFootprint511(texture,uv)*m.color.a;
            if(range.y<cutoff)continue;if(range.x<cutoff){uncertain=Math.Min(uncertain,depth);continue;}
            front=t;weights=b;nearest=depth;
        }
        if(uncertain<=nearest){UncertainCandidates++;return false;}
        if(front==null||front.renderer!=0||!ClothRegion524.Active540(front.submesh)){OccludedCandidates++;return false;}return true;
    }
    public static void BeginFrame(){current=null;Packets.Clear();Requested=Unsupported=OccludedCandidates=UncertainCandidates=0;BuildMs=0;}
    public static void Prepare(Full319View335 f,Color[] centre,Color[] owner)
    {
        if(!ClothRegion524.Ready(f))return;long start=Stopwatch.GetTimestamp();
        var requests=new bool[480*272];var cells=new List<Vector2Int>();
        foreach(var part in ClothRegion524.Parts540)
        {
            if(!ClothRegion524.Active540(part.submesh))continue;var region=part.bounds;
            for(int y=0;y<region.height;y++)for(int x=0;x<region.width;x++){int at=y*region.width+x,px=x+region.x,py=y+region.y,i=(271-py)*480+px;if(part.selected[at]&&!requests[i]&&centre[i].r<=0&&owner[i].b<=0){requests[i]=true;cells.Add(new Vector2Int(px,py));}}
        }
        Requested=cells.Count;if(Requested==0){current=f;BuildMs=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;return;}
        Geometry(f);var clothing=triangles.Where(t=>t.renderer==0&&ClothRegion524.Active540(t.submesh)).ToArray();
        foreach(var cell in cells)
        {
            var centrePoint=new Vector2(cell.x+.5f,cell.y+.5f);Packet best=null;
            // Support bound follows the existing curve error and cell radius.
            float radius=HeadRegion502.CurveError+Mathf.Sqrt(.5f),bestError=radius*radius;
            foreach(var t in clothing)
            {
                if(!ClothRegion524.Selected540(t.submesh,cell.x,cell.y))continue;
                if(t.maxX<cell.x-radius||t.minX>cell.x+1+radius||t.maxY<cell.y-radius||t.minY>cell.y+1+radius)continue;
                var candidates=new List<Vector2>();var near=Closest(centrePoint,t);var b=Bary(near,t);b=b*.99999f+Vector3.one*(.00001f/3);candidates.Add(t.pa*b.x+t.pb*b.y+t.pc*b.z);
                var polygon=new List<Vector2>{t.pa,t.pb,t.pc};polygon=Clip(polygon,0,cell.x,true);polygon=Clip(polygon,0,cell.x+1,false);polygon=Clip(polygon,1,cell.y,true);polygon=Clip(polygon,1,cell.y+1,false);if(polygon.Count>=3)candidates.Add(polygon.Aggregate(Vector2.zero,(sum,p)=>sum+p)/polygon.Count);
                foreach(var q in candidates)
                {
                    float error=(q-centrePoint).sqrMagnitude;if(error>bestError)continue;var own=Bary(q,t);if(own.x<0||own.y<0||own.z<0)continue;var sourceUV=t.ua*own.x+t.ub*own.y+t.uc*own.z;if(!ClothRegion524.Parts540[t.submesh].opacity.Opaque(sourceUV))continue;
                    if(!Visible(f,q,out var source,out var weights)||!ClothRegion524.Selected540(source.submesh,cell.x,cell.y))continue;sourceUV=source.ua*weights.x+source.ub*weights.y+source.uc*weights.z;if(!ClothRegion524.Parts540[source.submesh].opacity.Opaque(sourceUV))continue;
                    var world=source.wa*weights.x+source.wb*weights.y+source.wc*weights.z;float depth=-f.motion.camera.worldToCameraMatrix.MultiplyPoint3x4(world).z;
                    if(error==bestError&&best!=null&&depth>=best.depth)continue;bestError=error;best=new Packet{x=cell.x,y=cell.y,primitive=source.primitive,submesh=source.submesh,barycentric=weights,world=world,uv=sourceUV,sourceProjection=q,depth=depth,distance=Mathf.Sqrt(error)};
                }
            }
            if(best==null)Unsupported++;else Packets.Add(best);
        }
        Upload(f);current=f;BuildMs=1000.0*(Stopwatch.GetTimestamp()-start)/Stopwatch.Frequency;
    }
    static void Upload(Full319View335 f)
    {
        if(!quads)quads=new Mesh{name="525 sparse visible clothing source packets",hideFlags=HideFlags.DontSave,indexFormat=IndexFormat.UInt32};
        var output=f.motion.surface.outputs[0];var mesh=output.sharedMesh;var verts=mesh.vertices;var normals=mesh.normals;var tangents=mesh.tangents;var indices=Enumerable.Range(0,4).Select(sm=>mesh.GetIndices(sm)).ToArray();var v=new List<Vector3>();var n=new List<Vector3>();var ta=new List<Vector4>();var uv=new List<Vector2>();var pr=new List<Vector4>();var source=new List<Vector4>();var ix=Enumerable.Range(0,4).Select(_=>new List<int>()).ToArray();var inv=f.effectiveProjection.inverse;var toWorld=f.motion.camera.cameraToWorldMatrix;var toLocal=output.transform.worldToLocalMatrix;
        foreach(var p in Packets)
        {
            var ids=indices[p.submesh];int a=ids[p.primitive*3],b=ids[p.primitive*3+1],c=ids[p.primitive*3+2],at=v.Count;var weights=p.barycentric;var local=verts[a]*weights.x+verts[b]*weights.y+verts[c]*weights.z;var normal=(normals[a]*weights.x+normals[b]*weights.y+normals[c]*weights.z).normalized;var tangent=tangents[a]*weights.x+tangents[b]*weights.y+tangents[c]*weights.z;
            foreach(var corner in new[]{new Vector2(p.x,p.y),new Vector2(p.x+1,p.y),new Vector2(p.x+1,p.y+1),new Vector2(p.x,p.y+1)}){var q=inv*new Vector4(corner.x/240-1,1-corner.y/136,0,1);q/=q.w;var target=toWorld.MultiplyPoint3x4(new Vector3(q.x,q.y,-p.depth));v.Add(toLocal.MultiplyPoint3x4(target));n.Add(normal);ta.Add(tangent);uv.Add(p.uv);pr.Add(new Vector4(p.primitive,p.x,p.y,1));source.Add(new Vector4(local.x,local.y,local.z,1));}
            var pa=f.Project(output.transform.TransformPoint(verts[a]));var pb=f.Project(output.transform.TransformPoint(verts[b]));var pc=f.Project(output.transform.TransformPoint(verts[c]));bool forward=Cross(pb-pa,pc-pa)>0;foreach(int i in forward?new[]{0,1,2,0,2,3}:new[]{0,2,1,0,3,2})ix[p.submesh].Add(at+i);
        }
        quads.Clear();quads.SetVertices(v);quads.SetNormals(n);quads.SetTangents(ta);quads.SetUVs(0,uv);quads.SetUVs(3,pr);quads.SetUVs(4,source);quads.subMeshCount=4;for(int sm=0;sm<4;sm++)quads.SetTriangles(ix[sm],sm);quads.bounds=mesh.bounds;
    }
    public static void Draw(RasterCommandBuffer cmd,Full319View335 f,Material source,int kind)
    {
        if(current!=f||!ClothRegion524.Ready(f)||Packets.Count==0)return;
        foreach(var part in ClothRegion524.Parts540)
        {
        if(!ClothRegion524.Active540(part.submesh)||!Packets.Any(p=>p.submesh==part.submesh))continue;
        source=kind==0?f.motion.materials[part.submesh]:f.legacySignalsMats[part.submesh];var key=(source,kind);
        if(!materials.TryGetValue(key,out var material)||!material){var shader=Shader.Find("EValidation/HeadRegion502"+(kind==0?"Probe":"Legacy"));if(!shader)throw new InvalidOperationException("525 existing packet shader missing");material=new Material(source){shader=shader,hideFlags=HideFlags.DontSave};material.shaderKeywords=source.shaderKeywords;material.SetFloat("_M_CullMode",0);materials[key]=material;}
        material.SetTexture("_Region502Mask",part.mask);cmd.SetGlobalVector("_Source329Metadata",new Vector4(7+part.submesh,0,0,0));cmd.SetGlobalMatrix("_Region502ViewProjection",f.effectiveProjection*f.motion.camera.worldToCameraMatrix);cmd.SetGlobalFloat("_Region502Scale",1);cmd.SetGlobalVector("_Region502OwnedShift",f.motion.clipShift);cmd.SetGlobalInt("_Region502Quad",1);cmd.SetGlobalInt("_Region502Hair",0);cmd.DrawMesh(quads,f.motion.surface.outputs[0].transform.localToWorldMatrix,material,part.submesh,0);cmd.SetGlobalInt("_Region502Quad",0);
        }
    }
    public static void Release(){BeginFrame();if(quads)UnityEngine.Object.DestroyImmediate(quads);quads=null;foreach(var m in materials.Values)if(m)UnityEngine.Object.DestroyImmediate(m);materials.Clear();triangles.Clear();}
}
