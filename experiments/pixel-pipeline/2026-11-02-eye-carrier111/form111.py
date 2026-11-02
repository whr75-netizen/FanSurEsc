"""Actual111 dense8x source IDs replace110 nearest-rest ID transport.
No new form weights, forced output size, or RGB score. Current availability
precedes immutable-bank conditioning; all complete layout candidates are ranked.
"""
from fractions import Fraction
import sys,json
import numpy as np
from geometry111 import H,R,read
P22=R/'argon22-boundary'if(R/'argon22-boundary').exists()else R/'2026-11-01-argon22-boundary';sys.path.insert(0,str(P22))
from form22 import rank_source

def rank(eye):
    records=eye['sourceIDs'];assert all(v['sourceKeyUnique']for v in records),'Do not infer a unique source key from ambiguous sample metadata';maps={};expected={};available={}
    for r in records:
        key=tuple(r['sourceKeys'][0]);p=1 if r['part']==1 else 2;y,x=r['cellYX'];q=maps.setdefault((y,x,p),{});weight=Fraction(r['certainWeight']);q[key]=q.get(key,Fraction(0))+weight;available[key]=Fraction(1);v=expected.setdefault(key,[Fraction(0),Fraction(0),Fraction(0)]);yy,xx=r['fineYX'];v[0]+=weight;v[1]+=weight*Fraction(2*xx+1,16);v[2]+=weight*Fraction(2*yy+1,16)
    expected={key:(v[1]/v[0],v[2]/v[0])for key,v in expected.items()};canonical=available.copy();variant=next(v for v in eye['variants']if v['componentFirst']);layouts=[np.array(v)for v in variant['labels']];points=[tuple(map(int,q))for q in np.argwhere(np.any(np.array(layouts)>0,axis=0))];vectors=[[int(a[q])for q in points]for a in layouts];chosen,info=rank_source(vectors,points,maps,available,canonical,expected)
    return {'completeLayoutPool':variant['solver']['allOptimalSolutionsEnumerated'],'selectedIndices':chosen,'details':info,'allDense8xSourceKeysUniqueUnderFloat32Bounds':True,'IDSource':'same-frame GPU dense8x rest/bank branch + exact registration projection; role/RGB checks, no nearest source key','historyUsed':False,'sourceVisibleKeys':[list(k)for k in sorted(available)]}
def main():
    out=[]
    for p in sorted(H.glob('ANALYSIS111-frame*.json'),key=lambda p:int(p.stem.split('frame')[1])):
        d=read(p);q={'sourceId':d['sourceId'],'frame':d['frame'],'eyes':[]}
        for e in d['eyes']:
            ranking=rank(e);q['eyes'].append({'owner':e['owner'],**ranking})
        out.append(q)
    (H/'FORM111.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'frame':v['frame'],'eyes':[{'owner':e['owner'],'selected':e['selectedIndices']}for e in v['eyes']]}for v in out]))
if __name__=='__main__':main()
