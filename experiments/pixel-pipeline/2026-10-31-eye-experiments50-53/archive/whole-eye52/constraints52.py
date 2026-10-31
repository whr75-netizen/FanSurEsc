"""Small visibility/feasibility checks; no repeated phase sweep or Unity."""
from pathlib import Path
import copy,hashlib,json,sys
import numpy as np
from whole52 import WholeEye52,compose_registered,native_representative
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';L=R.parent/'lid-evidence51'
sys.path[:0]=[str(B),str(L)]
from candidate49 import CachedCell,StateBoundCluster,projected_anchor,representative,known_final_occlusion
from registered_aperture51 import evaluate_registered51
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
bundle=load(R/'WHOLE_KEYFORM52.json');cache=WholeEye52(bundle,bundle['referenceAnchor'])
m=load(B/'fixtures/frames.json');z=np.load(B/'fixtures/replay-inputs.npz');source=load(L/'KEYFORM_BUNDLE51.json')
sources={v['sourceId']for v in m}
cells=[CachedCell(v['cellId'],v['eye'],v['role'],tuple(v['referenceXY']),tuple(v['rgba8']))for v in source['cells']]
cluster=StateBoundCluster('52','open-reference',bundle['referenceAnchor'],cells,m[0]['styleJson'])
checks=[]
def check(name,value):
    if not value:raise AssertionError(name)
    checks.append(name)
for i,meta in enumerate(m):
    d={k.split('_',1)[1]:z[k]for k in z.files if k.startswith(f'f{i:02}_')and not k.endswith('_GPU')}
    before={k:hashlib.sha256(a.tobytes()).hexdigest()for k,a in d.items()}
    anchor,_=projected_anchor(meta);placed=cache.request(cache.key,'existing-open-reference',anchor)
    lines=[v for v in placed['cells']if v['role']==6]
    hair=dict(d);hair['hair-meta']=np.full_like(d['hair-meta'],[1,12,1,1])
    rows=evaluate_registered51(cluster,cluster.key,cluster.state,meta,hair,source,sources,representative,known_final_occlusion,projected_anchor)
    check('front hair hides every eye pixel '+str(meta['frame']),not any(v['visible']for v in rows))
    check('front hair hides every native-lid candidate '+str(meta['frame']),not any(native_representative(hair,meta,v,known_final_occlusion).get('support')for v in lines))
    absent=dict(d);absent['S3META']=np.zeros_like(d['S3META'])
    check('no native-lid emission without measured source '+str(meta['frame']),not any(native_representative(absent,meta,v,known_final_occlusion).get('support')for v in lines))
    absent['S1META']=np.zeros_like(d['S1META']);absent['S2META']=np.zeros_like(d['S2META'])
    rows=evaluate_registered51(cluster,cluster.key,cluster.state,meta,absent,source,sources,representative,known_final_occlusion,projected_anchor)
    check('no source-free iris or sclera fill '+str(meta['frame']),not any(v['visible']for v in rows))
    other=dict(d);other['S0META']=np.full_like(d['S0META'],[1,8,1,1]);other['S0POINT']=d['S0POINT'].copy();other['S0POINT'][...,3]=1
    rows=evaluate_registered51(cluster,cluster.key,cluster.state,meta,other,source,sources,representative,known_final_occlusion,projected_anchor)
    check('foreign material never erased as face underlay '+str(meta['frame']),not any(v['visible']for v in rows if v['eye']==1))
    check('all frozen arrays unchanged '+str(meta['frame']),before=={k:hashlib.sha256(a.tobytes()).hexdigest()for k,a in d.items()})

last=load(L/'APERTURE_RESULTS.json')[-1];row=next(v for v in last['registered51']if v['eye']==1 and v['role']==1 and v['xy']==[222,52])
source50=load(R.parent/'eye-composition50'/'RESULTS.json')[-1]
lid=source50['eyes']['1']['sourceLid'];iris=[v['xy']for v in last['registered51']if v['eye']==1 and v['role']==1 and v['visible']]
check('actual frame101 lid overlaps registered iris cell',lid==[[222,52]]and lid[0]in iris)
check('four-cell reference comes from existing Template, not fixed minimum',len(iris)==sum(v['eye']==1 and v['role']==1 for v in source['cells']))
truth=[]
for lid_first in[False,True]:
    visible_iris=[v for v in iris if not lid_first or v not in lid]
    visible_lid=[v for v in lid if lid_first or v not in iris]
    truth.append(dict(rule='lid-first'if lid_first else'iris-first',iris=visible_iris,lid=visible_lid,
        bothOriginalPartsIntact=(visible_iris==iris and visible_lid==lid)))
check('changing only priority cannot keep both fixed overlapping parts',not any(v['bothOriginalPartsIntact']for v in truth))
record=dict(frame=101,sourceId=m[-1]['sourceId'],xy=[222,52],cachedIrisSourceCell=row,
    originalSourceNativeLid=lid,existingReferenceIris=iris,orderTruthTable=truth,
    conclusion='This particular fixed raster plus the source lid is incompatible at one opaque cell. It does not prove eye correction impossible; a joint state raster must change their shared placement rather than merely priority.',
    newDesignAdopted=False,productModified=False)
(R/'FRAME101_FEASIBILITY52.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
(R/'CONSTRAINT_TESTS52.json').write_text(json.dumps(dict(assertions=len(checks),allPassed=True,cases=checks),ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(constraintAssertions=len(checks),frame101FixedRasterAndLidCompatible=False,allPassed=True),indent=2))
