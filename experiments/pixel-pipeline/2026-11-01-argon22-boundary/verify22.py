"""One explicit Argon2.2 boundary hypothesis on existing frozen inputs.
No parameter sweep, Unity call, source modification, or new capture.
"""
from pathlib import Path
import sys,json,gzip,itertools
import numpy as np
from paths22 import H,R,OLD
from aperture22 import column_rows,classify,component_count,domain_counterexamples
from stored110 import P108,P109,source_packet
from reconstruct110 import template,recover
from geometry109 import prepare_packet
from identity110 import transport,rank_with_relative,observed_key_centres

def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
    old=OLD;rows=read(P108/'INPUT108.json');domain,templates=template();cache=read(P109/'NATIVE_CACHE109.json');out=[]
    for path in sorted((old/'separated').glob('*-result.json')):
        prior=read(path);sid=prior['metadata']['sourceId'];row=next(r for r in rows if r['sourceId']==sid);owner=prior['owner'];stem=path.name.removesuffix('-result.json')
        with gzip.open(old/(stem+'-footprint.json.gz'),'rt',encoding='utf8')as f:raw=json.load(f)
        saved=np.load(P108/'fixtures'/(row['name']+'.npz'));keys=[tuple(map(int,k))for k in saved['keys']];low=saved['lower'];high=saved['upper'];i=keys.index((owner,1));w=keys.index((owner,4));ww,hh=prior['metadata']['canonicalSize'];elig=np.load(old/'separated'/(stem+'.npz'));carrier=np.zeros((hh,ww),bool)
        for j,(y,x)in enumerate(elig['cells']):carrier[y,x]=elig['eligibility'][j,3]
        curve=np.asarray(raw['reference']['nativeCurvePoints']);vis=np.array([v['visibleBounds'][0]>0 for v in raw['reference']['nativeCurveVisibility']]);columns,curveInfo=column_rows(curve,vis);closed=bool(high[i].sum()==0 and high[w].sum()==0)
        # The existing102 compositor transports a SOURCE intrinsic cell to a
        # display pixel. Looking up an unmoved source mesh at the phase-shifted
        # display location was an additional110 restriction, not its contract.
        # Keep the display-grid diagnostic, but use current SOURCE curve
        # support for canonical boundary allocation. This is NOT permission to
        # copy one point's depth to the whole destination pixel.
        displayCarrier=carrier.copy();carrier=np.zeros_like(carrier);sourceWitnesses=[];extra=[];pointCache=next(c for c in cache['curves']if c['owner']==owner)['points']
        for x,y in columns.items():
            ids=np.where(vis&(curve[:,0]>=x)&(curve[:,0]<=x+1)&(curve[:,1]>=y)&(curve[:,1]<=y+1))[0].tolist()
            assert all(pointCache[k]['sourceAlpha']>0 for k in ids)
            sourceWitnesses.append({'cellYX':[y,x],'sourcePointIndices':ids,'actualSourcePrimitiveIds':sorted({pointCache[k]['primitive']for k in ids}),'wholeCellDepthOrFinalOwnerClaimed':False})
            if 0<=x<ww and 0<=y<hh:carrier[y,x]=bool(ids)
            elif ids:extra.append({'cellYX':[y,x],'part':3,'reason':'actual native pigment source support outside old bank+padding ROI','sourcePointIndices':ids,'finalRGBOrExternalVisibilityObserved':False})
        labels,info=classify(low[i],high[i],low[w],high[w],columns,carrier,closed);info['oldDisplayAlignedCarrierMissing']=[[int(y),int(x)]for x,y in columns.items()if 0<=x<ww and 0<=y<hh and not displayCarrier[y,x]];info['carrierContract']='intrinsic source support, then explicit source-cell-to-display mapping; destination exposure remains separate'
        solutions=[labels.copy()];ties=info['childExactTies'];tieInfo={'exactTiedChildCells':len(ties),'fullTieEnumeration':len(ties)<=8,'noSourceCountTarget':True}
        if ties and len(ties)<=8:
            if row['name'].startswith('closed105'):ctx=prepare_packet(source_packet(row),domain,cache)
            else:ctx,_,_=recover(row,domain,templates)
            maps,available,canonical,check=transport(row,owner,ctx,raw['footprints'],raw['reference'],domain,cache,False);points=[tuple(map(int,p))for p in np.argwhere((labels>0)|(labels==-1))];candidates=[]
            for values in itertools.product([1,2],repeat=len(ties)):
                a=labels.copy()
                for cell,value in zip(ties,values):a[tuple(cell)]=value
                candidates.append([int(a[p])if a[p]>=0 else 0 for p in points])
            selected,_,tieInfo=rank_with_relative(candidates,points,maps,available,canonical,[],observed_key_centres(row,owner));solutions=[]
            for k in selected:
                a=labels.copy()
                for point,p in zip(points,candidates[k]):
                    if list(point)in ties:a[point]=p
                solutions.append(a)
            tieInfo|={'exactTiedChildCells':len(ties),'fullTieEnumeration':True,'noSourceCountTarget':True}
        record={'sourceId':sid,'frame':row['frame'],'dataset':row['name'],'owner':owner,'Close':prior['metadata']['Close'],'curve':curveInfo,'classification':info,'tieResolution':tieInfo,
            'sourceEmptyIrisWhite':closed,'counts':[{'iris':int((a==1).sum()),'white':int((a==2).sum()),'upperLine':int((a==3).sum()),'unresolved':int((a<0).sum())}for a in solutions],
            'lineComponents8':[component_count(a==3)for a in solutions],'literalBoundaryRowsXY':[[x,y]for x,y in sorted(columns.items())],'labels':[a.tolist()for a in solutions],'sourceSupportWitnesses':sourceWitnesses,'extraBoundarySourceLabelsOutsideOldROI':extra,
            'sameInputOnly':True,'newUnityCalls':0,'actualNewGPU':False,'finalRGBProduced':False,'adopted':False,'scope':'single-valued canonical eye-column boundary hypothesis; not all rotations or continuous source shape proof'}
        out.append(record)
    summary={'inputs':len(out),'direct105ClosedInputs':sum(not r['dataset'].startswith('actual107')for r in out),'casesWithCurrentCarrierMissingBoundary':sum(bool(r['classification']['boundaryCellsWithoutCertainCurrentCarrier'])for r in out),
      'casesWithSourceSuppressedAbovePigmentBoundary':sum(bool(r['classification']['positiveSourceSuppressedAboveProposedBoundary'])for r in out),'casesWithMultiComponentLine':sum(any(len(v)>1 for v in r['lineComponents8'])for r in out),
      'casesWithXNonmonotonePigmentCurve':sum(not r['curve']['xMonotone']for r in out),'casesWithAdjacentColumnJump':sum(bool(r['curve']['adjacentColumnJumpsOverOne'])for r in out),'casesWithUnresolvedCells':sum(any(v['unresolved']for v in r['counts'])for r in out),'casesRequiringSourceDerivedROIBeyondOldPadding':sum(bool(r['extraBoundarySourceLabelsOutsideOldROI'])for r in out),
      'syntheticDomainCounterexamples':domain_counterexamples(),'newUnity':0,'newGPU':0,'productApplied':False}
    (H/'RESULTS22.json').write_text(json.dumps({'summary':summary,'cases':out},indent=2,default=lambda v:v.item()if isinstance(v,np.generic)else str(v))+'\n',encoding='utf8');print(json.dumps(summary));print(json.dumps([{'frame':r['frame'],'owner':r['owner'],'counts':r['counts'],'missing':r['classification']['boundaryCellsWithoutCertainCurrentCarrier'],'above':r['classification']['positiveSourceSuppressedAboveProposedBoundary']}for r in out if r['frame']in [99,101,103,107,192,207]],ensure_ascii=False))
if __name__=='__main__':main()
