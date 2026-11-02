"""CPU compilers only; never execute compiled Unity/host DLL or create a GPU."""
from pathlib import Path
import ctypes as C,hashlib,json,re,subprocess,sys
H=Path(__file__).resolve().parent;B=H.parent;sys.path.insert(0,str(B/'prefix24'))
import compile_hlsl_cpu as fx
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hlsl():
    out=H/'build';out.mkdir(exist_ok=True);source=H/'ForwardEye113_Geometry24.compute';raw=source.read_bytes()
    code=re.sub(rb'(?m)^#pragma (?:kernel|target) [^\r\n]+\r?\n',b'',raw);assert b'#include'not in code and b'115'not in code
    before=fx.modules();dll=C.WinDLL(str(fx.DLL),winmode=0x800);fn=dll.D3DCompile
    fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
    buf=C.create_string_buffer(code);rows=[]
    for entry in ['BuildSubsets113','Enumerate113','Reduce113','Write113','Query','CurveColumns24','ColumnVisibility24','PrepareCells113','CarrierQueries113','AssignedVisibility24','ComposeRegion113','PackPart','Refit','Select','GatherEye113']:
        result=C.c_void_p();errors=C.c_void_p()
        try:
            hr=fn(buf,len(code),b'Geometry24.compute',None,None,entry.encode(),b'cs_5_0',(1<<11)|(1<<15),0,C.byref(result),C.byref(errors));diagnostic=fx.blob(errors).decode('utf-8',errors='replace')
            (out/(entry+'.diagnostics.txt')).write_text(diagnostic,encoding='utf-8');print(entry,hr,diagnostic[:700]);assert hr>=0
            binary=fx.blob(result);bindings,constants=fx.reflect(dll,binary);audit=fx.token_audit(binary,allow_arrays=True)
            if entry not in ['Select','GatherEye113']:
                assert 'forcing loop'not in diagnostic and 'not natively addressable'not in diagnostic and 'X4714'not in diagnostic
            assert sum(b['Type']==6 for b in bindings)<=8
            if entry in ['BuildSubsets113','Enumerate113','Reduce113','Write113']:assert not audit['privateArrayDeclarations']
            (out/(entry+'.dxbc')).write_bytes(binary)
            rows.append({'entry':entry,'activeEntrypoint':entry.encode()in re.findall(rb'^#pragma kernel (\w+)',raw,re.M),'sourceSHA256':sha(source),'dxbcSHA256':hashlib.sha256(binary).hexdigest(),'audit':audit,'bindings':bindings,'constants':constants,'diagnostics':diagnostic})
        finally:fx.release(result);fx.release(errors)
    after=fx.modules();bad=[p for p in after if re.search(r'(?i)(?:d3d11|d3d12|dxgi|amdxx64|amddxx64|nvwgf2umx|igd10iumd64)\.dll$',p)];assert not bad
    (H/'HLSL_RUNTIME24.json').write_text(json.dumps({'GPUOrUnityCalls':0,'GPUDeviceCreated':False,'GPUDriverModules':bad,'newModules':sorted(set(after)-set(before)),'compilerSHA256':sha(fx.DLL),'kernels':rows,'notDriverSafetyEvidence':True},indent=2)+'\n')

def class_span(s,name):
    match=re.search(r'(?:public|internal)\s+(?:(?:sealed|partial)\s+)*class\s+'+name+r'\b',s);assert match,name
    start=match.start();masked=re.sub(r'@"(?:[^"]|"")*"|"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/|\'(?:\\.|[^\'\\])\'',lambda m:' '*len(m[0]),s,flags=re.S)
    first=masked.index('{',start);level=1;i=first+1
    while level:
        if masked[i]=='{':level+=1
        elif masked[i]=='}':level-=1
        i+=1
    return start,i
def csharp():
    editor=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data');repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
    original=B.parent/'argon23-runtime113/attempt5/RUN_Capture113e.cs.txt';s=original.read_text(encoding='utf-8')
    for cls,file in [('Forward113','Forward113_Geometry24.cs'),('RegionDriver113','RegionDriver113_Geometry24.cs'),('SourcePigment113','SourcePigment113_Geometry24.cs'),('WholeEye107','WholeEye107_Geometry24.cs')]:
        a,b=class_span(s,cls);replacement=(H/file).read_text(encoding='utf-8');c,d=class_span(replacement,cls);s=s[:a]+replacement[c:d]+s[b:]
    # This exact historical dependency bundle is compiler input only, not a
    # command submission deliverable. Remove its Execute entrypoint class.
    a,b=class_span(s,'CommandScript');s=s[:a]+s[b:]
    s+='\n'+(H/'DispatchBounds24.cs').read_text(encoding='utf-8')
    assert 'EvaluateForm115'not in s and 'class CommandScript'not in s
    out=H/'build';out.mkdir(exist_ok=True);unit=out/'COMPILE_ONLY.cs';unit.write_bytes(s.encode())
    refs=[editor/'NetStandard/ref/2.1.0/netstandard.dll',editor/'NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll']
    refs+=sorted((editor/'Managed/UnityEngine').glob('*.dll'))
    refs+=sorted((repo/'Library/ScriptAssemblies').glob('*.dll'))
    args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:library','/langversion:latest','/out:'+str(out/'Geometry24.dll')]+['/reference:'+str(p)for p in refs]+[str(unit)]
    rsp=out/'compile.rsp';rsp.write_text('\n'.join('"'+a+'"'for a in args)+'\n',encoding='utf-8')
    dot=r'C:\Program Files\dotnet\dotnet.exe';csc=r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll'
    p=subprocess.run([dot,'exec',csc,'/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');diagnostics=p.stdout+p.stderr;(H/'CS_RUNTIME24.diagnostics.txt').write_text(diagnostics,encoding='utf-8');print('C# return',p.returncode,diagnostics[:5000]);assert p.returncode==0
    (H/'CS_RUNTIME24.json').write_text(json.dumps({'success':True,'GPUOrUnityCalls':0,'compiledOutputExecuted':False,'dependencyBundleSHA256':sha(original),'unitSHA256':sha(unit),'candidateSourceSHA256':{p.name:sha(p)for p in H.glob('*.cs')},'referenceCount':len(refs),'diagnostics':diagnostics,'argumentsResponseSHA256':sha(rsp)},indent=2)+'\n')
if __name__=='__main__':
    if len(sys.argv)==1 or sys.argv[1]=='hlsl':hlsl()
    if len(sys.argv)==1 or sys.argv[1]=='cs':csharp()
