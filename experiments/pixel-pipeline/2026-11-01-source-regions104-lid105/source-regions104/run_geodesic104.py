from pathlib import Path
import json,time,sys,hashlib
import numpy as np
from PIL import Image
from watershed104 import segment
from graph_regions104 import boundary
from run_graph104 import debug
H=Path(__file__).resolve().parent;SOURCE=H.parent/'source-regions103'
sys.path.insert(0,str(H.parent/'uv-features64'));from uv_features64 import lab

def main():
    rows=[]
    for part in (3,6):
        d=np.load(SOURCE/f'part{part}/hierarchy.npz');mask=d['mask'];rgb=d['rgba'][...,:3]
        started=time.perf_counter();a=segment(rgb,mask);elapsed=time.perf_counter()-started
        labels=a['labels'];valid=mask&(labels>=0);sizes=np.bincount(labels[valid]);col=lab(rgb)
        lo=np.full((a['markerCount'],3),np.inf);hi=np.full_like(lo,-np.inf)
        for c in range(3):
            np.minimum.at(lo[:,c],labels[valid],col[valid,c]);np.maximum.at(hi[:,c],labels[valid],col[valid,c])
        out=H/f'part{part}';out.mkdir(exist_ok=True)
        np.savez_compressed(out/'geodesic-labels.npz',**a,mask=mask)
        preview=debug(np.maximum(labels,0),valid);preview[mask&(labels==-2)]=[255,255,255,255]
        Image.fromarray(preview).save(out/'geodesic-regions.png')
        overlay=d['rgba'].copy();overlay[boundary(labels,mask)]=[255,0,255,255]
        Image.fromarray(overlay).save(out/'geodesic-source-boundaries.png')
        q=np.nan_to_num(a['gradient'],nan=0,posinf=0)
        gradient=np.rint(np.clip(q/max(float(q.max()),1e-30),0,1)*255).astype(np.uint8)
        Image.fromarray(gradient).save(out/'gradient-diagnostic-normalized.png')
        row={'part':part,'method':'RGB8 precision h-minima + positive additive geodesic labels; independent diagnostic, not exact watershed',
             'sourceSHA256':hashlib.sha256(rgb.tobytes()+mask.tobytes()).hexdigest(),'hSourceRGBCodeGradient':a['h'],
             'markerCount':a['markerCount'],'regions':int((sizes>0).sum()),'singletons':int((sizes==1).sum()),
             'uncertainTies':int((mask&(labels==-2)).sum()),'missingSeedSupport':int((mask&(labels==-1)).sum()),
             'regionLRangeMax':float((hi-lo)[:,0].max()),'largestRegions':sorted(sizes.tolist(),reverse=True)[:12],
             'seconds':elapsed,'sourceRGBAChanged':0,'paletteApplied':False}
        if part==3:
            row['scalpSkinProbe']=[{'cropXY':[x,y],'region':int(labels[y,x]),'RGB8':rgb[y,x].tolist()}for x,y in [(503,9),(461,760)]]
            row['scalpSkinSeparated']=bool(labels[9,503]!=labels[760,461]and min(labels[9,503],labels[760,461])>=0)
        rows.append(row);print(json.dumps(row),flush=True)
    (H/'GEODESIC104.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':main()
