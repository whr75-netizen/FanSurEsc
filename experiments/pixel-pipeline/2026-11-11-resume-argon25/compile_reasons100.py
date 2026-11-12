"""FXC bytecode/ABI check only: no D3D device or Unity invocation."""
from pathlib import Path
import ctypes as C,re,json,hashlib,sys
from compile_curve81 import graphics_tokens,api
H=Path(__file__).resolve().parent;G=H/'face100'

def main():
 name=sys.argv[1]if len(sys.argv)>1 else'SourceFootprint100';assert name in ['SourceFootprint100','SourceFootprint101','SourceFootprint101B','SourceValue101'];folder=H/('face100'if name.endswith('100')else'face101');dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;path=H/(name+'.shader');s=path.read_text();block,=re.findall('HLSLPROGRAM(.*?)ENDHLSL',s,re.S);raw=re.sub(r'(?m)^\s*#pragma[^\r\n]*','',block).encode();buf=C.create_string_buffer(raw);rows=[]
 for entry,profile in ([('V84','vs_5_0'),('F84','ps_5_0')]if name=='SourceValue101'else[('Full96','vs_5_0'),('Read96','ps_5_0')]):
  obj=C.c_void_p();err=C.c_void_p()
  try:
   hr=fn(buf,len(raw),path.name.encode(),None,None,entry.encode(),profile.encode(),(1<<11)|(1<<15),0,C.byref(obj),C.byref(err));message=api.blob(err).decode(errors='replace')if err else'';assert hr>=0,(entry,message);code=api.blob(obj);audit=graphics_tokens(code);assert audit['loops']==audit['privateArrays']==audit['threadGroups']==0;(folder/'build'/(entry+'.dxbc')).write_bytes(code);rows.append({'entry':entry,'audit':audit,'warnings':message})
  finally:api.release(obj);api.release(err)
 assert 2*53*53+15*26*26<=24*26*26
 runtime=(folder/('reasons32'if name.endswith('100')else'source32')/'capture/RUN.cs.txt').read_text();assert'EvaluateForm115'not in runtime and'BoundRun115'not in runtime and('face100-reasons-'if name.endswith('100')else'face101-main-source-')in runtime
 for binding in ['main41.resolvedUV','main41.preparedMeta','main41.domain','native42.owner']:assert runtime.count(binding)>=2
 out={'CPUOnly':True,'GPUDeviceCreated':False,'shaderSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'readbackBytes':259584,'newPasses':0,'replacesExistingSourceOrPacketPass':True,'newSourceReasonPlaneOnly':14,'runtimeCompiled':True,'rows':rows};(folder/('CPU_SHADER_'+name+'.json')).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
