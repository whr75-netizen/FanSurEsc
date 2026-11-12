"""Select only94 work and our production hunks, preserving pre-existing edits."""
from pathlib import Path
import json,subprocess,sys,difflib
import checkpoint92 as c
H=c.H;R=c.R;P=c.P;G=H/'face94';DOC=c.DOC;HEAD='e432cc8edeafd045063928f3e8b306e0a2349379';BASE='Assets/EUnityValidation01/ClothRegion524/Runtime/'
def names():
 code='WindingTests94.cs audit_winding94.py UnionCapture94.cs.txt prepare_union94.py relay94.py union_input94.py trace_union94.py minimal_carrier94.py DoubleUnionTests94.cs prepare_compile94.py relay_compile94.py prepare_verify94.py observer_transport94.py test_observer_transport94.py prepare_held94.py OpacityFixtureTests94.cs build_opacity_fixture94.py audit_opacity_fixture94.py DoubleUnionInvariant94.cs audit_colour_transitions94.py audit_colour_footprint94.py review_motion_ribbon93.py relay33.py checkpoint_cloth94.py'.split()
 data='face94/CPU_WINDING94.json face94/ClosedRegion.before.cs face94/ClosedRegion.trace94.cs face94/PATCH_TARGETS94.json face94/APPLIED94.json face94/BEFORE_SOURCE94.json face94/CPU_UNION94-baseline-frame102_TRACE.json face94/CPU_UNION94-failure-frame429_TRACE.json face94/EXACT_FRAGMENT94.json face94/MINIMAL_CARRIER94.json face94/DOUBLE_UNION94.json face94/CPU_INVARIANTS94.json face94/MINIMAL94-float-before.d94 face94/MINIMAL94-relative-double.d94 face94/FIXTURE_CONTRACT94.json face94/OpacityFixtureSource94.cs face94/actual-baseline-v2.fixture94 face94/saved-failure-source.fixture94 face94/CPU_FULL_SOURCE94.json face94/APPLICATION_SCOPE94.json face94/RELAY_IDLE_EVIDENCE94.json face94/ACTUAL_MOTION93-DELIVERABLE94.json face94/ACTUAL_SEQUENCE94-DELIVERABLE94.json face94/capture/RUN.cs.txt face94/capture/FAILED.json face94/capture/UNION_INPUT94_baseline_COMPLETE.json face94/capture/UNION_INPUT94_failure_COMPLETE.json face94/capture/UNION94-baseline-frame102.bin face94/capture/UNION94-failure-frame429.bin face94/post/final/STATE.json face94/recompile/pre/BACKUP_COMPLETE.json face94/recompile/pre/NATIVE_BEFORE73.json face94/recompile/pre/INPUT.json face94/recompile/pre/GLOBALS.bin face94/recompile/pre/OWN_LOCK_HELD.json face94/recompile/release/RELEASED.json face94/recompile/post/RESULT.json face94/recompile/post/GLOBALS.bin face94/verify480/capture/FAILED.json face94/verify480/post/final/STATE.json face94/held480/CPU_PREPARED94.json face94/held480/capture/RUN.cs.txt face94/held480/capture/COMPLETE.json face94/held480/capture/TRANSPORT_HOLD.json face94/held480/capture/RUNTIME_PALETTE89.json face94/held480/capture/RUNTIME_PALETTE89.rgb face94/held480/capture/SOURCE_TABLE77.json face94/held480/capture/UNION_INPUT94_baseline_COMPLETE.json face94/held480/capture/UNION_INPUT94_final_COMPLETE.json face94/held480/ACTUAL_RIBBON93.json face94/held480/ACTUAL_RIBBON93.png face94/held480/ACTUAL_MOTION93.json face94/held480/ACTUAL_MOTION93.webp face94/held480/ACTUAL_RGB_CONTINUITY93.npz face94/held480/ACTUAL_PROVENANCE93.json face94/held480/COLOUR_TRANSITIONS94.json face94/held480/COLOUR_FOOTPRINT94.json face94/held480/ACTUAL_SEQUENCE94.png face94/held480/post/final/STATE.json face94/held480/console/REPLY.json'.split()
 for n in ['ClosedRegion524.cs','OpacityRegion525.cs','ClothRegion524.cs']:data+=['face94/before/'+n+'.bin','face94/candidate/'+n,'face94/index-candidate/'+n]
 report=json.loads((G/'held480/capture/COMPLETE.json').read_text());assert report['packetComplete']and report['ownedResourcesReleased']and report['restorationChecksPass']and not report['errors'];frames=report['stream77']['frames']
 for i in [0,327,479]:
  f=frames[i];data+=['face94/held480/capture/'+n for n in [f['compressedFile'],f['light84']['sourceGeometryFile'],f['ribbon93']['file']]]
 for p in sorted((G/'held480/capture').glob('UNION94-*.bin')):data.append(str(p.relative_to(H)).replace('\\','/'))
 return code+data
def normal(b):return b.decode('utf-8-sig').replace('\r\n','\n').rstrip('\n')
def preserved():
 user=json.loads((H/'face55/BEFORE_GIT55.json').read_text())['user30'];protected=json.loads((H/'face55/backup/DISK_BEFORE.json').read_text());targets=json.loads((G/'PATCH_TARGETS94.json').read_text());applied=json.loads((G/'APPLIED94.json').read_text())
 for n,v in targets.items():
  before=(G/'before'/(n+'.bin')).read_bytes();assert c.sha(G/'before'/(n+'.bin'))==v['beforeSHA'];now=(R/BASE/n).read_bytes();assert c.sha(R/BASE/n)==applied[n]['appliedSHA256']and normal(now)==normal((G/'candidate'/n).read_bytes())
  if n=='ClosedRegion524.cs':
   s=normal(now);a=s.index('    // Preserve high-precision projected source coordinates');b=s.index('    static List<Vector2[]> BuildCounts(',a);assert s[:a]+s[b:]==normal(before)
  elif n=='ClothRegion524.cs':assert normal(now).replace('Opacity.ProjectExact94(p,UseOpacityCurves527)','Opacity.Project(p,UseOpacityCurves527)')==normal(before)
 for p,sha in user.items():
  if p.startswith(BASE)and Path(p).name in targets:assert c.sha(G/'before'/(Path(p).name+'.bin'))==sha
  else:assert c.sha(R/p)==sha,p
 for x in protected:
  if not x['exists']:continue
  p=x['path']
  if p.startswith(BASE)and Path(p).name in targets:assert c.sha(G/'before'/(Path(p).name+'.bin'))==x['sha256']
  else:assert c.sha(R/p)==x['sha256'],p
 for n in targets:assert(R/(BASE+n+'.meta')).read_bytes()==subprocess.check_output(['git','show','HEAD:'+BASE+n+'.meta'],cwd=R)
def main():
 ns=names();assert len(ns)==len(set(ns));missing=[n for n in ns if not(H/n).is_file()];assert not missing,missing;manifest=[{'path':n,'sha256':c.sha(H/n),'bytes':(H/n).stat().st_size}for n in ns];selection={'files':manifest,'count':len(ns),'bytes':sum(x['bytes']for x in manifest),'all480RawCopied':False,'oldDeniedBulkRetried':False};c.save(G/'SELECTION94.json',selection);print(json.dumps({k:v for k,v in selection.items()if k!='files'}),flush=True)
 if '--publish'not in sys.argv:return
 assert c.git('rev-parse','HEAD')==HEAD and not c.git('diff','--cached','--name-only');preserved();s=json.loads((G/'held480/post/final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['allRTCount']==30 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==s['sourceFlatTexturesRemaining67']==0
 old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);doc=(R/DOC).read_bytes();assert doc.startswith(old)and doc[len(old):].decode('utf-8').lstrip().startswith('## 94.')
 changed=[]
 for x in manifest:
  dst=R/P/x['path'];present=dst.exists()
  if present:assert dst.read_bytes()==subprocess.check_output(['git','show','HEAD:'+P+'/'+x['path']],cwd=R)
  else:dst.parent.mkdir(parents=True,exist_ok=True)
  if not present or dst.read_bytes()!=(H/x['path']).read_bytes():dst.write_bytes((H/x['path']).read_bytes());changed.append(P+'/'+x['path'])
  assert c.sha(dst)==x['sha256']
 c.save(R/P/'face94/SELECTION94.json',selection)
 # Apply only our hunks to HEAD's index. The working files retain all original
 # user modifications. No stash/reset or whole-file add of dirty user source.
 patch=''
 for n in ['ClosedRegion524.cs','OpacityRegion525.cs','ClothRegion524.cs']:
  path=BASE+n;before=subprocess.check_output(['git','show','HEAD:'+path],cwd=R).decode('utf-8');after=(G/'index-candidate'/n).read_bytes().decode('utf-8');patch+=''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),'a/'+path,'b/'+path))
 p=G/'INDEX_ONLY94.patch';p.write_text(patch,encoding='utf-8',newline='\n');c.git('apply','--cached','--check',str(p));c.git('apply','--cached',str(p))
 for n in ['ClosedRegion524.cs','OpacityRegion525.cs','ClothRegion524.cs']:assert normal(subprocess.check_output(['git','show',':'+BASE+n],cwd=R))==normal((G/'index-candidate'/n).read_bytes())
 selected=changed+[P+'/face94/SELECTION94.json',DOC];spec=G/'SELECT94.paths';spec.write_bytes(('\0'.join(selected)+'\0').encode('utf-8'));c.git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');expected=set(selected)|{BASE+n for n in ['ClosedRegion524.cs','OpacityRegion525.cs','ClothRegion524.cs']};assert set(c.git('diff','--cached','--name-only').splitlines())==expected;exact=[n for n in expected if n.endswith('RUN.cs.txt')];c.git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--','.',*[f':(exclude){n}'for n in exact]);preserved()
 body=G/'COMMIT_BODY94.txt';body.write_text('Preserve precise opacity carriers and verify480 normal render frames\n\nReproduce the actual body1 negative-union input on CPU, isolate a41-edge subpixel loop, and preserve original double barycentrics through the existing1e8 union grid. Update exactly three clothing source paths while selecting only our hunks over HEAD and retaining original user edits. Confirm actual compilation and native47/input/global preservation.\n\nKeep official MCP transport alive through observer completion after diagnosing180-second idle shutdown. Validate480 actual consecutive movement/rotation frames,8simulated seconds, finite face RGB, normal exit and resource release. Record single-point source-colour alias counterexamples and remaining full-pixel visibility/opacity/art limits. No115/default face-eye switch, reset, force termination or push.\n',encoding='utf-8');c.git('commit','--file',str(body));assert not c.git('diff','--cached','--name-only');preserved();out={'commit':c.git('rev-parse','HEAD'),'selectedChangedPaths':len(expected),'productionClothingFiles':3,'onlyOurProductionHunksStaged':True,'user30AndProtected128ContentPreservedExceptApprovedOwnHunks':True,'actualGPUFrames':480,'simulationSeconds':8,'product77FaceEyeDefaultChanged':False,'finalArtAdopted':False,'push':False};c.save(G/'COMMIT94.json',out);print(json.dumps(out))
if __name__=='__main__':main()
