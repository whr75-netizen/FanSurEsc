from pathlib import Path
import hashlib,json,zipfile,subprocess,sys
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');P='experiments/pixel-pipeline/2026-11-11-resume-argon25';D=R/P;BASE='474de71131ddf4d31185b28d9ed2b3971887697b'
ROOTS=['attach_current_colour47.py','BandFixture46.cs.txt','CompleteOwned49.cs.txt','complete_owned49.py','CompletionScope50.cs','CompletionTests50.cs','CurveHistory45.cs','CurveHistoryTests45.cs','fix_domain49_public.py','preflight_owner45.py','prepare_band46.py','prepare_carrier48.py','prepare_domain49.py','prepare_owner45.py','prepare_owner47.py','recover_native_carrier47.py','relay45.py','relay46.py','relay47.py','relay48.py','relay49.py','repair_lifetime50.py','ReplayHistory45.cs','review_band46.py','review_carrier48.py','review_owner45.py','review_owner47.py','SourceCarrier48.compute','SourceDomain49.compute','SourceOwner45.compute','SourceOwner47.compute','test_history45.py','VariableStroke46.shader','variable_stroke46.py','relay33.py','archive_progress50.py','audit_source45.py','audit_rigid45.py']
NAMES={45:'SourceOwner45.compute',46:'VariableStroke46.shader',47:'SourceOwner47.compute',48:'SourceCarrier48.compute',49:'SourceDomain49.compute'}
ASSETS=[f'Assets/EUnityValidation01/SourceBoundary{n}{suffix}'for n,name in NAMES.items()for suffix in ['.meta','/'+name,'/'+name+'.meta']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8',newline='\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True,encoding='utf-8').strip()
def data(p):
 r=json.loads(p.read_text())['result'];return r.get('structuredContent')or next(json.loads(x['text'])for x in r.get('content',[])if x.get('type')=='text')
def main():
 assert git('rev-parse','HEAD')==BASE and not git('diff','--cached','--name-only');user=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(user)==30 and all(sha(R/p)==v for p,v in user.items())
 completed={}
 for n in [45,46,47,48]:
  r=json.loads((H/f'face{n}/capture/COMPLETE.json').read_text());assert r['ownedResourcesReleased'];assert r.get('pendingOwners',r.get('pending'))==0;assert r.get('restorationChecksPass',r.get('stateUnchanged'));completed[str(n)]={'utc':r['utc'],'restored':True,'resourcesReleased':True,'nativeEqual':sum(x.get('equal')is True for x in r['nativeChecks']),'nativeTotal':len(r['nativeChecks']),'beforeMemory':r.get('beforeMemory'),'afterMemory':r.get('afterMemory')}
 assert data(H/'face48/console/REPLY.json')['data']==data(H/'face33/console/REPLY.json')['data'];failed48=json.loads((H/'face48/ACTUAL_CARRIER48.json').read_text());assert failed48['geometryCarrierPass']is False and len(failed48['invalidGeometryClaims'])==18
 incomplete=H/'face49/capture';assert not(incomplete/'COMPLETE.json').exists()and not(incomplete/'FAILED.json').exists();r=json.loads((incomplete/'STATE-004-Edit-restoration-checked.json').read_text());assert r['restorationChecksPass']and r['Edit']and not r['errors'];denial=data(H/'face49/recovery/owned-completion/REPLY.json');assert denial['success']is False and'System.Reflection'in denial['error']and not(H/'face49/recovery/STARTED.txt').exists()
 status={'baselineCommit':BASE,'completedGPUCases':completed,'48GeometryRejected':True,'49SettingsRestored':True,'49OwnedResourcesReleased':False,'49BeforeRTs':r['beforeMemory']['RTCount'],'49AfterRTs':r['afterMemory']['RTCount'],'49RetainedOwnedRTs':45,'49AllocatedMiBChange':(r['afterMemory']['allocated']-r['beforeMemory']['allocated'])/1048576,'49CompletionReadDeniedBeforeExecution':denial['error'],'49CompletionReadSubmitted':False,'49PendingAcknowledgementNotProofOfBusyGPU':True,'future50CPUPatchOnly':True,'product77Changed':False,'user30Equal':True,'facePaletteComplete':False,'characterVariableWidthComplete':False,'renderHistoryStabilizationClaimed':False,'newGPUAllowedBeforeOwnedDrain':False,'GPU115':0,'CUA':0,'SaveAssets':0,'killResetDriverGC':0,'push':False};save(H/'face50/STATUS50.json',status)
 raw=[p for n in range(45,50)for p in(H/f'face{n}/capture').glob('*')if p.suffix=='.f32'or p.name.startswith('geometry-frame')or p.name=='COMPLETE.json'];raw.append(H/'face45/ACTUAL_INPUT45.bin');z=H/'face50/ACTUAL_PACKETS45_49.zip'
 if not z.exists():
  with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED,compresslevel=6)as out:
   for p in sorted(raw):out.write(p,p.relative_to(H).as_posix())
 with zipfile.ZipFile(z)as out:
  assert out.testzip()is None and set(out.namelist())=={p.relative_to(H).as_posix()for p in raw}
  for p in raw:assert hashlib.sha256(out.read(p.relative_to(H).as_posix())).hexdigest()==sha(p)
 selected=ROOTS[:]
 for n in range(45,51):
  for p in(H/f'face{n}').rglob('*'):
   if not p.is_file()or'build'in p.parts or p.name.startswith(('native-before-','TRACE-'))or p.suffix in ['.f32','.bin','.dll','.pdb','.rsp']or p.name in ['ARCHIVE50.json','COMMIT50.json','COMMIT_BODY50.txt','SCHEMA.json']:continue
   selected.append(p.relative_to(H).as_posix())
 selected=sorted(set(selected));rows=[{'path':p,'bytes':(H/p).stat().st_size,'SHA256':sha(H/p)}for p in selected];save(H/'face50/ARCHIVE50.json',{'files':rows,'assets':[{'path':p,'SHA256':sha(R/p)}for p in ASSETS],'rawZipSHA256':sha(z),'live49PendingStatePreserved':True,'nativeBackupsRemainInWorkspace':True})
 if'--publish'in sys.argv:
  for row in rows+[{'path':'face50/ARCHIVE50.json','SHA256':sha(H/'face50/ARCHIVE50.json')}] :
   dst=D/row['path'];src=H/row['path']
   if dst.exists()and sha(dst)!=row['SHA256']:
    assert row['path']=='relay33.py','Do not overwrite existing snapshot '+row['path'];head=subprocess.check_output(['git','show',BASE+':'+P+'/relay33.py'],cwd=R);assert dst.read_bytes().replace(b'\r\n',b'\n')==head.replace(b'\r\n',b'\n')
   dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
  doc=R/'docs/ai/PIXEL_ALBEDO_20261030.md';assert not git('diff','--name-only','--',str(doc));old=doc.read_bytes();add=(H/'face50/HANDOFF_APPEND50.md').read_bytes();assert not old.endswith(add);doc.write_bytes(old+add);assert all(sha(R/p)==v for p,v in user.items())
 print(json.dumps({'files':len(rows)+1,'bytes':sum(x['bytes']for x in rows),'published':'--publish'in sys.argv,'user30Equal':True,'49ResourcesPending':True}))
 if'--commit'in sys.argv:
  assert'--publish'in sys.argv;names=[P+'/'+r['path']for r in rows]+[P+'/face50/ARCHIVE50.json','docs/ai/PIXEL_ALBEDO_20261030.md']+ASSETS;assert not(set(names)&set(user))and len(names)==len(set(names));git('add','--',*names);assert set(git('diff','--cached','--name-only').splitlines())==set(names)
  check=subprocess.run(['git','-c','core.whitespace=trailing-space,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',':(exclude)*.meta'],cwd=R,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
  body=H/'face50/COMMIT_BODY50.txt';body.write_text('Separate curve ownership and source history; preserve width and carrier counterexamples\n\nValidate scoped source-point correspondence, actual native owner receipts and a bounded GPU variable-width operator. Keep canonical source tags distinct from mesh primitives. Preserve the failed single-point carrier48 and feature-mode49 execution, including restored settings, retained owned RTs, denied completion recovery and the CPU-only finally/fence repair50.\n\nDo not adopt the experiments into product77 or claim whole-face palette, temporal or art completion. No push.\n',encoding='utf-8');git('commit','--file',str(body));assert not git('diff','--cached','--name-only')and all(sha(R/p)==v for p,v in user.items());save(H/'face50/COMMIT50.json',{'commit':git('rev-parse','HEAD'),'files':len(names),'user30Equal':True,'product77Changed':False,'49ResourcesPending':True,'push':False});print((H/'face50/COMMIT50.json').read_text())
if __name__=='__main__':main()
