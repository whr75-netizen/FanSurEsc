"""Small exact-call timing; frozen inputs, not animated/runtime performance."""
import pickle,json,time,statistics
import active516 as G,span517 as N
W=G.ROOT;D=W/'State521'
with(W/'State520/current-static.pickle').open('rb')as f:a=pickle.load(f)
with(W/'State520/past-held516.pickle').open('rb')as f:b=pickle.load(f)
rows=[]
for repeat in range(3):
    for label,x,y in[('held-to-static',b,a),('static-to-held',a,b)]:
        start=time.perf_counter();result=N.compare(x['arcs'],x['bindings'],y['arcs'],y['bindings'],True);elapsed=time.perf_counter()-start;assert result['valid']and not result['geometryEventResets']and result['raw']==36
        row={'repeat':repeat,'direction':label,'seconds':elapsed,'raw':result['raw'],'scope':'span517.compare call only, same-geometry frozen inputs, no overlay/mask construction/Unity'};rows.append(row);print(json.dumps(row),flush=True)
out={'calls':6,'secondsMedian':statistics.median(r['seconds']for r in rows),'secondsMin':min(r['seconds']for r in rows),'secondsMax':max(r['seconds']for r in rows),'rows':rows,'noRuntimeFPSOrAllocationClaim':True,'noOptimizationImplemented':True};(D/'COST521.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='rows'}),flush=True)
