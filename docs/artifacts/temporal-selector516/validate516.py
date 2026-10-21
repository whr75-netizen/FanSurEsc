from pathlib import Path
import ast,json,hashlib,zipfile,subprocess
import numpy as np
from PIL import Image
W=Path(__file__).parent;D=W/'Temporal516';R=W/'Loop514';P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
z=np.load(D/'ALL_REGION_SEQUENCES516.npz');assert list(z['masks'].shape)==[3,81,272,480]
for k,eta in enumerate(z['etas']):
 for i in range(81):assert np.array_equal(z['masks'][k,i],np.load(D/('eta-'+str(eta))/f'{i:03d}.npy'))
checks.append('All3x81 full-grid masks bit-match stored selector outputs')
ts=z['timestamps'];assert len(ts)==81 and np.all(np.diff(ts)>0)and abs((ts[-1]-ts[0])-1.3333331774376411)<1e-10
checks.append('All81 source timestamps retained;80 intervals1333ms')
with Image.open(D/'FULLBODY_CONTEXT_OFFLINE_MASKS516.webp')as im:
 assert im.n_frames==80;elapsed=0
 for i in range(80):
  im.seek(i);im.load();elapsed+=im.info['duration'];actual=np.array(im.convert('RGB'))[46:356,2:226]
  with Image.open(R/f'{i:03d}_ALT.png')as source:expected=np.array(source.convert('RGB').crop((332,48,556,358)))
  assert np.array_equal(actual,expected),(i,'Body diagnostic is not pixel-lossless')
 assert elapsed==1333
checks.append('Decoded80-frame WebP duration1333ms and actual body crop matches every source PNG exactly; candidate panels are unrendered masks')
f=json.loads((D/'FINAL516.json').read_text());assert f['sourceCorrespondenceFailure']['sameRegionControlSlideTemporalCost']==5.5 and f['historyCostFailure']['stationaryAllMoves']['oneCellLocalFixedPoint']
assert json.loads((D/'SUPPORT516.json').read_text())['novelSelectionObservations']==471
checks.append('Reparameterization failure and stationary switching barrier preserved; all471 novel packets remain uncertified')
for row in json.loads((W/'APPLIED_SOURCE512.json').read_text())['files']:assert sha(P/row['path'])==row['after']
settings=json.loads((W/'RECORDED514.json').read_text())['protectedSettings']
for rel,h in settings.items():assert sha(P/rel)==h
checks.append('Runtime/shader and user Quality/Time hashes unchanged')
sources=['active516.py','span516.py','select516.py','context516.py','test516.py','review516.py','failure516.py','support516.py','finish516.py','validate516.py']
for name in sources:ast.parse((W/name).read_text())
checks.append('Ten analysis/prototype Python sources parse; no C# project edits')
local=[]
for i in range(81):
 for ending in ['_curves.json','_areas.bin','_MASK.bin.gz','_packets.json','_ALT_bodyrefs512.json','_ALT_projection.json','.hairgeom','_ALT.raymesh']:
  p=R/(f'{i:03d}'+ending);local.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)})
(D/'LOCAL_INPUTS516.json').write_text(json.dumps(local,indent=2)+'\n')
for name in ['ALL_SELECTOR_TRACES516.zip']:
 with zipfile.ZipFile(D/name)as archive:assert archive.testzip()is None
checks.append('All selector trace ZIP entries CRC-valid;648 stored local inputs fingerprinted')
out={'checks':checks,'artifactIntegrityPassed':True,'visualOrRuntimeAdoptionPassed':False,'decision':'REJECTED_OFFLINE_PROTOTYPE','defaultOFF':True,'noNewUnityCalls':True,'protectedSettings':settings,'sources':[{'name':n,'sha256':sha(W/n)}for n in sources]}
(D/'VALIDATION516.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
