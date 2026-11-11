from pathlib import Path
import json,hashlib,sys,ctypes as C
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face42'
def main():
 for n in ['build','capture','import','shaders','final','console']:(G/n).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 old=H/'face41/capture/RUN.cs.txt';s=old.read_text().replace('face41\\capture','face42\\capture').replace('id="face41-final-"','id="face42-native-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('readonly RTHandle[] Fields=new RTHandle[13]','readonly RTHandle[] Fields=new RTHandle[15]')
 rep(' void Prepare(){\n',' void Prepare(){\n  PrepareWorld41();\n')
 rep('Fields[12]=Target(QROI.width*15,QROI.height,uav:true);','Fields[12]=Target(QROI.width*15,QROI.height,uav:true);Fields[13]=Target(2*QROI.width,2*QROI.height);Fields[14]=Target(2*QROI.width,2*QROI.height,uav:true);')
 rep('tasks.Add(new Plane(false,12,"atlas40",extent.x,extent.y));','tasks.Add(new Plane(false,12,"atlas40",extent.x,extent.y));foreach(int ni42 in new[]{13,14}){var ne42=producer.FieldExtent40(false,ni42);tasks.Add(new Plane(false,ni42,ni42==13?"nativeBefore42":"nativeAfter42",ne42.x,ne42.y));}')
 a=s.rindex('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {');helper=(H/'FinalContour42.cs').read_text();helper=helper[helper.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];s=s[:a]+helper
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/native42.dll')
 imp=(H/'face41/fix1/import/RUN.cs.txt').read_text();prefix,body=imp.split('internal class CommandScript',1);body=body.replace('face41\\fix1\\import','face42\\import').replace('face41\\shaders','face42\\shaders').replace('SourceBoundary41','SourceBoundary42').replace('ContourFinal41.compute','ContourNative42.compute').replace('FinalContour41','NativeContour42');imp=prefix+'internal class CommandScript'+body;p=G/'import/RUN.cs.txt';p.write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import42.dll')
 raw=(H/'ContourNative42.compute').read_bytes();(G/'shaders/ContourNative42.compute').write_bytes(raw);sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;blob=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(raw,len(raw),b'ContourNative42',None,None,b'NativeContour42',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(err));assert hr>=0,api.blob(err).decode(errors='replace');audit=api.token_audit(api.blob(blob));assert audit['threads']==[8,8,1]and audit['loops']==0 and not audit['privateArrayDeclarations']
 finally:api.release(blob);api.release(err)
 source=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\NativePlayer395\Shaders\Native395.compute');(G/'PRESENTER_INPUT42.json').write_text(json.dumps({'path':str(source),'SHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'shaderSourceReadOnly':True,'sampling':'q=floor((p+.5-origin)/scale-delta); worldSample=floor(origin+(q+.5+delta)*scale), clamped; same q shares world colour/depth','41Limit':'Compose333 480 output is intermediate. Actual delivered source is NativeWorldFeature395.Present at601, output960x544. Candidate consumer at605.'},indent=2),encoding='utf-8')
 (G/'PREPARED42.json').write_text(json.dumps({'CPUCompile':True,'CPUHLSL':audit,'UnityGPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'maxThreads':4096,'maxReadBytes':262144,'nativeScaleSupported':2,'extraNativeRTs':2,'borrowedWrites':False,'historyWrites':False},indent=2),encoding='utf-8');print('native42 CPU C#9/HLSL compiled; no Unity/GPU execution')
if __name__=='__main__':main()
