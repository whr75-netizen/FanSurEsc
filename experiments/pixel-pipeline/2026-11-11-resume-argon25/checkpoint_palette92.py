"""Narrow continuation of92, after actual GPU success; no bulk old archive."""
from pathlib import Path
import json,subprocess,sys,shutil
import checkpoint92 as prior
H=prior.H;R=prior.R;P=prior.P;G=H/'face92';DOC=prior.DOC;HEAD='a67a656366c1965b4b588195de884796a50b4cea';git=prior.git;sha=prior.sha;save=prior.save
def names():
 code='palette_constraints92.py PaletteConstraints92.cs test_palette_constraints92.py audit_palette_constraints92.py PaletteConstraintsTests92.cs audit_palette_port92.py prepare_capture92.py prepare_motion92.py relay92.py review_colour92.py review_motion_sheet92.py PaletteRuntime89.cs SourceField89.cs.txt prepare_colour89.py review_colour89.py review_rgb_history91.py checkpoint_palette92.py'.split()
 data='face92/CPU_PALETTE_CONSTRAINTS92.json face92/PALETTE_CONSTRAINTS92.json face92/CONSTRAINED92.rgb face92/PALETTE_CONSTRAINT_INPUT92.npz face92/CONTRAST92.i32 face92/CSHARP_CONSTRAINED92.rgb face92/CPU_PALETTE_PORT92.json face92/ADDRESS92.r32 face92/TABLE92.json face92/gpu/CPU_PREPARED92.json face92/gpu/ACTUAL_COLOUR92.json face92/gpu/ACTUAL_COLOUR92.png face92/gpu/ACTUAL_COLOUR92.webp face92/gpu/ACTUAL_PALETTE_CONSTRAINTS92.json face92/gpu/DELIVERABLE92.json face92/motion240/CPU_PREPARED92.json face92/motion240/ACTUAL_COLOUR92.json face92/motion240/ACTUAL_COLOUR92.png face92/motion240/ACTUAL_COLOUR92.webp face92/motion240/ACTUAL_SEQUENCE92.png face92/motion240/ACTUAL_PALETTE_CONSTRAINTS92.json face92/motion240/RGB_CONTINUITY91.npz face92/motion240/RGB_CONTINUITY91.json face92/motion240/RGB_CONTINUITY_PROVENANCE91.json'.split()
 for group in ['face92/gpu','face92/motion240']:
  data += [group+'/'+n for n in ['capture/RUN.cs.txt','capture/COMPLETE.json','capture/RUNTIME_PALETTE89.json','capture/RUNTIME_PALETTE89.rgb','post/final/STATE.json','console/REPLY.json']]
  frames=json.loads((H/group/'capture/COMPLETE.json').read_text())['stream77']['frames'];chosen=frames if group=='face92/gpu'else[frames[0],frames[-1]]
  for f in chosen:data += [group+'/capture/'+f['compressedFile'],group+'/capture/'+f['light84']['sourceGeometryFile']]
 return code+data
def main():
 ns=names();assert len(ns)==len(set(ns))and all((H/n).is_file()for n in ns);manifest=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns];selection={'files':manifest,'count':len(ns),'bytes':sum(x['bytes']for x in manifest),'all240RawIncluded':False,'oldBulkArchiveRetried':False};save(G/'SELECTION_PALETTE92.json',selection);print(json.dumps({k:v for k,v in selection.items()if k!='files'}),flush=True)
 if '--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only')
 user=json.loads((H/'face55/BEFORE_GIT55.json').read_text())['user30'];protected=json.loads((H/'face55/backup/DISK_BEFORE.json').read_text())
 def preserved():assert all(sha(R/p)==v for p,v in user.items())and all(sha(R/x['path'])==x['sha256']for x in protected if x['exists'])
 preserved();s=json.loads((H/'face92/motion240/post/final/STATE.json').read_text());assert s['Edit']and not s['compiling']and s['inputJSONExact']and len(s['dirty'])==31 and s['allRTCount']==30 and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==s['sourceFlatTexturesRemaining67']==0
 old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);doc=(R/DOC).read_bytes();assert doc.startswith(old)and doc[len(old):].decode('utf-8').lstrip().startswith('### 92 추가:')
 for x in manifest:
  dst=R/P/x['path']
  if dst.exists():assert dst.read_bytes()==subprocess.check_output(['git','show','HEAD:'+P+'/'+x['path']],cwd=R)
  else:dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes((H/x['path']).read_bytes());assert sha(dst)==x['SHA256']
 save(R/P/'face92/SELECTION_PALETTE92.json',selection)
 # Test the committed-source candidate against saved source data, all output
 # written only to this workspace. This creates no Unity/GPU object.
 check=G/'repo-check-constraints';check.mkdir(exist_ok=True)
 for n in ['SOURCE_VALUE92.npz','REFERENCES92.rgb','ORDERS92.i32']:shutil.copyfile(H/'face92'/n,check/n)
 program='import sys,numpy as np;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import audit_palette_constraints92 as a;a.H=Path(sys.argv[1]);a.G=Path(sys.argv[2]);a.main();import audit_palette_port92 as p;p.H=a.H;p.G=a.G;p.main();assert (a.G/"CSHARP_CONSTRAINED92.rgb").read_bytes()==(a.H/"face92/CSHARP_CONSTRAINED92.rgb").read_bytes();import review_rgb_history91 as q;q.verify(Path(sys.argv[3]))'
 run=subprocess.run([sys.executable,'-B','-X','utf8','-c',program,str(R/P),str(check),str(H/'face92/motion240')],capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
 selected=[P+'/'+n for n in ns]+[P+'/face92/SELECTION_PALETTE92.json',DOC];spec=G/'SELECT_PALETTE92.paths';spec.write_bytes(('\0'.join(selected)+'\0').encode('utf-8'));git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(selected);exact=[p for p in selected if p.endswith('RUN.cs.txt')];git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in exact]);preserved()
 body=G/'COMMIT_BODY_PALETTE92.txt';body.write_text('Preserve native colour contrasts through finite palette RGB8 rounding\n\nKeep original58 continuous targets and floor-ceil bounds. CPU bounded constraint propagation/search preserves3822 native RGB directions and Y orders, with exact Python/C# parity. Reuse existing91 raster without new shader/import/compute. Validate actual6 and240 consecutive normal-input frames, finite RGB lookup, current visibility/alpha and source-carrier history.\n\nPreserve product77/user30/protected128 and Edit/input/native/resource state. Four seconds is not long gameplay stability. General variable line width, source colour distortion and final art remain incomplete. No push.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only');preserved();save(G/'COMMIT_PALETTE92.json',{'commit':git('rev-parse','HEAD'),'selectedFiles':len(selected),'repositoryCPURecheckExact':True,'actualGPUFrames':246,'product77Changed':False,'user30Protected128Equal':True,'generalLineWidthOrFinalArtAdopted':False,'push':False});print((G/'COMMIT_PALETTE92.json').read_text())
if __name__=='__main__':main()
