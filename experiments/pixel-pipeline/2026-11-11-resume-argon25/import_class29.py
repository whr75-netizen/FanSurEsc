"""One bounded classifier shader-only import; fixed8x8 ABI and CPU compile."""
from pathlib import Path
import ctypes as C,hashlib,json,shutil,sys
H=Path(__file__).resolve().parent;G=H/'face29'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 root=G/'class-import';root.mkdir(exist_ok=True);assert not(root/'IMPORT_REQUEST.json').exists()
 # D3DCompile creates CPU bytecode only; there is no device/context creation.
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile
 fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 p=G/'LineClass29.compute';raw=p.read_bytes();blob=C.c_void_p();error=C.c_void_p();hr=fn(raw,len(raw),b'LineClass29',None,None,b'Classify29',b'cs_5_0',1<<11,0,C.byref(blob),C.byref(error))
 def read_blob(ptr):
  vt=C.cast(ptr,C.POINTER(C.POINTER(C.c_void_p)))[0];get=C.WINFUNCTYPE(C.c_void_p,C.c_void_p)(vt[3]);size=C.WINFUNCTYPE(C.c_size_t,C.c_void_p)(vt[4]);return C.string_at(get(ptr),size(ptr))
 try:
  diagnostic=read_blob(error).decode('utf-8',errors='replace')if error else'';(G/'CPU_CLASS_DIAGNOSTICS29.txt').write_text(diagnostic,encoding='utf-8',newline='\n');assert hr>=0,diagnostic
  bytecode=read_blob(blob);(G/'LineClass29.cpu.dxbc').write_bytes(bytecode)
 finally:
  for ptr in [blob,error]:
   if ptr:
    vt=C.cast(ptr,C.POINTER(C.POINTER(C.c_void_p)))[0];C.WINFUNCTYPE(C.c_ulong,C.c_void_p)(vt[2])(ptr)
 s=(G/'fixed-import/RUN_Import25.cs.txt').read_text(encoding='utf-8').replace(str(G/'fixed-import'),str(root));start=s.index('    const string folder=');end=s.index('    var after=Json(State(c,"after"))',start)
 block='''    const string folder="Assets/EUnityValidation01/SourceBoundary29",target=folder+"/LineClass29.compute";
    string project=Directory.GetParent(Application.dataPath).FullName;if(project!=@"C:\\Users\\15352\\Documents\\work\\Fantasy Survival Escape Game"||!AssetDatabase.IsValidFolder(folder)||File.Exists(Path.Combine(project,target)))throw new IOException("29 unexpected project/folder or existing compute; no overwrite");
    var bytes=File.ReadAllBytes(@"'''+str(p)+'''");if(Hash(bytes)!="'''+sha(p)+'''")throw new IOException("29 classifier source changed");New("INTENT.json",Json(receipt));
    using(var f=new FileStream(Path.Combine(project,target),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){f.Write(bytes,0,bytes.Length);f.Flush(true);}AssetDatabase.ImportAsset(target,ImportAssetOptions.ForceSynchronousImport);Stable();
    var cs=AssetDatabase.LoadAssetAtPath<ComputeShader>(target);if(!cs)throw new IOException("29 classifier import missing");var messages=new List<string>();foreach(var m in ShaderUtil.GetComputeShaderMessages(cs)){messages.Add(m.severity+"|"+m.message);if(m.severity.ToString()=="Error")throw new IOException("29 classifier compile: "+m.message);}uint x,y,z;cs.GetKernelThreadGroupSizes(cs.FindKernel("Classify29"),out x,out y,out z);if(x!=8||y!=8||z!=1)throw new IOException("29 classifier ABI mismatch");receipt.Messages=messages.ToArray();receipt.Guid=AssetDatabase.AssetPathToGUID(target);receipt.KernelGroups=new[]{"Classify29:8,8,1"};
'''
 s=s[:start]+block+s[end:];out=root/'RUN_Import25.cs.txt';out.write_text(s,encoding='utf-8',newline='\n');shutil.copyfile(G/'fixed-import/CASE.json',root/'CASE.json')
 sys.path.insert(0,str(H/'producer'));from prepare_live import compile_cs
 compile_cs(out)
 relay=(G/'relay29_fix.py').read_text(encoding='utf-8').replace("'fixed-import'","'class-import'").replace("H/'fixed-import/COMPLETE.json'","H/'class-import/COMPLETE.json'").replace("H/'import/FAILED.json'","H/'class-import/FAILED.json'").replace('PREPARED_IMPORT29_FIX.json','PREPARED_CLASS29.json')
 (G/'relay_class29.py').write_text(relay,encoding='utf-8',newline='\n')
 result={'importSourceSHA256':sha(out),'captureSourceSHA256':sha(G/'run/RUN_Capture25.cs.txt'),'classifierSHA256':sha(p),'CPUBytecodeSHA256':hashlib.sha256(bytecode).hexdigest(),'CPUCompile':'passed','deviceCreated':False,'maxLogicalOutputs':4096,'maxSamplesPerOutput':64,'maxNeighboursPerOutput':4,'BVHOrEnumeration':False,'resultMeaning':'3 independent source-evidence channels; no final RGB editing'}
 (G/'PREPARED_CLASS29.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
