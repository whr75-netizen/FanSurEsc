"""Read-only source/capture analysis. No Unity, shader compilation or GPU work."""
from pathlib import Path
import collections,datetime,hashlib,json,os,sys
import numpy as np

H=Path(__file__).resolve().parent;R=H.parent
os.environ['PIXEL111_FROZEN_INPUTS']='1'
sys.path.insert(0,str(R/'support-contract112'))
from source112 import Source,load,packet_list,read
from support112 import Support

def main():
    doc=Path(r'C:\Users\15352\Desktop\Argon2.5.md')
    if not doc.exists():doc=H/'reference/Argon2.5.md'
    s=Source();_,paths=packet_list();ctx=load(paths[3]);support=Support(s,ctx)
    known=read(R/'bounded-form115/runtime24/full-render24/carrier-fix24/CLOSE75_SKIN_AFFILIATION24.json')
    assert support.key==known['immutableSourceCacheKey'],'Source cache identity changed'
    sourceMap={int(v[2]):i for i,v in enumerate(ctx['sources'])if list(v[:2])==[1,3]}
    rows=[]
    for proof in known['rows']:
        primitive=proof['primitive'];idx=sourceMap[primitive];vertices=support.tri[primitive-1]
        assert vertices.tolist()==proof['vertices']
        tags=np.rint(ctx['triOwners'][idx,:3]).astype(int)
        norms={e:np.linalg.norm(support.deltas[e][vertices].astype(np.float64),axis=1)for e in [1,2]}
        sums={e:float(v.sum())for e,v in norms.items()}
        ipsilateral=int((tags==1).sum())>=2 and sums[1]>=sums[2]
        rows.append({'primitive':primitive,'vertices':vertices.tolist(),'recordedVertexOwners':tags.tolist(),
            'blinkDisplacementsMetres':{str(e):v.tolist()for e,v in norms.items()},'sumMetres':sums,
            'eye1Dominant':bool(ipsilateral),'eye1ActiveNonzero':bool(norms[1].max()>0),
            'epsilonNotSpecifiedInDocument':True,'ringContact':proof['ringContact']})
    phase=read(R/'bounded-form115/runtime24/full-render24/carrier-fix24/PHASE_EXPOSURE24.json')
    coordinateRows=[]
    for row in phase['rows']:
        for sample in row['samples']:
            # Screen and destination queries use bottom-left +Y; hair ROI uses
            # top-left +Y. Preserve that distinction instead of changing signs
            # independently in producer and consumer.
            p=np.array(sample['tile'],int);delta=np.array(sample['commonEyeGridSnapDelta'],np.float64)
            shift=np.rint(np.array([-delta[0],delta[1]])*4).astype(int)
            topLeft=p*4+shift
            coordinateRows.append({'phase':row['phase'],'frame':row['frame'],'sourceId':row['sourceId'],
                'owner':sample['owner'],'canonical':sample['canonical'],'tile':p.tolist(),'snapDelta':delta.tolist(),
                'hairShift4x':shift.tolist(),'firstHairSubsample':topLeft.tolist(),
                'destinationCentreCanonical':(np.array(sample['destinationCentre'])-delta).tolist(),
                'nearest4xCoordinateErrorPx':(shift/4-np.array([-delta[0],delta[1]])).tolist()})
    key=(2,3,4);selected=[x for x in coordinateRows if (x['owner'],*x['canonical'])==key]
    assert len(selected)==10
    assert selected[0]['firstHairSubsample']==selected[1]['firstHairSubsample'],'Document x example does not reproduce'
    maximum=max(abs(v)for x in coordinateRows for v in x['nearest4xCoordinateErrorPx'])
    assert maximum<=.125,'Nearest4x error exceeded its mathematical half-texel bound'
    report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'document':str(doc),'documentSHA256':hashlib.sha256(doc.read_bytes()).hexdigest(),
        'sourceCacheKey':support.key,'skinRows':rows,'dominantActiveSkinCount':sum(x['eye1Dominant']and x['eye1ActiveNonzero']for x in rows),
        'phaseRows':coordinateRows,'documentPhaseExampleReproduced':True,'maximumNearest4xErrorPx':maximum,
        'knownCanonicalCell':selected,'sourcePacketsNotNewCapture':True,'UnityGPUCalls':0,
        'limits':['A zero/nonzero source displacement read is not an invented epsilon; an epsilon policy is not adopted.',
            'Edge-vs-vertex adjacency and SocketLimit spatial reference for the optional two-ring extension need explicit matching definitions.',
            'Correcting hair fetch alone does not correct DirectDepth24/CarrierQueries113/AssignedVisibility24; their 16 coordinates and depth/alpha queries must use the same transformed footprint.',
            'Existing physical-destination depth/visibility records cannot be relabelled as new canonical-coordinate results.',
            'This calculation does not measure corrected final hair occlusion or image quality.',
            'Section3 fixed 1/2-cell shapes and .88/.08/.30 art thresholds are not adopted; source template/geometry and user no-hardcoding constraint remain.']}
    (H/'ARGON25_CPU.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'skin9DominantActive':report['dominantActiveSkinCount'],'sourceCacheIdentityExact':True,'phaseExampleReproduced':True,
        'nearest4xMaxErrorPx':maximum,'correctedFinalOcclusionVerified':False,'UnityGPUCalls':0}))
if __name__=='__main__':main()
