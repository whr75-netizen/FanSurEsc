"""Offline regressions, finite perturbation probes and footprint evidence.
Does not call Unity or certify a continuous visibility field from samples.
"""
from pathlib import Path
from fractions import Fraction
import json,gzip,hashlib,itertools,math,time
import numpy as np
from stored110 import H,P108,P109,source_packet,plane
from resolver110 import tests,solve,distances,feasible
from identity110 import relative_form,rank_with_relative
from reconstruct110 import template,recover
from fields110 import FaceVisibility
from geometry109 import prepare_packet
from native109 import uv_bary,read
from io109 import buffer

def loaded(f,o):
    root=H/'separated';d=np.load(root/f'frame{f}-eye{o}.npz');r=read(root/f'frame{f}-eye{o}-result.json')
    return {'cells':[tuple(map(int,v))for v in d['cells']],'eligibility':d['eligibility'],'references':{p:d['reference'+str(p)]for p in [1,2,3]},'connectivity':{int(p):v for p,v in r['connectivity'].items()}},r

def d4_tests():
    checked=0
    for frame,owner in [(103,1),(107,1)]:
        p,r=loaded(frame,owner);baseline=solve(**p,witness_limit=None);assert baseline['enumerationComplete'];expected=set(map(tuple,baseline['solutions']))
        for swap in [False,True]:
            for sx,sy in itertools.product([-1,1],repeat=2):
                matrix=np.array([[0,sx],[sy,0]])if swap else np.diag([sx,sy]);cells=[]
                for y,x in p['cells']:
                    corners=(np.array([[x,y],[x+1,y],[x,y+1],[x+1,y+1]])@matrix.T);q=corners.min(0);cells.append(tuple(map(int,q[::-1])))
                new=p|{'cells':cells,'references':{k:v@matrix.T for k,v in p['references'].items()}};q=solve(**new,witness_limit=None)
                assert abs(q['errorPixels']-baseline['errorPixels'])<1e-12 and set(map(tuple,q['solutions']))==expected;checked+=1
        ix=list(range(len(p['cells'])))[::-1];q=solve(**(p|{'cells':[p['cells'][i]for i in ix],'eligibility':p['eligibility'][ix]}),witness_limit=None)
        assert {tuple(v[::-1])for v in q['solutions']}==expected;checked+=1
    return checked

def source_shape_counterexample():
    # Equal source-ID distributions do NOT imply equal spatial form.
    a=(1,1,10,10);b=(1,1,11,10);available={a:Fraction(1),b:Fraction(1)};canonical=available;expected={a:(Fraction(1,2),Fraction(1,2)),b:(Fraction(3,2),Fraction(1,2))};cells=[(0,0),(0,1)]
    transport={(0,0,1):{a:Fraction(1),b:Fraction(1)},(0,1,1):{b:Fraction(2)}}
    v1=relative_form(cells,[1,0],transport,expected,available);v2=relative_form(cells,[0,1],transport,expected,available)
    assert v1['1:relativeGeometry']>0 and v2['1:missingSourcePairs']>0
    # A separate exact mapping with each key in its own cell has zero error.
    exact={(0,0,1):{a:Fraction(1)},(0,1,1):{b:Fraction(1)}}
    v=relative_form(cells,[1,1],exact,expected,available);assert all(x==0 for x in v.values())
    # Occlusion always removes availability before comparing history.
    ix,_,_=rank_with_relative([[0,0]],cells,transport,{},canonical,[available],expected);assert ix==[0]
    return {'histogramIsNotShape':True,'relativeSourcePairsMeasuredSeparately':True,'historyDoesNotReanimateUnavailableSource':True}

def count_bound_oracle():
    checked=0
    for n in range(1,6):
        cells=[(0,i)for i in range(n)];domains=[7]*n;clauses=[(1,sum(1<<i for i in range(n)if i%2==0)),(2,(1<<n)-1)]
        allValues=[v for v in itertools.product(range(3),repeat=n)if any(v[i]==1 for i in range(n)if i%2==0)and 2 in v]
        for part in [1,2]:
            for count in range(n+1):
                q,_=feasible(domains,clauses,cells,{},1,{part:(count,count)});expected=[v for v in allValues if v.count(part)==count];assert bool(q)==bool(expected)
                if q:assert q[0]in expected
                checked+=1
    return checked

def source_query_proofs(rows,domain,templates):
    out=[]
    for frame in [101,192]:
        row=next(r for r in rows if r['name']=='actual107-frame'+str(frame));p=source_packet(row);ctx,_,_=recover(row,domain,templates);w,h=ctx['manifest']['forward102']['denseSize'];proof=buffer(p/'dense-skin-query-proof.f32').reshape(h,w,2,4);uv=np.flipud(plane(p/'D-lid-uv.plane')[1]);world=[]
        for y,x in np.argwhere((proof[:,:,0,0]>0)&(proof[:,:,0,3]==1)&(proof[:,:,1,2]==1)):
            prim=round(float(uv[y,x,2]))-1;ids=ctx['indices'][6][prim];b=uv_bary(ctx['uv'][ids],uv[y,x,:2]);world.append(b@ctx['world'][ids])
        hits=FaceVisibility(ctx).query(world);blocked=sum(h['visibleBounds']==[0.,0.]for h in hits);assert blocked==len(hits)
        out.append({'frame':frame,'sourceId':row['sourceId'],'certainGPUFrontAlphaWitnesses':len(hits),'independentReconstructionAlsoBlocked':blocked})
    return out

def footprint_checks(rows,domain,templates):
    samples=pieces=partial=0;maxspread=0.;ambiguous=0;clipping=0.;external=0;frontChangedAcrossSameCell=0
    for file in H.glob('*frame*-eye*-footprint.json.gz'):
        with gzip.open(file,'rt',encoding='utf8')as f:d=json.load(f)
        row=next(r for r in rows if r['sourceId']==d['metadata']['sourceId'])
        if row['name'].startswith('closed105'):ctx=prepare_packet(source_packet(row),domain,read(P109/'NATIVE_CACHE109.json'))
        else:ctx,_,_=recover(row,domain,templates)
        for rec in d['footprints']:
            origin=np.array(rec['targetOriginCanonical']);z=[];front=[]
            for piece in rec['pieces']:
                q=np.array(piece['XY']);b=np.array(piece['barycentric']);ids=ctx['indices'][rec['sourcePart']][piece['primitive']-1];assert np.max(abs(b.sum(1)-1))<1e-10 and b.min()>-1e-8;assert np.max(abs(b@ctx['depth'][ids]-piece['depth']))<1e-11;clipping=max(clipping,float(np.maximum(np.maximum(origin-q,q-origin-1),0).max()));pieces+=1
            for s in rec['samples']:
                samples+=1;z.append(s['depth']);world=np.r_[s['world'],1];assert abs(-float(ctx['view'][2]@world)-s['depth'])<1e-11
                v=s['visibleBounds'];assert 0<=v[0]<=v[1]<=1
                if v[0]!=v[1]:ambiguous+=1
                if 'externalHair'in s:
                    hair=s['externalHair'];h=hair['metadata'];assert hair['sourceId']==row['sourceId'];assert (h[0]>0 and h[3]>0 and h[0]<s['depth']-3e-5)==hair['inFrontOfThisSurface'] or h[3]<=0
                    front.append(hair['inFrontOfThisSurface']);external+=1
            if z:maxspread=max(maxspread,max(z)-min(z))
            if front and any(front)and not all(front):frontChangedAcrossSameCell+=1
            if rec['eligibleWitnessNotWholeCellOwner']and any(s['visibleBounds'][1]==0 for s in rec['samples']):partial+=1
    assert clipping<1e-10
    return {'piecesRetainingBaryUVWorldDepth':pieces,'independentSurfaceSamples':samples,'hairQueriesAtExactRecordedS4Coordinates':external,'partiallyVisibleCarrierCells':partial,'oneCellHasBothHairFrontAndNonFront':frontChangedAcrossSameCell,'maximumWithinCellCarrierDepthRangeMetres':maxspread,'unknownAlphaOrUnobservedSamples':ambiguous,'maxClippingError':clipping,'finiteSamplesNotWholeFootprintProof':True}

def perturbation_probes():
    # EMPIRICAL observed discrepancy, NOT a universal uncertainty bound.
    dx=.0015835195588774103;out=[]
    for frame,owner in [(103,1),(107,1),(207,1)]:
        p,r=loaded(frame,owner);base=solve(**p,witness_limit=None);before=set(map(tuple,base['solutions']));changed=[]
        for angle in range(8):
            delta=dx*np.array([math.cos(angle*math.pi/4),math.sin(angle*math.pi/4)]);ref=p['references'].copy();ref[3]=ref[3]+delta;q=solve(**(p|{'references':ref}),witness_limit=None);after=set(map(tuple,q.get('solutions',[])))
            changed.append({'direction':angle,'deltaXY':delta.tolist(),'optimalLabelSetChanged':before!=after,'before':len(before),'after':len(after),'errorPixels':q.get('errorPixels')})
        out.append({'frame':frame,'owner':owner,'finitePerturbations':changed,'notIntervalCertification':True,'carrierEligibilityHeldFixed':True})
    return {'coordinateMagnitudeFromIndependentReconstruction':dx,'probes':out,'universalErrorBoundClaimed':False,'producerAlphaDifferenceIsNotAnOpacityAllowance':.0017272338764194872}

def main():
    t=time.perf_counter();rows=read(P108/'INPUT108.json');domain,templates=template();q={'solver':tests(),'countDiagnosticIndependentExhaustiveCases':count_bound_oracle(),'fullProblemD4AndOrderChecks':d4_tests(),'sourceShapeCounterexample':source_shape_counterexample(),'independentGPUQueryWitnesses':source_query_proofs(rows,domain,templates),'footprints':footprint_checks(rows,domain,templates),'reprojectionSensitivity':perturbation_probes(),'UnityCalls':0,'GPUDispatches':0,'productApplied':False};q['seconds']=time.perf_counter()-t
    (H/'CHECK110.json').write_text(json.dumps(q,indent=2)+'\n',encoding='utf8');print(json.dumps(q))
if __name__=='__main__':main()
