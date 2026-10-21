"""Same81 stored masks/poses: correspondence and cost only, no reselection."""
from pathlib import Path
import json,time,struct,hashlib,collections
import numpy as np
import active516 as G,arc517 as A,span517 as N,span516 as O
from context516 import signature
W=G.ROOT;R=G.INPUT;D=W/'Temporal517'/'SpanArcV2';D.mkdir(parents=True,exist_ok=True)
MODEL=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01/HeadRegion502/Resources/HeadCurve511.bytes')
header=struct.unpack_from('<4iQ',MODEL.read_bytes());modelKey=f'{header[2]}:{header[3]}:{header[4]:016x}'

def old_groups(spans):
    out={}
    for span in spans:out.setdefault((span['ring'],span['segment']),[]).append(span)
    return out
def arc_record(arc):
    return {'points':arc['p'].tolist(),'area':arc['area'],'sign':arc['sign'],'depth':arc['depth'],'totalLength':arc['total'],'sourceLineage':sorted(arc['lineage'])}
rows=[];previous=None;previous516=None;start=time.perf_counter();contexts=set();inputHashes=[]
for i in range(81):
    begin=time.perf_counter();doc=json.loads((R/f'{i:03d}_curves.json').read_text());rings=[[(q['x'],q['y'])for q in r['points']]for r in doc['curves']]
    cache=json.loads((W/'Temporal516'/f'{i:03d}_ACTIVE.json').read_text());arcs,junctions=A.active_arcs(cache['active']);mask=G.read_mask(i);bindings,unsupported=A.bind(mask,arcs)
    variantChecks=[]
    for arc in arcs:
        p=[tuple(q)for q in arc['p']];split=[];slide=[]
        for a,b in zip(p,p[1:]+p[:1]):
            split.extend([a,G.lerp(a,b,.25),G.lerp(a,b,.5),G.lerp(a,b,.75)]);slide.extend([a,G.lerp(a,b,.2),G.lerp(a,b,.7)])
        variants=[A.make_arc(split),A.make_arc(slide),A.make_arc(p[len(p)//2:]+p[:len(p)//2])]
        invariant=all(A.equal_geometry(arc,v)and np.array_equal(arc['p'],v['p'])for v in variants)
        variantChecks.append(invariant)
    cfg=json.loads((R/f'{i:03d}_ALT_projection.json').read_text());context=signature(modelKey,cfg['headProjection'],cfg['headView'],'Rig|Walk_Loop');contexts.add(context)
    result=None;before=None
    if previous:
        if previous['context']!=context:result={'raw':0.,'valid':False,'rows':[],'geometryEventResets':[{'reason':'MODEL_CAMERA_OR_CLIP_CONTEXT_RESET'}],'failedCorrespondences':[]}
        else:result=N.compare(previous['arcs'],previous['bindings'],arcs,bindings,True)
        old=old_groups(previous516['spans']);cur=old_groups(cache['spans']);keys=set(old)|set(cur)
        before=sum(O.channel_cost(old.get(key,[]),cur.get(key,[]),rings,previous516['active'],cache['active'],key)['raw']for key in keys)
    row={'target':i,'phase':i/80,'actualGeometryArcs':[arc_record(a)for a in arcs],'pixelLoops':len(A.pixel_loops(mask)),'boundPixelLoops':len(bindings),'boundUnitEdges':sum(len(b['samples'])for b in bindings.values()),'sourcePixelBoundaryEdges':len(G.boundary(mask)),'unsupportedBindings':unsupported,'junctionEvents':junctions,'sameGeometryVariantChecks':variantChecks,'allVariantsCanonicalBitIdentical':all(variantChecks),'old516RawCost':before,'new517':result,'costComparable':i>0 and not unsupported and not previous['unsupported']and result['valid']and not junctions,'seconds':time.perf_counter()-begin,'maskUnchangedSHA256':hashlib.sha256(mask.tobytes()).hexdigest()}
    (D/f'{i:03d}_AUDIT.json').write_text(json.dumps(row,separators=(',',':'))+'\n');rows.append({k:v for k,v in row.items()if k not in['actualGeometryArcs','new517']})
    previous={'arcs':arcs,'bindings':bindings,'unsupported':unsupported,'context':context};previous516=cache
    if i%5==0:print(json.dumps({'frame':i,'arcs':len(arcs),'pixelLoops':row['pixelLoops'],'boundEdges':row['boundUnitEdges'],'totalEdges':row['sourcePixelBoundaryEdges'],'unsupported':len(unsupported),'oldCost':before,'newCost':None if result is None else result['raw'],'seconds':row['seconds']}),flush=True)
valid=[i for i,r in enumerate(rows)if r['costComparable']];newRows=[json.loads((D/f'{i:03d}_AUDIT.json').read_text())for i in range(81)]
comparisons=[{'target':i,'old':newRows[i]['old516RawCost'],'new':newRows[i]['new517']['raw'],'geometryEventResets':newRows[i]['new517']['geometryEventResets'],'failedCorrespondences':newRows[i]['new517']['failedCorrespondences']}for i in range(1,81)]
for i in range(81):
    for ending in ['_curves.json','_MASK.bin.gz','_ALT_projection.json']:
        p=R/f'{i:03d}{ending}';inputHashes.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
out={'mode':'SAME_STORED81_POSES_MASKS_CORRESPONDENCE_AND_COST_ONLY','frames':81,'seconds':time.perf_counter()-start,'modelKeyFromSourceTopologyHeader':modelKey,'modelKeyIsNotControlAssetHash':True,'contextCount':len(contexts),'allPerPoseVariantsCanonicalBitIdentical':all(r['allVariantsCanonicalBitIdentical']for r in rows),'fullyBoundFrames':sum(r['boundUnitEdges']==r['sourcePixelBoundaryEdges']and not r['unsupportedBindings']for r in rows),'comparablePairs':len(valid),'all80PairsComparable':len(valid)==80,'rows':rows,'comparisons':comparisons,'comparableOldCostSum':sum(newRows[i]['old516RawCost']for i in valid),'comparableNewCostSum':sum(newRows[i]['new517']['raw']for i in valid),'betaAndAtomicCostChanged':False,'temporalStateCostChanged':False,'selectorRuns':0,'newUnityCalls':0,'novelDonorVisibility':'516 novel471 remain uncertified; no new selection or packet pass is claimed','sourceInputs':inputHashes,'limits':['Numeric total cost changes are not visual improvement or time-stability proof.','Closed-arc cyclic start and monotone geometric correspondence replace per-control channels; 516 atomic edit rules remain fixed.','Explicit physical visibility reset is fixture-tested; lack of a selected span is not treated as physical occlusion.','Non-bijective geometric component events and unresolved binding are reported, never forced into successful cost comparisons.']}
(D/'AUDIT517.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['rows','comparisons','sourceInputs','limits']}),flush=True)
