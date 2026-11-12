from pathlib import Path
import json,subprocess,sys
import checkpoint_cloth94 as prior
from checkpoint92 import H,R,P,DOC,sha,git,save
G=H/'face97';HEAD='030f0d56b7918004108402d96cd4c781f0bd34d6'

def selected():
 ns=[p.name for p in H.glob('*97.py')if p.name!='joint_visibility97.py']+['JointLine97.cs','JointLineTests97.cs','JointLineFixture97.cs','JointRibbon97.cs.txt','JointRibbon97.shader','SourceFootprint97.shader','face97/CPU_SHADER97.json','face97/CPU_FIXTURE97.json','face97/FAILED_COMPILATION97.json','face97/SUMMARY97.json']
 for shader in['JointRibbon97','SourceFootprint97']:ns += ['face97/import-'+shader+'/import/'+n for n in['RUN.cs.txt','EXPECTED.json','COMPLETE.json']]
 for name in['oneB','oneC','motion64']:
  root=G/name;r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];assert r['stream77']['sourceAlpha97ManagedBytesAfterRelease']==0
  ns += ['face97/'+name+'/'+n for n in ['CPU_PREPARED97.json','capture/RUN.cs.txt','capture/COMPLETE.json','capture/TRANSPORT_HOLD.json','capture/RUNTIME_PALETTE89.rgb','capture/RUNTIME_PALETTE89.json','capture/SOURCE_TABLE77.json','capture/ACTOR_MATERIALS96.json','capture/ALPHA96.zip','capture/INPUT_BEFORE.json','capture/NATIVE_BEFORE73.json','capture/GLOBALS_BEFORE.bin','post/final/STATE.json','ACTUAL_JOINT97.json','ACTUAL_JOINT97.png','ACTUAL_SEQUENCE97.webp']]
  for f in r['stream77']['frames']:
   if'actorSource96'not in f:continue
   ns += ['face97/'+name+'/capture/'+n for n in[f['compressedFile'],f['light84']['sourceGeometryFile'],f['ribbon93']['file'],f['actorSource96']['file']]]
 ns += ['face97/motion64/SEQUENCE_REVIEW97.png']
 return list(dict.fromkeys(ns))

def main():
 prior.preserved();ns=selected();assert all((H/n).is_file()for n in ns),[n for n in ns if not(H/n).is_file()];manifest={'files':[{'path':n,'sha256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns],'all64RawCopied':False,'actualFullActorFramesCopied':6,'defaultProduct77Changed':False,'oldDeniedBulkRetried':False};save(G/'SELECTION97.json',manifest);print(json.dumps({'files':len(ns),'bytes':sum(x['bytes']for x in manifest['files'])}),flush=True)
 if '--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only');old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);now=(R/DOC).read_bytes();assert now.startswith(old)and now[len(old):].decode('utf-8').lstrip().startswith('## 97.')
 for n in ns:
  dst=R/P/n;assert not dst.exists(),'new97 snapshot collision: '+n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((H/n).read_bytes());assert sha(dst)==sha(H/n)
 save(R/P/'face97/SELECTION97.json',manifest);assets=[]
 for shader in['JointRibbon97','SourceFootprint97']:
  group=['Assets/EUnityValidation01/'+shader+'.meta','Assets/EUnityValidation01/'+shader+'/'+shader+'.shader','Assets/EUnityValidation01/'+shader+'/'+shader+'.shader.meta'];assert sha(R/group[1])==sha(H/(shader+'.shader'))and all(not git('ls-files','--',n)for n in group);assets+=group
 paths=[P+'/'+n for n in ns]+[P+'/face97/SELECTION97.json',DOC]+assets;spec=G/'SELECT97.paths';spec.write_bytes(('\0'.join(paths)+'\0').encode());git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in paths if p.endswith('.meta')or p.endswith('RUN.cs.txt')]);prior.preserved()
 body=G/'COMMIT_BODY97.txt';body.write_text('Connect current-frame joint source/destination line visibility\n\nImplement bounded CPU selection from evaluated actor geometry and original alpha, then compose current finite LUT/original ink on GPU. Preserve partial source support and explicit unknown appearance, remove only fully covered source pieces, and release a single outer-owned alpha cache after normal exit.\n\nPreserve the dynamic-compiler pre-execution failure and rejected GetPixelBilinear sampler mismatch. Correct texel-centre sampling, verify1+1+64 actual frames,156 captured source/destination point queries,33 removed occluded line cells and86 recovered cells. Keep the opaque-area/art/performance limitations explicit and product77/default/user changes unchanged. No115, reset, forced termination, broad save or push.\n',encoding='utf-8');print(git('commit','--file',str(body)),flush=True);assert not git('diff','--cached','--name-only');prior.preserved();save(G/'COMMIT97.json',{'commit':git('rev-parse','HEAD'),'paths':len(paths),'user30Protected128PreservedWithApproved94Hunks':True,'product77DefaultChanged':False,'currentFullOpacityVariantAdopted':False,'GPUActualRuns':[1,1,64],'sourceAlphaCacheBytesAfterRelease':0,'newGPUCompute':0,'push':False});print((G/'COMMIT97.json').read_text())
if __name__=='__main__':main()
