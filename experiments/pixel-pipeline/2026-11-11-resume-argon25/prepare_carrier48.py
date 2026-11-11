from pathlib import Path
import json,hashlib,ctypes as C,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face48'
def main():
 for name in ['build','capture','import','shaders','final','console']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 cs=(H/'SourceOwner47.compute').read_text().replace('SourceOwner47','SourceCarrier48').replace('Texture2D<float4> _NativeOwner47,_SurfaceUV47;','Texture2D<float4> _NativeOwner47,_SurfaceUV47,_SelectedSource48;\nint _RegisteredRole48,_RegisteredTriangleCount48;')
 cs=cs.replace('_OwnerReceipts47[local+int2(2*_Size41.x,0)]=use?float4(proof.y,proof.z,0,0):originalOwner;\n _OwnerReceipts47[local+int2(3*_Size41.x,0)]=float4(nativeVisible?1:0,inside?1:0,matched?1:0,ownerReceipt?1:0);','float4 selectedSource=inside?_SelectedSource48.Load(int3(q,0)):0;\n bool sourceCarrier=ownerReceipt&&nativeVisible&&all(isfinite(selectedSource))&&selectedSource.x==originalOwner.z&&selectedSource.y==originalOwner.x&&selectedSource.z==originalOwner.y&&selectedSource.y==_RegisteredRole48&&selectedSource.w>0&&selectedSource.w<=_RegisteredTriangleCount48&&selectedSource.w==round(selectedSource.w);\n _OwnerReceipts47[local+int2(2*_Size41.x,0)]=selectedSource;\n _OwnerReceipts47[local+int2(3*_Size41.x,0)]=sourceCarrier?float4(4,selectedSource.y,selectedSource.z,selectedSource.w):0;')
 (H/'SourceCarrier48.compute').write_text(cs,encoding='utf-8',newline='\n');(G/'shaders/SourceCarrier48.compute').write_text(cs,encoding='utf-8',newline='\n')
 s=(H/'face47/capture/RUN.cs.txt').read_text().replace('face47\\capture','face48\\capture').replace('id="face47-typed-owner-"','id="face48-selected-carrier-"').replace('SourceBoundary47/SourceOwner47.compute','SourceBoundary48/SourceCarrier48.compute').replace('FindKernel("SourceOwner47")','FindKernel("SourceCarrier48")')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('native42.owner,main41.resolvedUV,main41.colour','native42.owner,main41.resolvedUV,main41.colour,main41.preparedMeta')
 rep('T("_NativeOwner47",native42.owner);','T("_SelectedSource48",main41.preparedMeta);T("_NativeOwner47",native42.owner);')
 rep('cmd.SetComputeIntParam(final41,"_OwnerScope45",1);','int materialSlot48=originals.Take(renderer).Sum(v=>v.Length)+submesh;int role48=Mathf.RoundToInt(qOriginals[materialSlot48].GetFloat("_Auto245Role"))+1;if(role48<1||role48>16)throw new InvalidOperationException("48 registered source role missing");cmd.SetComputeIntParam(final41,"_RegisteredRole48",role48);cmd.SetComputeIntParam(final41,"_RegisteredTriangleCount48",(int)meshes[renderer].GetIndexCount(submesh)/3);FrameInfo40["sourceCarrier48"]=new Obj40{["registeredRole"]=role48,["rendererOrdinal"]=renderer,["subMesh"]=submesh,["triangleCount"]=(int)meshes[renderer].GetIndexCount(submesh)/3,["layout"]="sidecar2 actual selected preparedMeta; sidecar3 kind4 verified matching mesh carrier. Existing render owner kind is preserved separately. Native canonical owner.w is never decoded as a triangle."};cmd.SetComputeIntParam(final41,"_OwnerScope45",1);')
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/carrier48.dll')
 p=G/'import/RUN.cs.txt';p.write_text((H/'face47/import/RUN.cs.txt').read_text().replace('face47\\import','face48\\import').replace('face47\\shaders','face48\\shaders').replace('SourceBoundary47','SourceBoundary48').replace('SourceOwner47','SourceCarrier48'),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import48.dll')
 (G/'final/RUN.cs.txt').write_text((H/'face47/final/RUN.cs.txt').read_text().replace('face47\\final','face48\\final'),encoding='utf-8',newline='\n');(G/'console/ARGS.json').write_bytes((H/'face47/console/ARGS.json').read_bytes())
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;blob=C.c_void_p();error=C.c_void_p();raw=cs.encode()
 try:
  hr=fn(raw,len(raw),b'SourceCarrier48',None,None,b'SourceCarrier48',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(error));assert hr>=0,api.blob(error).decode(errors='replace');audit=api.token_audit(api.blob(blob));assert audit['loops']==0 and not audit['privateArrayDeclarations'];(G/'SourceCarrier48.cpu.dxbc').write_bytes(api.blob(blob))
 finally:api.release(blob);api.release(error)
 (G/'PREPARED48.json').write_text(json.dumps({'CPU_CSharp9':True,'CPUHLSL':audit,'GPUExecuted':False,'newRTsComparedTo47':0,'maxReadBytesPerRequest':262144,'productionOwnerHistoryWrites':False,'carrierIsColourFamily':False,'captureSHA256':hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest()},indent=2),encoding='utf-8');print('48 selected source-carrier C#9/HLSL CPU compiled; no Unity/GPU executed')
if __name__=='__main__':main()
