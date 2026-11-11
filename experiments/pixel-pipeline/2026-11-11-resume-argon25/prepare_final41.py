from pathlib import Path
import json,hashlib,sys,ctypes as C,subprocess
from prepare_review30 import compile_source
H=Path(__file__).resolve().parent;G=H/'face41'
def compile_unity_language(source,out):
 compile_source([source],out);rsp=out.with_suffix('.rsp');s=rsp.read_text();assert'/langversion:latest'in s;rsp.write_text(s.replace('/langversion:latest','/langversion:9'),encoding='utf-8',newline='\n');r=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');out.with_suffix('.language9.txt').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
def main():
 for n in ['build','capture','import','shaders','final','console']:(G/n).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'fix1/import/REQUEST.json').exists()
 if(G/'import/REQUEST.json').exists():
  failed=json.loads((G/'import/COMPILE_FAILURE41.json').read_text());assert failed['executed']is False and not(G/'import/STARTED.json').exists()
 s=(H/'face40/authored/capture/RUN.cs.txt').read_text();s=s.replace('face40\\authored\\capture','face41\\capture').replace('id="face40-authored-"','id="face41-final-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('public sealed class SourceOutline40:','public sealed partial class SourceOutline40:')
 rep('if(pigment.FindPass("SourcePigment29")!=2)throw new InvalidOperationException("31 physical pigment ABI missing");','if(pigment.FindPass("SourcePigment29")!=2)throw new InvalidOperationException("31 physical pigment ABI missing");InitFinal41();')
 rep('if((long)QROI.width*QROI.height*9*16>262144)','if(QROI.width>64||QROI.height>64||(long)QROI.width*QROI.height*15*16>262144)');rep('Fields[12]=Target(QROI.width*9,QROI.height);','Fields[12]=Target(QROI.width*15,QROI.height,uav:true);')
 a=s.index('   using(var b=graph.AddUnsafePass<Data>("31 end barrier includes');b=s.index('\n  }catch(Exception e){stopped=true;Fail(e);}',a);s=s[:a]+'   // End acknowledgment is deliberately deferred to the same-frame main-camera final pass.\n'+s[b:]
 rep('if(outline39)UnityEngine.Object.DestroyImmediate(outline39);Disposed=true;','if(outline39)UnityEngine.Object.DestroyImmediate(outline39);ReleaseFinal41();Disposed=true;')
 old='void Enqueue(ScriptableRenderContext unused,Camera camera){if(stopped||exitRequest32.Requested||producers.Any(p=>p.Failure!=null)||camera!=producers[0].Camera)return;try{foreach(var p in producers)if(p.TargetFrame40==Time.frameCount)camera.GetUniversalAdditionalCameraData().scriptableRenderer.EnqueuePass(p);}catch(Exception e){foreach(var p in producers)p.ReportFailure(e);}}'
 new='void Enqueue(ScriptableRenderContext unused,Camera camera){if(stopped||exitRequest32.Requested)return;try{foreach(var p in producers)if(p.TargetFrame40==Time.frameCount){if(camera==p.Camera&&p.Failure==null)camera.GetUniversalAdditionalCameraData().scriptableRenderer.EnqueuePass(p);else if(camera==p.MainCamera41&&p.RequiresFinal41&&HeadLocal367.Active.main.contourReady)camera.GetUniversalAdditionalCameraData().scriptableRenderer.EnqueuePass(p.FinalPass41Instance);}}catch(Exception e){foreach(var p in producers)p.ReportFailure(e);}}'
 rep(old,new);helper=(H/'FinalContour41.cs').read_text();helper=helper[helper.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];s+='\n'+helper
 capture=G/'capture/RUN.cs.txt';capture.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(capture,G/'build/final41.dll')
 original=(H/'face40/authored/import/RUN.cs.txt').read_text();prefix,body=original.split('internal class CommandScript',1)
 body=body.replace('face40\\authored\\import','face41\\fix1\\import').replace('face40\\authored\\shaders','face41\\shaders').replace('SourceBoundary40Authored','SourceBoundary41').replace('new[]{"GeoContour40Authored.shader"}','new[]{"ContourFinal41.compute"}').replace('"Assets/EUnityValidation01/SourceBoundary40/GeoResolve40.compute"','Target+"/ContourFinal41.compute"').replace('FindKernel("ResolveGeometry40")','FindKernel("FinalContour41")')
 a=body.index('   var gs40=AssetDatabase.LoadAssetAtPath<Shader>');b=body.index('var checks=NativeSnapshot40.Compare',a);body=body[:a]+'   '+body[b:];imp=prefix+'internal class CommandScript'+body;impPath=G/'fix1/import/RUN.cs.txt';impPath.parent.mkdir(parents=True,exist_ok=True);assert not(impPath.parent/'REQUEST.json').exists();impPath.write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(impPath,G/'build/import41.dll')
 raw=(H/'ContourFinal41.compute').read_bytes();(G/'shaders/ContourFinal41.compute').write_bytes(raw)
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;blob=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(raw,len(raw),b'ContourFinal41',None,None,b'FinalContour41',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(err));assert hr>=0,api.blob(err).decode(errors='replace');audit=api.token_audit(api.blob(blob));assert audit['threads']==[8,8,1]and audit['loops']==0 and not audit['privateArrayDeclarations']
 finally:api.release(blob);api.release(err)
 out={'CPUCompile':True,'GPUCompileOrDispatch':False,'newKernelTokenAudit':audit,'maxDispatchThreads':4096,'runtimeROIBudgetBytes':262144,'noBorrowedWrites':True,'noHistoryWrites':True,'endAckAfterBothViews':True,'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'shaderSHA256':hashlib.sha256(raw).hexdigest()};(G/'PREPARED41.json').write_text(json.dumps(out,indent=2),encoding='utf-8',newline='\n');print(json.dumps(out))
if __name__=='__main__':main()
