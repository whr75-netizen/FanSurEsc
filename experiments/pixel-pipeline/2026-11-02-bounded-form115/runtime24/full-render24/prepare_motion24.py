"""Reuse validated97 normal game-input/relative-phase stimuli; no GPU call."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
H=Path(__file__).resolve().parent;S=H/'motion24';Q=H/'sequence24'
assert not S.exists(),'Inspect existing outcome; never replace an execution'
s=json.loads(next(Q.glob('STATE113-*-finished.json')).read_text())
assert s['PlayExited']and not s.get('error')and not s.get('restorationError')
assert all(x['equal']for x in s['nativeComparisons72'])and not s['globalRestoreErrors']and s['motionRestoration82']['allRestored']
S.mkdir();code=(Q/'RUN_CaptureFull24.cs.txt').read_text()
assert hashlib.sha256(code.encode()).hexdigest()==json.loads((Q/'CPU_COMPILE_FULL24.json').read_text())['commandSHA256']
assert code.count('Sequence111 motion82;')==1 and code.count('new Sequence111(n,output)')==1
code=code.replace(str(Q),str(S)).replace('Sequence111 motion82;','MotionScope97 motion82;').replace('new Sequence111(n,output)','new MotionScope97(n,output)')
sys.path.insert(0,str(H.parent));from compile_runtime_cpu import class_span
original=(H.parents[2]/'live-joint96/MotionScope97.cs').read_text();a,b=class_span(original,'MotionScope97');motion=original[a:b]
# Existing97 stimuli return true on every sampled frame; this adapter property
# supplies the same explicit host contract used by Sequence111.
motion=motion.replace('public bool HasWarmup=>warm>0;','public bool HasWarmup=>warm>0;public bool CaptureThis=>true;')
code=code.replace('using FantasySurvival.Controls;','using FantasySurvival.Controls;\nusing FantasySurvival.SceneFlow;\nusing UnityEngine.InputSystem.LowLevel;')
code+='\nnamespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\n'+motion+'\n}\n'
for bad in ['EvaluateForm115','BoundRun115','Shader.SetGlobalBuffer(','SaveAssets(','ClearDirty(','File.Delete(','File.Move(']:assert bad not in code
assert not re.search(r'InputSystem\.settings\s*=(?!=)',code)
(S/'RUN_CaptureFull24.cs.txt').write_text(code,encoding='utf8',newline='\n');(S/'GLOBAL_NAMES66.json').write_bytes((H/'GLOBAL_NAMES66.json').read_bytes())
build=S/'build';build.mkdir();rsp=(Q/'build/compile.rsp').read_text().replace(str(Q),str(S));(build/'compile.rsp').write_text(rsp,encoding='utf8')
p=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(build/'compile.rsp')],capture_output=True,text=True,encoding='utf8')
(S/'CPU_DIAGNOSTICS.txt').write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
record={'cpuCSharpSuccess':True,'commandSHA256':hashlib.sha256(code.encode()).hexdigest(),'shaderSHA256':json.loads((H/'CPU_COMPILE_FULL24.json').read_text())['shaderSHA256'],'UnityCalls':0,'GPUCalls':0,'compiledAssemblyExecuted':False,'stimulusBasis':'live-joint96/MotionScope97.cs','stimulusSHA256':hashlib.sha256(original.encode()).hexdigest(),'phaseFrames':10,'walkFrames':8,'turnFrames':10,'settingsReplacement':False}
(S/'CPU_COMPILE_FULL24.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
relay=(Q/'relay_full24.py').read_text().replace("'new Sequence111('in text","'new MotionScope97('in text").replace('one Play/existing12 evaluated Close and hair states; runtime graph dispatches','one Play/existing28 measured-phase walk turn frames; runtime graph dispatches')
(S/'relay_full24.py').write_text(relay,encoding='utf8',newline='\n');print(json.dumps(record,indent=2))
