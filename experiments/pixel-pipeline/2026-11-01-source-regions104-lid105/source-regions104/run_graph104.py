from pathlib import Path
import json,time,sys,hashlib
import numpy as np
from PIL import Image
from graph_regions104 import graph,partition,stats,boundary

H=Path(__file__).resolve().parent;SOURCE=H.parent/'source-regions103'
sys.path.insert(0,str(H.parent/'uv-features64'))
from uv_features64 import lab

def debug(labels,mask):
    result=np.zeros((*mask.shape,4),np.uint8);v=labels[mask].astype(np.uint32)+1
    result[mask,:3]=np.column_stack([(v*73)%223+32,(v*131)%223+32,(v*191)%223+32]).astype(np.uint8)
    result[mask,3]=255
    return result

def main():
    results=[]
    for part in (3,6):
        d=np.load(SOURCE/f'part{part}/hierarchy.npz');rgb=d['rgba'][...,:3];mask=d['mask']
        output=H/f'part{part}';output.mkdir(exist_ok=True)
        started=time.perf_counter();g=graph(rgb,mask,sigma=.8);labels=partition(g,k=300.)
        dt=time.perf_counter()-started
        np.savez_compressed(output/'graph-labels.npz',labels=labels,mask=mask)
        Image.fromarray(debug(labels,mask)).save(output/'regions.png')
        overlay=d['rgba'].copy();edge=boundary(labels,mask);overlay[edge]=[255,0,255,255]
        Image.fromarray(overlay).save(output/'source-boundaries.png')
        colour=lab(rgb);n=labels.max()+1;count=np.bincount(labels[mask]);lo=np.full((n,3),np.inf);hi=np.full((n,3),-np.inf)
        for c in range(3):
            np.minimum.at(lo[:,c],labels[mask],colour[mask,c]);np.maximum.at(hi[:,c],labels[mask],colour[mask,c])
        row={'part':part,'inputSHA256':hashlib.sha256(rgb.tobytes()+mask.tobytes()).hexdigest(),
             'policy':{'algorithm':'FH2004 Algorithm1 independent implementation','weights':'sRGB8 Euclidean, masked Gaussian sigma .8 for detection only','k':300,'connectivity':4,'minSizeMerge':False,'paletteApplied':False},
             **stats(labels,mask),'regionLRangeMax':float((hi[:,0]-lo[:,0]).max()),'seconds':dt,
             'graphEdges':len(g['w']),'graphEdgeBytes':g['edgeBytes']}
        if part==3:
            pair=[(503,9),(461,760)]
            row['scalpSkinProbe']=[{'cropXY':[x,y],'RGB8':rgb[y,x].tolist(),'region':int(labels[y,x])}for x,y in pair]
            row['scalpSkinSeparated']=labels[9,503]!=labels[760,461]
        results.append(row);print(json.dumps(row,default=bool),flush=True)
    (H/'RESULT104.json').write_text(json.dumps(results,indent=2,default=bool))
if __name__=='__main__':main()
