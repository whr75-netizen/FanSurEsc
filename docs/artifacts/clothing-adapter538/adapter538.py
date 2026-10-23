"""Offline labelled evaluation view; the region mask remains authoritative.

No fill reconstruction, selector, temporal state, radius search or Unity call.
Reference incidence is geometric boundary/owner-cell intersection, not a claim
about 3D triangle, UV, visibility or unique feature-line correspondence.
"""
from pathlib import Path
from collections import defaultdict
import hashlib, json, math
import numpy as np

O=Path(__file__).resolve().parent
W=O.parent
ns={'__file__':str(W/'Feature535/compare535.py')}
exec((W/'Feature535/compare535.py').read_text().split('\nrows = []')[0],ns)
saved,boundaries=ns['saved'],ns['boundaries']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def clip_segment(a,b,cell):
    lo,hi=0.,1.;d=b-a
    for axis in [0,1]:
        x=cell[axis]
        if d[axis]==0:
            if not x<=a[axis]<=x+1:return None
        else:
            t,u=(x-a[axis])/d[axis],(x+1-a[axis])/d[axis]
            lo=max(lo,min(t,u));hi=min(hi,max(t,u))
            if lo>hi:return None
    return [float(lo),float(hi)]

def make_view(case,label,refs,mask,box,input_path=None):
    before=hashlib.sha256(mask.tobytes()).hexdigest();mask.setflags(write=False)
    loops,turns=boundaries(mask,box);nodes=[];edges=[];paths=[];pixels=defaultdict(list)
    cache={}
    def incidences(cell):
        if cell not in cache:
            v=[]
            for ri,r in enumerate(refs):
                for ei,(a,b)in enumerate(zip(r,np.roll(r,-1,axis=0))):
                    t=clip_segment(a,b,cell)
                    if t is not None:v.append({'referenceBoundaryID':f'{case}/reference/{ri}',
                        'referenceEdgeIndex':ei,'t':t})
            cache[cell]=v
        return cache[cell]
    for li,loop in enumerate(loops):
        bid=f'{case}/{label}/boundary/{li}';groups=[];curve_edges=[]
        for ei,(aa,bb)in enumerate(zip(loop,np.roll(loop,-1,axis=0))):
            a,b=tuple(map(int,aa)),tuple(map(int,bb));dx,dy=b[0]-a[0],b[1]-a[1]
            assert abs(dx)+abs(dy)==1
            owner=a if dx==1 else(a[0]-1,a[1])if dy==1 else(b[0],b[1]-1)if dx==-1 else b
            assert mask[owner[1]-box[1],owner[0]-box[0]]
            if not groups or groups[-1]['owner']!=owner:groups.append({'owner':owner,'edgeIndices':[]})
            groups[-1]['edgeIndices'].append(ei)
            curve_edges.append({'boundaryID':bid,'edgeIndex':ei,'from':a,'to':b,'insideOwnerCell':owner})
        if len(groups)>1 and groups[0]['owner']==groups[-1]['owner']:
            groups[0]['edgeIndices']=groups[-1]['edgeIndices']+groups[0]['edgeIndices'];groups.pop()
        ids=[]
        for ni,g in enumerate(groups):
            owner=g['owner'];nid=f'{bid}/node/{ni}';ids.append(nid);pixels[owner].append(nid)
            nodes.append({'id':nid,'boundaryID':bid,'xy':[owner[0]+.5,owner[1]+.5],
                'insideOwnerCell':owner,'carrierEdgeIndices':g['edgeIndices'],'referenceIncidences':incidences(owner)})
            for ei in g['edgeIndices']:curve_edges[ei]['centreNodeID']=nid
        unique=len({g['owner']for g in groups})
        paths.append({'id':bid,'closedRegionBoundary':True,'centreNodeIDs':ids,
            'simpleCentreCycle':len(groups)>=3 and unique==len(groups),
            'degenerateCentrePath':len(groups)<3,'nonconsecutiveRepeatedPixels':len(groups)-unique,
            'signedRegionArea':float(sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(loop,np.roll(loop,-1,axis=0))))*.5})
        edges.extend(curve_edges)
    after=hashlib.sha256(mask.tobytes()).hexdigest();assert before==after
    for path in paths:
        carried=[i for n in nodes if n['boundaryID']==path['id']for i in n['carrierEdgeIndices']]
        expected=[e['edgeIndex']for e in edges if e['boundaryID']==path['id']]
        assert sorted(carried)==sorted(expected)and len(carried)==len(set(carried))
    referenceIDs={v['referenceBoundaryID']for n in nodes for v in n['referenceIncidences']}
    multi=[{'xy':list(p),'nodeIDs':v}for p,v in sorted(pixels.items())if len(v)>1]
    return {'case':case,'candidate':label,'coordinateContract':'logical pixel edges integer; centres owner+(0.5,0.5)',
        'authority':{'kind':'original selected closed region','box':box,'maskSHA256':before,'maskUnchanged':True,
                     'inputPath':str(input_path)if input_path else None,'inputSHA256':sha(input_path)if input_path else None},
        'referenceBoundaries':[{'id':f'{case}/reference/{i}','vertices':r.tolist()}for i,r in enumerate(refs)],
        'paths':paths,'nodes':nodes,'edges':edges,'sharedPixelIncidences':multi,
        'unrepresentedReferenceBoundaryIDs':sorted({f'{case}/reference/{i}'for i in range(len(refs))}-referenceIDs),
        'regionBoundaryTurnDecisions':turns,'generatedFill':False,
        'directIncidenceNotUniqueFeatureMatching':True}

def whole_spatial_input_gate(v):
    # Do not create numeric partial sums or add missing-feature penalties.
    missing={
      'Eso':['common reference/output feature-line identity and phase, including omitted/merged/degenerate lines'],
      'Esc':['fixed original pixel-line footprint with its warp and Manhattan weights; region cell area is not ci'],
      'Eqs':['paper pixel-path vectorization and reference pixel-perturbation, not535 list exclusion'],
      'Eqj':['same pixel-path/extremum/span graph and fixed initial span denominator']}
    concrete=[]
    if v['unrepresentedReferenceBoundaryIDs']:concrete.append('reference boundary has no direct selected-outline carrier incidence')
    if any(p['degenerateCentrePath']for p in v['paths']):concrete.append('centre path has fewer than3 points; closed normalized turning function undefined')
    if v['sharedPixelIncidences']:concrete.append('distinct region boundaries share physical pixels; labelled nodes intentionally remain distinct')
    if len(v['referenceBoundaries'])!=len(v['paths']):concrete.append('continuous reference and selected region have different boundary counts')
    return {'case':v['case'],'candidate':v['candidate'],'spatialWeights':[1,.5,1,.5],
        'completeScore':None,'allTermsSameInputReady':False,'missingByTerm':missing,
        'concreteRepresentationEvents':concrete,'notNumericalFailure':True}

def run():
    source=json.loads((W/'Feature535/METRIC_AUDIT535.json').read_text())
    views=[]
    for q in source['rows']:
        refs=[np.array(r,float)for r in q['fixedReference']]
        for label,a in q['alternatives'].items():
            p=Path(a['path']);assert sha(p)==a['sha256'];_,box,_,mask=saved(p)
            views.append(make_view(q['case'],label,refs,mask,box,p))
    for name,mask in [('diagonalContact',np.array([[1,0],[0,1]],bool)),('holeWall1',np.array([[1,1,1],[1,0,1],[1,1,1]],bool))]:
        box=(0,0,mask.shape[1],mask.shape[0]);refs,_=boundaries(mask,box)
        views.append(make_view(name,'fixed',refs,mask,box))
    gates=[whole_spatial_input_gate(v)for v in views]
    (O/'VIEWS538.json').write_text(json.dumps(views,separators=(',',':')),encoding='utf-8')
    (O/'WHOLE_SPATIAL_INPUT_GATE538.json').write_text(json.dumps(gates,indent=2),encoding='utf-8')
    brief=[{'case':v['case'],'candidate':v['candidate'],'regionMaskUnchanged':v['authority']['maskUnchanged'],
        'referenceBoundaryCount':len(v['referenceBoundaries']),'regionBoundaryCount':len(v['paths']),
        'edges':len(v['edges']),'centreNodes':len(v['nodes']),'sharedPhysicalPixels':len(v['sharedPixelIncidences']),
        'degeneratePaths':sum(p['degenerateCentrePath']for p in v['paths']),
        'unrepresentedReferences':v['unrepresentedReferenceBoundaryIDs']}for v in views]
    summary={'status':'LABELLED_OFFLINE_VIEW_CONNECTED_COMPLETE_SPATIAL_EVALUATION_NOT_READY',
        'offlineAdapterImplemented':True,'runtimeAdapterImplemented':False,'candidateViews':len(views),
        'caseCount':len({v['case']for v in views}),'allRegionMasksPreserved':all(v['authority']['maskUnchanged']for v in views),
        'completeSpatialScoresComputed':0,'requiredWholeSpaceTermsImplemented':[],
        'missingTerms':['Eso exact common line input','Esc source stroke/warp','Eqs exact vectorization/reference perturbation','Eqj initial span graph'],
        'numericalImprovementOrRegressionVerdict':None,'selectorReplacement':False,
        'newUnityCalls':0,'newCaptures':0,'newProductCode':False,'defaultOFF':True,'weightsTuned':False,
        'extraPenaltiesAdded':False,'rows':brief}
    (O/'SUMMARY538.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items()if k!='rows'}))
    print(json.dumps([q for q in brief if q['case']in['actual43','actual44','actual50','thin0_0','diagonalContact','holeWall1']]))

if __name__=='__main__':run()
