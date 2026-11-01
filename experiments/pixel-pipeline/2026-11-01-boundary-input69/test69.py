"""Small counterexamples plus actual packet invariants; no Unity or tuning sweep."""
from pathlib import Path
import json,numpy as np
from coverage_boundary69 import both_diagonals,clip,area
from schema69 import shade_labels
from probe69 import CAPTURE
R=Path(__file__).resolve().parent;passed=[]
triangle=np.array([[0,0,0],[1,0,1],[0,1,0]],float);assert abs(area(clip(triangle,2,.5))-.125)<1e-12;passed.append('exact clipped triangle area')
h,w=8,10;yy,xx=np.indices((h,w));g=np.clip(.08*xx+.04*yy-.1,0,1);valid=np.ones((h,w),bool);mask=np.ones((h//2,w//2),bool);q=(g[1::2,1::2]>=.5).astype(int);faces={(x,y):(0,0,0) for y in range(h) for x in range(w)};vertices={(0,0,0):{0}}
a,*_=both_diagonals(q,mask,g,valid,faces,vertices)
for turns in [1,2,3]:
 gg=np.rot90(g,turns);vv=np.rot90(valid,turns);qq=np.rot90(q,turns);mm=np.rot90(mask,turns);ff={(x,y):(0,0,0) for y in range(len(gg)) for x in range(gg.shape[1])};b,*_=both_diagonals(qq,mm,gg,vv,ff,vertices);assert np.array_equal(np.rot90(a,turns),b)
passed.append('90/180/270 rotation invariance over both diagonals')
hole=mask.copy();hole[2,2]=False;before=q.copy();out,*_=both_diagonals(q,hole,g,valid,faces,vertices);assert out[2,2]==before[2,2];passed.append('source-domain hole / excluded eye cell unchanged')
strip=np.zeros_like(g);strip[:,4:6]=1;qq=(strip[1::2,1::2]>.5).astype(int);o,*_=both_diagonals(qq,mask,strip,valid,faces,vertices);assert np.all(o[1:-1,2]==1);passed.append('thin supported bright stripe not removed by region size')
unknown={p:(1,0,0) if p[0]>=5 else (0,0,0) for p in faces};vv={(0,0,0):{0},(1,0,0):{1}};o,b,d,u,_,_=both_diagonals(q,mask,g,valid,unknown,vv);assert u[:,2].min()>.49;passed.append('different physical sources remain unknown, not interpolated')
try:shade_labels(np.zeros((2,2,4)),np.ones((2,2),bool),'EyeFeature348.postEyeUV')
except ValueError:passed.append('post-eye UV schema rejected as Q')
else:raise AssertionError('wrong Q schema accepted')
d=np.load(R/'CANDIDATE69.npz');assert np.all(d['QCandidate'][~d['mask']]==d['QBefore'][~d['mask']]);passed.append('actual packet outside-domain label changes zero')
raw=json.loads((R/'RESULT69.json').read_text());assert len(raw['schemaCollisionCells'])==9;assert all(x['hardFeatureLock'] is False and x['UVAndIndexHashMatchedCurrentGeometry'] for x in raw['source64SoftContours']);passed.append('actual source evidence is typed soft, not hard feature bins')
assert not raw['referenceGate']['passesNonRegression'] and np.array_equal(d['QAccepted'],d['QBefore']);passed.append('actual tangent regression rejects spatial candidate and keeps original output')
src=(CAPTURE/'CaptureRetry66.cs').read_text(encoding='utf-8');patch=(CAPTURE/'EYE_OBSERVER68.patch').read_text(encoding='utf-8');repo=next((p for p in R.parents if (p/'Assets/EUnityValidation01').is_dir()),Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game'));host=(repo/'Assets/EUnityValidation01/HeadLocal367/Runtime/HeadLocal367.cs').read_text(encoding='utf-8-sig');assert 'n.host.headEyes:n.host.mainEyes' in patch and 'public EyeFeature348 mainEyes' in host and 'public EyeFeature348 headEyes' in host and 'FirstOrDefault(x=>x.full==f)' in src;passed.append('eye observer direct-host patch source contract, remains unapplied')
result={'passed':len(passed),'cases':passed,'limits':['source-connected scalar reference remains an estimate','No actual motion / blink / GPU candidate integration']};(R/'TEST69.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
