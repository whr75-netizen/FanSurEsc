"""Self-contained raw109/cache checks; reads sibling107/108 for the real tie.
Writes only CHECK109.json in this experiment. No Unity/network/import/Play.
"""
from pathlib import Path
from fractions import Fraction
import json,hashlib,zipfile,time
import numpy as np
from native109 import H,R,read,bilinear,section_centres,cache_key
from io109 import ZipNode,mesh,packet
from geometry109 import prepare_packet,physical,transform
from measure109 import mesh_graph
from footprint109 import clip,area,tests as footprint_tests
import history109

def source_tests(domain,cache):
    counts=0
    for c in cache['curves']:
        points=np.argwhere(domain['components']==c['selectedComponent']);xy=points[:,::-1];alpha=domain['rgba'][points[:,0],points[:,1],3];corners=[x['nearestPigment'][2:]for x in c['cornerMatches']];axis,a,ambiguous=section_centres(xy,alpha,corners);assert not ambiguous
        for f,undo in [(lambda q:q[:,::-1]*[1,-1],lambda q:q[:,::-1]*[-1,1]),(lambda q:q*[-1,1],lambda q:q*[-1,1]),(lambda q:-q,lambda q:-q)]:
            # Integer source-pixel INDEX rotation requires centre offsets.
            q=f(xy.astype(float));shift=np.maximum(0,-q.min(0)).astype(int);trans=q+shift;corn=f(np.array(corners))+shift;_,b,amb=section_centres(trans.astype(int),alpha,corn);assert not amb
            # Map transformed pixel CENTRES back through the corresponding
            # affine index transform, accounting for the half-texel offset.
            original=np.array([v for k,v in a]);mapped=undo(np.array([v for k,v in b])-.5-shift)+.5
            assert np.max(abs(original-mapped))<1e-10;counts+=1
        _,reverse,amb=section_centres(xy[::-1],alpha[::-1],corners);assert not amb and all(np.array_equal(x[1],y[1])for x,y in zip(a,reverse));counts+=1
    assert section_centres(np.array([[0,0],[1,1]]),np.array([255,255]),[[0,0],[1,1]])[2]
    mat=cache['material'];reg=read(H/'inputs/REGISTRATION89.json');base=cache_key(domain['rest'],domain['uv'],domain['triangles'],mat,reg);assert base==cache['cacheKey']
    changed=domain['uv'].copy();changed[0,0]+=np.float32(.01);assert cache_key(domain['rest'],changed,domain['triangles'],mat,reg)!=base
    material=mat|{'baseColorFactorLinear':[.9,1,1,1]};assert cache_key(domain['rest'],domain['uv'],domain['triangles'],material,reg)!=base
    return counts+3

def intermediate_carrier_checks(domain,cache):
    points=[];image=domain['rgba'].astype(float)/255;h,w=image.shape[:2]
    for c in cache['curves']:
        valid=[v for v in c['points']if not v.get('unresolved')]
        for a,b in zip(valid,valid[1:]):
            u=np.array(a['sourceUV']);v=np.array(b['sourceUV']);n=max(1,int(np.ceil(np.max(abs((v-u)*[w,h]))*4)));points.extend(u[None]+np.linspace(0,1,n+1)[:,None]*(v-u)[None])
    t=domain['uv'][domain['triangles']].astype(float);mat=np.stack([t[:,1]-t[:,0],t[:,2]-t[:,0]],axis=2);valid=abs(np.linalg.det(mat))>1e-18;inv=np.zeros_like(mat);inv[valid]=np.linalg.inv(mat[valid]);points=np.array(points)
    for start in range(0,len(points),64):
        p=points[start:start+64];ab=np.einsum('tij,tqj->tqi',inv,p[None]-t[:,0,None]);inside=valid[:,None]&(ab.min(2)>=-1e-10)&(ab.sum(2)<=1+1e-10);assert inside.any(0).all()
        assert all(bilinear(image,q)[3]>0 for q in p)
    return len(points)

def main():
    started=time.perf_counter();index=read(H/'RAW_INPUT109_INDEX.json');assert hashlib.sha256((H/'RAW109.zip').read_bytes()).hexdigest()==index['archiveSHA256']
    with zipfile.ZipFile(H/'RAW109.zip')as z:
        for r in index['rawFiles']:assert hashlib.sha256(z.read(r['file'])).hexdigest()==r['sha256']
    for r in index['static']:assert hashlib.sha256((H/r['file']).read_bytes()).hexdigest()==r['sha256']
    domain=np.load(H/'NATIVE_DOMAIN109.npz');cache=read(H/'NATIVE_CACHE109.json');tests=source_tests(domain,cache);intermediate=intermediate_carrier_checks(domain,cache);geom=read(H/'GEOMETRY109.json');measure=read(H/'MEASURE109.json');g,groups,sizes=mesh_graph(domain['triangles']);carrierCount=0;depthMax=0.;localMax=0.
    footprintPieces=0
    for entry in index['entries105']:
        p=packet(H,entry,'105');ctx=prepare_packet(p,domain,cache);record=next(r for r in geom if r['sourceId']==ctx['manifest']['sourceId']);assert record['frame']==entry['frame']
        for c in cache['curves']:
            e=next(x for x in record['eyes']if x['owner']==c['owner']);a=np.array([p['barycentric']@ctx['maps'][c['owner']][np.array(p['vertices'])]for p in c['points']if not p.get('unresolved')]);assert np.max(abs(a-e['nativePigmentCurve']))<1e-12
        for row in measure['rows']:
            if row['sourceId']!=ctx['manifest']['sourceId']:continue
            for d in row['destinations']:
                if not d['sameConnectedCarrier']:continue
                ids=domain['triangles'][d['targetPrimitive']-1];b=np.array(d['targetBarycentric']);world=b@ctx['world'][ids];depth=-float((ctx['view']@np.r_[world,1])[2]);xy=b@ctx['maps'][row['owner']][ids];depthMax=max(depthMax,abs(depth-d['targetDepth']));localMax=max(localMax,float(np.linalg.norm(xy-np.array(d['cellXY'])-.5)));assert groups[d['sourcePrimitive']-1]==groups[d['targetPrimitive']-1];carrierCount+=1
        if entry['frame']==104:
            for case in read(H/'FOOTPRINT109.json')['cases']:
                owner=next(c['owner']for c in cache['curves']if groups[c['points'][0]['primitive']-1]==case['component'])
                for piece in case['sameCarrierFootprintPieces']:
                    tid=piece['primitive']-1;ids=domain['triangles'][tid];assert groups[tid]==case['component'];poly=clip(ctx['maps'][owner][ids],case['cellXY']);assert area(poly)>0 and np.max(abs(poly[:,:2]-piece['polygonCanonicalXY']))<1e-12;assert np.max(abs(poly[:,2:]@ctx['depth'][ids]-piece['polygonDepth']))<1e-12;footprintPieces+=1
    assert depthMax<1e-12 and localMax<1e-12
    trajectories=np.load(H/'REAL_CARRIER_TRAJECTORIES109.npz');correspondence=read(H/'REAL_CORRESPONDENCE109.json');motionPoints=0
    for entry in index['entries87']:
        p=packet(H,entry,'87');m=read(p/'RAW_MANIFEST.json');ident,model,current,uv,indices=mesh(p/'eye-evaluated.mesh');assert ident['sourceId']==m['sourceId']and ident['frameIndex']==m['frameIndex'];world=transform(model,current)[:,:3];assert np.array_equal(uv,domain['uv'])and np.array_equal(indices[6],domain['triangles'])
        for c in cache['curves']:
            pts=[v for v in c['points']if not v.get('unresolved')];actual=np.array([np.array(v['barycentric'])@world[np.array(v['vertices'])]for v in pts]);expected=trajectories[f'f{entry["frame"]}-eye{c["owner"]}-world'];assert np.max(abs(actual-expected))<1e-12;motionPoints+=len(actual)
    def decode(a):return {tuple(v['key']):Fraction(v['weight'])for v in a}
    for f in read(H/'HISTORY_TIED_INPUTS109.json'):
        cells={tuple(x['cell']):decode(x['histogram'])for x in f['cells']};prior=[decode(x)for x in f['prior']];available=decode(f['available']);win,_,info=history109.rank(f['candidates'],prior,cells,available,f['owner'],f['q']);assert win==f['expectedWinners']and info['exactScores']==f['expectedExactScores']
        native=read(H/'inputs/SOURCE_FIXTURE88.json')['source'];intrinsic,vectors=history109.canonical_rank(f['candidates'],native,cells,available,f['owner'],f['q']);assert intrinsic==f['expectedCanonicalWinners']and vectors==f['expectedCanonicalPartVectors']
        assert history109.transform_check(f['q'],f['candidates'],prior,cells,available,f['owner'])==9
    # Independently re-extract the tie's source metadata from the previous
    # committed raw107 ZIP, not just its calculated history fixture.
    oldzip=R/'joint-lid107/RAW107.zip'if(R/'joint-lid107/RAW107.zip').exists()else R/'2026-11-01-joint-visibility107/RAW107.zip';related=R/'joint-model108'if(R/'joint-model108').exists()else R/'2026-11-01-joint-objective108';base=read(related/'RESULTS108.json');rows=read(related/'INPUT108.json');src=read(H/'inputs/SOURCE_FIXTURE88.json');bank={(x['owner'],x['part'],x['x'],x['y']):src['paletteRGB8'][x['palette']]for x in src['source']};projection={e['eye']:np.asarray(e['nativeToAuthoredProjection'],np.float32)for e in read(H/'inputs/REGISTRATION89.json')['eyes']};prior=[];sequence=[]
    for frame in [103,105,107,109]:
        row=next(r for r in rows if r['name']==f'actual107-frame{frame}');cells,available,checks=history109.source_histograms(row,bank,projection,ZipNode(oldzip,f'final54/frame{frame}'));assert checks['unresolvedSourceKeys']==checks['bankRGB8Mismatch']==0;q=base[row['name']]['noCurve']['2'];candidates=q['massFirstDistinctWitnesses'];win,hist,flags=history109.rank(candidates,prior,cells,available,2,q)
        if frame==107:assert not any(k[1]in [1,4]for k in available)and all(1 not in c and 2 not in c for c in candidates)
        if frame in [105,109]:assert win==[0]
        if any(hist):prior=[x for x in hist if x]
        sequence.append({'frame':frame,'winners':win,'currentVisibleBankKeys':len(available)})
    result={'rawFilesSHA256':len(index['rawFiles']),'staticSHA256':len(index['static']),'nativeCentrePoints':sum(len(c['points'])for c in cache['curves']),'sourceIntermediateAlphaAndCarrierProbes':intermediate,'sourceAxisStorageAndInvalidationChecks':tests,'carrierDestinationsSameConnectedMesh':carrierCount,'maxTargetDepthEquationResidual':depthMax,'maxTargetCanonicalEquationResidual':localMax,
      'realSourceCorrespondencePoints':motionPoints,'realSavedFrames':len(index['entries87']),'adjacentSavedPairs':correspondence['adjacentPairs'],'footprint':footprint_tests(),'actualCarrierFootprintPieces':footprintPieces,'history':history109.tests(),'realHistoryRawReplay':sequence,'seconds':time.perf_counter()-started,'newPlay':0,'newUnityCalls':0,'productApplied':False}
    (H/'CHECK109.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
