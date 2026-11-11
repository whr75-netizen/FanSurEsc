from pathlib import Path
import json,hashlib,ctypes as C,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face49'
def main():
 for name in ['build','capture','import','shaders','final','console']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 cs=(H/'SourceCarrier48.compute').read_text().replace('SourceCarrier48','SourceDomain49').replace('_SelectedSource48;','_SelectedSource48,_FeatureDomain49;')
 cs=cs.replace('bool nativeVisible=cell.z==1;','float4 domain49=inside?_FeatureDomain49.Load(int3(q,0)):0;bool designed49=domain49.x>=.5;bool nativeVisible=cell.z==1;')
 cs=cs.replace('ownerReceipt?(nativeVisible?2:3):0','ownerReceipt?(nativeVisible?(designed49?4:2):3):0')
 cs=cs.replace('bool sourceCarrier=ownerReceipt&&nativeVisible','bool sourceCarrier=!designed49&&ownerReceipt&&nativeVisible')
 cs=cs.replace('sourceCarrier?float4(4,selectedSource.y,selectedSource.z,selectedSource.w):0;','designed49?float4(-4,domain49.yzw):sourceCarrier?float4(4,selectedSource.y,selectedSource.z,selectedSource.w):0;')
 (H/'SourceDomain49.compute').write_text(cs,encoding='utf-8',newline='\n');(G/'shaders/SourceDomain49.compute').write_text(cs,encoding='utf-8',newline='\n')
 s=(H/'face48/capture/RUN.cs.txt').read_text().replace('face48\\capture','face49\\capture').replace('id="face48-selected-carrier-"','id="face49-source-domain-"').replace('SourceBoundary48/SourceCarrier48.compute','SourceBoundary49/SourceDomain49.compute').replace('FindKernel("SourceCarrier48")','FindKernel("SourceDomain49")')
 assert s.count('main41.colour,main41.preparedMeta')==1;s=s.replace('main41.colour,main41.preparedMeta','main41.colour,main41.preparedMeta,main41.domain');assert s.count('T("_SelectedSource48",main41.preparedMeta);')==1;s=s.replace('T("_SelectedSource48",main41.preparedMeta);','T("_FeatureDomain49",main41.domain);T("_SelectedSource48",main41.preparedMeta);')
 s=s.replace('["layout"]="sidecar2 actual selected preparedMeta; sidecar3 kind4 verified matching mesh carrier. Existing render owner kind is preserved separately. Native canonical owner.w is never decoded as a triangle."','["layout"]="sidecar2 actual selected preparedMeta; sidecar3 +4=ordinary mesh carrier, -4=designed eye-feature footprint domain, 0=unresolved. Primary owner kind4=designed feature, never a native point. Canonical owner tags are not triangles."')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('Fields=new RTHandle[17]','Fields=new RTHandle[18]');rep('Fields[16]=Target(QROI.width,QROI.height);','Fields[16]=Target(QROI.width,QROI.height);Fields[17]=Target(4*QROI.width,QROI.height);')
 rep('main41.colour,main41.preparedMeta,main41.domain','main41.colour,main41.preparedMeta,main41.domain,eye.intrinsic,eye.visible,eye.domain,eye.supportMeta');rep('new[]{Fields[12],Fields[13],Fields[14],Fields[15],Fields[16]}','new[]{Fields[12],Fields[13],Fields[14],Fields[15],Fields[16],Fields[17]}')
 rep('finalRecorded41=true;join41=','if(!eye||eye.intrinsic==null||!eye.intrinsic.rt||!eye.intrinsic.rt.IsCreated()||!eye.candidateEnabled||eye.samplesOnly||eye.full!=host41.head)throw new InvalidOperationException("49 current head feature producer mode invalid; no unproduced texture accepted");finalRecorded41=true;join41=')
 rep('T("_FeatureDomain49",main41.domain);','FrameInfo40["featureProducer49"]=new Obj40{["sourceFeatureInstance"]=eye.GetEntityId().ToString(),["candidateEnabled"]=eye.candidateEnabled,["samplesOnly"]=eye.samplesOnly,["shader"]=AssetDatabase.GetAssetPath(eye.candidateShader),["layout"]="intrinsic/visible/domain/supportMeta from existing unpacked producer RTs; domain must match transported main domain; no legacy ComputeBuffer alias or full-buffer readback"};T("_FeatureDomain49",main41.domain);')
 rep('cmd.CopyTexture(main41.colour.rt,0,0,','int field49=0;foreach(var src49 in new[]{eye.intrinsic,eye.visible,eye.domain,eye.supportMeta}){if(src49.rt.width!=480||src49.rt.height!=272||src49.rt.graphicsFormat!=Fields[17].rt.graphicsFormat)throw new InvalidOperationException("49 feature producer RT ABI");cmd.CopyTexture(src49.rt,0,0,QROI.x,272-QROI.y-QROI.height,QROI.width,QROI.height,Fields[17].rt,0,0,field49++*QROI.width,0);}cmd.CopyTexture(main41.colour.rt,0,0,')
 rep('report["frameInfo"]=producer.FrameInfo40;','var ef49=producer.FieldExtent40(false,17);tasks.Add(new Plane(false,17,"featureProducer49",ef49.x,ef49.y));report["frameInfo"]=producer.FrameInfo40;')
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/domain49.dll')
 p=G/'import/RUN.cs.txt';p.write_text((H/'face48/import/RUN.cs.txt').read_text().replace('face48\\import','face49\\import').replace('face48\\shaders','face49\\shaders').replace('SourceBoundary48','SourceBoundary49').replace('SourceCarrier48','SourceDomain49'),encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import49.dll')
 (G/'final/RUN.cs.txt').write_text((H/'face48/final/RUN.cs.txt').read_text().replace('face48\\final','face49\\final'),encoding='utf-8',newline='\n');(G/'console/ARGS.json').write_bytes((H/'face48/console/ARGS.json').read_bytes())
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;blob=C.c_void_p();error=C.c_void_p();raw=cs.encode()
 try:
  hr=fn(raw,len(raw),b'SourceDomain49',None,None,b'SourceDomain49',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(error));assert hr>=0,api.blob(error).decode(errors='replace');audit=api.token_audit(api.blob(blob));assert audit['loops']==0 and not audit['privateArrayDeclarations'];(G/'SourceDomain49.cpu.dxbc').write_bytes(api.blob(blob))
 finally:api.release(blob);api.release(error)
 (G/'PREPARED49.json').write_text(json.dumps({'CPU_CSharp9':True,'CPUHLSL':audit,'GPUExecuted':False,'newRTsComparedTo48':1,'maxReadBytesPerRequest':262144,'productionOwnerHistoryWrites':False,'borrowedComputeBufferInputs':0,'hypothesis':'48 single-point failures belong to designed feature footprint domain, not ordinary point carriers','captureSHA256':hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest()},indent=2),encoding='utf-8');print('49 domain-separated source C#9/HLSL CPU compiled; no Unity/GPU executed')
if __name__=='__main__':main()
