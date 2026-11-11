"""Prepare reviewed import and a TWO-frame normal phase capture. No execution."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
H=Path(__file__).resolve().parent;R=H.parents[1];FULL=R/'bounded-form115/runtime24/full-render24'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def body(p):return re.sub(r'(?m)^using [^;\n]+;\r?\n?','',p.read_text(encoding='utf-8-sig'))
def compile_cs(p):
    editor=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data');repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');out=p.parent/'build';out.mkdir(exist_ok=True)
    refs=[editor/'NetStandard/ref/2.1.0/netstandard.dll',editor/'NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll']+sorted((editor/'Managed/UnityEngine').glob('*.dll'))+sorted((repo/'Library/ScriptAssemblies').glob('*.dll'))
    args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:library','/langversion:latest','/out:'+str(out/(p.stem+'.dll'))]+['/reference:'+str(x)for x in refs]+[str(p)]
    rsp=out/(p.stem+'.rsp');rsp.write_text('\n'.join('"'+a+'"'for a in args),encoding='utf-8',newline='\n')
    q=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8')
    (p.parent/(p.stem+'.diagnostics.txt')).write_text(q.stdout+q.stderr,encoding='utf-8',newline='\n');assert q.returncode==0,q.stdout+q.stderr
def main():
    old=(FULL/'carrier-fix24/RUN_ImportFull24.cs.txt').read_text(encoding='utf-8');start=old.index('  public void Execute(ExecutionResult result){');tail=old.index('\nnamespace Prefix24 {',start)
    imp=H/'import';imp.mkdir(exist_ok=True);imported=(imp/'INTENT.json').exists()
    if imported:
        done=json.loads((imp/'COMPLETE.json').read_text(encoding='utf-8-sig'))
        assert done['Status']=='complete'and done['StateEqual']and not(imp/'FAILED.json').exists(),'Import outcome not complete; no preparation overwrite'
    front=old[:start].replace(str(FULL/'carrier-fix24/import'),str(imp))
    compute=H/'ForwardEye113_HeadHair25.compute';surface=H/'HeadHair25.shader'
    execute=r'''  public void Execute(ExecutionResult result){
   var receipt=new ImportFullReceipt24{Status="begin",Utc=DateTime.UtcNow.ToString("O")};
   try{
    Stable();if(SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Direct3D11)throw new IOException("Confirmed D3D11 required");
    var typed=(global::Prefix24.Case24)global::Prefix24.PrefixMetadata24.Decode(File.ReadAllBytes(Path.Combine(Root,"CASE.json")),typeof(global::Prefix24.Case24));
    var c=new PrefixImportCase24{Globals=typed.Globals.Select(g=>new PrefixImportGlobal24{Name=g.Name,Type=g.Type}).ToArray()};
    byte[] before=Json(State(c,"before"));New("BEFORE.json",before);receipt.BeforeSha=Hash(before);
    const string folder="Assets/EUnityValidation01/HeadHair25",compute=folder+"/ForwardEye113_HeadHair25.compute",surface=folder+"/HeadHair25.shader";
    string project=Directory.GetParent(Application.dataPath).FullName;
    if(project!=@"C:\Users\15352\Documents\work\Fantasy Survival Escape Game")throw new IOException("Project changed");
    if(Directory.Exists(Path.Combine(project,folder))||File.Exists(Path.Combine(project,folder)+".meta")||AssetDatabase.IsValidFolder(folder))throw new IOException("Candidate folder already exists; never overwrite");
    var paths=new[]{COMPUTE_SOURCE,SURFACE_SOURCE};var hashes=new[]{COMPUTE_HASH,SURFACE_HASH};var targets=new[]{compute,surface};
    var bytes=paths.Select(File.ReadAllBytes).ToArray();for(int i=0;i<2;i++)if(Hash(bytes[i])!=hashes[i])throw new IOException("Reviewed source changed");
    New("INTENT.json",Json(receipt));if(String.IsNullOrEmpty(AssetDatabase.CreateFolder("Assets/EUnityValidation01","HeadHair25")))throw new IOException("Folder creation incomplete");
    for(int i=0;i<2;i++){using(var f=new FileStream(Path.Combine(project,targets[i]),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){f.Write(bytes[i],0,bytes[i].Length);f.Flush(true);}AssetDatabase.ImportAsset(targets[i],ImportAssetOptions.ForceSynchronousImport);}
    Stable();var cs=AssetDatabase.LoadAssetAtPath<ComputeShader>(compute);var shader=AssetDatabase.LoadAssetAtPath<Shader>(surface);
    if(!cs||!shader||!shader.isSupported)throw new IOException("Isolated shaders unavailable/unsupported");
    var messages=new List<string>();foreach(var m in ShaderUtil.GetComputeShaderMessages(cs)){messages.Add(m.severity+"|"+m.message);if(m.severity.ToString()=="Error")throw new IOException("Compute compile error: "+m.message);}
    foreach(var m in ShaderUtil.GetShaderMessages(shader)){messages.Add(m.severity+"|"+m.message);if(m.severity.ToString()=="Error")throw new IOException("Surface compile error: "+m.message);}
    receipt.Messages=messages.ToArray();receipt.Guid=AssetDatabase.AssetPathToGUID(compute)+"|"+AssetDatabase.AssetPathToGUID(surface);
    var groups=new List<string>();foreach(string entry in new[]{"CarrierQueries113","AssignedVisibility24","ComposeRegion113","ComposeWhole113"}){uint x,y,z;cs.GetKernelThreadGroupSizes(cs.FindKernel(entry),out x,out y,out z);groups.Add(entry+":"+x+","+y+","+z);}receipt.KernelGroups=groups.ToArray();
    var after=Json(State(c,"after"));New("AFTER.json",after);receipt.AfterSha=Hash(after);receipt.StateEqual=before.SequenceEqual(after);
    if(!receipt.StateEqual)throw new IOException("Current public/native content changed; stop before render");
    receipt.Status="complete";New("COMPLETE.json",Json(receipt));result.Log("25 shader-only import complete; current state equal; no dispatch/Play");
   }catch(Exception e){receipt.Status="failed";receipt.Error=e.ToString();New("FAILED.json",Json(receipt));result.Log("25 import stopped; no dispatch/Play: "+e.Message);}
  }
 }
}
'''
    for key,p in [('COMPUTE',compute),('SURFACE',surface)]:execute=execute.replace(key+'_SOURCE','@"'+str(p)+'"').replace(key+'_HASH',json.dumps(sha(p)))
    importSource=H/'RUN_Import25.cs.txt';importText=front+execute+old[tail:]
    if imported:assert importSource.read_text(encoding='utf-8')==importText,'Do not rewrite an executed import source'
    else:importSource.write_text(importText,encoding='utf-8',newline='\n');compile_cs(importSource)
    capture=(FULL/'carrier-fix24/motion/RUN_CaptureFull24.cs.txt').read_text(encoding='utf-8')
    oldBody=body(R/'bounded-form115/runtime24/Forward113_Geometry24.cs').replace('Direct24Geometry','Direct24Carrier');assert capture.count(oldBody)==1
    capture=capture.replace(oldBody,body(H/'HeadHair25.cs')+'\n'+body(H/'Forward113_HeadHair25.cs'))
    run=H/'phase-run';run.mkdir(exist_ok=True);assert not (run/'CAPTURE_STARTED76.json').exists()
    capture=capture.replace(str(FULL/'carrier-fix24/motion'),str(run)).replace('Assets/EUnityValidation01/Direct24Carrier/ForwardEye113_Geometry24.compute','Assets/EUnityValidation01/HeadHair25/ForwardEye113_HeadHair25.compute')
    oldGate='if(motion82.Advance())';assert capture.count(oldGate)==1
    capture=capture.replace(oldGate,'if(captured76>=2){report["boundedTwoPhaseFrames25"]=true;BeginExit();return;}'+oldGate)
    timeout='if(!armed102&&EditorApplication.timeSinceStartup-start>70)'
    assert capture.count(timeout)==1
    capture=capture.replace(timeout,'if(armed102&&forward102!=null&&forward102.Source.Engine.Frames>64)throw new TimeoutException("25 bounded64 normal producer frames; exit without retry");'+timeout)
    needle='  foreach(var row in new[]{new{n="rgba",i=0},new{n="meta",i=1},new{n="rest",i=2},new{n="uv",i=3}})'
    assert capture.count(needle)==1
    extra='''   for(int ch25=0;ch25<5;ch25++){var ht25=forward102.HeadHair.Fields[ch25];Plane(hf,"H25-"+new[]{"rgba","meta","rest","uv","shade"}[ch25],ht25,new RectInt(0,0,ht25.rt.width,ht25.rt.height),"same-frame original hair on continuous native eye grid","exact footprint; original physical S4 retained");}
'''
    capture=capture.replace(needle,extra+needle)
    for bad in ['EvaluateForm115','BoundRun115','Shader.SetGlobalBuffer(','SaveAssets(','ClearDirty(','File.Delete(','File.Move(']:assert bad not in capture,bad
    assert not re.search(r'InputSystem\.settings\s*=(?!=)',capture)
    captureSource=run/'RUN_Capture25.cs.txt';captureSource.write_text(capture,encoding='utf-8',newline='\n');compile_cs(captureSource)
    (run/'GLOBAL_NAMES66.json').write_bytes((FULL/'GLOBAL_NAMES66.json').read_bytes())
    result={'importSourceSHA256':sha(importSource),'captureSourceSHA256':sha(captureSource),'computeSHA256':sha(compute),'surfaceSHA256':sha(surface),
        'csharpCompiled':True,'captureFramesBound':2,'newShaderAssets':2,'newComputeKernels':0,'GPUOrUnityExecuted':False,
        'requiresBeforeRender':['import/COMPLETE.json StateEqual=true and no failed/pending import','current instance/source and native/input snapshot','no new errors; no device reset']}
    (H/'LIVE_PREPARED.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
