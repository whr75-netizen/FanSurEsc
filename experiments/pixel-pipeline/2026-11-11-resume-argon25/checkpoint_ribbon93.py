"""Narrow completed93 sources/evidence. Never archive every long-run atlas."""
from pathlib import Path
import json,subprocess,sys
import checkpoint92 as old
H=old.H;R=old.R;P=old.P;DOC=old.DOC;G=H/'face93';sha=old.sha;git=old.git;save=old.save;HEAD='6eac9a825ced1fb791be56aac08c1380c052ed91'

def names():
 code='projected_ribbon93.py test_projected_ribbon93.py audit_ribbon93.py ProjectedRibbon93.shader compile_ribbon93.py Ribbon93.cs.txt prepare_state93.py relay93.py prepare_ribbon93.py prepare_packed93.py test_codec93.py prepare_witness_fix93.py prepare_long_ribbon93.py review_packed93.py review_motion_ribbon93.py audit_source_ranges93.py build_reference_ranges93.py test_reference_ranges93.py chromatic_value92.py checkpoint_ribbon93.py'.split()
 data='face93/CPU_PREPARED93.json face93/CPU_RIBBON93.json face93/CPU_SHADER93.json face93/SAVED_GEOMETRY93.json face93/CPU_REFERENCE_RANGES93.json face93/SOURCE_RANGE_AUDIT93.json face93/SOURCE_RANGE_AUDIT93.png face93/SOURCE_RANGE_CANDIDATE93.json face93/SOURCE_RANGE_CANDIDATE93.npz face93/SOURCE_RANGE_CANDIDATE93.png face93/RANGE_REFINEMENT93.json face93/RENDER_AND_FAILURE93.png face93/DELIVERABLE93.json face93/capture/FAILED.json face93/witness-fix/CPU_SHADER93.json face93/witness-fix/ProjectedRibbon93.before.shader face93/witness-fix/BEFORE_PATCH93.json face93/motion480/CPU_PREPARED93.json face93/motion480/capture/RUN.cs.txt face93/motion480/capture/FAILED.json face93/motion480/post/final/STATE.json face93/motion480/console/REPLY.json face93/motion480/INCOMPLETE_MOTION93.json face93/motion480/INCOMPLETE_RGB_CONTINUITY93.npz face93/motion480/INCOMPLETE_PROVENANCE93.json face93/motion480/INCOMPLETE_MOTION93.webp face93/motion480/INCOMPLETE_RIBBON93.json face93/motion480/INCOMPLETE_STRIP93.png'.split()
 for group in ['face93/packed1','face93/witness-fix']:
  data +=[group+'/'+n for n in ['capture/RUN.cs.txt','capture/COMPLETE.json','capture/RUNTIME_PALETTE89.json','capture/RUNTIME_PALETTE89.rgb','capture/SOURCE_TABLE77.json','ACTUAL_RIBBON93.json','ACTUAL_RIBBON93.png','post/final/STATE.json']]
  r=json.loads((H/group/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['ownedResourcesReleased']and r['restorationChecksPass']and not r['errors'];f=r['stream77']['frames'][0];data +=[group+'/capture/'+f['compressedFile'],group+'/capture/'+f['light84']['sourceGeometryFile'],group+'/capture/'+f['ribbon93']['file']]
 data+=['face93/packed1/CPU_CODEC93.json','face93/witness-fix/import/COMPLETE.json']
 r=json.loads((G/'motion480/capture/FAILED.json').read_text());assert not r['packetComplete']and r['received77']==r['submitted77']==328 and r['restorationChecksPass']and r['ownedResourcesReleased'];assert not(G/'motion480/capture/COMPLETE.json').exists()
 for i in [0,80,160,240,327]:
  f=r['stream77']['frames'][i];data+=['face93/motion480/capture/'+n for n in [f['compressedFile'],f['light84']['sourceGeometryFile'],f['ribbon93']['file']]]
 return code+data

def main():
 ns=names();assert len(ns)==len(set(ns));missing=[n for n in ns if not(H/n).is_file()];assert not missing,missing;manifest=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns];selection={'files':manifest,'count':len(ns),'bytes':sum(x['bytes']for x in manifest),'all328RawCopied':False,'allRawRemainLocal':str(G/'motion480/capture'),'oldDeniedBulkRetried':False};save(G/'SELECTION93.json',selection);print(json.dumps({k:v for k,v in selection.items()if k!='files'}),flush=True)
 if '--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only');user=json.loads((H/'face55/BEFORE_GIT55.json').read_text())['user30'];protected=json.loads((H/'face55/backup/DISK_BEFORE.json').read_text())
 def preserved():
  assert all(sha(R/p)==v for p,v in user.items());assert all(sha(R/x['path'])==x['sha256']for x in protected if x['exists'])
 preserved();s=json.loads((G/'motion480/post/final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['allRTCount']==30 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==s['sourceFlatTexturesRemaining67']==0
 prior=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);doc=(R/DOC).read_bytes();assert doc.startswith(prior)and doc[len(prior):].decode('utf-8').lstrip().startswith('## 93.')
 for x in manifest:
  dst=R/P/x['path']
  if dst.exists():assert dst.read_bytes()==subprocess.check_output(['git','show','HEAD:'+P+'/'+x['path']],cwd=R)
  else:dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes((H/x['path']).read_bytes());assert sha(dst)==x['SHA256']
 save(R/P/'face93/SELECTION93.json',selection)
 # Tests load copied source, observed previous inputs and explicit unchanged
 # baseline92. Their reports remain in the owned experiment subtree only.
 program='import sys;sys.path.insert(0,sys.argv[1]);import test_projected_ribbon93 as a;a.main();import test_reference_ranges93 as b;b.main()'
 q=subprocess.run([sys.executable,'-B','-X','utf8','-c',program,str(R/P)],capture_output=True,text=True,encoding='utf-8');assert q.returncode==0,q.stdout+q.stderr
 assets=['Assets/EUnityValidation01/ProjectedRibbon93.meta','Assets/EUnityValidation01/ProjectedRibbon93/ProjectedRibbon93.shader','Assets/EUnityValidation01/ProjectedRibbon93/ProjectedRibbon93.shader.meta'];assert all(not git('ls-files','--',p)for p in assets);assert sha(R/assets[1])==sha(H/'ProjectedRibbon93.shader')
 selected=[P+'/'+n for n in ns]+[P+'/face93/SELECTION93.json',DOC]+assets;paths=G/'SELECT93.paths';paths.write_bytes(('\0'.join(selected)+'\0').encode('utf-8'));git('add','--pathspec-from-file='+str(paths),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(selected);exact=[p for p in selected if p.endswith('RUN.cs.txt')or p.endswith('.meta')];git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in exact]);preserved()
 body=G/'COMMIT_BODY93.txt';body.write_text('Project native outline widths and preserve source gamut counterexamples\n\nImplement bounded one-sided native width ribbons with common-anchor placement. Correct HLSL out-parameter witness clobbering and retain the failing input. Keep256KiB readback cap through explicit24-plane packing and exact codec tests. Validate the corrected one-frame GPU output. Record the480-frame attempt as FAILED after328 frames on existing clothing negative union winding; retain diagnostic receipts, never a completion marker.\n\nAudit source92 range escapes and test optional observed-range representative constraints on CPU only. Keep colour distortion, whole-cell visibility and art/long-term stability limits explicit. Preserve product77, user30/protected128, Edit/input/native/options/resources. No push.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only');preserved();save(G/'COMMIT93.json',{'commit':git('rev-parse','HEAD'),'selectedFiles':len(selected),'repositoryCPURecheck':True,'user30Protected128Equal':True,'product77DefaultChanged':False,'completedWitnessFrames':1,'longRunCompleted':False,'diagnosticPrefixFrames':328,'rangeCandidateGPUOrArtAdopted':False,'push':False});print((G/'COMMIT93.json').read_text())
if __name__=='__main__':main()
