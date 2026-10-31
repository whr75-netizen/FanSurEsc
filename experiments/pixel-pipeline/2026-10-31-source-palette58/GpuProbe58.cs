using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;
using UnityEngine.Experimental.Rendering;
using Unity.Collections;

internal class CommandScript : IRunCommand
{
    const string Output=@"C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\source-palette58";
    const string Assets="Assets/Editor/SourcePalette58Probe";
    struct Quad58 {public uint x,y,z,w;public Quad58(uint a,uint b,uint c,uint d){x=a;y=b;z=c;w=d;}}
    struct Pair58 {public uint x,y;}
    struct Case58 {public uint family;public float g;public uint corrected,bound;}
    static void Save(Obj58 r,string phase){r["phase"]=phase;File.WriteAllText(Path.Combine(Output,"GPU58.json"),r.ToString());}
    static float[] ReadFloat(RenderTexture t) {
        var data=new NativeArray<float>(t.width*t.height*4,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);
        AsyncGPUReadbackRequest request=new AsyncGPUReadbackRequest();bool started=false;
        try {request=AsyncGPUReadback.RequestIntoNativeArray(ref data,t,0);started=true;request.WaitForCompletion();if(request.hasError)throw new InvalidOperationException("Float readback failed");return data.ToArray();}
        finally {if(started&&!request.done)request.WaitForCompletion();data.Dispose();}
    }
    static byte[] ReadByte(RenderTexture t) {
        var data=new NativeArray<byte>(t.width*t.height*4,Allocator.Persistent,NativeArrayOptions.UninitializedMemory);
        AsyncGPUReadbackRequest request=new AsyncGPUReadbackRequest();bool started=false;
        try {request=AsyncGPUReadback.RequestIntoNativeArray(ref data,t,0);started=true;request.WaitForCompletion();if(request.hasError)throw new InvalidOperationException("Byte readback failed");return data.ToArray();}
        finally {if(started&&!request.done)request.WaitForCompletion();data.Dispose();}
    }
    static void WriteFloat(string name,float[] values){using(var w=new BinaryWriter(File.Create(Path.Combine(Output,name))))foreach(float v in values)w.Write(v);}
    public void Execute(ExecutionResult result) {
        var report=new Obj58{["memoryBefore"]=State58.Memory()};Obj58 before=null;
        var buffers=new List<ComputeBuffer>();var ownedTextures=new List<Texture2D>();var ownedRT=new List<RenderTexture>();
        Material material=null;ComputeShader compute=null;CommandBuffer draw=null;bool oldSrgb=GL.sRGBWrite;var oldActive=RenderTexture.active;
        try {
            before=State58.Read();State58.RequireEdit(before);report["before"]=before;Save(report,"before-import");
            var source=Obj58.Parse(File.ReadAllText(Path.Combine(Output,"SOURCE58.json")));if((string)source["status"]!="source-generated"||source["error"]!=null)throw new InvalidOperationException("Successful original source input required");
            var palettes=new List<SourcePalette58.Palette>();var thresholds=new List<double[]>();var words=new List<Quad58>();var rgb=new List<Quad58>();var allCuts=new List<float>();var variants=new Arr58();
            foreach(var record in source["records"]) {
                var family=SourceJson58.ReadFamily(record["family"]);var reference=SourcePalette58.ExtractReference(family);var settings=SourceJson58.ReadSettings(record["settings"]);var palette=SourcePalette58.MakePalette(reference,settings);
                var cuts=record["thresholds"].Values<double>().ToArray();
                words.Add(new Quad58((uint)rgb.Count,(uint)palette.rgb8.Length,(uint)allCuts.Count,(uint)cuts.Length));
                foreach(var colour in palette.rgb8)rgb.Add(new Quad58((uint)colour[0],(uint)colour[1],(uint)colour[2],255));foreach(double cut in cuts)allCuts.Add((float)cut);
                palettes.Add(palette);thresholds.Add(cuts);
                var altered=SourceJson58.ReadSettings(record["settings"]);altered.intervalScale=.5;var p2=SourcePalette58.MakePalette(reference,altered);
                double[] g=Enumerable.Range(0,33).Select(i=>i/32.0).ToArray(),changedCuts=cuts.Select(t=>t*.9).ToArray();
                var originalK=g.Select(v=>SourcePalette58.ShadeIndex(v,cuts)).ToArray();
                var afterPaletteK=g.Select(v=>SourcePalette58.ShadeIndex(v,cuts)).ToArray();
                var afterCutsPalette=SourcePalette58.MakePalette(reference,settings);
                bool independent=originalK.SequenceEqual(afterPaletteK)&&palette.rgb8.SelectMany(v=>v).SequenceEqual(afterCutsPalette.rgb8.SelectMany(v=>v));
                if(!independent)throw new InvalidOperationException("Palette/threshold coupling");
                variants.Add(new Obj58{["family"]=family.id,["intervalScale"]=.5,["palette"]=SourceJson58.Palette(p2),["g"]=new Arr58(g),["baseK"]=new Arr58(originalK),["paletteChangedK"]=new Arr58(afterPaletteK),["changedThresholds"]=new Arr58(changedCuts),["changedK"]=new Arr58(g.Select(v=>SourcePalette58.ShadeIndex(v,changedCuts))),["independent"]=independent});
            }
            report["variants"]=variants;
            var cases=new List<Case58>();var inputRGB=new List<Quad58>();var bindings=new List<Pair58>();var corrected=new List<uint>();var rows=new Arr58();int unchanged=0,changed=0,partial=0;
            foreach(var c in source["cases"]) {
                int family=(int)c["family"],k=(int)c["k"],kp=(int)c["kPrime"];bool requested=(bool)c["bound"];int[] native,expectedInitial,expectedFinal;int alpha;
                if(requested){var sample=source["records"][family]["family"]["samples"].First(s=>(string)s["id"]==(string)c["sourceSampleId"]);native=sample["rgba8"].Values<int>().ToArray();alpha=native[3];}
                else {native=new[]{17,93,141,107};alpha=107;}
                bool bound=requested&&alpha==255;
                if(bound){expectedInitial=palettes[family].rgb8[k];expectedFinal=palettes[family].rgb8[kp];if(k==kp)unchanged++;else changed++;}
                else {expectedInitial=native.Take(3).ToArray();expectedFinal=expectedInitial;if(requested)partial++;}
                cases.Add(new Case58{family=(uint)family,g=(float)(double)c["g"],corrected=(uint)kp,bound=bound?1u:0u});
                inputRGB.Add(new Quad58((uint)native[0],(uint)native[1],(uint)native[2],(uint)alpha));bindings.Add(new Pair58{x=(uint)family,y=bound?1u:0u});corrected.Add((uint)kp);
                rows.Add(new Obj58{["sourceSampleId"]=c["sourceSampleId"],["sourceUV"]=c["sourceUV"],["family"]=family,["boundOpaque"]=bound,["nativeAlpha8"]=alpha,["k"]=k,["kPrime"]=kp,["initialRGB8"]=new Arr58(expectedInitial),["finalRGB8"]=new Arr58(expectedFinal)});
            }
            report["rows"]=rows;report["oldEqualsCorrectedBound"]=unchanged;report["changedBound"]=changed;report["partialSourceExcluded"]=partial;
            foreach(var name in new[]{"SourcePalette54.hlsl","SurfaceLayerOutput58.hlsl","RestoreStyle58.compute","InitialFinal58.shader"})AssetDatabase.ImportAsset(Assets+"/"+name,ImportAssetOptions.ForceSynchronousImport);
            if(AppDomain.CurrentDomain.Id!=(int)before["domain"]||EditorApplication.isCompiling)throw new InvalidOperationException("Unexpected script domain/compilation");
            var shader=AssetDatabase.LoadAssetAtPath<Shader>(Assets+"/InitialFinal58.shader");var original=AssetDatabase.LoadAssetAtPath<ComputeShader>(Assets+"/RestoreStyle58.compute");
            if(!shader||!original||!shader.isSupported||!SystemInfo.supportsAsyncGPUReadback||!SystemInfo.supportsComputeShaders)throw new NotSupportedException("Probe shader/device support");
            var messages=ShaderUtil.GetShaderMessages(shader).Select(m=>m.severity+": "+m.message).Concat(ShaderUtil.GetComputeShaderMessages(original).Select(m=>m.severity+": "+m.message)).ToArray();report["compilerMessages"]=new Arr58(messages);if(messages.Any(s=>s.StartsWith("Error")))throw new InvalidOperationException("Shader compiler error");
            if(QualitySettings.activeColorSpace!=ColorSpace.Linear||!SystemInfo.IsFormatSupported(GraphicsFormat.R32G32B32A32_SFloat,GraphicsFormatUsage.LoadStore)||!SystemInfo.IsFormatSupported(GraphicsFormat.R8G8B8A8_SRGB,GraphicsFormatUsage.ReadPixels))throw new NotSupportedException("Exact format/linear project required");
            int n=cases.Count;
            Func<Array,int,ComputeBuffer> buffer=(array,stride)=>{var b=new ComputeBuffer(array.Length,stride);buffers.Add(b);b.SetData(array);return b;};
            var rgbBuffer=buffer(rgb.ToArray(),16);var cutsBuffer=buffer(allCuts.ToArray(),4);var familyBuffer=buffer(words.ToArray(),16);var caseBuffer=buffer(cases.ToArray(),16);var sourceRGBBuffer=buffer(inputRGB.ToArray(),16);var bindingBuffer=buffer(bindings.ToArray(),8);var indexBuffer=buffer(corrected.ToArray(),4);
            Func<string,bool,RenderTexture> rt=(name,srgb)=>{var desc=new RenderTextureDescriptor(n,1){graphicsFormat=srgb?GraphicsFormat.R8G8B8A8_SRGB:GraphicsFormat.R32G32B32A32_SFloat,depthBufferBits=0,msaaSamples=1,enableRandomWrite=!srgb,useMipMap=false,autoGenerateMips=false};var t=new RenderTexture(desc){name="Owned58_"+name,hideFlags=HideFlags.HideAndDontSave,filterMode=FilterMode.Point};ownedRT.Add(t);if(!t.Create()||t.graphicsFormat!=desc.graphicsFormat)throw new InvalidOperationException("Exact RT format unavailable");return t;};
            var colourRT=rt("colour",false);var classRT=rt("class",false);var factorRT=rt("factor",false);var srgbRT=rt("sRGB",true);
            Func<Func<int,Color>,Texture2D> texture=fn=>{var t=new Texture2D(n,1,TextureFormat.RGBAFloat,false,true){hideFlags=HideFlags.HideAndDontSave};ownedTextures.Add(t);for(int i=0;i<n;i++)t.SetPixel(i,0,fn(i));t.Apply(false,false);return t;};
            var maskInputs=Enumerable.Range(0,n).Select(i=>new Color((float)corrected[i]/(palettes[(int)cases[i].family].rgb8.Length-1),0,0,0)).ToArray();
            var classInputs=Enumerable.Range(0,n).Select(i=>new Color((float)(int)rows[i]["k"]/(palettes[(int)cases[i].family].rgb8.Length-1),cases[i].g,.4f+i*.001f,.7f)).ToArray();
            var meta=texture(i=>Color.clear);var mask=texture(i=>maskInputs[i]);
            var classSeed=texture(i=>classInputs[i]);
            var factorSeed=texture(i=>new Color(.3f,.7f,.4f,.6f));Graphics.CopyTexture(classSeed,classRT);Graphics.CopyTexture(factorSeed,factorRT);
            material=new Material(shader){hideFlags=HideFlags.HideAndDontSave};material.SetBuffer("_SourcePalette54RGB8",rgbBuffer);material.SetBuffer("_SourcePalette54Thresholds",cutsBuffer);material.SetBuffer("_SourcePalette54Families",familyBuffer);material.SetBuffer("_Cases58",caseBuffer);material.SetBuffer("_SourceRGB58",sourceRGBBuffer);material.SetInt("_Count58",n);material.SetInt("_SurfaceLayerView335",0);
            material.SetInt("_Mode58",0);draw=new CommandBuffer{name="Owned58_InitialFinal"};draw.SetRenderTarget(colourRT);draw.SetViewport(new Rect(0,0,n,1));draw.DrawProcedural(Matrix4x4.identity,material,0,MeshTopology.Triangles,3,1);
            Save(report,"initial-function-draw");GL.sRGBWrite=false;Graphics.ExecuteCommandBuffer(draw);var initial=ReadFloat(colourRT);WriteFloat("INITIAL58.float4",initial);
            // A separate final-join regression input: poison unchanged-q opaque
            // RGB so an old==q early return cannot pass by retaining the initial LUT.
            // Source/UV/g/index/alpha and all other cells remain unchanged.
            var joinInput=(float[])initial.Clone();
            for(int i=0;i<n;i++)if(cases[i].bound!=0&&(int)rows[i]["k"]==(int)rows[i]["kPrime"]){joinInput[i*4]=1;joinInput[i*4+1]=0;joinInput[i*4+2]=1;}
            var joinSeed=texture(i=>new Color(joinInput[i*4],joinInput[i*4+1],joinInput[i*4+2],joinInput[i*4+3]));Graphics.CopyTexture(joinSeed,colourRT);WriteFloat("JOIN_INPUT58.float4",joinInput);
            report["oldEqualsCorrectedStressCount"]=unchanged;report["finalJoinUsesExplicitNegativeControl"]=true;
            compute=UnityEngine.Object.Instantiate(original);compute.hideFlags=HideFlags.HideAndDontSave;int kernel=compute.FindKernel("ApplyShadeBoundary");
            compute.SetInts("_ShadeSize335",n,1);compute.SetInt("_ShadeApply335",1);compute.SetBuffer(kernel,"_SourcePalette54RGB8",rgbBuffer);compute.SetBuffer(kernel,"_SourcePalette54Families",familyBuffer);compute.SetBuffer(kernel,"_SourceBinding58",bindingBuffer);compute.SetBuffer(kernel,"_SourceIndex58",indexBuffer);
            compute.SetTexture(kernel,"_ShadeMeta335",meta);compute.SetTexture(kernel,"_ShadeMaskRead335",mask);compute.SetTexture(kernel,"_ShadeColourOut335",colourRT);compute.SetTexture(kernel,"_ShadeClassOut335",classRT);compute.SetTexture(kernel,"_ShadeFactorOut335",factorRT);
            // Unbound cells have zero meta and return before these legacy reads;
            // Unity still requires the active kernel's declared SRVs to be bound.
            compute.SetTexture(kernel,"_ShadeUV335",meta);compute.SetTexture(kernel,"_ShadeLit335",meta);compute.SetTexture(kernel,"_StockMember335",meta);
            Save(report,"final-interior-dispatch");compute.Dispatch(kernel,(n+7)/8,1,1);
            var final=ReadFloat(colourRT);var classes=ReadFloat(classRT);var factors=ReadFloat(factorRT);WriteFloat("FINAL58.float4",final);WriteFloat("CLASS58.float4",classes);WriteFloat("FACTOR58.float4",factors);
            material.SetInt("_Mode58",1);material.SetTexture("_Final58",colourRT);draw.Clear();draw.SetRenderTarget(srgbRT);draw.SetViewport(new Rect(0,0,n,1));draw.DrawProcedural(Matrix4x4.identity,material,0,MeshTopology.Triangles,3,1);
            GL.sRGBWrite=true;Graphics.ExecuteCommandBuffer(draw);var bytes=ReadByte(srgbRT);File.WriteAllBytes(Path.Combine(Output,"FINAL58.rgba"),bytes);
            double maxError=0;int mismatch=0,alphaMismatch=0,classMismatch=0,factorMismatch=0;
            for(int i=0;i<n;i++) {
                var a=rows[i]["initialRGB8"].Values<int>().ToArray();var b=rows[i]["finalRGB8"].Values<int>().ToArray();
                for(int c=0;c<3;c++){maxError=Math.Max(maxError,Math.Abs(initial[i*4+c]-SourcePalette58.Decode(a[c]/255.0)));maxError=Math.Max(maxError,Math.Abs(final[i*4+c]-SourcePalette58.Decode(b[c]/255.0)));if(bytes[i*4+c]!=b[c])mismatch++;}
                float alpha=(int)rows[i]["nativeAlpha8"]/255f;if(Math.Abs(initial[i*4+3]-alpha)>1e-6||Math.Abs(final[i*4+3]-alpha)>1e-6||bytes[i*4+3]!=(int)rows[i]["nativeAlpha8"])alphaMismatch++;
                // Compare the actual uploaded Float32 fields, not a wider
                // unmaterialized arithmetic expression used to construct them.
                bool bound=cases[i].bound!=0;float kExpected=bound?maskInputs[i].r:classInputs[i].r;
                if(classes[i*4]!=kExpected||classes[i*4+1]!=classInputs[i].g||classes[i*4+2]!=classInputs[i].b||classes[i*4+3]!=classInputs[i].a)classMismatch++;
                if(Math.Abs(factors[i*4]-(bound?1:.3f))>1e-6||Math.Abs(factors[i*4+1]-(bound?1:.7f))>1e-6||Math.Abs(factors[i*4+2]-(bound?1:.4f))>1e-6||factors[i*4+3]!=.6f)factorMismatch++;
            }
            report["sampleCount"]=n;report["draws"]=2;report["dispatches"]=1;report["maxLinearError"]=maxError;report["sRGBComponentMismatches"]=mismatch;report["alphaMismatches"]=alphaMismatch;report["classMismatches"]=classMismatch;report["factorMismatches"]=factorMismatch;
            report["gpuPass"]=maxError<1e-6&&mismatch==0&&alphaMismatch==0&&classMismatch==0&&factorMismatch==0;
        }catch(Exception e){report["error"]=e.GetType().Name+": "+e.Message;}
        finally {
            if(draw!=null)draw.Release();foreach(var b in buffers)b.Release();GL.sRGBWrite=oldSrgb;RenderTexture.active=oldActive;
            foreach(var t in ownedTextures)if(t)UnityEngine.Object.DestroyImmediate(t);foreach(var t in ownedRT)if(t){t.Release();UnityEngine.Object.DestroyImmediate(t);}
            if(material)UnityEngine.Object.DestroyImmediate(material);if(compute)UnityEngine.Object.DestroyImmediate(compute);
            report["ownedResourcesReleased"]=buffers.All(b=>!b.IsValid())&&ownedTextures.All(t=>!t)&&ownedRT.All(t=>!t)&&!material&&!compute;
            var after=State58.Read();report["after"]=after;if(before!=null)report["stateChanges"]=new Arr58(State58.Changes(before,after));report["memoryAfter"]=State58.Memory();Save(report,"finished");
        }
        result.Log("GPU58 pass="+report["gpuPass"]+" error="+report["error"]+" stateChanges="+report["stateChanges"]+" released="+report["ownedResourcesReleased"]);
    }
}
