"""One ablation: move the102 parent/child area decision to feature scope.

The native upper boundary is unchanged. No extra line cells, source colours,
eye size constants, or weights are introduced. This is an OFFLINE hypothesis;
all optima are retained before source-form filtering, never first-N ranking.
"""
from pathlib import Path
import sys,json,gzip
import numpy as np
from paths22 import H,R,OLD
from interior22 import allocate,allocate_topology,tests
from aperture22 import component_count
from stored110 import P108,P109,source_packet
from reconstruct110 import template,recover
from geometry109 import prepare_packet
from identity110 import transport,rank_with_relative,observed_key_centres
from form22 import rank_source

def read(p):return json.loads(p.read_text(encoding='utf8'))

def main():
    topology='--topology'in sys.argv;baseline=read(H/'RESULTS22.json');rows=read(P108/'INPUT108.json');domain,templates=template();cache=read(P109/'NATIVE_CACHE109.json');out=[]
    for c in baseline['cases']:
        row=next(v for v in rows if v['sourceId']==c['sourceId']);owner=c['owner'];d=np.load(P108/'fixtures'/(c['dataset']+'.npz'));keys=[tuple(map(int,k))for k in d['keys']];i=keys.index((owner,1));w=keys.index((owner,4));loI,hiI,loW,hiW=d['lower'][i],d['upper'][i],d['lower'][w],d['upper'][w];columns=dict(c['literalBoundaryRowsXY']);carrier=np.zeros_like(loI,bool)
        for witness in c['sourceSupportWitnesses']:
            y,x=witness['cellYX']
            if 0<=y<len(carrier)and 0<=x<carrier.shape[1]:carrier[y,x]=bool(witness['sourcePointIndices'])
        source=read(P109/'inputs/SOURCE_FIXTURE88.json');bankConnected=[]
        for part in [1,4]:
            bank=[v for v in source['source']if v['owner']==owner and v['part']==part];m=np.zeros((256,256),bool)
            for v in bank:m[v['y'],v['x']]=True
            bankConnected.append(len(component_count(m,False))==1)
        layouts,info=allocate_topology(loI,hiI,loW,hiW,columns,carrier,bankConnected)if topology else allocate(loI,hiI,loW,hiW,columns,carrier)
        info['immutableBankConnectedIrisWhite']=bankConnected
        assert info['completeOptimalEnumeration'],'Do not Pareto-rank an incomplete pool'
        selected=list(range(len(layouts)));ranking={'noChoiceNeeded':len(layouts)==1,'historyApplied':False};stem=f'frame{row["frame"]}-eye{owner}'
        if c['dataset'].startswith('closed105'):stem='closed105-eye'+str(owner)
        # Find the existing footprint by sourceId, rather than matching frame
        # numbers from independent captures as if they were the same source.
        prior=next(p for p in (OLD/'separated').glob('*-result.json')if read(p)['metadata']['sourceId']==c['sourceId']and read(p)['owner']==owner);stem=prior.name.removesuffix('-result.json')
        if len(layouts)>1:
            with gzip.open(OLD/(stem+'-footprint.json.gz'),'rt',encoding='utf8')as f:raw=json.load(f)
            if c['dataset'].startswith('closed105'):ctx=prepare_packet(source_packet(row),domain,cache)
            else:ctx,_,_=recover(row,domain,templates)
            maps,available,canonical,check=transport(row,owner,ctx,raw['footprints'],raw['reference'],domain,cache,False);points=[tuple(map(int,p))for p in np.argwhere(np.any(np.array(layouts)>0,axis=0))];vectors=[[int(a[p])for p in points]for a in layouts]
            selected,ranking=rank_source(vectors,points,maps,available,canonical,observed_key_centres(row,owner))if topology else (lambda v:(v[0],v[2]))(rank_with_relative(vectors,points,maps,available,canonical,[],observed_key_centres(row,owner)));ranking|={'sourceTransport':check,'historyApplied':False,'allAreaOptimalLayoutsConsidered':True}
        result=[layouts[k]for k in selected];parts=[]
        for a in result:
            parts.append({'iris':int((a==1).sum()),'white':int((a==2).sum()),'upperLine':int((a==3).sum()),'unresolved':int((a<0).sum()),'irisComponents4':component_count(a==1,False),'whiteComponents4':component_count(a==2,False),'lineComponents8':component_count(a==3)})
        lost=[]
        for code,name,lo in [(1,'iris',loI),(2,'white',loW)]:
            if lo.sum()>0 and all(not np.any(a==code)for a in result):lost.append({'part':name,'sourceMass':float(lo.sum())})
        positiveUnion=bool(loI.sum()+loW.sum()>0);extinguished=positiveUnion and all(not np.any((a==1)|(a==2))for a in result)
        assert not c['sourceEmptyIrisWhite']or all(not np.any((a==1)|(a==2))for a in result)
        assert all(np.array_equal(a==3,np.array(c['labels'][0])==3)for a in result)
        out.append({'sourceId':c['sourceId'],'dataset':c['dataset'],'frame':c['frame'],'owner':owner,'Close':c['Close'],'allocation':info,'formRanking':ranking,'selectedIndices':selected,'labels':[a.tolist()for a in result],'counts':parts,'positiveSourcePartsLost':lost,'positiveUnionExtinguished':extinguished,'boundaryIdenticalToLocal22':True,'sourceEmptyIrisWhite':c['sourceEmptyIrisWhite'],'extraBoundarySourceLabelsOutsideOldROI':c['extraBoundarySourceLabelsOutsideOldROI']})
        print(json.dumps({'frame':c['frame'],'owner':owner,'areaOptima':len(layouts),'formOptima':len(result),'counts':parts,'positiveUnionExtinguished':extinguished}),flush=True)
    phase=[]
    for owner in [1,2]:
        q=[next(c for c in out if c['dataset']==f'actual107-frame{f}'and c['owner']==owner)for f in [121,125,129]];phase.append({'owner':owner,'frames':[121,125,129],'completeCanonicalLayoutSetsEqual':q[0]['labels']==q[1]['labels']==q[2]['labels']})
    summary={'actualEyeStates':len(out),'synthetic':tests(),'incompleteAreaEnumerations':sum(not c['allocation']['completeOptimalEnumeration']for c in out),'ambiguousSourceFormCases':sum(len(c['labels'])>1 for c in out),'positiveUnionsExtinguished':sum(c['positiveUnionExtinguished']for c in out),'positivePartsExtinguished':sum(bool(c['positiveSourcePartsLost'])for c in out),'disconnectedIrisOrWhiteCases':sum(any(len(v['irisComponents4'])>1 or len(v['whiteComponents4'])>1 for v in c['counts'])for c in out),'phase':phase,'newUnityCalls':0,'newGPU':0,'productApplied':False,'lineAreaQuota':False,'fixedEyeSize':False,'screenRGBHistory':False,'newFinalRGBProduced':False}
    summary['sourceTopologyConstraintAblation']=topology
    (H/('TOPOLOGY_RESULTS22.json'if topology else'REGION_RESULTS22.json')).write_text(json.dumps({'summary':summary,'cases':out},indent=2,default=lambda v:v.item()if isinstance(v,np.generic)else str(v))+'\n',encoding='utf8');print(json.dumps(summary))
if __name__=='__main__':main()
