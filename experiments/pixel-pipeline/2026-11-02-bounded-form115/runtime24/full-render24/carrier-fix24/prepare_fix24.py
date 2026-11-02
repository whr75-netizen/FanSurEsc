"""One source-valid lid fallback correction; preserve allocator/queries/palette.
CPU preparation/compilation only. New shader asset and fresh capture roots.
"""
from pathlib import Path
import ctypes as C,hashlib,json,re,subprocess,sys
H=Path(__file__).resolve().parent;R=H.parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
assert not any(H.glob('*_REQUEST.json'))and not(H/'import/INTENT.json').exists()
expected=read=lambda p:json.loads(p.read_text(encoding='utf8'))
replay=expected(H/'REPLAY_CARRIER24.json');assert replay['pairedGPUQueries']==176 and len(replay['newCases'])==11
raw=(R/'ForwardEye113_Geometry24.compute').read_text()
old='if(z<=0)z=count>0?sum/count:(id.z>=range.x&&id.z<=range.y?id.z:0);'
new='if(z<=0)z=count>0?sum/count:((role==6||id.z>=range.x&&id.z<=range.y)?id.z:0);'
assert raw.count(old)==1
shader=raw.replace(old,new);assert 'EvaluateForm115'not in shader
(H/'ForwardEye113_Geometry24.compute').write_text(shader,encoding='utf8',newline='\n')
sourceSHA=hashlib.sha256(shader.encode()).hexdigest();oldSHA=expected(R/'CPU_COMPILE_FULL24.json')['shaderSHA256']
sys.path.insert(0,str(R.parent.parent/'prefix24'));import compile_hlsl_cpu as fx
dll=C.WinDLL(str(fx.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
code=re.sub(r'(?m)^#pragma (?:kernel|target) [^\n]+\n','',shader).encode();blob=C.create_string_buffer(code);binary=C.c_void_p();errors=C.c_void_p()
try:
 hr=fn(blob,len(code),b'CarrierFix24.compute',None,None,b'CarrierQueries113',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(binary),C.byref(errors));assert hr>=0,fx.blob(errors)
 bytecode=fx.blob(binary);audit=fx.token_audit(bytecode,allow_arrays=True);bindings,constants=fx.reflect(dll,bytecode)
 assert audit['threads']==[64,1,1]and not audit['privateArrayDeclarations']
finally:fx.release(binary);fx.release(errors)
bad=[x for x in fx.modules()if re.search(r'(?i)(?:d3d11|d3d12|dxgi|nvwgf2umx|amdxx64|amddxx64)\.dll$',x)];assert not bad
records={'sourceSHA256':sourceSHA,'baselineSHA256':oldSHA,'changedExpression':[old,new],'changedKernel':'CarrierQueries113','dispatchCountsChanged':False,'newBuffersOrBindings':False,'newThresholds':False,'audit':audit,'bindings':bindings,'GPUDriverModules':bad,'GPUCalls':0}
def compile_cs(source,out):
 build=out/'build';build.mkdir(exist_ok=True)
 rsp=(R/'sequence24/build/compile.rsp').read_text().replace(str(R/'sequence24'),str(out))
 #The source always keeps the established command filename even for import.
 rsp=rsp.replace(str(out/'RUN_CaptureFull24.cs.txt'),str(source))
 (build/'compile.rsp').write_text(rsp,encoding='utf8')
 p=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(build/'compile.rsp')],capture_output=True,text=True,encoding='utf8')
 (out/'CPU_DIAGNOSTICS.txt').write_text(p.stdout+p.stderr,encoding='utf8');assert p.returncode==0,p.stdout+p.stderr
 return hashlib.sha256(source.read_bytes()).hexdigest()
#Reuse the previously successful explicit import/ABI/native-state collector.
imp=(R/'RUN_ImportFull24.cs.txt').read_text().replace(str(R/'import'),str(H/'import')).replace(str(R/'ForwardEye113_Geometry24.compute'),str(H/'ForwardEye113_Geometry24.compute')).replace(oldSHA,sourceSHA).replace('Direct24Geometry','Direct24Carrier')
impSource=H/'RUN_ImportFull24.cs.txt';impSource.write_text(imp,encoding='utf8',newline='\n');impSHA=compile_cs(impSource,H)
(H/'CPU_IMPORT24.json').write_text(json.dumps({'sources':{impSource.name:impSHA},'compiled':True,'GPUCalls':0},indent=2)+'\n',encoding='utf8')
relay=(R/'relay_full24.py').read_text();assert "mode=sys.argv[1]"in relay
(H/'relay_full24.py').write_text(relay.replace('Direct24Geometry','Direct24Carrier'),encoding='utf8',newline='\n')
for name,oldRoot in [('close',R/'sequence24'),('motion',R/'motion24')]:
 out=H/name;out.mkdir(exist_ok=True);assert not(out/'CaptureFull24_REQUEST.json').exists()
 c=(oldRoot/'RUN_CaptureFull24.cs.txt').read_text().replace(str(oldRoot),str(out)).replace('Direct24Geometry','Direct24Carrier')
 assert 'EvaluateForm115'not in c and 'BoundRun115'not in c and not re.search(r'InputSystem\.settings\s*=(?!=)',c)
 source=out/'RUN_CaptureFull24.cs.txt';source.write_text(c,encoding='utf8',newline='\n');sha=compile_cs(source,out)
 (out/'GLOBAL_NAMES66.json').write_bytes((R/'GLOBAL_NAMES66.json').read_bytes())
 (out/'CPU_COMPILE_FULL24.json').write_text(json.dumps({'cpuCSharpSuccess':True,'commandSHA256':sha,'shaderSHA256':sourceSHA,'UnityCalls':0,'GPUCalls':0,'compiledAssemblyExecuted':False},indent=2)+'\n',encoding='utf8')
 rr=(oldRoot/'relay_full24.py').read_text().replace('Direct24Geometry','Direct24Carrier')
 (out/'relay_full24.py').write_text(rr,encoding='utf8',newline='\n')
records['sourceProvenance']='Existing Write113 emits positive role6 only from current validated native pigment/curve proof. Finite positive depth and destination occlusion tests unchanged.'
(H/'PREPARED_FIX24.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in records.items()if k not in ['bindings']},ensure_ascii=False))
