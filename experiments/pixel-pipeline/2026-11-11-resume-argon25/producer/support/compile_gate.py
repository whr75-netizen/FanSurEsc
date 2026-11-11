"""Compile/reflection of changed HLSL on CPU; creates no GPU device."""
from pathlib import Path
import ctypes as C,hashlib,json,re,sys
H=Path(__file__).resolve().parent;R=H.parents[2];G=H/'gate'
sys.path.insert(0,str(R/'bounded-form115/prefix24'));import compile_hlsl_cpu as fx
def main():
 global G
 if '--source-alpha'in sys.argv:G=H/'gate-alpha'
 if '--native-proof'in sys.argv:G=H/'native-proof'
 dll=C.WinDLL(str(fx.DLL),winmode=0x800);fn=dll.D3DCompile
 fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 file=G/('NativeProof26.compute'if '--native-proof'in sys.argv else'SharedSource26.compute'if(G/'SharedSource26.compute').exists()else'SharedSkin26.compute')
 code=re.sub(rb'(?m)^#pragma (?:kernel|target) [^\r\n]+\r?\n',b'',file.read_bytes());source=C.create_string_buffer(code);rows=[]
 entries=['PrepareCells113','CurveColumns24','ColumnVisibility24','AssignedVisibility24']if '--native-proof'in sys.argv else['PrepareCells113','ColumnVisibility24','AssignedVisibility24']
 for entry in entries:
  binary=C.c_void_p();errors=C.c_void_p()
  try:
   hr=fn(source,len(code),b'SharedSkin26.compute',None,None,entry.encode(),b'cs_5_0',(1<<11)|(1<<15),0,C.byref(binary),C.byref(errors));assert hr>=0,fx.blob(errors)
   data=fx.blob(binary);audit=fx.token_audit(data,allow_arrays=True);bindings,constants=fx.reflect(dll,data)
   rows.append({'entry':entry,'audit':audit,'bindings':bindings,'bytecodeBytes':len(data),'bytecodeSHA256':hashlib.sha256(data).hexdigest()})
  finally:fx.release(binary);fx.release(errors)
 drivers=[p for p in fx.modules()if re.search(r'(?i)(?:d3d11|d3d12|dxgi|amdxx64|amddxx64|nvwgf2umx|igd10iumd64)\.dll$',p)];assert not drivers
 source=next(r for r in rows if r['entry']=='ColumnVisibility24');destination=next(r for r in rows if r['entry']=='AssignedVisibility24')
 assert '_SharedSkin26'not in str(source['bindings']),'Source visibility must not bind additional destination exemptions'
 if '--native-proof'in sys.argv:assert '_OwnSkin113'not in str(source['bindings'])
 assert all(k in str(destination['bindings'])for k in ['_SharedSkin26','_Cells113','_ReadIdentity96'])
 out={'source':file.name,'sourceSHA256':hashlib.sha256(file.read_bytes()).hexdigest(),'compiledEntries':rows,'GPUDeviceCreated':False,'GPUDriverModules':drivers,'sourceAdditionalMaskBindingAbsent':True,'newComputeKernels':0,'UnityCalls':0}
 (G/'CPU_HLSL_GATE26.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'changedEntriesCompiled':len(rows),'sourceAdditionalMaskBindingAbsent':True,'GPUDeviceCreated':False,'GPUDriverModules':drivers}))
if __name__=='__main__':main()
