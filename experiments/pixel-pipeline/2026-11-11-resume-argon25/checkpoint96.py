"""Preserve completed96 source evidence; never stage original user edits."""
from pathlib import Path
import json,subprocess,sys
import checkpoint_cloth94 as prior
from checkpoint92 import H,R,P,DOC,sha,git,save
G=H/'face96';HEAD='debc72476fec5079cd0c4d0aae627d6578883856'

def names():
 code=[p.name for p in H.glob('*96.py')]+['ActorSource96.cs.txt','AlphaChannel96.cs.txt','AlphaChannelTests96.cs','SourceFootprint96.shader']
 data=['face96/CPU_SHADER96.json','face96/CPU_ALPHA96.json','face96/SUMMARY96.json','face96/DELIVERY96.json','face96/import/RUN.cs.txt','face96/import/EXPECTED.json','face96/import/COMPLETE.json','face96/alphaVerified/final/RUN.cs.txt','face96/alphaVerified/final/COMPLETE.json']
 for name in['probe1','geometry64']:
  data += ['face96/'+name+'/'+p for p in ['capture/RUN.cs.txt','capture/COMPLETE.json','capture/TRANSPORT_HOLD.json','capture/RUNTIME_PALETTE89.json','capture/RUNTIME_PALETTE89.rgb','capture/SOURCE_TABLE77.json','capture/ACTOR_MATERIALS96.json','capture/INPUT_BEFORE.json','capture/NATIVE_BEFORE73.json','capture/GLOBALS_BEFORE.bin','post/final/STATE.json','final/STATE.json']]
 data += ['face96/geometry64/'+n for n in ['capture/ALPHA96.zip','ACTOR_VISIBILITY96.json','VISIBLE_RIBBON96.json','COLOUR_VISIBLE96.json','ACTUAL_SOURCE_VISIBILITY96.png','ACTUAL_SEQUENCE96.webp','SEQUENCE_REVIEW96.png']]
 report=json.loads((G/'geometry64/capture/COMPLETE.json').read_text());assert report['packetComplete']and report['ownedResourcesReleased']and report['restorationChecksPass']and not report['errors']
 for f in report['stream77']['frames']:
  if 'actorSource96'not in f:continue
  data += ['face96/geometry64/capture/'+n for n in [f['compressedFile'],f['light84']['sourceGeometryFile'],f['ribbon93']['file'],f['actorSource96']['file']]]
 return list(dict.fromkeys(code+data))

def main():
 prior.preserved();ns=names();assert all((H/n).is_file()for n in ns),[n for n in ns if not(H/n).is_file()];selection={'files':[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns],'all64RawCopied':False,'fullActorFramesCopied':4,'alphaFilesLosslesslySelected':15,'oldDeniedBulkRetried':False};save(G/'SELECTION96.json',selection);print(json.dumps({'files':len(ns),'bytes':sum(x['bytes']for x in selection['files'])}),flush=True)
 if '--copy'not in sys.argv and '--commit'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD;old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);now=(R/DOC).read_bytes();assert now.startswith(old)and now[len(old):].decode('utf-8').lstrip().startswith('## 96.')
 copied=R/P/'face96/SELECTION96.json';previous={x['path']:x['SHA256']for x in json.loads(copied.read_text())['files']}if copied.exists()else{}
 for n in ns:
  dst=R/P/n
  if dst.exists()and dst.read_bytes()!=(H/n).read_bytes():assert n in previous and sha(dst)==previous[n]and not git('ls-files','--',P+'/'+n),'96 own copied snapshot changed unexpectedly: '+n
  if not dst.exists()or dst.read_bytes()!=(H/n).read_bytes():dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((H/n).read_bytes())
  assert sha(dst)==sha(H/n)
 save(R/P/'face96/SELECTION96.json',selection);prior.preserved()
 if '--commit'not in sys.argv:return
 assert not git('diff','--cached','--name-only');proof=json.loads((G/'PORTABLE96.json').read_text());assert proof['complete']and proof['alphaArchiveUsed']and proof['selectedFrames']==4;save(R/P/'face96/PORTABLE96.json',proof)
 assets=['Assets/EUnityValidation01/SourceFootprint96.meta','Assets/EUnityValidation01/SourceFootprint96/SourceFootprint96.shader','Assets/EUnityValidation01/SourceFootprint96/SourceFootprint96.shader.meta'];assert sha(R/assets[1])==sha(H/'SourceFootprint96.shader')and all(not git('ls-files','--',n)for n in assets)
 paths=[P+'/'+n for n in ns]+[P+'/face96/SELECTION96.json',P+'/face96/PORTABLE96.json',DOC]+assets;spec=G/'SELECT96.paths';spec.write_bytes(('\0'.join(paths)+'\0').encode());git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in paths if p.endswith('.meta')or p.endswith('RUN.cs.txt')]);prior.preserved()
 body=G/'COMMIT_BODY96.txt';body.write_text('Capture current actor visibility and isolate line/colour footprint failures\n\nAdd a bounded private halo/source observer without changing product77 defaults. Complete actual1 and64-frame runs, source UV/LUT matching, normal exit and state/resource preservation. Capture all current actor geometry and publicly verified original alpha for four representative frames.\n\nCheck every ribbon piece against same-location depth/alpha: preserve partial coverage and unknown results. Reproduce an occluded chosen witness and quantify stable visible colour-area leadership alongside small detected source components. Keep rejected95 colour mapping rejected; no new line/colour/art adoption. Preserve selected raw inputs, CPU regressions and exact remaining runtime/opacity/region limits. No115, reset, forced exit, broad save or push.\n',encoding='utf-8');print(git('commit','--file',str(body)),flush=True);assert not git('diff','--cached','--name-only');prior.preserved();out={'commit':git('rev-parse','HEAD'),'selectedPaths':len(paths),'user30Protected128PreservedWithApproved94Hunks':True,'product77DefaultChanged':False,'actualRuns':[1,64],'runtimeJointLineResolver':False,'nearest95Adopted':False,'fullPipelineComplete':False,'push':False};save(G/'COMMIT96.json',out);print(json.dumps(out))
if __name__=='__main__':main()
