from pathlib import Path
import json,hashlib,sys,ctypes as C
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face45'
def main():
 for name in ['build','capture','import','shaders','final','console']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 cs=(H/'ContourNative42.compute').read_text().replace('NativeContour42','SourceOwner45')
 assert cs.count('int2 _Size41')==1;cs=cs.replace('int2 _Size41','int _OwnerScope45;\nint2 _Size41')
 cs=cs.replace('_Atlas41[local+int2(14*_Size41.x,0)]=cell;','_Atlas41[local+int2(14*_Size41.x,0)]=cell;\n // Explicit SourceCurve namespace; zero means unchanged native backing with unresolved source owner.\n _Atlas41[local+int2(15*_Size41.x,0)]=use?float4(1,proof.y,_OwnerScope45,proof.z):0;')
 (H/'SourceOwner45.compute').write_text(cs,encoding='utf-8',newline='\n');(G/'shaders/SourceOwner45.compute').write_text(cs,encoding='utf-8',newline='\n')
 s=(H/'face44/capture/RUN.cs.txt').read_text().replace('face44\\capture','face45\\capture').replace('id="face44-nearest-"','id="face45-owner-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('Assets/EUnityValidation01/SourceBoundary42/ContourNative42.compute','Assets/EUnityValidation01/SourceBoundary45/SourceOwner45.compute');rep('FindKernel("NativeContour42")','FindKernel("SourceOwner45")')
 rep('QROI.width*QROI.height*15*16','QROI.width*QROI.height*16*16');rep('Fields[12]=Target(QROI.width*15,QROI.height,uav:true);','Fields[12]=Target(QROI.width*16,QROI.height,uav:true);')
 rep('cmd.SetComputeIntParams(final41,"_Size41",QROI.width,QROI.height);','cmd.SetComputeIntParam(final41,"_OwnerScope45",1);cmd.SetComputeIntParams(final41,"_Size41",QROI.width,QROI.height);')
 rep('if(FrameInfo40!=null&&worldProof41!=null)FrameInfo40["worldFixture41"]=worldProof41;','if(FrameInfo40!=null&&worldProof41!=null)FrameInfo40["worldFixture41"]=worldProof41;FrameInfo40["sourceOwner45"]=new Obj40{["slot"]=1,["ownerKind"]="SourceCurve",["featureOwnerInstance"]=eye.GetEntityId().ToString(),["cameraInstance"]=cameraIdentity,["model"]=model,["lifetimeSourcePacket"]=packet.Split(new[]{"/sequence"},StringSplitOptions.None)[0],["layout"]="kind1,sourceEdge,localScopeSlot,finiteSourceT; zero=unresolved unchanged native backing",["productionHistoryWrites"]=false};')
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/owner45.dll')
 s=(H/'face42/import/RUN.cs.txt').read_text();prefix,body=s.split('internal class CommandScript',1);body=body.replace('face42\\import','face45\\import').replace('face42\\shaders','face45\\shaders').replace('SourceBoundary42','SourceBoundary45').replace('ContourNative42.compute','SourceOwner45.compute').replace('NativeContour42','SourceOwner45');p=G/'import/RUN.cs.txt';p.write_text(prefix+'internal class CommandScript'+body,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import45.dll')
 p=G/'final/RUN.cs.txt';p.write_text((H/'face44/final/RUN.cs.txt').read_text().replace('face44\\final','face45\\final'),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/final45.dll')
 (G/'console/ARGS.json').write_bytes((H/'face44/console/ARGS.json').read_bytes())
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;blob=C.c_void_p();error=C.c_void_p();raw=cs.encode()
 try:
  hr=fn(raw,len(raw),b'SourceOwner45',None,None,b'SourceOwner45',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(error));assert hr>=0,api.blob(error).decode(errors='replace');audit=api.token_audit(api.blob(blob));assert audit['threads']==[8,8,1]and audit['loops']==0 and not audit['privateArrayDeclarations'];(G/'SourceOwner45.cpu.dxbc').write_bytes(api.blob(blob))
 finally:api.release(blob);api.release(error)
 (G/'PREPARED45.json').write_text(json.dumps({'CPU_CSharp9':True,'CPUHLSL':audit,'GPUExecuted':False,'newRTs':0,'atlasFields':16,'maxReadBytes':262144,'newKernel':'SourceOwner45 derived from executed NativeContour42 with one extra typed-owner store; no selector/BVH/loop','captureSHA256':hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest(),'product77OrProductionOwnerWrites':False},indent=2),encoding='utf-8');print('owner45 C#9/HLSL CPU compilation passed; no Unity/GPU execution')
if __name__=='__main__':main()
