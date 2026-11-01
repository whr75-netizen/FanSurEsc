"""Fix the proven stage coupling; reuse stored footprints, NO new geometry.

External hair masks final exposure, not the canonical joint eye layout. Current
native face/Close is still a hard eligibility gate. Latent hidden source IDs
are not rendered through hair. This is an ablation of the SAME resolver, not a
new tuned objective or a new capture. Full RGB composition remains unimplemented.
"""
from pathlib import Path
from fractions import Fraction
import gzip,json,time,sys
import numpy as np
from fields110 import H,read,template,components
from stored110 import P108,P109
from reconstruct110 import recover
from geometry109 import prepare_packet
from stored110 import source_packet
from identity110 import transport,rank_with_relative,observed_key_centres,encode
from resolver110 import solve,metrics

def problem_from_fields(d,refs,shape):
    h,w=shape[1],shape[0];records=d['footprints'];cells=sorted({tuple(r['cellYX'])for r in records});lookup={p:i for i,p in enumerate(cells)};e=np.zeros((len(cells),4),bool);e[:,0]=True
    for r in records:e[lookup[tuple(r['cellYX'])],r['part']]=any(s['faceVisibleBounds'][0]>0 for s in r['samples'])
    keep=np.where(e[:,1:].any(1))[0];cells=[cells[i]for i in keep];e=e[keep];connectivity={}
    for p in [1,2,3]:
        mask=np.zeros((h,w),bool)
        for i,(y,x)in enumerate(cells):mask[y,x]=e[i,p]
        _,cc=components(mask,p==3)
        if len(cc)!=1:continue
        if p==3:
            if len(d['reference']['nativeVisibleRuns'])==1:connectivity[p]=True
        elif len(refs[p]):
            fine=np.zeros((h*8,w*8),bool);q=np.floor(refs[p]*8).astype(int);fine[q[:,1],q[:,0]]=True;_,sourceCC=components(fine,False)
            if len(sourceCC)==1:connectivity[p]=False
    return {'cells':cells,'eligibility':e,'references':refs,'connectivity':connectivity}

def exposure(problem,labels,records):
    by={(tuple(r['cellYX']),r['part']):r for r in records};out=[]
    for cell,p in zip(problem['cells'],labels):
        if not p:continue
        r=by[(tuple(cell),p)];groups={};unknown=0
        for s in r['samples']:
            key=tuple(s['displaySampleIndexYX'])if 'displaySampleIndexYX'in s else None
            if key is None:unknown+=1;continue
            groups.setdefault(key,[]).append(s)
        low=high=0.;spread=[];ties=0
        for ss in groups.values():
            z=min(s['depth']for s in ss);front=[s for s in ss if s['depth']<=z+3e-5]
            # Different current surfaces with tied depth remain an interval.
            lo=min(s['visibleBounds'][0]for s in front);hi=max(s['visibleBounds'][1]for s in front);low+=lo;high+=hi;ties+=len(front)>1;spread.append(max(s['depth']for s in ss)-z)
        out.append({'cellYX':list(cell),'part':p,'displayCellTopLeft':r['displayCellTopLeft'],'visibleCarrierSampleWeightBounds':[low/16,high/16],
            'zeroCertifiedVisibleSamples':low==0,'fullyMaskedAtRecordedSamples':high==0 and not unknown,'unobservedInteriorWitnesses':unknown,
            'tiedFrontSamples':ties,'maxSameSampleDepthSpread':max(spread,default=0),'notRGBOpacityOrPixelOwnerDecision':True})
    return out

def main():
    start=time.perf_counter();outdir=H/'separated';outdir.mkdir(exist_ok=True);rows=read(P108/'INPUT108.json');domain,templates=template();cache=read(P109/'NATIVE_CACHE109.json');prior={1:[],2:[]};scope={1:None,2:None};out=[]
    paths=sorted(H.glob('closed105-frame*-eye*-result.json'))if '--closed105'in sys.argv else sorted(H.glob('frame*-eye*-result.json'),key=lambda p:(int(p.name.split('-')[0][5:]),p.name))
    for path in paths:
        old=read(path);frame=old['metadata']['frame'];owner=old['owner'];row=next(v for v in rows if v['sourceId']==old['metadata']['sourceId']);stem=path.name.removesuffix('-result.json')
        with gzip.open(H/(stem+'-footprint.json.gz'),'rt',encoding='utf8')as f:d=json.load(f)
        raw=np.load(H/(stem+'.npz'));refs={p:raw['reference'+str(p)]for p in [1,2,3]};problem=problem_from_fields(d,refs,old['metadata']['canonicalSize'])
        if row['name'].startswith('closed105'):ctx=prepare_packet(source_packet(row),domain,cache)
        else:ctx,_,_=recover(row,domain,templates)
        ids,available,canonical,check=transport(row,owner,ctx,d['footprints'],d['reference'],domain,cache,False);ss=(ctx['manifest']['forward102']['scope'],cache['cacheKey'])
        if scope[owner]!=ss:prior[owner]=[];scope[owner]=ss
        q=solve(**problem,witness_limit=64);q['metrics']=[metrics(problem['cells'],v,refs)for v in q.get('solutions',[])];q['metadata']=old['metadata']|{'placementBeforeExternalHair':True};q['owner']=owner;q['connectivity']=problem['connectivity'];q['cells']=problem['cells']
        if q.get('solutions'):
            chosen,hist,info=rank_with_relative(q['solutions'],q['cells'],ids,available,canonical,prior[owner],observed_key_centres(row,owner));q['selectedIndicesWithinEnumeratedOptima']=chosen;q['sourceIdentity']=info|check;prior[owner]=hist;q['sourceHistograms']=[encode(v)for v in hist];q['exposureForConditionalChoices']=[exposure(problem,q['solutions'][i],d['footprints'])for i in chosen]
        else:prior[owner]=[]
        q['adopted']=False;q['finalRGBProduced']=False;q['externalHairMayHideButDoesNotReallocateFeature']=True;q['historyCannotBypassFinalExposure']=True;q['historyMayBeIncomplete']=not q.get('enumerationComplete',False)
        (outdir/(stem+'-result.json')).write_text(json.dumps(q,indent=2)+'\n',encoding='utf8');np.savez_compressed(outdir/(stem+'.npz'),cells=problem['cells'],eligibility=problem['eligibility'],**{'reference'+str(p):v for p,v in refs.items()});out.append(q)
        print(json.dumps({'frame':frame,'owner':owner,'error':q.get('errorPixels'),'conditionalChoices':len(q.get('selectedIndicesWithinEnumeratedOptima',[])),'complete':q.get('enumerationComplete')}),flush=True)
    allResults=[read(p)for p in sorted(outdir.glob('*-result.json'))];(outdir/'RESULTS110.json').write_text(json.dumps(allResults,indent=2)+'\n',encoding='utf8');print(json.dumps({'processedStates':len(out),'totalStates':len(allResults),'seconds':time.perf_counter()-start,'newUnity':0}))
if __name__=='__main__':main()
