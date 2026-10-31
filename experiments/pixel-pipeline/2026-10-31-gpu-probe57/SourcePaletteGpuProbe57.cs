// Run through existing Unity_RunCommand; keep OUTSIDE Assets to avoid script import/domain reload.
// No scene render, Play, asset save, global refresh, or legacy HairFinal/G/lighting path.
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Experimental.Rendering;
using UnityEngine.Profiling;
using UnityEngine.SceneManagement;
using Unity.Collections;

internal class CommandScript : IRunCommand
{
    const string Output = @"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\gpu-probe57";
    const string Assets = "Assets/Editor/SourcePalette54Probe";
    // C# value structs have sequential layout by default; no interop API or attribute.
    struct Sample57 { public uint family; public float g; }
    struct Quad57 { public uint x,y,z,w; public Quad57(uint a,uint b,uint c,uint d){x=a;y=b;z=c;w=d;} }
    [Serializable] class Safety57 {
        public int domainId; public string project, colourSpace;
        public bool playing, paused, transitioning, compiling, updating;
        public string[] dirtyObjectStateLines, diskFileLines, sceneStateLines, buildScenes, renderTextureIds;
    }
    [Serializable] class Report57 {
        public string utc, phase, error, graphicsDevice, colourSpace, rtFormat;
        public int domainBefore, domainAfter, samples, computeMismatches, rtMismatches, dispatches, draws;
        public bool preservationBefore, preservationAfter, ownedResourcesReleased, renderTextureIdentitiesSame;
        public long allocatedBefore, allocatedAfter, reservedBefore, reservedAfter, monoBefore, monoAfter;
        public string[] rows, compilerMessages, violations;
    }
    static string Hash(byte[] data) { using(var h=SHA256.Create()) return BitConverter.ToString(h.ComputeHash(data)).Replace("-","").ToLowerInvariant(); }
    static string[] DirtyLines() {
        return Resources.FindObjectsOfTypeAll<UnityEngine.Object>()
            .Where(o=>o && EditorUtility.IsPersistent(o) && EditorUtility.IsDirty(o))
            .Where(o=>AssetDatabase.GetAssetPath(o).StartsWith("Assets/") || AssetDatabase.GetAssetPath(o).StartsWith("ProjectSettings/"))
            .Select(o=>new { path=AssetDatabase.GetAssetPath(o), entity=o.GetEntityId().ToString(), value=string.Join("\t",new[]{
                AssetDatabase.GetAssetPath(o),AssetDatabase.AssetPathToGUID(AssetDatabase.GetAssetPath(o)),o.GetEntityId().ToString(),o.GetType().FullName,o.name,
                Hash(System.Text.Encoding.UTF8.GetBytes(EditorJsonUtility.ToJson(o))),"",EditorJsonUtility.ToJson(o)}) })
            .OrderBy(r=>r.path).ThenBy(r=>r.entity).Select(r=>r.value).ToArray();
    }
    static string[] SceneLines() {
        var active=SceneManager.GetActiveScene();
        return Enumerable.Range(0,SceneManager.sceneCount).Select(i=>SceneManager.GetSceneAt(i)).Select(s=>s.path+"\t"+s.name+"\t"+s.isLoaded+"\t"+s.isDirty+"\t"+(s==active)+"\t"+
            string.Join(",",s.isLoaded?s.GetRootGameObjects().Select(o=>o.GetEntityId().ToString()).OrderBy(i=>i).ToArray():new string[0])).ToArray();
    }
    static string[] Violations(Safety57 s) {
        var failures=new System.Collections.Generic.List<string>();
        if(s.project!=Application.dataPath) failures.Add("project changed");
        if(s.domainId!=AppDomain.CurrentDomain.Id) failures.Add("script domain changed");
        if(EditorApplication.isPlaying || EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isPaused!=s.paused) failures.Add("Play/pause changed");
        if(EditorApplication.isCompiling || EditorApplication.isUpdating) failures.Add("Editor compiling/updating");
        if(!DirtyLines().SequenceEqual(s.dirtyObjectStateLines)) failures.Add("dirty object content/identity/list changed");
        if(!SceneLines().SequenceEqual(s.sceneStateLines)) failures.Add("scene/root identity changed");
        if(!EditorBuildSettings.scenes.Select(v=>(v.enabled?"1":"0")+"\t"+v.path+"\t"+v.guid).SequenceEqual(s.buildScenes)) failures.Add("build scene list changed");
        foreach(var line in s.diskFileLines) { var parts=line.Split('\t'); if(!File.Exists(parts[0]) || Hash(File.ReadAllBytes(parts[0]))!=parts[1]) failures.Add("file changed: "+parts[0]); }
        return failures.ToArray();
    }
    static Quad57 Read4(BinaryReader r) { return new Quad57(r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32(),r.ReadUInt32()); }
    static void Phase(Report57 r,string phase) {r.phase=phase;File.WriteAllText(Path.Combine(Output,"GPU_RESULT.json"),JsonUtility.ToJson(r,true));}
    public void Execute(ExecutionResult result)
    {
        var report=new Report57 {utc=DateTime.UtcNow.ToString("O"),domainBefore=AppDomain.CurrentDomain.Id,
            graphicsDevice=SystemInfo.graphicsDeviceType.ToString(),colourSpace=QualitySettings.activeColorSpace.ToString(),
            allocatedBefore=Profiler.GetTotalAllocatedMemoryLong(),reservedBefore=Profiler.GetTotalReservedMemoryLong(),monoBefore=Profiler.GetMonoUsedSizeLong()};
        var safety=JsonUtility.FromJson<Safety57>(File.ReadAllText(Path.Combine(Output,"SAFETY_BEFORE.json")));
        ComputeBuffer palette=null,cuts=null,families=null,cases=null,output=null;
        ComputeShader compute=null; Material material=null; RenderTexture rt=null; CommandBuffer command=null;
        NativeArray<uint> gpu=new NativeArray<uint>(); NativeArray<byte> pixels=new NativeArray<byte>();
        AsyncGPUReadbackRequest computeRequest=new AsyncGPUReadbackRequest(),rtRequest=new AsyncGPUReadbackRequest();
        bool computeRequested=false,rtRequested=false;
        bool oldSRGB=GL.sRGBWrite; var oldActive=RenderTexture.active;
        var beforeRTs=Resources.FindObjectsOfTypeAll<RenderTexture>().Select(t=>t.GetEntityId().ToString()).OrderBy(i=>i).ToArray();
        try {
            Phase(report,"safety-check");
            if(safety.dirtyObjectStateLines==null || safety.dirtyObjectStateLines.Length==0) throw new InvalidOperationException("Missing dirty content snapshot");
            report.violations=Violations(safety);report.preservationBefore=report.violations.Length==0;
            if(!report.preservationBefore) throw new InvalidOperationException(string.Join(";",report.violations));
            if(QualitySettings.activeColorSpace!=ColorSpace.Linear) throw new InvalidOperationException("This sRGB output probe requires the unchanged Linear project");
            if(!SystemInfo.supportsComputeShaders || !SystemInfo.supportsAsyncGPUReadback) throw new NotSupportedException("Compute/readback unsupported");
            if(!SystemInfo.IsFormatSupported(GraphicsFormat.R8G8B8A8_SRGB,GraphicsFormatUsage.Render) ||
                !SystemInfo.IsFormatSupported(GraphicsFormat.R8G8B8A8_SRGB,GraphicsFormatUsage.ReadPixels)) throw new NotSupportedException("sRGB render/readback format unsupported");
            Quad57[] colours,familyData,expected;float[] thresholds;Sample57[] samples;
            using(var reader=new BinaryReader(File.OpenRead(Path.Combine(Output,"PACKET57.bin")))) {
                if(reader.ReadUInt32()!=0x37504753 || reader.ReadUInt32()!=1) throw new InvalidOperationException("Packet header");
                int np=reader.ReadInt32(),nt=reader.ReadInt32(),nf=reader.ReadInt32(),n=reader.ReadInt32();
                if(np!=12 || nt!=9 || nf!=3 || n!=30) throw new InvalidOperationException("Unexpected packet shape");
                colours=Enumerable.Range(0,np).Select(i=>Read4(reader)).ToArray(); thresholds=Enumerable.Range(0,nt).Select(i=>reader.ReadSingle()).ToArray();
                familyData=Enumerable.Range(0,nf).Select(i=>Read4(reader)).ToArray();
                samples=Enumerable.Range(0,n).Select(i=>new Sample57 {family=reader.ReadUInt32(),g=reader.ReadSingle()}).ToArray();
                expected=Enumerable.Range(0,n).Select(i=>Read4(reader)).ToArray();
                if(reader.BaseStream.Position!=reader.BaseStream.Length) throw new InvalidOperationException("Trailing data");
            }
            report.samples=samples.Length;
            Phase(report,"targeted-shader-import-no-csharp");
            foreach(var name in new[]{"SourcePalette54.hlsl","SourcePaletteProbe57.compute","SourcePaletteOffscreen57.shader"})
                AssetDatabase.ImportAsset(Assets+"/"+name,ImportAssetOptions.ForceSynchronousImport);
            if(AppDomain.CurrentDomain.Id!=report.domainBefore || EditorApplication.isCompiling) throw new InvalidOperationException("Unexpected script compilation/domain reload");
            var importedCompute=AssetDatabase.LoadAssetAtPath<ComputeShader>(Assets+"/SourcePaletteProbe57.compute");
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(Assets+"/SourcePaletteOffscreen57.shader");
            if(!importedCompute || !shader || !shader.isSupported) throw new InvalidOperationException("Probe shaders unavailable/unsupported");
            report.compilerMessages=ShaderUtil.GetComputeShaderMessages(importedCompute).Select(m=>m.severity+": "+m.message)
                .Concat(ShaderUtil.GetShaderMessages(shader).Select(m=>m.severity+": "+m.message)).ToArray();
            if(report.compilerMessages.Any(m=>m.StartsWith("Error"))) throw new InvalidOperationException("Shader compiler error");
            compute=UnityEngine.Object.Instantiate(importedCompute);compute.hideFlags=HideFlags.HideAndDontSave;
            material=new Material(shader) {hideFlags=HideFlags.HideAndDontSave};
            palette=new ComputeBuffer(colours.Length,16);palette.SetData(colours);
            cuts=new ComputeBuffer(thresholds.Length,4);cuts.SetData(thresholds);
            families=new ComputeBuffer(familyData.Length,16);families.SetData(familyData);
            cases=new ComputeBuffer(samples.Length,8);cases.SetData(samples);
            output=new ComputeBuffer(samples.Length,16);
            int kernel=compute.FindKernel("Probe57");
            compute.SetBuffer(kernel,"_SourcePalette54RGB8",palette);compute.SetBuffer(kernel,"_SourcePalette54Thresholds",cuts);
            compute.SetBuffer(kernel,"_SourcePalette54Families",families);compute.SetBuffer(kernel,"_Cases57",cases);compute.SetBuffer(kernel,"_Output57",output);compute.SetInt("_Count57",samples.Length);
            Phase(report,"single-compute-dispatch");
            compute.Dispatch(kernel,1,1,1);report.dispatches=1;
            gpu=new NativeArray<uint>(samples.Length*4,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);
            computeRequest=AsyncGPUReadback.RequestIntoNativeArray(ref gpu,output);computeRequested=true;computeRequest.WaitForCompletion();
            if(computeRequest.hasError) throw new InvalidOperationException("Compute readback failed");
            material.SetBuffer("_SourcePalette54RGB8",palette);material.SetBuffer("_SourcePalette54Thresholds",cuts);
            material.SetBuffer("_SourcePalette54Families",families);material.SetBuffer("_Cases57",cases);material.SetInt("_Count57",samples.Length);
            var desc=new RenderTextureDescriptor(samples.Length,1) {graphicsFormat=GraphicsFormat.R8G8B8A8_SRGB,depthBufferBits=0,msaaSamples=1,useMipMap=false,autoGenerateMips=false};
            rt=new RenderTexture(desc) {name="Owned_SourcePalette57_30x1",hideFlags=HideFlags.HideAndDontSave,filterMode=FilterMode.Point,wrapMode=TextureWrapMode.Clamp};
            if(!rt.Create() || rt.graphicsFormat!=GraphicsFormat.R8G8B8A8_SRGB) throw new InvalidOperationException("Exact sRGB RT creation failed");
            report.rtFormat=rt.graphicsFormat.ToString();
            command=new CommandBuffer {name="Owned_SourcePalette57_OneDraw"};
            command.SetRenderTarget(rt);command.SetViewport(new Rect(0,0,samples.Length,1));command.ClearRenderTarget(false,true,Color.clear);
            command.DrawProcedural(Matrix4x4.identity,material,0,MeshTopology.Triangles,3,1);
            Phase(report,"single-offscreen-draw");
            GL.sRGBWrite=true;Graphics.ExecuteCommandBuffer(command);report.draws=1;GL.sRGBWrite=oldSRGB;
            pixels=new NativeArray<byte>(samples.Length*4,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);
            rtRequest=AsyncGPUReadback.RequestIntoNativeArray(ref pixels,rt,0);rtRequested=true;rtRequest.WaitForCompletion();
            if(rtRequest.hasError) throw new InvalidOperationException("RT readback failed");
            var lines=new System.Collections.Generic.List<string>();
            for(int i=0;i<samples.Length;i++) {
                var e=expected[i]; uint[] actual={gpu[i*4],gpu[i*4+1],gpu[i*4+2],gpu[i*4+3]};
                int[] expect={(int)e.x,(int)e.y,(int)e.z,(int)e.w}; byte[] shown={pixels[i*4],pixels[i*4+1],pixels[i*4+2],pixels[i*4+3]};
                if(Enumerable.Range(0,4).Any(c=>actual[c]!=(uint)expect[c])) report.computeMismatches++;
                if(Enumerable.Range(0,4).Any(c=>shown[c]!=expect[c])) report.rtMismatches++;
                lines.Add(i+"\t"+samples[i].family+"\t"+samples[i].g.ToString("R",System.Globalization.CultureInfo.InvariantCulture)+"\t"+
                    string.Join(",",expect)+"\t"+string.Join(",",actual)+"\t"+string.Join(",",shown));
            }
            report.rows=lines.ToArray();
            File.WriteAllBytes(Path.Combine(Output,"RT57.rgba"),pixels.ToArray());
            using(var writer=new BinaryWriter(File.Create(Path.Combine(Output,"COMPUTE57.uint4")))) for(int i=0;i<gpu.Length;i++)writer.Write(gpu[i]);
            Phase(report,"outputs-saved");
        }
        catch(Exception e) {report.error=e.GetType().Name+": "+e.Message;}
        finally {
            // Wait only for this command's requests before disposing directly owned arrays.
            if(computeRequested && !computeRequest.done) computeRequest.WaitForCompletion();
            if(rtRequested && !rtRequest.done) rtRequest.WaitForCompletion();
            if(gpu.IsCreated)gpu.Dispose();if(pixels.IsCreated)pixels.Dispose();
            if(command!=null)command.Release();
            if(palette!=null)palette.Release();if(cuts!=null)cuts.Release();if(families!=null)families.Release();if(cases!=null)cases.Release();if(output!=null)output.Release();
            GL.sRGBWrite=oldSRGB;RenderTexture.active=oldActive;
            if(rt){rt.Release();UnityEngine.Object.DestroyImmediate(rt);} if(material)UnityEngine.Object.DestroyImmediate(material);if(compute)UnityEngine.Object.DestroyImmediate(compute);
            report.ownedResourcesReleased=!gpu.IsCreated && !pixels.IsCreated && !rt && !material && !compute &&
                (palette==null || !palette.IsValid()) && (cuts==null || !cuts.IsValid()) && (families==null || !families.IsValid()) &&
                (cases==null || !cases.IsValid()) && (output==null || !output.IsValid());
            report.renderTextureIdentitiesSame=Resources.FindObjectsOfTypeAll<RenderTexture>().Select(t=>t.GetEntityId().ToString()).OrderBy(i=>i).SequenceEqual(beforeRTs);
            report.domainAfter=AppDomain.CurrentDomain.Id;
            report.violations=Violations(safety);report.preservationAfter=report.violations.Length==0;
            report.allocatedAfter=Profiler.GetTotalAllocatedMemoryLong();report.reservedAfter=Profiler.GetTotalReservedMemoryLong();report.monoAfter=Profiler.GetMonoUsedSizeLong();
            Phase(report,"finished");
        }
        result.Log("GPU57 finished samples="+report.samples+" computeMismatch="+report.computeMismatches+" rtMismatch="+report.rtMismatches+
            " released="+report.ownedResourcesReleased+" preserved="+report.preservationAfter+" error="+report.error);
    }
}
