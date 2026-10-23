using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using FantasySurvival.WorldLighting;

public static class ExtractOrigins531B
{
    const string Root="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Origin531/Actual43_44_B/";
    const string Reference="C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Cloth527/FullLoopB/";
    [Serializable]class RefPose{public float phase;public string clip;}
    [Serializable]class PoseInfo{public int frame;public float requestedPhase,actualPhase,sourceFrame,evaluatedFrame,ortho;public string clip;public bool productClothEnabled,productCurveEnabled;public Vector3 rotation,playerPosition;public int segments,sourceLoops,sourcePoints,curvePoints;public double preprocessMs;}
    static bool armed,queued;static bool oldBg;static double deadline;static int frames;
    static void Status(string state,string error=""){File.WriteAllText(Root+"status.json","{\"status\":\""+state+"\",\"frames\":"+frames+",\"error\":\""+error.Replace("\\","/").Replace("\"","'").Replace("\r"," ").Replace("\n"," ")+"\",\"productEnabled\":false}");}
    static void V(BinaryWriter w,Vector2 p){w.Write(p.x);w.Write(p.y);}
    static void Matrix(BinaryWriter w,Matrix4x4 m){for(int i=0;i<16;i++)w.Write(m[i]);}
    static void Model(Full319View335 f,OpacityRegion525 op)
    {
        var mesh=f.motion.surface.source[0].sharedMesh;var v=mesh.vertices;var uv=mesh.uv;var weights=mesh.boneWeights;
        var canonical=new int[v.Length];var weld=new Dictionary<(Vector3,BoneWeight),int>();
        for(int i=0;i<v.Length;i++){var key=(v[i],weights[i]);if(!weld.TryGetValue(key,out int id))weld.Add(key,id=i);canonical[i]=id;}
        var tags=new Dictionary<int,int[]>();var headers=new Dictionary<int,int>();using(var r=new BinaryReader(new MemoryStream(f.bodyParts.bytes))){r.ReadInt32();int ns=r.ReadInt32();for(int j=0;j<ns;j++){int declared=r.ReadInt32();int sm=j,nt=r.ReadInt32();headers.Add(sm,declared);var ids=new int[nt*3];for(int k=0;k<ids.Length;k++)ids[k]=r.ReadInt32();if(!ids.SequenceEqual(mesh.GetIndices(sm)))throw new Exception("531 part/source topology mismatch");var t=new int[nt*3];for(int k=0;k<t.Length;k++)t[k]=r.ReadInt32();tags.Add(sm,t);}}
        using(var w=new BinaryWriter(File.Create(Root+"MODEL531.bin")))
        {
            w.Write(531);w.Write(v.Length);
            for(int i=0;i<v.Length;i++){w.Write(v[i].x);w.Write(v[i].y);w.Write(v[i].z);V(w,uv[i]);w.Write(canonical[i]);}
            w.Write(mesh.subMeshCount);for(int sm=0;sm<mesh.subMeshCount;sm++){var ids=mesh.GetIndices(sm);w.Write(sm);w.Write(headers[sm]);w.Write(ids.Length);foreach(int id in ids)w.Write(id);var t=tags[sm];w.Write(t.Length);foreach(int id in t)w.Write(id);}
            w.Write(op.Anchors.Count);foreach(var a in op.Anchors){w.Write(a.a);w.Write(a.b);w.Write(a.c);w.Write(a.weights.x);w.Write(a.weights.y);w.Write(a.weights.z);}
            w.Write(op.Segments.Count);foreach(var s in op.Segments){w.Write(s.primitive);w.Write(s.a);w.Write(s.b);w.Write(s.opacity);}
        }
    }
    static void Tick()
    {
        if(!armed)return;
        if(!EditorApplication.isPlaying||EditorApplication.timeSinceStartup>deadline){Finish("FAILED","single setup deadline/Play ended");return;}
        var g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected)return;
        if(queued)return;queued=true;EditorApplication.isPaused=true;EditorApplication.delayCall+=Work;
    }
    static void Work()
    {
        Gameplay397 g=null;Animator a=null;float loc=0,speed=0,time=0,sourceFrame=0;int state=0;Quaternion rotation=Quaternion.identity;bool anim=false,moveEnabled=false;PlayerMovement move=null;
        try
        {
            g=UnityEngine.Object.FindFirstObjectByType<Gameplay397>();if(!g||!g.connected||g.runInputTest)throw new Exception("531 expected connected original runtime, no synthetic input test");
            var h=g.player.host;var f=h.main;var m=f.motion;a=m.animation.target;move=g.player.player.GetComponent<PlayerMovement>();
            if(ClothRegion524.Enabled||ClothRegion524.UseOpacityCurves527||HeadRegion502.Enabled||h.post.candidateEnabled)throw new Exception("531 preserve existing experiment flags");
            if(f.validateRender!=null&&f.validateRender.GetInvocationList().Any(x=>!(x.Target is PostView366)))throw new Exception("531 other render hook active");
            loc=a.GetFloat("LocomotionSpeed");speed=a.speed;anim=a.enabled;rotation=a.transform.rotation;var initial=a.GetCurrentAnimatorStateInfo(0);state=initial.fullPathHash;time=initial.normalizedTime;sourceFrame=m.sourceFrame;moveEnabled=move.enabled;move.enabled=false;
            var op=new OpacityRegion525(m.surface.source[0].sharedMesh,3,m.materials[3]);Model(f,op);
            foreach(int frame in new[]{43,44})
            {
                var reference=JsonUtility.FromJson<RefPose>(File.ReadAllText(Reference+frame.ToString("D3")+"_probe.json"));
                a.enabled=true;a.speed=0;a.SetFloat("LocomotionSpeed",1);a.Play(state,0,reference.phase);a.Update(0);a.transform.rotation=Quaternion.Euler(0,80,0);
                g.player.avatar.position=g.player.feet.position;g.player.avatar.localScale=Vector3.one*(g.player.bodyHeight/g.player.sourceHeight);
                m.sourceFrame=reference.phase*40;g.player.bake.Evaluate();h.RenderFrame();
                var clip=a.GetCurrentAnimatorClipInfo(0)[0].clip.name;if(clip!=reference.clip)throw new Exception("531 actual Walk clip mismatch:"+clip);
                var mf=m.surface.outputs[0];var original=mf.sharedMesh;var p=original.vertices.Select(mf.transform.TransformPoint).Select(f.Project).ToArray();
                var anchors=op.Anchors.Select(x=>p[x.a]*x.weights.x+p[x.b]*x.weights.y+p[x.c]*x.weights.z).ToArray();
                var emitted=op.Project(p,true);var loops=ClosedRegion524.BuildSegments(emitted);var fits=loops.Select(r=>ClosedRegion524.Fit(r,HeadRegion502.CurveError*(op.UsedCurveFit527 ? .5f : 1f))).ToArray();
                string prefix=Root+frame.ToString("D3");
                using(var w=new BinaryWriter(File.Create(prefix+"_PROJECTION.bin"))){w.Write(p.Length);foreach(var q in p)V(w,q);w.Write(anchors.Length);foreach(var q in anchors)V(w,q);w.Write(emitted.Count);foreach(var e in emitted){V(w,e.Item1);V(w,e.Item2);}Matrix(w,f.effectiveProjection);Matrix(w,m.camera.worldToCameraMatrix);Matrix(w,mf.transform.localToWorldMatrix);}
                using(var w=new BinaryWriter(File.Create(prefix+"_GEOMETRY.bin"))){foreach(var list in new[]{loops,fits.ToList()}){w.Write(list.Count);foreach(var r in list){w.Write(r.Length);foreach(var q in r)V(w,q);}}}
                var info=new PoseInfo{frame=frame,requestedPhase=reference.phase,actualPhase=Mathf.Repeat(a.GetCurrentAnimatorStateInfo(0).normalizedTime,1),sourceFrame=m.sourceFrame,evaluatedFrame=m.evaluatedFrame,clip=clip,ortho=m.camera.orthographicSize,rotation=a.transform.rotation.eulerAngles,playerPosition=g.player.player.position,productClothEnabled=ClothRegion524.Enabled,productCurveEnabled=ClothRegion524.UseOpacityCurves527,segments=emitted.Count,sourceLoops=loops.Count,sourcePoints=loops.Sum(r=>r.Length),curvePoints=fits.Sum(r=>r.Length),preprocessMs=op.PreprocessMs};File.WriteAllText(prefix+"_POSE.json",JsonUtility.ToJson(info,true));frames++;Status("EXTRACTING");
            }
            a.SetFloat("LocomotionSpeed",loc);a.speed=speed;a.Play(state,0,time);a.Update(0);a.transform.rotation=rotation;a.enabled=anim;move.enabled=moveEnabled;m.sourceFrame=sourceFrame;Finish("EXTRACTED");
        }
        catch(Exception e)
        {
            if(a){a.SetFloat("LocomotionSpeed",loc);a.speed=speed;if(state!=0){a.Play(state,0,time);a.Update(0);}a.transform.rotation=rotation;a.enabled=anim;}if(move)move.enabled=moveEnabled;Finish("FAILED",e.ToString());
        }
    }
    static void Finish(string status,string error="")
    {
        if(!armed)return;armed=false;EditorApplication.update-=Tick;EditorApplication.delayCall-=Work;Application.runInBackground=oldBg;Status(status,error);EditorApplication.isPaused=false;if(EditorApplication.isPlaying)EditorApplication.isPlaying=false;
    }
    public static void Start()
    {
        if(Application.dataPath!="C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets"||!EditorApplication.isPlaying)throw new Exception("531 expected current Play");
        if(Directory.Exists(Root))throw new Exception("531 output exists; no duplicate extraction");Directory.CreateDirectory(Root);oldBg=Application.runInBackground;Application.runInBackground=true;armed=true;queued=false;frames=0;deadline=EditorApplication.timeSinceStartup+120;EditorApplication.update+=Tick;Status("WAITING_RUNTIME");EditorApplication.QueuePlayerLoopUpdate();
    }
}
