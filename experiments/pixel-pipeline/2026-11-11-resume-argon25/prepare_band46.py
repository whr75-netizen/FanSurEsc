from pathlib import Path
import json,hashlib,ctypes as C,sys,struct
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face46'
def graphics_audit(code,stage):
 assert code[:4]==b'DXBC'
 for i in range(struct.unpack_from('<I',code,28)[0]):
  at=struct.unpack_from('<I',code,32+4*i)[0]
  if code[at:at+4]not in[b'SHEX',b'SHDR']:continue
  size=struct.unpack_from('<I',code,at+4)[0];words=struct.unpack_from('<'+'I'*(size//4),code,at+8);assert words[0]>>16==stage;p=2;ops=[]
  while p<len(words):
   op=words[p]&2047;n=words[p+1]if op==53 else(words[p]>>24)&127;assert n and p+n<=len(words);ops.append(op);p+=n
  assert 48 not in ops and 105 not in ops and 155 not in ops
  return {'stage':'vertex'if stage==1 else'fragment','instructions':len(ops),'loops':0,'privateArrays':0}
 raise AssertionError('No SM5 instruction chunk')
def main():
 for name in ['build','capture','import','shaders','final','console']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 prefix=(H/'face45/import/RUN.cs.txt').read_text().split('internal class CommandScript',1)[0]
 p=G/'capture/RUN.cs.txt';p.write_text(prefix+(H/'BandFixture46.cs.txt').read_text(),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/band46.dll')
 source=(H/'face45/import/RUN.cs.txt').read_text();prefix,body=source.split('internal class CommandScript',1);body=body.replace('face45\\import','face46\\import').replace('face45\\shaders','face46\\shaders').replace('SourceBoundary45','SourceBoundary46').replace('SourceOwner45.compute','VariableStroke46.shader');a=body.index('var messages=new Arr40();');b=body.index('var checks=NativeSnapshot40.Compare',a);body=body[:a]+'var messages=new Arr40();var shader=AssetDatabase.LoadAssetAtPath<Shader>(Target+"/VariableStroke46.shader");if(!shader||!shader.isSupported)throw new InvalidOperationException("46 shader unavailable");foreach(var m in ShaderUtil.GetShaderMessages(shader)){messages.Add(m.message);if(m.severity.ToString()=="Error")throw new InvalidOperationException(m.message);}\n   '+body[b:];p=G/'import/RUN.cs.txt';p.write_text(prefix+'internal class CommandScript'+body,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import46.dll')
 for mode in ['final']:(G/mode/'RUN.cs.txt').write_text((H/'face45/final/RUN.cs.txt').read_text().replace('face45\\final','face46\\final'),encoding='utf-8',newline='\n')
 (G/'console/ARGS.json').write_bytes((H/'face45/console/ARGS.json').read_bytes());raw=(H/'VariableStroke46.shader').read_bytes();(G/'shaders/VariableStroke46.shader').write_bytes(raw);hlsl=raw.decode().split('HLSLPROGRAM',1)[1].split('ENDHLSL',1)[0];hlsl='\n'.join(x for x in hlsl.splitlines()if not x.strip().startswith('#pragma')).encode()
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;audits={}
 for entry,profile in [(b'Vert46',b'vs_5_0'),(b'Frag46',b'ps_5_0')]:
  blob=C.c_void_p();error=C.c_void_p()
  try:
   hr=fn(hlsl,len(hlsl),b'VariableStroke46',None,None,entry,profile,(1<<11)|(1<<15),0,C.byref(blob),C.byref(error));assert hr>=0,api.blob(error).decode(errors='replace');audit=graphics_audit(api.blob(blob),1 if profile.startswith(b'vs')else 0);audits[entry.decode()]=audit;(G/(entry.decode()+'.cpu.dxbc')).write_bytes(api.blob(blob))
  finally:api.release(blob);api.release(error)
 (G/'PREPARED46.json').write_text(json.dumps({'CPU_CSharp9':True,'CPUHLSL':audits,'GPUExecuted':False,'draws':6,'maxFragmentInvocations':6144,'totalReadBytes':196608,'Play':0,'runtimeModelWidthMappingSpecified':False,'product77Changed':False,'captureSHA256':hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest()},indent=2),encoding='utf-8');print('46 external C#9/vertex+fragment HLSL CPU compiled; no Unity/GPU executed')
if __name__=='__main__':main()
