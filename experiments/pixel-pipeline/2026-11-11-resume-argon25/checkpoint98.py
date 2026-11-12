"""Publish only the completed98 implementation/evidence; no older bulk archive."""
from pathlib import Path
import json,subprocess,sys
import checkpoint_cloth94 as guard
from checkpoint92 import H,R,P,DOC,sha,git,save
G=H/'face98';HEAD='dc77d3ccc03b82091b55d40bf6e213d2e70c7115'
def selected():
 ns=['JointLine97.cs','CurveOpacity98.cs','CurveOpacity98B.cs','CurveOpacityTests98.cs','JointOpacityFixture98.cs','CoupledRibbon98.cs.txt','CoupledRibbon98.shader','CoupledRibbon98B.shader','SourceFootprint98.shader']+[p.name for p in H.glob('*98.py')]
 ns += ['face98/'+n for n in ['CPU_SHADER98.json','CPU_FIXTURE98.json','CPU_TESTS98.json','COLOUR_JOINT_SUPPORT98.json','COLOUR_CONTRACT98.json','SUMMARY98.json','DELIVERY98.json']]
 for shader in ['CoupledRibbon98','CoupledRibbon98B','SourceFootprint98']:ns += ['face98/import-'+shader+'/import/'+n for n in ['RUN.cs.txt','EXPECTED.json','COMPLETE.json']]
 for name in ['one','motion64','oneB','motion64B']:
  root=G/name;r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['Edit']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];assert r['stream77']['sourceAlpha97ManagedBytesAfterRelease']==0
  ns += ['face98/'+name+'/'+n for n in ['CPU_PREPARED98.json','capture/RUN.cs.txt','capture/COMPLETE.json','capture/TRANSPORT_HOLD.json','capture/RUNTIME_PALETTE89.rgb','capture/RUNTIME_PALETTE89.json','capture/SOURCE_TABLE77.json','capture/ACTOR_MATERIALS96.json','capture/ALPHA96.zip','capture/INPUT_BEFORE.json','capture/NATIVE_BEFORE73.json','capture/GLOBALS_BEFORE.bin','post/final/STATE.json','ACTUAL_COUPLED98.json','ACTUAL_COUPLED98.png','ACTUAL_SEQUENCE98.webp','SEQUENCE_REVIEW98.png']]
  for f in r['stream77']['frames']:
   ns += ['face98/'+name+'/capture/'+n for n in [f['compressedFile'],f['ribbon93']['file']]]
   if 'actorSource96'in f:ns += ['face98/'+name+'/capture/'+n for n in [f['light84']['sourceGeometryFile'],f['actorSource96']['file']]]
 ns += ['face98/'+n+'/TEMPORAL98.json'for n in ['motion64','motion64B']]+['face98/motion64B/FOCUS98B.png']
 return list(dict.fromkeys(ns))
def main():
 guard.preserved();ns=selected();assert all((H/n).is_file()for n in ns),[n for n in ns if not(H/n).is_file()];manifest={'files':[{'path':n,'sha256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns],'actualRuns':[1,64,1,64],'oldDeniedBulkRetried':False,'defaultProduct77Changed':False,'allMotionPacketsIncludedForTemporalReproduction':True};save(G/'SELECTION98.json',manifest);print(json.dumps({'selectedFiles':len(ns),'bytes':sum(x['bytes']for x in manifest['files'])}),flush=True)
 if '--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only');old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);now=(R/DOC).read_bytes();assert now.startswith(old)and now[len(old):].decode('utf-8').lstrip().startswith('## 98.')
 for n in ns:
  dst=R/P/n
  if dst.exists():
   assert n=='JointLine97.cs'and dst.read_bytes()==subprocess.check_output(['git','show','HEAD:'+P+'/'+n],cwd=R),'existing snapshot collision: '+n
  else:dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes((H/n).read_bytes());assert sha(dst)==sha(H/n)
 save(R/P/'face98/SELECTION98.json',manifest);assets=[]
 for shader in ['CoupledRibbon98','CoupledRibbon98B','SourceFootprint98']:
  group=['Assets/EUnityValidation01/'+shader+'.meta','Assets/EUnityValidation01/'+shader+'/'+shader+'.shader','Assets/EUnityValidation01/'+shader+'/'+shader+'.shader.meta'];assert sha(R/group[1])==sha(H/(shader+'.shader'))and all(not git('ls-files','--',n)for n in group);assets+=group
 paths=[P+'/'+n for n in ns]+[P+'/face98/SELECTION98.json',DOC]+assets;spec=G/'SELECT98.paths';spec.write_bytes(('\0'.join(paths)+'\0').encode());git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in paths if p.endswith('.meta')or p.endswith('RUN.cs.txt')]);guard.preserved()
 body=G/'COMMIT_BODY98.txt';body.write_text('Validate same-feature integer line cell redundancy\n\nConnect current source/destination continuity and common centreline representatives to a fixed private GPU raster composite. Preserve partial/unknown/sole/wide fragments and original finite LUT/ink. Retain the failed all-neighbours variant and its123/124/125 temporal counterexample.\n\nActual1+64+1+64 frames, source visibility20 and curve66 CPU checks, four unchanged97 fixtures. Final64 removes5 redundant cells, exact backing/control colours, normal Edit restoration and owned-resource release. Keep performance, continuous world coverage, full opacity/art and colour-feature semantic limitations explicit. Add18 stored-input joint region/family support checks. Product77/default/user30/protected128 preserved; no115, reset, forced termination, broad save or push.\n',encoding='utf-8');print(git('commit','--file',str(body)),flush=True);assert not git('diff','--cached','--name-only');guard.preserved();save(G/'COMMIT98.json',{'commit':git('rev-parse','HEAD'),'paths':len(paths),'product77DefaultChanged':False,'user30Protected128PreservedWithApproved94Hunks':True,'artAdopted':False,'actualRuns':[1,64,1,64],'push':False});print((G/'COMMIT98.json').read_text())
if __name__=='__main__':main()
