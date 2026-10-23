from pathlib import Path
import json
import numpy as np

O=Path(__file__).resolve().parent
views=json.loads((O/'VIEWS538.json').read_text())
def intersects(a,b,c,d):
    r=b-a;s=d-c;den=r[0]*s[1]-r[1]*s[0];q=c-a
    if den==0:
        if q[0]*r[1]-q[1]*r[0]!=0:return False
        return all(max(min(a[k],b[k]),min(c[k],d[k]))<=min(max(a[k],b[k]),max(c[k],d[k]))for k in[0,1])
    t=(q[0]*s[1]-q[1]*s[0])/den;u=(q[0]*r[1]-q[1]*r[0])/den
    return bool(0<=t<=1 and 0<=u<=1)

rows=[]
for case in ['actual43','actual44','actual50']:
    v=next(x for x in views if x['case']==case)
    r0,r1=[np.array(r['vertices'])for r in v['referenceBoundaries']]
    area=float(sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(r1,np.roll(r1,-1,axis=0)))*.5)
    cross=int(sum(intersects(a,b,c,d)for a,b in zip(r0,np.roll(r0,-1,axis=0))for c,d in zip(r1,np.roll(r1,-1,axis=0))))
    cell=np.floor(r1.mean(axis=0)).astype(int).tolist()
    nv=next((n for n in v['nodes']if n['insideOwnerCell']==cell),None)
    rows.append({'case':case,'smallReferenceRingArea':area,
        'smallReferenceBBox':[r1.min(axis=0).tolist(),r1.max(axis=0).tolist()],
        'boundaryIntersectionsWithMain':cross,'containingCell':cell,
        'centreCarrierForCell':None if nv is None else{'nodeID':nv['id'],
            'referenceIDs':sorted({t['referenceBoundaryID']for t in nv['referenceIncidences']})}})
(O/'REFERENCE_EVENTS538.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows));print('views bytes',(O/'VIEWS538.json').stat().st_size)
