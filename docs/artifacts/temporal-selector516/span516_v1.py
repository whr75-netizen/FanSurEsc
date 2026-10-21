"""Motion-conditioned span edit cost, an explicit project prototype, NOT Eq5.

Add/delete: unit-edge count. Substitute: unmatched length plus L1 travel of
uniformly ordered span samples, capped by delete+add. Merge/split use the same
substitution on concatenated spans. Persistent parameter order is preserved.
No image/RGB history, temporal averaging, fixed-coordinate or phase rule.
"""
import math
import active516 as G

def inside_range(lo,hi,intervals):
    at=lo
    for a,b in sorted(intervals):
        if b<at-1e-10:continue
        if a>at+1e-10:return False
        at=max(at,b)
        if at>=hi-1e-10:return True
    return False

def common_ranges(previous,current,key):
    a=[(e['t0'],e['t1'])for e in previous if(e['ring'],e['segment'])==key and len(e.get('lineages',[]))<=1]
    b=[(e['t0'],e['t1'])for e in current if(e['ring'],e['segment'])==key and len(e.get('lineages',[]))<=1]
    return [(max(x,u),min(y,v))for x,y in a for u,v in b if min(y,v)>=max(x,u)]

def predicted_samples(span,currentRings):
    ring=currentRings[span['ring']];a=ring[span['segment']];b=ring[(span['segment']+1)%len(ring)];v=G.sub(b,a);length=math.hypot(*v)
    if length<1e-12:raise ValueError('Degenerate current segment')
    now=(v[0]/length,v[1]/length);out=[]
    for s in span['samples']:
        old=s['tangent'];cos=old[0]*now[0]+old[1]*now[1];sin=G.cross(old,now);r=G.sub(s['q'],s['reference']);c=G.lerp(a,b,s['u'])
        out.append((c[0]+cos*r[0]-sin*r[1],c[1]+sin*r[0]+cos*r[1]))
    return out

def concatenate(spans,previous,currentRings):
    samples=[]
    for span in spans:
        points=predicted_samples(span,currentRings)if previous else[s['q']for s in span['samples']]
        samples.extend((s['u'],p)for s,p in zip(span['samples'],points))
    return [p for _,p in sorted(samples,key=lambda v:(v[0],v[1]))]

def substitute(old,new,currentRings):
    a=concatenate(old,True,currentRings);b=concatenate(new,False,currentRings);n,m=len(a),len(b)
    if not n or not m:return float(n+m)
    count=min(n,m);cost=float(abs(n-m))
    # Evaluate the ordered geometric span; no colour/pixel image interpolation.
    for k in range(count):
        i=min(n-1,int((k+.5)*n/count));j=min(m-1,int((k+.5)*m/count))
        cost+=abs(a[i][0]-b[j][0])+abs(a[i][1]-b[j][1])
    return min(float(n+m),cost)

def edit(old,new,currentRings,trace=False):
    n,m=len(old),len(new);dp=[[math.inf]*(m+1)for _ in range(n+1)];back={};dp[0][0]=0.
    for i in range(n+1):
        for j in range(m+1):
            options=[]
            if i<n:options.append((i+1,j,float(old[i]['length']),'delete'))
            if j<m:options.append((i,j+1,float(new[j]['length']),'add'))
            if i<n and j<m:options.append((i+1,j+1,substitute(old[i:i+1],new[j:j+1],currentRings),'substitute'))
            if i+1<n and j<m:options.append((i+2,j+1,substitute(old[i:i+2],new[j:j+1],currentRings),'merge'))
            if i<n and j+1<m:options.append((i+1,j+2,substitute(old[i:i+1],new[j:j+2],currentRings),'split'))
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

def channel_cost(old,new,currentRings,previousActive,currentActive,key,trace=False):
    intervals=common_ranges(previousActive,currentActive,key)
    validOld=[s for s in old if inside_range(*s['uRange'],intervals)]
    validNew=[s for s in new if inside_range(*s['uRange'],intervals)]
    result=edit(validOld,validNew,currentRings,trace)
    result['resetOldSpans']=len(old)-len(validOld);result['resetNewSpans']=len(new)-len(validNew)
    return result
