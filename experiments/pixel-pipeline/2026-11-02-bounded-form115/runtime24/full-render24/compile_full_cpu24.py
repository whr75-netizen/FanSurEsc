"""CPU compilers only. Never execute the Unity command or create a GPU device."""
from pathlib import Path
import sys,json,hashlib,subprocess,re,ctypes as C
H=Path(__file__).resolve().parent;R=H.parent;B=R.parent;sys.path.insert(0,str(B/'prefix24'));import compile_hlsl_cpu as fx
repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');editor=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data');out=H/'build';out.mkdir(exist_ok=True)
source=H/'RUN_CaptureFull24.cs.txt';refs=[editor/'NetStandard/ref/2.1.0/netstandard.dll',editor/'NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll']+sorted((editor/'Managed/UnityEngine').glob('*.dll'))+sorted((repo/'Library/ScriptAssemblies').glob('*.dll'))
args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:library','/langversion:latest','/out:'+str(out/'Full24.dll')]+['/reference:'+str(p)for p in refs]+[str(source)]
rsp=out/'compile.rsp';rsp.write_text('\n'.join('"'+x+'"'for x in args)+'\n',encoding='utf-8')
p=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');print(p.stdout+p.stderr);assert p.returncode==0
result={'cpuCSharpSuccess':True,'commandSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'diagnostics':p.stdout+p.stderr,'compiledAssemblyExecuted':False,'UnityCalls':0,'GPUDeviceCreated':False}
raw=(H/'ForwardEye113_Geometry24.compute').read_bytes();code=re.sub(rb'(?m)^#pragma (?:kernel|target) [^\r\n]+\r?\n',b'',raw)
assert code==re.sub(rb'(?m)^#pragma (?:kernel|target) [^\r\n]+\r?\n',b'',(R/'ForwardEye113_Geometry24.compute').read_bytes())
before=fx.modules();dll=C.WinDLL(str(fx.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
buffer=C.create_string_buffer(code);compiled=C.c_void_p();errors=C.c_void_p()
try:
 hr=fn(buffer,len(code),b'Full24.compute',None,None,b'ComposeWhole113',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(compiled),C.byref(errors));assert hr>=0
 binary=fx.blob(compiled);audit=fx.token_audit(binary,allow_arrays=True);assert not audit['privateArrayDeclarations']and audit['loops']==0
 bindings,constants=fx.reflect(dll,binary)
 result.update({'shaderSHA256':hashlib.sha256(raw).hexdigest(),'mathSourceIdenticalIgnoringPragmas':True,'composeAudit':audit,'composeBindings':bindings,'composeDXBCSHA256':hashlib.sha256(binary).hexdigest(),'composeDispatch':[60,34,1],'composeThreads':130560,'allOther14KernelsPreviouslyCpuCompiledSameMath':True})
finally:fx.release(compiled);fx.release(errors)
bad=[p for p in fx.modules()if re.search(r'(?i)(?:d3d11|d3d12|dxgi|amdxx64|amddxx64|nvwgf2umx|igd10iumd64)\.dll$',p)];assert not bad;result['GPUDriverModules']=bad
with(H/'CPU_COMPILE_FULL24.json').open('x',encoding='utf-8')as f:json.dump(result,f,indent=2)
print(json.dumps(result,indent=2))
