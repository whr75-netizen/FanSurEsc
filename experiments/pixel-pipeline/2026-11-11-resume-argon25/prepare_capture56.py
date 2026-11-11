"""Reuse executed49 and reviewed50; one source frame, existing49 shader only."""
from pathlib import Path
import difflib,json,hashlib,subprocess
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face56';B=G/'build'
def main():
 (G/'capture').mkdir(parents=True,exist_ok=True);B.mkdir(exist_ok=True);assert not(G/'capture/REQUEST.json').exists()and not(G/'capture/STARTED.json').exists()
 old=(H/'face50/REVIEW_ONLY_PATCHED_SOURCE50.cs.txt').read_text();s=old.replace('resume-20261111\\face49\\capture','resume-20261111\\face56\\capture')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 # One real source frame; no six-frame animation claim or new width/colour policy.
 rep('cohort=new SourceOutline40[6];try{for(int i=0;i<6;i++)','cohort=new SourceOutline40[1];try{for(int i=0;i<1;i++)')
 rep('producers.Length!=6','producers.Length!=1');rep('36 six captures on one view required','56 one capture on one view required')
 rep('id="face49-source-domain-"','id="face56-source-domain-"');s=s.replace('Save("six-packets-copied")','Save("one-packet-copied")')
 rep('["newEyeAllocator"]=false','["newEyeAllocator"]=false,["plannedSourceFrames"]=1,["temporalStabilityValidated"]=false')
 assert 'face49\\capture'not in s
 # Always enqueue the final owner pass when its camera is present. Candidate
 # readiness still fails closed inside RecordFinalCandidate50; finally records ACK.
 rep('camera==p.MainCamera41&&p.RequiresFinal41&&HeadLocal367.Active.main.contourReady','camera==p.MainCamera41&&p.RequiresFinal41')
 needle=' public void PumpExit(){exitRequest32.RequireOwner();exitRequest32.Drain(BeginExitOnEditor32);exit.Pump(!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode&&!EditorApplication.isCompiling&&!EditorApplication.isUpdating,()=>producers.All(p=>p.CanRelease)'
 rep(needle,needle.replace('exit.Pump(', 'foreach(var p in producers)p.DrainStopped56();exit.Pump('))
 needle=' bool completionRecorded50;'
 adapter=''' bool completionRecorded50;
 public void DrainStopped56(){
  if(!stopped)return;
  FailureCompletion56.AfterStop(ref completionRecorded50,stopped,submission,FrameKey,generation,
   done=>AsyncGPUReadback.Request(Classification.rt,0,0,1,0,1,0,1,r=>{try{bool complete=r.done,error=r.hasError;done(complete,error,complete&&!error?r.layerDataSize:0);}catch(Exception e){Fail(e);}}),Fail);
 }
'''
 rep(needle,adapter)
 # Cross-assembly safety: old diagnostic owners cannot be hidden by a new static.
 needle='  if(active!=null||File.Exists(Path.Combine(Root,"STARTED.json")))'
 if needle not in s:
  lines=[x for x in s.splitlines()if'active!=null'in x and'STARTED'in x];assert len(lines)==1;needle=lines[0].split('throw',1)[0]
  rep(needle,'  if(Resources.FindObjectsOfTypeAll<RenderTexture>().Any(t=>t&&(t.name.StartsWith("31 owned source field_",StringComparison.Ordinal)||t.name.StartsWith("31 owned depth_",StringComparison.Ordinal)||t.name.StartsWith("33 immutable same-frame existing stage_",StringComparison.Ordinal))))throw new InvalidOperationException("56 prior diagnostic resources remain; do not arm");\n'+needle)
 else:
  rep(needle,'  if(Resources.FindObjectsOfTypeAll<RenderTexture>().Any(t=>t&&(t.name.StartsWith("31 owned source field_",StringComparison.Ordinal)||t.name.StartsWith("31 owned depth_",StringComparison.Ordinal)||t.name.StartsWith("33 immutable same-frame existing stage_",StringComparison.Ordinal))))throw new InvalidOperationException("56 prior diagnostic resources remain; do not arm");\n'+needle)
 helper=(H/'FailureCompletion56.cs').read_text();helper='\n'.join(x for x in helper.splitlines()if not x.startswith('using '));s+='\n'+helper
 assert 'EvaluateForm115'not in s and'BoundRun115'not in s and'cohort=new SourceOutline40[1]'in s
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',B/'capture56.dll')
 # Standalone .NET tests reuse the exact submission state machine from50.
 a=old.index('public sealed class Submission40');b=old.index('// Stop/request-exit',a);submission=old[a:b]
 test='using System;\n'+submission+'\n'+helper+'\n'+'\n'.join(x for x in(H/'FailureCompletionTests56.cs').read_text().splitlines()if not x.startswith('using '));(B/'Tests56.cs').write_text(test,encoding='utf-8')
 refs=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0');dotnet=r'C:\Program Files\dotnet\dotnet.exe';csc=r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll';dll=B/'Tests56.dll';args=['/nologo','/nostdlib+','/target:exe','/langversion:9','/out:'+str(dll)]+['/reference:'+str(p)for p in refs.glob('*.dll')]+[str(B/'Tests56.cs')];rsp=B/'tests.rsp';rsp.write_text('\n'.join('"'+x+'"'for x in args));r=subprocess.run([dotnet,'exec',csc,'/noconfig','@'+str(rsp)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 (B/'Tests56.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}));r=subprocess.run([dotnet,str(dll)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;result=json.loads(r.stdout)
 result.update({'fullExternalCSharp9Compiled':True,'plannedSourceFrames':1,'existingSource49ShaderUnchanged':True,'newShaderImport':False,'cleanupOnlyFallbackBytes':16,'GPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest()});(G/'CPU_PREPARED56.json').write_text(json.dumps(result,indent=2));(G/'from50.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='reviewed50',tofile='capture56')),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
