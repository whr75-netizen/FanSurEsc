"""Offline bound/reference only. No layouts from this file are injected into GPU."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
for p in[R/'argon23-runtime113',R/'eye-failures114']:sys.path.insert(0,str(p))
from inputs113 import load_packets,buffer
from oracle113 import subsets,scopes,interval,F,K
from tie114 import transport,rank_source
def pool(path,owner,width):
    frame=buffer(path/'REGION113-frame.f32').reshape(64,4);cells=buffer(path/'REGION113-cells.f32').reshape(512,7,4);tags=buffer(path/'REGION113-tags.f32').reshape(512,4).view(np.uint32);gpu=buffer(path/'REGION113-best.f32').reshape(2,3,4);e=owner-1;points=[c for c in range(len(cells))if cells[c,3,0]==owner and cells[c,5,0]==1 and cells[c,0,0]+cells[c,0,2]>0];neighbours=[sum(1<<p for p,n in enumerate(points)if abs(c%width-n%width)+abs(c//width-n//width)==1)for c in points];sc=scopes(cells,tags,owner,width,points);aa,bb=(subsets(cells,tags,points,p,sc,neighbours)for p in[0,1]);mass=frame[e*32+1];active=frame[e*32+2].view(np.uint32);canvas=frame[e*32+3,0];target=gpu[e,0];bm=np.array([v[0]for v in bb],np.uint32);bc=np.array([v[1]for v in bb],np.uint32);bn=np.array([v[3]for v in bb],np.float32);bd=np.array([v[4]for v in bb],np.float32);found=[]
    for am,ac,ak,an,ad in aa:
        valid=np.where((bm&am)==0)[0]
        if not len(valid):continue
        score=np.column_stack([np.array([(int(active[0])&~ac).bit_count()+(int(active[1])&~int(c)).bit_count()for c in bc[valid]],np.float32),interval(F(an)*K+bn[valid]*K,F(mass[0]+mass[2]),F(mass[1]+mass[3])),interval(F(an)*K,mass[0],mass[1])+interval(bn[valid]*K,mass[2],mass[3]),np.maximum(F(canvas+ad)+bd[valid],0)])
        for j in valid[np.where((score==target).all(1))[0]]:found.append((int(am),int(bm[j])))
    return [(c//width,c%width)for c in points],found
def main():
    P=R/'argon23-runtime113';reg=json.loads((R/'eye-failures114/REGISTRATION_CURRENT102.json').read_text());source=json.loads((P/'SOURCE113.json').read_text());_,packets=load_packets(P);rows=[]
    for entry,path in packets:
        meta=json.loads((path/'RAW_MANIFEST.json').read_text());width=meta['forward102']['canonicalSize'][0]//4;eyes=[]
        for owner in[1,2]:
            points,masks=pool(path,owner,width);assert masks;labels=[[1 if a&(1<<p)else 2 if b&(1<<p)else 0 for p in range(len(points))]for a,b in masks];maps,avail,expected,records=transport(path,owner,reg,source);win,detail=rank_source(labels,points,maps,avail,avail.copy(),expected);eyes.append({'owner':owner,'primaryFourMetricOptima':len(masks),'sourceFormSurvivors':len(win),'masks':masks,'selectedIndices':win,'pointsYX':points,'details':detail})
        rows.append({'sourceId':entry['sourceId'],'frame':entry['frame'],'eyes':eyes})
    (H/'REFERENCE115.json').write_text(json.dumps({'rows':rows,'notRuntimeInput':True,'removedProxySourceKeyCountFromPrimaryRanking':True},indent=2)+'\n',encoding='utf8');print(json.dumps([{'frame':r['frame'],'eyes':[(e['primaryFourMetricOptima'],e['sourceFormSurvivors'])for e in r['eyes']]}for r in rows]))
if __name__=='__main__':main()
