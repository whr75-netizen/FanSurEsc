"""517 correspondence adapter; 516 atomic costs/DP/weights remain unchanged.

Only span channel = actual geometric arc, transport = ordered curve geometry,
and cyclic start equivalence differ. No selector or temporal-state recurrence.
"""
import math
import arc517 as A

def substitute(a,b):
    n,m=len(a),len(b)
    if not n or not m:return float(n+m)
    count=min(n,m);cost=float(abs(n-m))
    for k in range(count):
        i=min(n-1,int((k+.5)*n/count));j=min(m-1,int((k+.5)*m/count));cost+=abs(a[i][0]-b[j][0])+abs(a[i][1]-b[j][1])
    return min(float(n+m),cost)

def linear_edit(old,new,cache=None,offset=0,trace=False):
    n,m=len(old),len(new);dp=[[math.inf]*(m+1)for _ in range(n+1)];back={};dp[0][0]=0.;cache={}if cache is None else cache
    def sub(i,ni,j,nj):
        key=(i,ni,(j+offset)%m if m else 0,nj)
        if key not in cache:cache[key]=substitute([p for s in old[i:i+ni]for p in s['points']],[p for s in new[j:j+nj]for p in s['points']])
        return cache[key]
    for i in range(n+1):
        for j in range(m+1):
            options=[]
            if i<n:options.append((i+1,j,float(old[i]['length']),'delete'))
            if j<m:options.append((i,j+1,float(new[j]['length']),'add'))
            if i<n and j<m:options.append((i+1,j+1,sub(i,1,j,1),'substitute'))
            if i+1<n and j<m:options.append((i+2,j+1,sub(i,2,j,1),'merge'))
            if i<n and j+1<m:options.append((i+1,j+2,sub(i,1,j,2),'split'))
            for ii,jj,cost,op in options:
                value=dp[i][j]+cost
                if value<dp[ii][jj]-1e-12:dp[ii][jj]=value;back[ii,jj]=(i,j,cost,op)
    operations=[]
    if trace:
        i,j=n,m
        while i or j:
            ii,jj,cost,op=back[i,j];operations.append({'operation':op,'oldSpanRange':[ii,i],'newSpanRange':[jj,j],'cost':cost});i,j=ii,jj
        operations.reverse()
    total=sum(s['length']for s in old+new)
    return {'raw':dp[n][m],'deleteAddUpperBound':total,'normalizedDiagnostic':dp[n][m]/total if total else 0.,'operations':operations}

def cyclic_edit(old,new,trace=False):
    if not old or not new:return{**linear_edit(old,new,trace=trace),'cyclicOffset':0}
    cache={};best=None;bestOffset=0
    for offset in range(len(new)):
        rotated=new[offset:]+new[:offset];value=linear_edit(old,rotated,cache,offset)
        if best is None or value['raw']<best['raw']-1e-10:best=value;bestOffset=offset
    if trace:best=linear_edit(old,new[bestOffset:]+new[:bestOffset],cache,bestOffset,True)
    return{**best,'cyclicOffset':bestOffset}

def compare(oldArcs,oldBindings,newArcs,newBindings,trace=False):
    matches,resets=A.match_arcs(oldArcs,newArcs);rows=[];failed=[]
    for match in matches:
        i,j=match['old'],match['new'];old=oldBindings.get(i);new=newBindings.get(j)
        if old:
            predicted=A.transport(old,oldArcs[i],newArcs[j],match['fit'])
            if predicted is None:failed.append({'old':i,'new':j,'reason':'NO_MONOTONE_CURVE_TRANSPORT'});continue
            a=predicted['spans']
        else:predicted=None;a=[]
        b=[{'length':s['length'],'points':[q['q']for q in s['samples']]}for s in new['spans']]if new else[]
        result=cyclic_edit(a,b,trace)
        rows.append({'old':i,'new':j,'oldPixelSpans':len(a),'newPixelSpans':len(b),'fitScore':match['fit']['score'],'exactSameGeometry':match['fit']['exactSameGeometry'],'rotationRadians':match['fit']['angle'],'translation':match['fit']['t'].tolist(),'nearEqualGeometricFits':match['fit']['nearEqualFits'],'curveMapFit':predicted['curveMapFit']if predicted else None,'maxPredictedMovement':predicted['maxPredictedMovement']if predicted else 0.,**result})
    return {'raw':sum(r['raw']for r in rows),'rows':rows,'geometryEventResets':resets,'failedCorrespondences':failed,'valid':not failed,'noSelectedSpanAbsenceAsOcclusion':True}
