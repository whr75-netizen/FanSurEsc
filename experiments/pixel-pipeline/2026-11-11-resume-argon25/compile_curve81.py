"""FXC CPU compile/SM5 token audit. No D3D device or Unity operation."""
from pathlib import Path
import ctypes as C,struct,re,sys,json,hashlib
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'))
import compile_hlsl_cpu as api

def graphics_tokens(code):
 # Reuse24's bounded token traversal; a graphics shader has no thread-group
 # declaration, so its compute-only assertion cannot be used for this profile.
 count=struct.unpack_from('<I',code,28)[0]
 for i in range(count):
  at=struct.unpack_from('<I',code,32+i*4)[0]
  if code[at:at+4]not in[b'SHEX',b'SHDR']:continue
  size=struct.unpack_from('<I',code,at+4)[0];w=struct.unpack_from('<'+'I'*(size//4),code,at+8);p=2;ops=[]
  while p<len(w):
   op=w[p]&2047;n=w[p+1]if op==53 else(w[p]>>24)&127;assert n and p+n<=len(w);ops.append(op);p+=n
  return {'instructions':len(ops),'loops':ops.count(48),'privateArrays':ops.count(105),'threadGroups':ops.count(155)}
 raise AssertionError('SM5 graphics chunk required')

def main():
 shader=H/(sys.argv[1]if len(sys.argv)>1 else'FeatureCurve81.shader');outroot=H/('face83'if shader.name=='FeatureCurve83.shader'else'face81');(outroot/'build').mkdir(parents=True,exist_ok=True)
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;source=shader.read_text();blocks=re.findall('HLSLPROGRAM(.*?)ENDHLSL',source,re.S);assert len(blocks)==2;rows=[]
 for i,block in enumerate(blocks):
  data=re.sub(r'(?m)^\s*#pragma[^\r\n]*','',block).encode();buf=C.create_string_buffer(data)
  for entry,profile in([('Vert81','vs_5_0'),('Frag81','ps_5_0')]if i==0 else[('Full81','vs_5_0'),('Compose81','ps_5_0')]):
   obj=C.c_void_p();err=C.c_void_p()
   try:
    hr=fn(buf,len(data),shader.name.encode(),None,None,entry.encode(),profile.encode(),(1<<11)|(1<<15),0,C.byref(obj),C.byref(err));message=api.blob(err).decode(errors='replace')if err else'';assert hr>=0,(entry,message);code=api.blob(obj);a=graphics_tokens(code);assert a['loops']==a['privateArrays']==a['threadGroups']==0;rows.append({'entry':entry,'profile':profile,'audit':a,'warnings':message});(outroot/'build'/('shader-'+entry+'.dxbc')).write_bytes(code)
   finally:api.release(obj);api.release(err)
 result={'CPUCompiledNoGPUDevice':True,'shaderSHA256':hashlib.sha256(shader.read_bytes()).hexdigest(),'entries':rows};(outroot/'CPU_SHADER81.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
