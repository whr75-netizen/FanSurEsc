"""Preserve100/101 source-reason evidence without promoting an untested branch."""
from pathlib import Path
import json,subprocess,sys
import checkpoint_cloth94 as guard
from checkpoint92 import H,R,P,DOC,sha,git,save
G=H/'face101';HEAD='921865f814414392c65a07d9c9046c0eeadac40f'

def selected():
 ns=[p.name for n in ['100','101']for p in H.glob('*'+n+'.py')]+['SourceFootprint100.shader','SourceValue101.shader','SourceFootprint101.shader','SourceFootprint101B.shader','actor_visibility96.py','face99/COMMIT99.json']
 for folder,name in [('face100','reasons32'),('face101','source32')]:
  base=H/folder;root=base/name;r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['Edit']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']and r['received77']==32
  ns += [str(p.relative_to(H)).replace('\\','/')for p in base.glob('*.json')if p.name not in ['COMMIT101.json','SELECTION101.json']]
  ns += [folder+'/'+name+'/'+n for n in ['capture/RUN.cs.txt','capture/COMPLETE.json','capture/TRANSPORT_HOLD.json','capture/RUNTIME_PALETTE89.rgb','capture/RUNTIME_PALETTE89.json','capture/SOURCE_TABLE77.json','capture/ACTOR_MATERIALS96.json','capture/ALPHA96.zip','capture/PACKETS99.zip','capture/INPUT_BEFORE.json','capture/NATIVE_BEFORE73.json','capture/GLOBALS_BEFORE.bin','preflight/final/STATE.json','post/final/STATE.json']]
  ns += [str(p.relative_to(H)).replace('\\','/')for p in root.glob('*')if p.is_file()and p.suffix in ['.json','.png','.webp']]
  for f in r['stream77']['frames']:
   if 'actorSource96'in f:ns += [folder+'/'+name+'/capture/'+n for n in [f['actorSource96']['file'],f['light84']['sourceGeometryFile'],f['ribbon93']['file']]]
  for importFolder in base.glob('import*'):
   if importFolder.is_dir()and(importFolder/'import/COMPLETE.json').is_file():ns += [str((importFolder/'import'/n).relative_to(H)).replace('\\','/')for n in ['RUN.cs.txt','EXPECTED.json','COMPLETE.json']]
 return list(dict.fromkeys(ns))

def main():
 guard.preserved();ns=selected();assert all((H/n).is_file()for n in ns),[n for n in ns if not(H/n).is_file()];actorCount=sum(sum('actorSource96'in f for f in json.loads((H/d/n/'capture/COMPLETE.json').read_text())['stream77']['frames'])for d,n in [('face100','reasons32'),('face101','source32')]);manifest={'files':[{'path':n,'sha256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns],'actualRuns':[32,32],'allOriginalPacketsLosslesslyArchived':True,'selectedActorGeometryFrames':actorCount,'mainViewAlternativeExercised':False,'mainViewAlternativeAdopted':False,'product77DefaultChanged':False,'oldDeniedBulkRetried':False};save(G/'SELECTION101.json',manifest);print(json.dumps({'files':len(ns),'bytes':sum(x['bytes']for x in manifest['files'])}),flush=True)
 if '--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only');old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);now=(R/DOC).read_bytes();assert now.startswith(old)and now[len(old):].decode('utf-8').lstrip().startswith('## 100.')
 state=json.loads((G/'source32/post/final/STATE.json').read_text());assert state['Edit']and not state['compiling']and state['inputJSONExact']and len(state['dirty'])==31 and state['allRTCount']==30 and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==0
 for n in ns:
  dst=R/P/n
  if dst.exists():assert n=='actor_visibility96.py'and dst.read_bytes()==subprocess.check_output(['git','show','HEAD:'+P+'/'+n],cwd=R),'snapshot collision: '+n
  else:dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes((H/n).read_bytes());assert sha(dst)==sha(H/n)
 save(R/P/'face101/SELECTION101.json',manifest);assets=[]
 for name in ['SourceFootprint100','SourceValue101','SourceFootprint101','SourceFootprint101B']:
  group=['Assets/EUnityValidation01/'+name+'.meta','Assets/EUnityValidation01/'+name+'/'+name+'.shader','Assets/EUnityValidation01/'+name+'/'+name+'.shader.meta'];assert sha(R/group[1])==sha(H/(name+'.shader'))and all(not git('ls-files','--',p)for p in group);assets+=group
 paths=[P+'/'+n for n in ns]+[P+'/face101/SELECTION101.json',DOC]+assets;spec=G/'SELECT101.paths';spec.write_bytes(('\0'.join(paths)+'\0').encode());git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in paths if p.endswith('RUN.cs.txt')or p.endswith('.meta')]);guard.preserved()
 body=G/'COMMIT_BODY101.txt';body.write_text('Distinguish raw face source from final visible owner\n\nRecord exact source-exclusion flags, selected camera and final native role in existing bounded packet padding. Compile fixed raster bytecode without loops/private arrays/compute, preserve normal32+32 GPU frames, and restore Edit/input/native/global/resource state.\n\nCorrect the analysis premise:23 ordinary raw-face exclusions belong to final role8;480 actual ordinary face samples already use the finite LUT. Implement a strict main-view source alternative based on actual91, but record zero executions and do not adopt it as a fix. Keep source colour aliasing, pigment/AA/gradient contracts, general opacity and continuous world limits explicit. Preserve product77/user30/protected128; no115, reset, broad save or push.\n',encoding='utf-8');print(git('commit','--file',str(body)),flush=True);assert not git('diff','--cached','--name-only');guard.preserved();save(G/'COMMIT101.json',{'commit':git('rev-parse','HEAD'),'paths':len(paths),'actualGPUFrames':64,'mainAlternativeExercised':False,'product77DefaultChanged':False,'user30Protected128PreservedWithApproved94Hunks':True,'finalArtAdopted':False,'push':False});print((G/'COMMIT101.json').read_text())
if __name__=='__main__':main()
