"""Select this performance/960-frame result only; retain user/product changes."""
from pathlib import Path
import json,subprocess,sys
import checkpoint_cloth94 as guard
from checkpoint92 import H,R,P,DOC,sha,git,save
G=H/'face99';HEAD='89e7a7d2a3c022d60055bb6f5ac0b4e27b7bc857'

def selected():
 ns=[p.name for p in H.glob('*99.py')]+['JointLine99.cs','JointLine99B.cs','JointLine99C.cs','CurveOpacity99.cs','JointOpacityFixture99.cs','VisibilityOracle99.cs','SourceWidthCache99.cs.txt','WorldInventory99.cs.txt','ReadOriginal99.cs.txt','ReadWorldAssets99.cs.txt','actor_visibility96.py','review_coupled98.py']
 ns+=['face99/'+p.name for p in G.glob('*.json')if p.name not in ['SELECTION99.json','COMMIT99.json']]+['face99/CPU_FIXTURES99.zip']
 for name in ['profile12','optimized12','cached64','fine64','long960']:
  root=G/name;r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['Edit']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];assert r['stream77']['sourceAlpha97ManagedBytesAfterRelease']==0
  ns+=['face99/'+name+'/'+n for n in ['capture/RUN.cs.txt','capture/COMPLETE.json','capture/TRANSPORT_HOLD.json','capture/RUNTIME_PALETTE89.rgb','capture/RUNTIME_PALETTE89.json','capture/SOURCE_TABLE77.json','capture/ACTOR_MATERIALS96.json','capture/ALPHA96.zip','capture/PACKETS99.zip','capture/INPUT_BEFORE.json','capture/NATIVE_BEFORE73.json','capture/GLOBALS_BEFORE.bin','post/final/STATE.json']]
  for p in root.glob('*'):
   if p.is_file()and p.suffix in ['.json','.png','.webp']:ns.append(str(p.relative_to(H)).replace('\\','/'))
  for n in ['VALIDATED_ALPHA96.json','WORLD_INVENTORY99.json']:
   if(root/'capture'/n).exists():ns.append('face99/'+name+'/capture/'+n)
  # Performance-only12-frame runs retain the full immutable command, packet,
  # source identities and metrics. Geometry proof/long review uses these runs.
  if name not in ['profile12','optimized12']:
   for f in r['stream77']['frames']:
    if 'actorSource96'in f:ns+=['face99/'+name+'/capture/'+n for n in [f['actorSource96']['file'],f['light84']['sourceGeometryFile'],f['ribbon93']['file']]]
 for group in ['original99','world-assets99']:
  for p in (G/group/'details').glob('*'):
   if p.is_file()and p.name not in ['SCHEMA.json','RELAY_STDERR.txt']:ns.append(str(p.relative_to(H)).replace('\\','/'))
 ns+=['face99/world-assets99/WORLD_ASSETS_VALIDATED99.json']
 for name in ['final-review99','final-review99B']:
  for n in ['RUN.cs.txt','REQUEST.json','REPLY.json','STATE.json']:
   p=G/name/'post/final'/n
   if p.exists():ns.append(str(p.relative_to(H)).replace('\\','/'))
 return list(dict.fromkeys(ns))

def main():
 guard.preserved();ns=selected();missing=[n for n in ns if not(H/n).is_file()];assert not missing,missing
 manifest={'files':[{'path':n,'sha256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns],'actualRuns':[12,12,64,64,960],'allOriginal99R77PacketsLosslesslyArchived':True,'allRawGeometryRibbonsArchived':False,'selectedActorGeometryFrames':17,'product77DefaultChanged':False,'oldDeniedBulkArchiveRetried':False};save(G/'SELECTION99.json',manifest);print(json.dumps({'files':len(ns),'bytes':sum(x['bytes']for x in manifest['files'])}),flush=True)
 if '--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only');old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);now=(R/DOC).read_bytes();assert now.startswith(old)and now[len(old):].decode('utf-8').lstrip().startswith('## 99.')
 state=json.loads((G/'final-review99B/post/final/STATE.json').read_text());assert state['Edit']and not state['compiling']and not state['updating']and state['inputJSONExact']and len(state['dirty'])==31 and state['allRTCount']==30 and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==0
 for n in ns:
  dst=R/P/n
  if dst.exists():assert n in ['actor_visibility96.py','review_coupled98.py']and dst.read_bytes()==subprocess.check_output(['git','show','HEAD:'+P+'/'+n],cwd=R),'snapshot collision: '+n
  else:dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes((H/n).read_bytes());assert sha(dst)==sha(H/n)
 save(R/P/'face99/SELECTION99.json',manifest);paths=[P+'/'+n for n in ns]+[P+'/face99/SELECTION99.json',DOC];spec=G/'SELECT99.paths';spec.write_bytes(('\0'.join(paths)+'\0').encode());git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(paths);git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in paths if p.endswith('RUN.cs.txt')]);guard.preserved()
 body=G/'COMMIT_BODY99.txt';body.write_text('Reduce same-point CPU line query cost and validate960 actual frames\n\nSeparate visibility from selected-witness clearance, cache original UV width texels under one guarded owner, and add a conservative2x CPU spatial index while retaining97 pixels/radius and98B certificates. Reproduce16192 visibility and66 curve cases plus four actual fixtures. Keep rejected CPU-only multiplication alternative distinct.\n\nCapture12+12+64+64+960 normal GPU frames, validate finite LUT/ink/unknown contracts and exact lossless16-second APNG, then restore Edit/input22/native46/global74/resources. Isolate source-step amplification and reject93/95 mappings that increase changes. Record conditional ground-depth comparison and missing world wind/alpha/owner, general opacity, colour-feature semantics and art limits. Preserve product77/user30/protected128; no115, reset, forced termination, broad save or push.\n',encoding='utf-8');print(git('commit','--file',str(body)),flush=True);assert not git('diff','--cached','--name-only');guard.preserved();save(G/'COMMIT99.json',{'commit':git('rev-parse','HEAD'),'paths':len(paths),'user30Protected128PreservedWithApproved94Hunks':True,'product77DefaultChanged':False,'actualGPUFrames':1112,'longActualSimulationSeconds':16.000000834465027,'finalArtAdopted':False,'push':False});print((G/'COMMIT99.json').read_text())
if __name__=='__main__':main()
