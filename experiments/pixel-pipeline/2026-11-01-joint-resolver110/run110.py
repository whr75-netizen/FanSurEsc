from pathlib import Path
import json,time,sys,gzip
import numpy as np
from fields110 import H,R,read,template,build
from resolver110 import solve,metrics,tests
from identity110 import transport,rank,encode
from stored110 import P109,P108

def main():
    print(json.dumps(tests()),flush=True);domain,templates=template();cache=read(P109/'NATIVE_CACHE109.json');rows=read(P108/'INPUT108.json');out=[]
    targets=sys.argv[1:]or['103'];prior={1:[],2:[]};priorScope={1:None,2:None}
    for target in targets:
        row=next(r for r in rows if r['name'].startswith('closed105'))if target=='closed105'else next(r for r in rows if r['name']=='actual107-frame'+str(int(target)));frame=row['frame']
        for owner in [1,2]:
            stem=H/f'{"closed105-"if target=="closed105"else ""}frame{frame}-eye{owner}';t=time.perf_counter()
            print(json.dumps({'begin':frame,'owner':owner}),flush=True)
            problem,reference,footprint,meta,ctx=build(row,owner,domain,templates,cache)
            ids,available,canonical,idcheck=transport(row,owner,ctx,footprint,reference,domain,cache)
            np.savez_compressed(str(stem)+'.npz',cells=problem['cells'],eligibility=problem['eligibility'],**{'reference'+str(p):q for p,q in problem['references'].items()})
            with gzip.open(str(stem)+'-footprint.json.gz','wt',encoding='utf8')as f:json.dump({'metadata':meta,'reference':reference,'footprints':footprint},f,separators=(',',':'))
            print(json.dumps({'fieldsReady':frame,'owner':owner,'cells':len(problem['cells']),'referenceSizes':{str(p):len(q)for p,q in problem['references'].items()},'seconds':time.perf_counter()-t}),flush=True)
            q=solve(**problem,witness_limit=64);q['metrics']=[metrics(problem['cells'],v,problem['references'])for v in q.get('solutions',[])];q['metadata']=meta;q['owner']=owner;q['connectivity']=problem['connectivity'];q['cells']=problem['cells']
            scope=ctx['manifest']['forward102']['scope']+'|'+cache['cacheKey']
            if scope!=priorScope[owner]:prior[owner]=[];priorScope[owner]=scope
            if q.get('solutions'):
                winners,hist,info=rank(q['solutions'],problem['cells'],ids,available,canonical,prior[owner]);q['selectedIndicesWithinEnumeratedOptima']=winners;q['sourceIdentity']=info|idcheck;q['historyMayBeIncomplete']=not q['enumerationComplete'];prior[owner]=hist
                q['sourceHistograms']=[encode(v)for v in hist]
            else:q['sourceIdentity']=idcheck;prior[owner]=[]
            q['adopted']=False;q['finalPaletteRGBCompositorImplemented']=False
            Path(str(stem)+'-result.json').write_text(json.dumps(q,indent=2)+'\n',encoding='utf8');out.append(q)
            print(json.dumps({'result':frame,'owner':owner,'status':q['status'],'error':q.get('errorPixels'),'witnesses':q.get('witnesses'),'complete':q.get('enumerationComplete'),'seconds':q.get('seconds')}),flush=True)
    allResults=[read(p)for p in sorted(H.glob('*-result.json'))];(H/'RESULTS110.json').write_text(json.dumps(allResults,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
