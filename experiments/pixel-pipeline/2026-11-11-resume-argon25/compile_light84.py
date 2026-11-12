"""CPU FXC/token audit only: no GPU device or Unity operation."""
import ctypes as C,hashlib,json,re,sys
from pathlib import Path
from compile_curve81 import api,graphics_tokens
H=Path(__file__).resolve().parent;G=H/('face85'if '--85'in sys.argv else'face84')
def main():
 source=(H/('ShadeHistory85.shader'if '--85'in sys.argv else'SelectedLight84.shader')).read_text();block=re.findall('HLSLPROGRAM(.*?)ENDHLSL',source,re.S);assert len(block)==1;data=re.sub(r'(?m)^\s*#pragma[^\r\n]*','',block[0]).encode();dll=C.WinDLL(str(api.DLL),winmode=0x800);f=dll.D3DCompile;f.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];f.restype=C.c_long;buf=C.create_string_buffer(data);rows=[]
 for entry,profile in [('V84','vs_5_0'),('F84','ps_5_0')]:
  obj=C.c_void_p();err=C.c_void_p()
  try:
   hr=f(buf,len(data),b'SelectedLight84',None,None,entry.encode(),profile.encode(),(1<<11)|(1<<15),0,C.byref(obj),C.byref(err));message=api.blob(err).decode(errors='replace')if err else'';assert hr>=0,(entry,message);code=api.blob(obj);audit=graphics_tokens(code);assert audit['loops']==audit['privateArrays']==audit['threadGroups']==0;rows.append({'entry':entry,'audit':audit,'warnings':message});(G/'build'/('shader84-'+entry+'.dxbc')).write_bytes(code)
  finally:api.release(obj);api.release(err)
 result={'CPUCompiledNoGPUDevice':True,'shaderSHA256':hashlib.sha256(source.encode()).hexdigest(),'entries':rows};(G/'CPU_SHADER84.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
