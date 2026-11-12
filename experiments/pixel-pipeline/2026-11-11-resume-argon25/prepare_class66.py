"""Private classification fix: generic exterior contour cannot paint its own actor."""
from pathlib import Path
import json,hashlib,sys,ctypes as C,re
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face66'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=json.loads((H/'face65/capture/COMPLETE.json').read_text());assert old['Edit'] and old['restorationChecksPass'] and old['ownedResourcesReleased'] and old['pendingOwners']==0
 for d in ['capture','shaders','build','import','final']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 c=(H/'face62/shaders/SourceNativeHull60.compute').read_text()
 assert c.count('int _OwnerScope45;')==1;c=c.replace('int _OwnerScope45;','int _OwnerScope45;int _OutlineClass66; //0=native material hull reference,1=generic actor-exterior silhouette')
 needle='bool use=source&&style&&visible&&!child62;';assert c.count(needle)==1
 c=c.replace(needle,'bool classEligible66=_OutlineClass66==0||(_OutlineClass66==1&&cell.z!=1);bool use=source&&style&&visible&&!child62&&classEligible66;')
 assert'while('not in c and'for('not in c;(G/'shaders/SourceNativeHull60.compute').write_text(c,encoding='utf-8',newline='\n')
 # CPU shader compilation/reflection uses no D3D device or Unity API.
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 raw=re.sub(rb'(?m)^#pragma kernel [^\r\n]+\r?\n',b'',c.encode());data=C.create_string_buffer(raw);code=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(data,len(raw),b'SourceNativeHull60.compute',None,None,b'SourceNativeHull60',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(code),C.byref(err));assert hr>=0,api.blob(err).decode(errors='replace');bytecode=api.blob(code);audit=api.token_audit(bytecode);assert audit['loops']==0 and audit['threads']==[8,8,1] and not audit['privateArrayDeclarations'];bindings,constants=api.reflect(dll,bytecode);(G/'build/class66.cpu.dxbc').write_bytes(bytecode)
 finally:api.release(code);api.release(err)
 s=(H/'face65/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face65\\capture','resume-20261111\\face66\\capture').replace('face65-native-motion-','face66-exterior-motion-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('Fields[26]=Target(8*QROI.width,2*QROI.height);Fields[27]=Target(8*QROI.width,QROI.height);','Fields[26]=Target(10*QROI.width,2*QROI.height);Fields[27]=Target(10*QROI.width,QROI.height);')
 rep('cmd.SetComputeVectorParam(final41,"_Ink41",sourceInk);foreach(int c61 in new[]{0,2,3,1})','cmd.SetComputeVectorParam(final41,"_Ink41",sourceInk);foreach(int c61 in new[]{0,2,3,4,1})')
 rep('T("_Line41",Fields[field61]);T("_Proof41",Fields[field61+1]);cmd.DispatchCompute','T("_Line41",Fields[field61]);T("_Proof41",Fields[field61+1]);cmd.SetComputeIntParam(final41,"_OutlineClass66",c61==4?0:1);cmd.DispatchCompute')
 rep('["scales"]=new Arr40(0,1,8,32)','["scales"]=new Arr40(0,1,8,32,32),["classification66"]=new Arr40("exterior","exterior","exterior","exterior","native-hull-reference"),["defaultMode66"]="exterior only; current actor occupancy rejected; pigment and lid producer paths unchanged"')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/class66.dll')
 prefix=(H/'face49/capture/RUN.cs.txt').read_text();prefix=prefix[:prefix.index('// Prepared helper only')];imp=prefix+(H/'UpdateOwned62.cs.txt').read_text().replace('resume-20261111\\face62\\','resume-20261111\\face66\\');(G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import66.dll')
 before=H/'face62/shaders/SourceNativeHull60.compute';expected={'beforeSHA':sha(before),'afterSHA':sha(G/'shaders/SourceNativeHull60.compute'),'guid':'e6f555999930fe84986310c502927d67'};(G/'import/EXPECTED.json').write_text(json.dumps(expected,indent=2))
 pre=(H/'face65/post/RUN.cs.txt').read_text().replace('resume-20261111\\face65"','resume-20261111\\face66"').replace('Path.Combine(Root,"capture","INPUT_BEFORE.json")','@"'+str(H/'face65/capture/INPUT_BEFORE.json')+'"').replace('Path.Combine(Root,"post","STATE.json")','Path.Combine(Root,"final","STATE.json")')
 (G/'final/RUN.cs.txt').write_text(pre,encoding='utf-8',newline='\n');compile_unity_language(G/'final/RUN.cs.txt',G/'build/pre66.dll')
 result={'CSharp9Compiled':True,'CPUShaderCompiled':True,'tokenAudit':audit,'newGPUResources':0,'same8x8ABI':True,'newPrivateArray':False,'cases':['exterior0','exterior1','exterior8','exterior32','same-frame native hull32 control'],'normalConsecutiveFrames':6,'same120sDeadline':True,'perOwnerReads':1,'maxGlobalReadbacks':6,'readByteUpper':262144,'shadersOnlyImportRequired':True,'product77DefaultChanged':False,'GPUExecuted':False,'captureSHA256':sha(G/'capture/RUN.cs.txt'),'computeSHA256':expected['afterSHA']};(G/'CPU_PREPARED66.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
