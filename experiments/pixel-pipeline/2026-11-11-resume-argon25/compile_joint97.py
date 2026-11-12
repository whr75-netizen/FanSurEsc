from pathlib import Path
import ctypes as C,re,json,hashlib
from compile_curve81 import graphics_tokens,api
H=Path(__file__).resolve().parent;G=H/'face97'

def main():
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;rows=[]
 for name,entries in [('JointRibbon97',[('Full97','vs_5_0'),('Compose97','ps_5_0')]),('SourceFootprint97',[('Full96','vs_5_0'),('Read96','ps_5_0')])]:
  path=H/(name+'.shader');source=path.read_text();blocks=re.findall('HLSLPROGRAM(.*?)ENDHLSL',source,re.S);assert len(blocks)==1;data=re.sub(r'(?m)^\s*#pragma[^\r\n]*','',blocks[0]).encode();buf=C.create_string_buffer(data)
  for entry,profile in entries:
   obj=C.c_void_p();err=C.c_void_p()
   try:
    hr=fn(buf,len(data),path.name.encode(),None,None,entry.encode(),profile.encode(),(1<<11)|(1<<15),0,C.byref(obj),C.byref(err));message=api.blob(err).decode(errors='replace')if err else'';assert hr>=0,(entry,message);code=api.blob(obj);audit=graphics_tokens(code);assert audit['loops']==audit['privateArrays']==audit['threadGroups']==0;(G/'build'/(entry+'.dxbc')).write_bytes(code);rows.append({'shader':name,'shaderSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'entry':entry,'audit':audit,'warnings':message})
   finally:api.release(obj);api.release(err)
 out={'CPUCompiledNoGPUDevice':True,'newCompute':0,'newRasterPasses':1,'readbackBytesUnchanged':259584,'rows':rows};(G/'CPU_SHADER97.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
