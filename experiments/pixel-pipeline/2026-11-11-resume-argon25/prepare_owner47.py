from pathlib import Path
import json,hashlib,ctypes as C,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face47'
def main():
 for name in ['build','capture','import','shaders','final','console']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 cs=(H/'SourceOwner45.compute').read_text().replace('SourceOwner45','SourceOwner47')
 cs=cs.replace('RWTexture2D<float4> _Atlas41,_NativeAfter42;','Texture2D<float4> _NativeOwner47,_SurfaceUV47;\nRWTexture2D<float4> _Atlas41,_NativeAfter42,_OwnerReceipts47;')
 cs=cs.replace('_Atlas41[local+int2(15*_Size41.x,0)]=use?float4(1,proof.y,_OwnerScope45,proof.z):0;','float4 originalOwner=_NativeOwner47.Load(int3(p,0));float4 originalUV=inside?_SurfaceUV47.Load(int3(q,0)):0;\n bool nativeVisible=cell.z==1;bool ownerReceipt=inside&&finite&&matched&&all(isfinite(originalOwner))&&all(isfinite(originalUV));\n _Atlas41[local+int2(15*_Size41.x,0)]=use?float4(1,proof.y,_OwnerScope45,proof.z):float4(ownerReceipt?(nativeVisible?2:3):0,0,_OwnerScope45,0);\n _OwnerReceipts47[local]=originalOwner;_OwnerReceipts47[local+int2(_Size41.x,0)]=originalUV;\n _OwnerReceipts47[local+int2(2*_Size41.x,0)]=use?float4(proof.y,proof.z,0,0):originalOwner;\n _OwnerReceipts47[local+int2(3*_Size41.x,0)]=float4(nativeVisible?1:0,inside?1:0,matched?1:0,ownerReceipt?1:0);')
 (H/'SourceOwner47.compute').write_text(cs,encoding='utf-8',newline='\n');(G/'shaders/SourceOwner47.compute').write_text(cs,encoding='utf-8',newline='\n')
 s=(H/'face45/capture/RUN.cs.txt').read_text().replace('face45\\capture','face47\\capture').replace('id="face45-owner-"','id="face47-typed-owner-"').replace('SourceBoundary45/SourceOwner45.compute','SourceBoundary47/SourceOwner47.compute').replace('FindKernel("SourceOwner45")','FindKernel("SourceOwner47")')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('Fields=new RTHandle[15]','Fields=new RTHandle[16]');rep('Fields[14]=Target(2*QROI.width,2*QROI.height,uav:true);','Fields[14]=Target(2*QROI.width,2*QROI.height,uav:true);Fields[15]=Target(4*QROI.width,QROI.height,uav:true);')
 rep('native42.output,main41.resolvedMeta,native42.depthAudit,native42.cellID','native42.output,main41.resolvedMeta,native42.depthAudit,native42.cellID,native42.owner,main41.resolvedUV');rep('new[]{Fields[12],Fields[13],Fields[14]}','new[]{Fields[12],Fields[13],Fields[14],Fields[15]}');rep('T("_Atlas41",Fields[12]);','T("_NativeOwner47",native42.owner);T("_SurfaceUV47",main41.resolvedUV);T("_OwnerReceipts47",Fields[15]);T("_Atlas41",Fields[12]);')
 rep('report["frameInfo"]=producer.FrameInfo40;','var eo47=producer.FieldExtent40(false,15);tasks.Add(new Plane(false,15,"ownerReceipts47",eo47.x,eo47.y));report["frameInfo"]=producer.FrameInfo40;')
 s=s.replace('["layout"]="kind1,sourceEdge,localScopeSlot,finiteSourceT; zero=unresolved unchanged native backing"','["layout"]="kind1 SourceCurve(edge,t); kind2 original NativeProducerOwner raw payload, not assumed real triangle; kind3 WorldUnresolved; kind0 invalid receipt. Separate borrowed native backing/UV receipts; no curve-to-primitive alias"')
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/owner47.dll')
 p=G/'import/RUN.cs.txt';p.write_text((H/'face45/import/RUN.cs.txt').read_text().replace('face45\\import','face47\\import').replace('face45\\shaders','face47\\shaders').replace('SourceBoundary45','SourceBoundary47').replace('SourceOwner45','SourceOwner47'),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import47.dll')
 (G/'final/RUN.cs.txt').write_text((H/'face45/final/RUN.cs.txt').read_text().replace('face45\\final','face47\\final'),encoding='utf-8',newline='\n');(G/'console/ARGS.json').write_bytes((H/'face45/console/ARGS.json').read_bytes())
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;blob=C.c_void_p();error=C.c_void_p();raw=cs.encode()
 try:
  hr=fn(raw,len(raw),b'SourceOwner47',None,None,b'SourceOwner47',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(error));assert hr>=0,api.blob(error).decode(errors='replace');audit=api.token_audit(api.blob(blob));assert audit['loops']==0 and not audit['privateArrayDeclarations'];(G/'SourceOwner47.cpu.dxbc').write_bytes(api.blob(blob))
 finally:api.release(blob);api.release(error)
 (G/'PREPARED47.json').write_text(json.dumps({'CPU_CSharp9':True,'CPUHLSL':audit,'GPUExecuted':False,'newRTs':1,'maxReadBytesPerRequest':262144,'productionOwnerHistoryWrites':False,'typedOwners':['SourceCurve','OriginalNativeProducerOwner','WorldUnresolved'],'captureSHA256':hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest()},indent=2),encoding='utf-8');print('47 C#9/HLSL CPU compiled; no Unity/GPU executed')
if __name__=='__main__':main()
