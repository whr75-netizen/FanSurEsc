"""CPU FXC only; forbid dynamic loop/indexable-local-array GPU code."""
from pathlib import Path
import ctypes as C,re,json,hashlib,sys
from compile_curve81 import graphics_tokens,api
H=Path(__file__).resolve().parent;G=H/'face93'
def main():
 global G
 if '--output-root'in sys.argv:G=Path(sys.argv[sys.argv.index('--output-root')+1]).resolve()
 shader=H/'ProjectedRibbon93.shader';source=shader.read_text();blocks=re.findall('HLSLPROGRAM(.*?)ENDHLSL',source,re.S);assert len(blocks)==2;(G/'build').mkdir(exist_ok=True);dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;rows=[]
 for block,entries in zip(blocks,[[('Vert93','vs_5_0'),('Frag93','ps_5_0')],[('Full93','vs_5_0'),('Compose93','ps_5_0')]]):
  data=re.sub(r'(?m)^\s*#pragma[^\r\n]*','',block).encode();buf=C.create_string_buffer(data)
  for entry,profile in entries:
   obj=C.c_void_p();err=C.c_void_p()
   try:
    hr=fn(buf,len(data),shader.name.encode(),None,None,entry.encode(),profile.encode(),(1<<11)|(1<<15),0,C.byref(obj),C.byref(err));msg=api.blob(err).decode(errors='replace')if err else'';assert hr>=0,(entry,msg);code=api.blob(obj);audit=graphics_tokens(code);assert audit['loops']==audit['privateArrays']==audit['threadGroups']==0;(G/'build'/(entry+'.dxbc')).write_bytes(code);rows.append({'entry':entry,'profile':profile,'audit':audit,'warnings':msg})
   finally:api.release(obj);api.release(err)
 d={'CPUCompiledNoGPUDevice':True,'shaderSHA256':hashlib.sha256(shader.read_bytes()).hexdigest(),'maximumRibbonBBoxPixelsPerVariant':8192,'entries':rows};(G/'CPU_SHADER93.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
