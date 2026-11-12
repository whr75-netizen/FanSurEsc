"""Select only new102-105 work and its completed, bounded evidence."""
from pathlib import Path
import json,sys,subprocess,zipfile,hashlib
import checkpoint_cloth94 as guard
from checkpoint92 import H,R,P,DOC,sha,git,save
HEAD='8474ae74bc55b60e7e4fb98c6b7e1b39f1bf77a1'
G=H/'face105'
RUNS=['face103/rows64B','face103/rows64C','face103/long1800','face105/edge64']

def archive(root,name,files):
 path=root/name
 if not path.exists():
  with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
   for p in files:z.write(p,p.name)
 with zipfile.ZipFile(path)as z:
  assert z.namelist()==[p.name for p in files]and z.testzip()is None
  for p in files:assert hashlib.sha256(z.read(p.name)).hexdigest()==sha(p)

def selected():
 ns='joint_address102.py audit_joint_address102.py test_joint_address102.py review_joint_address102.py JointLine103.cs CurveOpacity103.cs RowParallel103.cs JointOpacityFixture103.cs RowLifetimeTests103.cs WarmRows103.cs prepare_rows103.py prepare_compile103.py relay103.py test_parallel103.py review_rows103.py audit_world104.py WorldSampleCases104.cs test_world104.py CurveOpacity105.cs OpacityCases105.cs test_opacity105.py prepare_opacity105.py relay105.py review_opacity105.py compare_opacity105.py summarize105.py persist_delivery105.py checkpoint105.py'.split()
 ns += [str(p.relative_to(H)).replace('\\','/')for p in sorted((H/'face102').glob('*'))if p.is_file()and p.suffix in['.json','.npz','.png']]
 ns += ['face103/CPU_PARALLEL103.json','face103/CPU_WARM103.json','face104/CPU_WORLD104.json','face105/CPU_OPACITY105.json','face105/SUMMARY105.json','face105/DELIVERY105.json','face103/rows64/capture/RUN.cs.txt','face103/rows64/capture/REQUEST.json','face103/rows64/capture/REPLY.json','face103/compileB/details/RUN.cs.txt','face103/compileB/details/REQUEST.json','face103/compileB/details/REPLY.json','face99/long960/WORLD_SAMPLE104.json']
 for name in RUNS:
  root=H/name;c=root/'capture';r=json.loads((c/'COMPLETE.json').read_text());assert r['packetComplete']and r['Edit']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];frames=r['stream77']['frames'];assert len(frames)==r['plannedSourceFrames']
  archive(c,'PACKETS99.zip',[c/f['compressedFile']for f in frames]);archive(c,'ALPHA96.zip',sorted(c.glob('source-alpha96-*.a8')))
  ns += [name+'/'+n for n in['capture/RUN.cs.txt','capture/COMPLETE.json','capture/REQUEST.json','capture/REPLY.json','capture/TRANSPORT_HOLD.json','capture/PACKETS99.zip','capture/ALPHA96.zip','capture/ACTOR_MATERIALS96.json','capture/SOURCE_TABLE77.json','capture/RUNTIME_PALETTE89.rgb','capture/RUNTIME_PALETTE89.json','capture/INPUT_BEFORE.json','capture/NATIVE_BEFORE73.json','capture/GLOBALS_BEFORE.bin','preflight/final/STATE.json','post/final/STATE.json']]
  # The delivery-named APNG is byte-identical to ACTUAL_LONG99.png. Keep one
  # byte stream in Git; preserve the alternate Library path/identity in metadata.
  ns += [str(p.relative_to(H)).replace('\\','/')for p in sorted(root.glob('*'))if p.is_file()and p.suffix in['.json','.png','.webp']and p.name!='ACTUAL_FACE_LINE_30S_103.png']
  for f in frames:
   if'actorSource96'in f:ns += [name+'/capture/'+n for n in[f['actorSource96']['file'],f['light84']['sourceGeometryFile'],f['ribbon93']['file']]]
 return list(dict.fromkeys(ns))

def main():
 guard.preserved();ns=selected();assert all((H/n).is_file()for n in ns),[n for n in ns if not(H/n).is_file()];manifest={'files':[{'path':n,'sha256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns],'scope':'Only102 rejected colour candidate,103 CPU row work and completed new captures,104 world-sample insufficiency,105 same-edge correction','oldDeniedBulkArchiveRetried':False,'product77DefaultChanged':False};total=sum(v['bytes']for v in manifest['files']);assert total<125829120,total;save(G/'SELECTION105.json',manifest);print(json.dumps({'files':len(ns),'bytes':total}),flush=True)
 if'--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only');old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);now=(R/DOC).read_bytes();assert now.startswith(old)and now[len(old):].decode().lstrip().startswith('## 102.')
 state=json.loads((G/'edge64/post/final/STATE.json').read_text());assert state['Edit']and not state['compiling']and not state['updating']and state['inputJSONExact']and len(state['dirty'])==31 and state['allRTCount']==30 and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==0
 assert not[n for n in ns if(R/P/n).exists()],'existing snapshot collision; do not overwrite'
 for n in ns:
  dst=R/P/n;assert not dst.exists(),'unexpected snapshot collision: '+n;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((H/n).read_bytes());assert sha(dst)==sha(H/n)
 save(R/P/'face105/SELECTION105.json',manifest);paths=[P+'/'+n for n in ns]+[P+'/face105/SELECTION105.json',DOC];spec=G/'SELECT105.paths';spec.write_bytes(('\0'.join(paths)+'\0').encode());git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in paths if p.endswith('RUN.cs.txt')]);guard.preserved()
 body=G/'COMMIT_BODY105.txt';body.write_text('Balance CPU line rows and preserve same-edge diagonal continuity\n\nKeep original source/LUT/unknown contracts, reject102 colour-address candidate after a temporal regression, and reproduce world representative gates plus a concrete four-sample insufficiency counterexample.\n\nValidate source-geometry-owned CPU row tasks with mandatory join/release, exact original-input certificates and actual normal frames. Verify same-edge split paths without joining different curves or erasing partial occlusion. Preserve product77/user30/protected128 and restored Edit/input/native/global/resource state. No115, new GPU kernels, reset, broad save, old denied bulk archive or push. General colour-feature semantics, opacity, continuous world occlusion and final art remain incomplete.\n',encoding='utf-8');print(git('commit','--file',str(body)),flush=True);assert not git('diff','--cached','--name-only');guard.preserved();save(G/'COMMIT105.json',{'commit':git('rev-parse','HEAD'),'paths':len(paths),'user30Protected128PreservedWithApproved94Hunks':True,'product77DefaultChanged':False,'push':False});print((G/'COMMIT105.json').read_text())

if __name__=='__main__':main()
