using System;
using System.Collections.Generic;
using UnityEngine;

// Shared source-alpha cache access only; exact505 area/union code is unchanged.
public static partial class HeadArea505
{
    public static byte[] SourceAlphaBytes525(Texture2D texture)
    {
        if(Application.isPlaying)return(byte[])Alpha(texture).Clone();
        var target=RenderTexture.GetTemporary(texture.width,texture.height,0,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Linear);var prior=RenderTexture.active;var readable=new Texture2D(texture.width,texture.height,TextureFormat.RGBA32,false,true);
        try{Graphics.Blit(texture,target);RenderTexture.active=target;readable.ReadPixels(new Rect(0,0,texture.width,texture.height),0,0,false);readable.Apply(false,false);var p=readable.GetPixels32();var result=new byte[p.Length];for(int i=0;i<p.Length;i++)result[i]=p[i].a;return result;}
        finally{RenderTexture.active=prior;RenderTexture.ReleaseTemporary(target);UnityEngine.Object.DestroyImmediate(readable);}
    }
    public static Vector2 SourceAlphaExtrema511(Texture2D texture)
    {var a=Alpha(texture);byte lo=255,hi=0;foreach(byte v in a){if(v<lo)lo=v;if(v>hi)hi=v;}return new Vector2(lo/255f,hi/255f);}
    public static Vector2 SourceAlphaFootprint511(Texture2D texture,Vector2 uv)
    {
        var a=Alpha(texture);double x=uv.x*texture.width-.5,y=uv.y*texture.height-.5;int ix=(int)Math.Floor(x),iy=(int)Math.Floor(y);byte lo=255,hi=0;
        for(int v=iy;v<=iy+1;v++)for(int u=ix;u<=ix+1;u++){byte b=a[Mod(v,texture.height)*texture.width+Mod(u,texture.width)];if(b<lo)lo=b;if(b>hi)hi=b;}
        return new Vector2(lo/255f,hi/255f);
    }
}

public static partial class HeadRegion502
{
    struct Camera511
    {
        public double x,y,z;
        public Camera511(Matrix4x4 m,Vector3 p){x=(double)m.m00*p.x+(double)m.m01*p.y+(double)m.m02*p.z+m.m03;y=(double)m.m10*p.x+(double)m.m11*p.y+(double)m.m12*p.z+m.m13;z=-((double)m.m20*p.x+(double)m.m21*p.y+(double)m.m22*p.z+m.m23);}
    }
    sealed class Blocker511 {public int renderer,sm,primitive,material,a,b,c;public Camera511 pa,pb,pc;public Vector2 ua,ub,uc;}
    sealed class Alpha511 {public Texture2D texture;public float cutoff;public int cull;public Vector2 range;}
    static readonly List<Blocker511> blockers511=new();
    static readonly List<Blocker511>[] blockerBins511=new List<Blocker511>[480*272];
    static readonly List<int> blockerUsed511=new();
    static readonly Mesh[] blockerMeshes511=new Mesh[3];
    static Alpha511[] alpha511;
    static Matrix4x4 visibility511;
    static Full319View335 view511;
    public static int Auto511HiddenCells,Auto511VisibilityTests,Auto511AlphaUncertain;
    static bool supported511;
    // Default-OFF: transport source-ray visibility with the designed hair cell.
    // The integer display move is not a second physical sampling operation.
    public static bool UseBodyRay512;
    [Serializable] public sealed class BodyReference512
    {
        public int x,y,submesh=-1,primitive=-1,kind; // 1 opaque,2 conservative behind bound,3 no body
        public float depth,alphaMin,alphaMax,hairDepth;
        public Vector2 uv;
        public Vector3 barycentric,sampleWorld;
    }
    public static readonly List<BodyReference512> BodyReferences512=new();
    static readonly Dictionary<int,BodyReference512> bodyReferences512=new();
    static void ClearBody512(){BodyReferences512.Clear();bodyReferences512.Clear();}
    static void BodyRay512(Packet p)
    {
        var point=new Camera511(visibility511,p.world);
        // Bins enclose each body triangle by the same1.1-cell donor radius.
        // Query the selected cell, so an off-centre donor just outside the
        // region bounds cannot be mistaken for an empty body-ray domain.
        BodyReference512 possible=null,opaque=null;var bin=blockerBins511[p.y*480+p.x];
        if(bin!=null)foreach(var t in bin)
        {
            if(t.renderer!=0)continue;var material=alpha511[t.material];if(material.range.y<material.cutoff)continue;
            double bx=t.pb.x-t.pa.x,by=t.pb.y-t.pa.y,cx=t.pc.x-t.pa.x,cy=t.pc.y-t.pa.y,px=point.x-t.pa.x,py=point.y-t.pa.y,det=bx*cy-by*cx;
            if(Math.Abs(det)<1e-20||material.cull==2&&det>=0)continue;
            double v=(px*cy-py*cx)/det,w=(bx*py-by*px)/det,u=1-v-w;
            if(u<-.00001||v<-.00001||w<-.00001)continue;
            float z=(float)(u*t.pa.z+v*t.pb.z+w*t.pc.z);if(z<=0)continue;
            var sampleUV=t.ua*(float)u+t.ub*(float)v+t.uc*(float)w;
            var range=material.range.x>=material.cutoff?material.range:HeadArea505.SourceAlphaFootprint511(material.texture,sampleUV);
            if(range.y<material.cutoff)continue;
            var hit=new BodyReference512{x=p.x,y=p.y,submesh=t.sm,primitive=t.primitive,kind=range.x>=material.cutoff?1:2,depth=z,uv=sampleUV,barycentric=new Vector3((float)u,(float)v,(float)w),alphaMin=range.x,alphaMax=range.y,hairDepth=p.depth,sampleWorld=p.world};
            if(possible==null||z<possible.depth)possible=hit;
            if(hit.kind==1&&(opaque==null||z<opaque.depth))opaque=hit;
        }
        // A known opaque foreground surface certifies occlusion. An uncertain
        // foreground surface cannot be turned into either a pass or hidden bias.
        BodyReference512 chosen;
        if(opaque!=null&&opaque.depth<p.depth-.0001f)chosen=opaque;
        else if(possible!=null&&possible.kind==2&&possible.depth<p.depth-.0001f)throw new InvalidOperationException("512 source-ray body alpha leaves foreground ownership undecided");
        else chosen=possible??new BodyReference512{x=p.x,y=p.y,kind=3,hairDepth=p.depth,sampleWorld=p.world};
        bodyReferences512.Add(p.y*480+p.x,chosen);BodyReferences512.Add(chosen);
    }
    static Color BodyMask512(int index,bool parent,bool hair)
    {
        if(UseAutomaticCurve511&&UseBodyRay512&&bodyReferences512.TryGetValue(index,out var reference))return new Color(parent?1:0,hair?1:0,reference.depth,reference.kind);
        return new Color(parent?1:0,hair?1:0,0,0);
    }
    public static void Warm511(Full319View335 f)
    {Indices511(f,f.motion.surface.outputs[2].sharedMesh);Materials511(f);}
    static void Materials511(Full319View335 f)
    {
        if(alpha511!=null&&view511==f)return;view511=f;alpha511=new Alpha511[f.motion.materials.Length];
        for(int i=0;i<alpha511.Length;i++)
        {
            var m=f.motion.materials[i];var t=m.mainTexture as Texture2D;
            if(!t||t.mipmapCount!=1||t.filterMode!=FilterMode.Bilinear||t.wrapMode!=TextureWrapMode.Repeat||m.GetVector("_MainTex_ST")!=new Vector4(1,1,0,0)||m.GetFloat("_UvAnimScrollXSpeed")!=0||m.GetFloat("_UvAnimScrollYSpeed")!=0||m.GetFloat("_UvAnimRotationSpeed")!=0||m.color.a!=1)throw new InvalidOperationException("511 unsupported source alpha sampling");
            int mode=(int)m.GetFloat("_AlphaMode"),cull=(int)m.GetFloat("_M_CullMode");
            if((mode!=1&&mode!=2)||(cull!=0&&cull!=2))throw new InvalidOperationException("511 unsupported source alpha/cull mode");
            alpha511[i]=new Alpha511{texture=t,cutoff=mode==1?m.GetFloat("_Cutoff"):6.103515625e-5f,cull=cull,range=HeadArea505.SourceAlphaExtrema511(t)};
        }
        int at=0;for(int r=0;r<2;r++)at+=f.motion.surface.outputs[r].sharedMesh.subMeshCount;
        for(int i=at;i<alpha511.Length;i++)if(alpha511[i].range.x<alpha511[i].cutoff||alpha511[i].cull!=0)throw new InvalidOperationException("511 automatic curve compiler currently requires opaque double-sided Hair");
    }
    static void Occluders511(Full319View335 f,RectInt bounds)
    {
        Materials511(f);visibility511=f.motion.camera.worldToCameraMatrix;
        if(!f.motion.camera.orthographic)throw new InvalidOperationException("511 requires the current orthographic ray contract");
        bool rebuild=false;for(int r=0;r<3;r++)if(blockerMeshes511[r]!=f.motion.surface.outputs[r].sharedMesh)rebuild=true;
        if(rebuild)
        {
            blockers511.Clear();int material=0;
            for(int r=0;r<3;r++)
            {
                var mesh=blockerMeshes511[r]=f.motion.surface.outputs[r].sharedMesh;var tex=mesh.uv;
                for(int s=0;s<mesh.subMeshCount;s++,material++){var ids=mesh.GetIndices(s);for(int i=0;i<ids.Length;i+=3)blockers511.Add(new Blocker511{renderer=r,sm=s,primitive=i/3,material=material,a=ids[i],b=ids[i+1],c=ids[i+2],ua=tex[ids[i]],ub=tex[ids[i+1]],uc=tex[ids[i+2]]});}
            }
        }
        foreach(int at in blockerUsed511)blockerBins511[at].Clear();blockerUsed511.Clear();
        var cp=new Camera511[3][];var sp=new Vector2[3][];
        for(int r=0;r<3;r++)
        {
            var mf=f.motion.surface.outputs[r];var v=r==2?vertices:mf.sharedMesh.vertices;cp[r]=new Camera511[v.Length];sp[r]=new Vector2[v.Length];
            for(int i=0;i<v.Length;i++){var w=r==2?world[i]:mf.transform.TransformPoint(v[i]);cp[r][i]=new Camera511(visibility511,w);sp[r][i]=r==2?projected[i]:f.Project(w);}
        }
        foreach(var t in blockers511)
        {
            t.pa=cp[t.renderer][t.a];t.pb=cp[t.renderer][t.b];t.pc=cp[t.renderer][t.c];var a=sp[t.renderer][t.a];var b=sp[t.renderer][t.b];var c=sp[t.renderer][t.c];
            int x0=Mathf.Max(bounds.x,Mathf.FloorToInt(Mathf.Min(a.x,Mathf.Min(b.x,c.x))-1.1f)),x1=Mathf.Min(bounds.xMax-1,Mathf.FloorToInt(Mathf.Max(a.x,Mathf.Max(b.x,c.x))+1.1f));
            int y0=Mathf.Max(bounds.y,Mathf.FloorToInt(Mathf.Min(a.y,Mathf.Min(b.y,c.y))-1.1f)),y1=Mathf.Min(bounds.yMax-1,Mathf.FloorToInt(Mathf.Max(a.y,Mathf.Max(b.y,c.y))+1.1f));
            for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){int at=y*480+x;if(blockerBins511[at]==null)blockerBins511[at]=new List<Blocker511>();if(blockerBins511[at].Count==0)blockerUsed511.Add(at);blockerBins511[at].Add(t);}
        }
        Auto511HiddenCells=Auto511VisibilityTests=Auto511AlphaUncertain=0;
    }
    static bool Visible511(Packet p)
    {
        var point=new Camera511(visibility511,p.world);var q=view511.Project(p.world);int x=Mathf.FloorToInt(q.x),y=Mathf.FloorToInt(q.y);
        if(x<0||y<0||x>=480||y>=272)return false;var bin=blockerBins511[y*480+x];if(bin==null)return true;
        foreach(var t in bin)
        {
            if(t.renderer==2&&t.sm==p.submesh&&t.primitive==p.primitive)continue;
            var material=alpha511[t.material];if(material.range.y<material.cutoff)continue;
            double bx=t.pb.x-t.pa.x,by=t.pb.y-t.pa.y,cx=t.pc.x-t.pa.x,cy=t.pc.y-t.pa.y,px=point.x-t.pa.x,py=point.y-t.pa.y,det=bx*cy-by*cx;
            if(Math.Abs(det)<1e-20||material.cull==2&&det>=0)continue;
            double v=(px*cy-py*cx)/det,w=(bx*py-by*px)/det,u=1-v-w;
            if(u<-.00001||v<-.00001||w<-.00001||u*t.pa.z+v*t.pb.z+w*t.pc.z>=point.z-.0001f)continue;
            Auto511VisibilityTests++;
            if(material.range.x>=material.cutoff)return false;
            var uv=t.ua*(float)u+t.ub*(float)v+t.uc*(float)w;var range=HeadArea505.SourceAlphaFootprint511(material.texture,uv);
            if(range.x>=material.cutoff)return false;
            if(range.y>=material.cutoff)Auto511AlphaUncertain++; // Preserve GPU decision; not certified opaque.
        }
        return true;
    }
    static void ReleaseVisibility511()
    {UseBodyRay512=false;ClearBody512();foreach(int at in blockerUsed511)blockerBins511[at]?.Clear();blockerUsed511.Clear();blockers511.Clear();Array.Clear(blockerMeshes511,0,blockerMeshes511.Length);alpha511=null;view511=null;}
}
