"""Read-only saved source audit. Affine-L compatibility is not semantic truth."""
from pathlib import Path
import hashlib,itertools,json
import numpy as np
from PIL import Image
from region62 import lab

R=Path(__file__).resolve().parent
T=Path('C:/Users/15352/Documents/Codex/2026-10-30/task/model-source')
S59=R.parent/'renderer-family59'
if not S59.exists():S59=R.parent/'2026-10-31-renderer-family59'
registry=json.loads((S59/'SOURCE_REGISTRY59.json').read_text());cells=json.loads((R/'CELLS62.json').read_text())
images={};support={};labels={}
for b in registry['bindings']:
 if b['rendererOrdinal']!=2:continue
 p=T/f"image-{b['imageIndex']}.png";raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==b['imageSHA256']
 images[b['materialId']]=np.array(Image.open(p).convert('RGBA'))
 a=np.load(R/f"source-{b['materialId']}-regions62.npz");support[b['materialId']]=a['support'];labels[b['materialId']]=a['labels']
corners=np.array(list(itertools.product([-.5,.5],repeat=3)))
def bounds(rgb):
 # RGB8 encoding uncertainty, not a fitted epsilon or an art threshold.
 values=lab(np.clip(np.array(rgb)+corners,0,255))[:,0]
 return float(values.min()),float(values.max())
rows=[]
for r in cells['rows']:
 m=r['materialId'];im=images[m];h,w=im.shape[:2];x,y=r['nativeTexel'];central=bounds(im[y,x,:3]);axes=[]
 for dx,dy in [(1,0),(0,1)]:
  lo=(x-dx,y-dy);hi=(x+dx,y+dy)
  if not all(0<=a<w and 0<=b<h and support[m][b,a]and im[b,a,3]==255 for a,b in [lo,hi]):continue
  a,b=[bounds(im[v,u,:3])for u,v in [lo,hi]];expected=((a[0]+b[0])/2,(a[1]+b[1])/2)
  compatible=max(central[0],expected[0])<=min(central[1],expected[1])
  residual=float(lab([im[y,x,:3]])[0,0]-(lab([im[lo[1],lo[0],:3]])[0,0]+lab([im[hi[1],hi[0],:3]])[0,0])/2)
  axes.append({'axis':'x'if dx else'y','nativeSamplesRGB8':[im[lo[1],lo[0],:3].tolist(),im[y,x,:3].tolist(),im[hi[1],hi[0],:3].tolist()],'centreLInterval':central,'affinePredictionLInterval':expected,'signedSecondDifferenceHalf':residual,'affineCompatibleWithinRGB8':compatible})
 rows.append({'x':r['x'],'yBottom':r['y'],'materialId':m,'nativeTexel':[x,y],'sourceRegionId':r['sourceRegionId'],'Q':r['Q'],'g':r['g'],'hasContrastCertificate':r['semanticFeature'].startswith('certified'),'axisMeasurements':axes,'bothAxesAffineCompatible':len(axes)==2 and all(a['affineCompatibleWithinRGB8']for a in axes),'meaning':'smooth/constant source-profile compatibility only. A curved texture gradient, authored thin mark, UV overlap and geometry edge require further evidence; no mask or label changed.'})
out={'sourceId':cells['sourceId'],'source':'original embedded PNGs, verified imageSHA256','scope':'current373 source point texels / native3-sample profiles, not screen blur','affineCompatibleBothAxes':sum(r['bothAxesAffineCompatible']for r in rows),'twoAxesMeasured':sum(len(r['axisMeasurements'])==2 for r in rows),'sourceLightingTermUsedForRegion':False,'labelsChanged':0,'semanticFeatureDetectionComplete':False,'rows':rows}
(R/'SOURCE_PROFILE_AUDIT62.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items()if k!='rows'},indent=2))
