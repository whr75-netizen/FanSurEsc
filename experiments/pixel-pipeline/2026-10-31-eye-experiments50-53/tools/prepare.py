from pathlib import Path
import hashlib,json,shutil
W=Path(__file__).resolve().parent
S=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21')
P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
O=W/'2026-10-31-eye-experiments50-53';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
origins={};excluded=[]
contracts={
 'eye-composition50':None,
 'lid-evidence51':{'APERTURE_RESULTS.json','APERTURE_SUMMARY.json','APERTURE_TESTS.json','KEYFORM_BUNDLE51.json','INPUTS.json','ORIGINAL_VRM_SCHEMA.json','PALETTE_AND_CARRIER_PROVENANCE.json','PRESERVATION.json','SUMMARY.json','TESTS.json','RESUME.json'},
 'whole-eye52':{'ACTUAL_SOURCE_BINDINGS52.json','CARRIER_ASSOCIATION52.json','CONSTRAINT_TESTS52.json','FRAME101_FEASIBILITY52.json','PHASE_TESTS52.json','PRESERVATION52.json','SOURCE_BINDING52.json','SUMMARY.json','TESTS.json','WHOLE_KEYFORM52.json','RESUME.json'},
 'joint-eye53':None}
evidence={
 'eye-composition50':{'comparison-1x.png','comparison-8x.png'},
 'lid-evidence51':{'aperture-comparison-1x.png','aperture-comparison-8x.png','existing-reference-curves.png'},
 'whole-eye52':{'actual6-layers-1x.png','actual6-layers-8x.png','source-close-geometry.png'},
 'joint-eye53':{'review-comparison-1x.png','review-comparison-12x.png','pair-preview.gif',*[f'frame{f}-{label}-{zoom}.png'for f in [100,101]for label in ['candidateB','candidateC','candidateB-isolated','candidateC-isolated']for zoom in ['1x']]}}
for group,keep in contracts.items():
 for p in sorted((S/group).rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(S/group);is_root=p.parent==S/group
  include=(is_root and(p.suffix in {'.py','.md','.compute','.shader','.diff'}or p.suffix=='.json'and(keep is None or p.name in keep)))
  include|=(not is_root and group=='joint-eye53'and p.suffix=='.py')
  include|=(group=='joint-eye53'and rel.as_posix()=='logical-gate-only/SUMMARY.json')
  include|=(is_root and p.name in evidence[group])
  original={'source':'EXP27/'+p.relative_to(S).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
  if not include:excluded.append(original);continue
  assert p.stat().st_size<400000,(p,p.stat().st_size)
  target=O/'archive'/group/rel;target.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,target)
  origins[target.relative_to(O).as_posix()]={'mode':'byte-exact copy',**original}
(O/'SOURCE_MANIFEST.json').write_text(json.dumps({'sourceAliases':{'EXP27':'%USERPROFILE%/Documents/Codex/2026-10-27/task-2/render-fix21'},'files':origins},indent=2),encoding='utf-8')
(O/'EXTERNAL_INPUTS.json').write_text(json.dumps({'fullAssetExtractionOrGPUReproduction':False,'sourceAliases':{'EXP27':'%USERPROFILE%/Documents/Codex/2026-10-27/task-2/render-fix21'},'excluded':excluded,'limits':['original VRM and Unity assets not copied','mesh/source re-extraction is not part of portable replay','clean Base/Backing for six vacated samples is missing, not substituted']},indent=2),encoding='utf-8')
dep=P/'experiments/pixel-pipeline/2026-10-30-eye-candidate49'
files={p.relative_to(P).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(dep.rglob('*'))if p.is_file()}
helper=P/'experiments/pixel-pipeline/2026-10-30-source-diagnostics/archive/exp30/flat-albedo-control/pngio.py';files[helper.relative_to(P).as_posix()]={'sha256':sha(helper),'bytes':helper.stat().st_size}
(O/'DEPENDENCIES.json').write_text(json.dumps({'baseCommit':'d0ca21f4ac87e82151357253582f9ce079596a2d','repositoryRelativeFiles':files,'duplicated49Input':False},indent=2),encoding='utf-8')
print(json.dumps({'copiedFiles':len(origins),'bytes':sum(p.stat().st_size for p in O.rglob('*')if p.is_file()),'existingRepoDependencyFiles':len(files),'excludedFiles':len(excluded)}))
