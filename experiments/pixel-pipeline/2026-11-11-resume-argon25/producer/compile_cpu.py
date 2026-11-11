"""Compile the actual external host and changed compute entries, CPU only."""
from pathlib import Path
import ctypes as C,hashlib,json,re,subprocess,sys
H=Path(__file__).resolve().parent;R=H.parents[1];FULL=R/'bounded-form115/runtime24/full-render24'
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def body(p):return re.sub(r'(?m)^using [^;\n]+;\r?\n?','',p.read_text(encoding='utf-8-sig'))
def main():
    bundle=(FULL/'carrier-fix24/motion/RUN_CaptureFull24.cs.txt').read_text(encoding='utf-8')
    old=body(R/'bounded-form115/runtime24/Forward113_Geometry24.cs').replace('Direct24Geometry','Direct24Carrier')
    assert bundle.count(old)==1,'Do not guess class boundaries in host'
    new=body(H/'HeadHair25.cs')+'\n'+body(H/'Forward113_HeadHair25.cs')
    bundle=bundle.replace(old,new)
    assert 'EvaluateForm115'not in bundle and 'BoundRun115'not in bundle
    assert not re.search(r'InputSystem\.settings\s*=(?!=)',bundle)
    # Preparation bundle is not executed, not yet a capture permission/receipt.
    source=H/'HOST_CPU_ONLY.cs.txt';source.write_text(bundle,encoding='utf-8',newline='\n')
    editor=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data');out=H/'build';out.mkdir(exist_ok=True)
    refs=[editor/'NetStandard/ref/2.1.0/netstandard.dll',editor/'NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll']+sorted((editor/'Managed/UnityEngine').glob('*.dll'))+sorted((REPO/'Library/ScriptAssemblies').glob('*.dll'))
    args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:library','/langversion:latest','/out:'+str(out/'Host25.dll')]+['/reference:'+str(p)for p in refs]+[str(source)]
    rsp=out/'compile.rsp';rsp.write_text('\n'.join('"'+x+'"'for x in args),encoding='utf-8',newline='\n')
    process=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8')
    (H/'CPU_DIAGNOSTICS.txt').write_text(process.stdout+process.stderr,encoding='utf-8',newline='\n');assert process.returncode==0,process.stdout+process.stderr
    sys.path.insert(0,str(R/'bounded-form115/prefix24'));import compile_hlsl_cpu as fx
    dll=C.WinDLL(str(fx.DLL),winmode=0x800);fn=dll.D3DCompile
    fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
    code=re.sub(rb'(?m)^#pragma (?:kernel|target) [^\r\n]+\r?\n',b'',(H/'ForwardEye113_HeadHair25.compute').read_bytes());text=C.create_string_buffer(code);compiled=[]
    for entry in ['CarrierQueries113','ComposeRegion113']:
        binary=C.c_void_p();errors=C.c_void_p()
        try:
            hr=fn(text,len(code),b'HeadHair25.compute',None,None,entry.encode(),b'cs_5_0',(1<<11)|(1<<15),0,C.byref(binary),C.byref(errors))
            assert hr>=0,fx.blob(errors)
            data=fx.blob(binary);audit=fx.token_audit(data,allow_arrays=True);bindings,constants=fx.reflect(dll,data)
            assert not audit['privateArrayDeclarations'];compiled.append({'entry':entry,'audit':audit,'bindings':bindings,'bytecodeSHA256':hashlib.sha256(data).hexdigest()})
        finally:fx.release(binary);fx.release(errors)
    drivers=[p for p in fx.modules()if re.search(r'(?i)(?:d3d11|d3d12|dxgi|amdxx64|amddxx64|nvwgf2umx|igd10iumd64)\.dll$',p)];assert not drivers
    report={'csharpCompiled':True,'sourceSHA256':digest(source),'diagnostics':process.stdout+process.stderr,'compute':compiled,'GPUDriverModules':drivers,
        'compiledAssemblyExecuted':False,'UnityCalls':0,'GPUDeviceCreated':False,'surfaceShaderNotYetCompiled':True}
    (H/'CPU_COMPILE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'csharpCompiled':True,'changedComputeEntriesCompiled':len(compiled),'GPUDeviceCreated':False,'GPUDriverModules':drivers,'hostExecuted':False}))
if __name__=='__main__':main()
