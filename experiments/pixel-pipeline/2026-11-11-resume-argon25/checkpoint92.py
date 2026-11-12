"""Select this completed colour work only; no old bulk archive or user staging."""
from pathlib import Path
import json,hashlib,subprocess,sys,shutil
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';G=H/'face92';DOC='docs/ai/PIXEL_ALBEDO_20261030.md';HEAD='57c742a7724bf31941f5f611099e0422ada63901'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
 p=subprocess.run(['git',*args],cwd=R,capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr;return p.stdout.strip()
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2),encoding='utf-8',newline='\n')
def names():
 code='source_value88.py test_source_value88.py audit_source_value88.py palette_round88.py PaletteTargets88.cs build_palette88.py compose_cpu88.py PaletteRuntime89.cs PaletteRuntimeTests89.cs SourceField89.cs.txt SourceValue89.shader SourceValue91.shader prepare_colour89.py prepare_current91.py prepare_long89.py prepare_lookup89.py prepare_long91.py prepare_bounded91.py relay89.py relay91.py review_colour89.py review_rgb_history91.py audit_ordered_value90.py chromatic_value92.py test_chromatic_value92.py audit_chromatic_value92.py review_palette92.py checkpoint92.py SourceShadeTests87.cs compile_light84.py'.split()
 data='face88/CPU_SOURCE_VALUE88.json face88/SOURCE_VALUE88.json face88/SOURCE_VALUE88.npz face88/SOURCE_VALUE88.png face88/PROFILE_INPUT88.npz face88/REFERENCES88.json face88/PALETTE88.rgb face88/PALETTE_TARGETS88.npz face88/PALETTE_ROUND88.json face88/CPU_FULL_COLOUR88.json face88/CPU_FULL_COLOUR88.png face88/ADDRESS89.r32 face88/REFERENCE88.rgb face88/ORDERS88.i32 face88/TABLE89.json face89/CPU_PORT89.json face89/CPU_PREPARED89.json face89/CPU_SHADER84.json face89/DISK_PREFLIGHT89.json face89/import/COMPLETE.json face89/fix2/ACTUAL_COLOUR89.json face89/fix2/ACTUAL_COLOUR89.png face89/fix2/ACTUAL_COLOUR89.webp face89/motion192/SOURCE_VALIDITY_FAILURE_AUDIT89.json face89/lookup64/EXACT_FAILURE89.json face90/SOURCE_VALUE90.json face90/SOURCE_VALUE90.npz face90/SOURCE_VALUE90.png face90/CPU_COLOUR90.json face90/CPU_COLOUR90.png face90/REFERENCES90.rgb face90/ORDERS90.i32 face91/EXACT_CURRENT_HISTORY_FIX91.json face91/CPU_SHADER84.json face91/import/COMPLETE.json face91/ACTUAL_COLOUR91.json face91/ACTUAL_COLOUR91.png face91/ACTUAL_COLOUR91.webp face91/DELIVERABLE91.json face91/motion192/WORLD_OCCLUSION91.json face91/motion192/LAST_FRAME_AUDIT91.json face91/bounded192/CPU_PREPARED_BOUNDED91.json face91/bounded192/ACTUAL_COLOUR91.json face91/bounded192/ACTUAL_COLOUR91.png face91/bounded192/ACTUAL_COLOUR91.webp face91/bounded192/RGB_CONTINUITY91.npz face91/bounded192/RGB_CONTINUITY91.json face91/bounded192/RGB_CONTINUITY_PROVENANCE91.json face92/CPU_CHROMATIC92.json face92/SOURCE_VALUE92.json face92/SOURCE_VALUE92.npz face92/SOURCE_VALUE92.png face92/REFINEMENT92.json face92/CPU_PALETTE92.json face92/CPU_PALETTE92.png face92/PALETTE92.rgb face92/REFERENCES92.rgb face92/ORDERS92.i32'.split()
 for group in ['face89/fix2','face91','face91/bounded192']:
  data += [group+'/'+f for f in ['capture/RUN.cs.txt','capture/COMPLETE.json','capture/RUNTIME_PALETTE89.json','capture/RUNTIME_PALETTE89.rgb','post/final/STATE.json','console/REPLY.json']]
  frames=json.loads((H/group/'capture/COMPLETE.json').read_text())['stream77']['frames'];selected=frames if group=='face89/fix2'else[frames[0],frames[-1]]
  for f in selected:data += [group+'/capture/'+f['compressedFile'],group+'/capture/'+f['light84']['sourceGeometryFile']]
 for group in ['face89/motion192','face89/lookup64','face91/motion192']:
  data += [group+'/capture/FAILED.json',group+'/capture/RUN.cs.txt']
 data += [str(p.relative_to(H)).replace('\\','/')for p in sorted((H/'face89/lookup64/capture').glob('FAILED_INPUT89-*'))]
 return code+data
def main():
 ns=names();assert len(ns)==len(set(ns));missing=[n for n in ns if not(H/n).is_file()];assert not missing,missing
 manifest=[{'path':n,'SHA256':sha(H/n),'bytes':(H/n).stat().st_size}for n in ns];selection={'files':manifest,'count':len(ns),'bytes':sum(x['bytes']for x in manifest),'allLongRawCopied':False,'oldBulk293Retried':False};save(G/'SELECTION92.json',selection);print(json.dumps({k:v for k,v in selection.items()if k!='files'}),flush=True)
 if '--publish'not in sys.argv:return
 assert git('rev-parse','HEAD')==HEAD and not git('diff','--cached','--name-only')
 user=json.loads((H/'face55/BEFORE_GIT55.json').read_text())['user30'];protected=json.loads((H/'face55/backup/DISK_BEFORE.json').read_text())
 def preserved():assert all(sha(R/p)==v for p,v in user.items())and all(sha(R/x['path'])==x['sha256']for x in protected if x['exists'])
 preserved();state=json.loads((H/'face91/bounded192/post/final/STATE.json').read_text());assert state['Edit']and not state['compiling']and state['inputJSONExact']and len(state['dirty'])==31 and state['allRTCount']==30 and state['diagnosticRTs']==state['diagnosticMaterials']==state['commandUpdateObservers']==state['sourceFlatTexturesRemaining67']==0
 old=subprocess.check_output(['git','show','HEAD:'+DOC],cwd=R);doc=(R/DOC).read_bytes();assert doc.startswith(old)and doc[len(old):].decode('utf-8').lstrip().startswith('## 88–92.')and not git('diff','--name-only','--',DOC).splitlines()[1:]
 for n in ns:
  dst=R/P/n
  if dst.exists():
   assert n in ['SourceShadeTests87.cs','compile_light84.py'];assert dst.read_bytes()==subprocess.check_output(['git','show','HEAD:'+P+'/'+n],cwd=R)
  else:dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes((H/n).read_bytes());assert sha(dst)==sha(H/n)
 save(R/P/'face92/SELECTION92.json',selection)
 # Recalculate the source field from the repository's original input, but put
 # all recalculation outputs in our workspace. No Library/Unity call or import.
 check=G/'repo-check';check.mkdir(exist_ok=True);shutil.copyfile(H/'face88/PROFILE_INPUT88.npz',check/'PROFILE_INPUT88.npz')
 program='import sys,json,numpy as np;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import audit_source_value88 as m;m.H=Path(sys.argv[1]);m.G=Path(sys.argv[2]);m.main();a=np.load(m.H/"face88/SOURCE_VALUE88.npz");b=np.load(m.G/"SOURCE_VALUE88.npz");assert a.files==b.files and all(np.array_equal(a[k],b[k]) for k in a.files);print("repository source arrays exact")'
 replay=subprocess.run([sys.executable,'-B','-X','utf8','-c',program,str(R/P),str(check)],capture_output=True,text=True);assert replay.returncode==0,replay.stdout+replay.stderr
 verify=subprocess.run([sys.executable,'-B','-X','utf8','-c','import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import review_rgb_history91 as m;m.verify(Path(sys.argv[2]))',str(R/P),str(H/'face91/bounded192')],capture_output=True,text=True);assert verify.returncode==0,verify.stdout+verify.stderr
 assets=[]
 for d in ['SourceValue89','SourceValue91']:
  ps=[f'Assets/EUnityValidation01/{d}.meta',f'Assets/EUnityValidation01/{d}/{d}.shader',f'Assets/EUnityValidation01/{d}/{d}.shader.meta'];assert sha(R/ps[1])==sha(H/(d+'.shader'))and all(not git('ls-files','--',p)for p in ps);assets+=ps
 selected=[P+'/'+n for n in ns]+[P+'/face92/SELECTION92.json',DOC]+assets;spec=G/'SELECT92.paths';spec.write_bytes(('\0'.join(selected)+'\0').encode('utf-8'));git('add','--pathspec-from-file='+str(spec),'--pathspec-file-nul');assert set(git('diff','--cached','--name-only').splitlines())==set(selected)
 exact=[p for p in selected if p.endswith('.meta')or p.endswith('RUN.cs.txt')];git('-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',*[f':(exclude){p}'for p in exact]);preserved()
 body=G/'COMMIT_BODY92.txt';body.write_text('Connect source colour addresses and actual GPU Q to finite RGB palettes\n\nSeparate linear brightness floor from OKLab interval units and current colour validity from conservative history validity. Validate actual6,64 and192-frame bounded normal-input renders with exact LUT RGB, alpha and current visibility. Record129-frame world-occlusion guard and the original one-ULP history-validity counterexample.\n\nPreserve product77/user30/protected128, Edit/native/input/options state and owned resource release. CPU source-address refinement92 remains unadopted because one dark palette contrast fails. General variable integer width, final art and long gameplay stability remain incomplete. No push.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only');preserved();save(G/'COMMIT92.json',{'commit':git('rev-parse','HEAD'),'files':len(selected),'user30Protected128Equal':True,'repositorySourceRecalculationExact':True,'actualGPUFramesInCompletedRuns':6+64+192,'product77Changed':False,'CPU92Adopted':False,'finalArtOrLongGameplayCompleted':False,'push':False});print((G/'COMMIT92.json').read_text())
if __name__=='__main__':main()
