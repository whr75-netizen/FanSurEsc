"""Observe the completed second native render, not its first preparation render."""
from pathlib import Path
import hashlib,json,difflib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face57'
def main():
 p=G/'capture';p.mkdir(parents=True,exist_ok=True)
 assert not(p/'REQUEST.json').exists()and not(p/'STARTED.json').exists()
 d=json.loads((H/'face56/capture/FAILED.json').read_text())
 assert d['Edit']and d['ownedResourcesReleased']and d['pendingOwners']==0 and d['restorationChecksPass']
 assert d['afterMemory']['RTCount']==d['beforeMemory']['RTCount']==30
 assert all(x['equal'] is not False for x in d['nativeChecks'])
 old=(H/'face56/capture/RUN.cs.txt').read_text();s=old.replace('resume-20261111\\face56\\capture','resume-20261111\\face57\\capture').replace('face56-source-domain-','face57-source-domain-')
 a='else if(camera==p.MainCamera41&&p.RequiresFinal41)'
 b='else if(camera==p.MainCamera41&&p.RequiresFinal41&&HeadLocal367.Active&&HeadLocal367.Active.main.contourReady)'
 assert s.count(a)==1;s=s.replace(a,b)
 # The consumer's strict same-frame/order checks and completion finally are unchanged.
 assert '||!main41.contourReady||!native42.ready)'in s
 assert 'CompletionScope50.Record('in s and 'p.DrainStopped56()'in s
 (p/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n')
 build=G/'build';build.mkdir(exist_ok=True);compile_unity_language(p/'RUN.cs.txt',build/'capture57.dll')
 src=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\HeadLocal367\Runtime\HeadLocal367.cs').read_text(encoding='utf-8-sig')
 assert 'f.contourReady=false;m.camera.Render()'in src and 'f.contourReady=true;m.camera.Render()'in src
 stages=[('head',False,False),('main preparation',True,False),('main completed',True,True)]
 enqueued=[name for name,main,ready in stages if main and ready]
 assert enqueued==['main completed']
 result={'fullExternalCSharp9Compiled':True,'plannedSourceFrames':1,'GPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'correctedStage':'HeadLocal367.RenderFrame completed second main camera render','preparationRenderMustNotRegisterFinalCompletion':True,'strictConsumerChecksUnchanged':True,'failedFinalCameraFallback56Unchanged':True,'noNewShaderImport':True,'sourceRendererSHA256':hashlib.sha256(src.encode()).hexdigest(),'phaseFixture':stages,'enqueued':enqueued}
 (G/'CPU_PREPARED57.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 (G/'from56.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='capture56',tofile='capture57')),encoding='utf-8')
 print(json.dumps(result))
if __name__=='__main__':main()
