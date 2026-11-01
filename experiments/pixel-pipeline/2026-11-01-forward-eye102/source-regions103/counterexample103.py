from pathlib import Path
import json,sys,numpy as np
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'uv-features64'));from uv_features64 import lab
rows=[]
for part in [3,6]:
 a=np.load(H/f'part{part}/hierarchy.npz');rgb=a['rgba'][...,:3];mask=a['mask'];labels=a['coarse'];counts=np.bincount(labels[mask]);rid=int(counts.argmax());ys,xs=np.nonzero(mask&(labels==rid));v=lab(rgb[ys,xs]);low=int(v[:,0].argmin());high=int(v[:,0].argmax());row={'part':part,'largestCoarseRegion':rid,'texels':int(counts[rid]),'sourceLRange':[float(v[low,0]),float(v[high,0])],'sameRegionContrastingSourcePoints':[{'cropXY':[int(xs[k]),int(ys[k])],'RGB8':rgb[ys[k],xs[k]].tolist(),'OKLab':v[k].tolist()}for k in [low,high]],'conclusion':'native affine-jump coarse partition does not separate all finite-width antialiased colour boundaries; do not assign one medoid/palette to this region as if feature extraction succeeded'};rows.append(row)
(H/'COUNTEREXAMPLES103.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows,ensure_ascii=False))
