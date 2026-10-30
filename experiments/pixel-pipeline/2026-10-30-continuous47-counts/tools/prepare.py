from pathlib import Path
import hashlib,json,struct,shutil
import numpy as np

W=Path(__file__).resolve().parent
S=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\continuous47-counts')
O=W/'2026-10-30-continuous47-counts'
assert not O.exists(),'Never overwrite an existing snapshot'
O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
origins={}
def info(p):
 p=Path(p);return {'source':'CONTINUOUS47/'+p.relative_to(S).as_posix()if p.is_relative_to(S)else 'EXP27/author33/feature34/eye_cache42.py','sha256':sha(p),'bytes':p.stat().st_size}
def copy(p,rel):
 d=O/rel;d.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,d);assert sha(d)==sha(p);origins[rel]={'mode':'byte-exact copy',**info(p)}

files=['analyse_counts.py','REPORT_KO.md','STATUS.json','FINAL_OCCLUSION_TRACE.json','FIRST_PACKET_TRACE.json',
 'analysis/SUMMARY.json','analysis/PACKET_REPLAY_AND_ALLOCATOR.json','analysis/RESTORATION.json','analysis/CONSOLE_DELTA.json',
 'candidate/EyeFeature348_visibility_gate47.compute','candidate/PROPOSED_ONLY.diff','candidate/STATIC_AND_COUNTERFACTUAL_VERIFIED.json',
 'Capture.cs','Begin.cs','Finish.cs','FinalState.cs']
for name in files:copy(S/name,'archive/'+name)
copy(S.parent/'author33/feature34/eye_cache42.py','archive/eye_cache42.py')
for name in ['analysis/actual-strip-1x.png','analysis/actual-strip-8x.png','analysis/actual-slow.gif','analysis/actual-features-above-offline-gate-below.png']:
 copy(S/name,'evidence/'+Path(name).name)
for frame in [96,97,98,99,100,101]:copy(S/f'analysis/frame{frame}-actual.png',f'evidence/frame{frame}-actual.png')

needed=['S0META','S0POINT','S1META','S1POINT','S2META','S2POINT','S3META','S3POINT','S4META','S5META','S6META','hair-meta','brow-meta','raw-meta','eye-visible']
arrays={};sources=[];meta=[]
for folder in sorted((S/'frames').iterdir()):
 index=int(folder.name);p=folder/'meta.json';meta.append(json.loads(p.read_text(encoding='utf-8-sig')));sources.append(info(p))
 for name in needed:
  p=folder/(name+'.bin');b=p.read_bytes();w,h=struct.unpack_from('<ii',b)
  arrays[f'f{index:02}_{name}']=np.frombuffer(b,'<f4',offset=8).reshape(h,w,4)[::-1].copy();sources.append(info(p))
 p=folder/'FeatureCounts19.bin';b=p.read_bytes();w,h,e,stride=struct.unpack_from('<iiii',b);assert e==2 and stride==48
 arrays[f'f{index:02}_GPU']=np.frombuffer(b,'<f4',offset=16).reshape(e,h,w,12)[:,::-1].copy();sources.append(info(p))
(O/'fixtures').mkdir()
np.savez_compressed(O/'fixtures/replay-inputs.npz',**arrays)
(O/'fixtures/frames.json').write_text(json.dumps(meta,separators=(',',':')),encoding='utf-8')
origins['fixtures/replay-inputs.npz']={'mode':'lossless bounded fixture','rule':'Only 15 consumed ROI arrays and FeatureCounts19 per frame; float32 values unchanged, y-flip as original read(); omit source UV/RGBA/full-scene inputs','sources':sources}
origins['fixtures/frames.json']={'mode':'bounded metadata fixture','rule':'six original metadata objects, compact JSON encoding','sources':[info(S/'frames'/f'{i:02}'/'meta.json')for i in range(6)]}
manifest={'sourceAliases':{'CONTINUOUS47':'%USERPROFILE%/Documents/Codex/2026-10-27/task-2/render-fix21/continuous47-counts','EXP27':'%USERPROFILE%/Documents/Codex/2026-10-27/task-2/render-fix21'},'sequenceId':'counts47-087454994917423fa13c5fe72eceb7f4','files':origins}
(O/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
excluded=[{'source':'CONTINUOUS47/'+p.relative_to(S).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in S.rglob('*')if p.is_file()and p.relative_to(S).as_posix()not in files and p.suffix.lower()not in ['.png','.gif']]
(O/'EXTERNAL_INPUTS.json').write_text(json.dumps({'standaloneBoundedPacketReplay':True,'fullUnityCaptureOrRestorationReplay':False,'sourceAliases':manifest['sourceAliases'],'excluded':excluded,'notIncluded':['original VRM/texture assets','full scene serialization dump','ongoing memory diagnosis','Unity executable and active Editor state']},indent=2),encoding='utf-8')
print(json.dumps({'files':sum(p.is_file()for p in O.rglob('*')),'bytes':sum(p.stat().st_size for p in O.rglob('*')if p.is_file()),'fixtureNPZBytes':(O/'fixtures/replay-inputs.npz').stat().st_size,'uncompressedFixtureBytes':sum(a.nbytes for a in arrays.values())}))
