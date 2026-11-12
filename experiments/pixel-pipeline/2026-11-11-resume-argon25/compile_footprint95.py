"""Compile a two-entry copy-only raster shader with the CPU FXC library."""
from pathlib import Path
import ctypes as C,re,json,hashlib
from compile_curve81 import graphics_tokens,api
H=Path(__file__).resolve().parent;G=H/'face95'
def main():
 (G/'build').mkdir(parents=True,exist_ok=True);shader=H/'SourceFootprint95.shader';blocks=re.findall('HLSLPROGRAM(.*?)ENDHLSL',shader.read_text(),re.S);assert len(blocks)==1
 data=re.sub(r'(?m)^\s*#pragma[^\r\n]*','',blocks[0]).encode();buf=C.create_string_buffer(data);dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;rows=[]
 for entry,profile in [('Full95','vs_5_0'),('Read95','ps_5_0')]:
  obj=C.c_void_p();err=C.c_void_p()
  try:
   hr=fn(buf,len(data),shader.name.encode(),None,None,entry.encode(),profile.encode(),(1<<11)|(1<<15),0,C.byref(obj),C.byref(err));msg=api.blob(err).decode(errors='replace')if err else'';assert hr>=0,(entry,msg);code=api.blob(obj);audit=graphics_tokens(code);assert audit['loops']==audit['privateArrays']==audit['threadGroups']==0;(G/'build'/(entry+'.dxbc')).write_bytes(code);rows.append({'entry':entry,'profile':profile,'audit':audit,'warnings':msg})
  finally:api.release(obj);api.release(err)
 out={'CPUCompiledNoGPUDevice':True,'shaderSHA256':hashlib.sha256(shader.read_bytes()).hexdigest(),'entries':rows,'readbackBytes':24*26*26*16,'newComputeDispatches':0,'continuousVisibilityProven':False};(G/'CPU_SHADER95.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
