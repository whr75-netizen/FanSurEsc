"""Offline active-boundary/span correspondence prototype; no Unity writes.

Canonical top-left logical grid. An active fragment has filled positive-winding
region on its left. IDs are persistent (ring, source-segment, parameter-range),
not screen-nearest role/material labels. Grid edges retain their inside packet.
"""
from pathlib import Path
import json,struct,gzip,math,hashlib,time
import numpy as np

ROOT=Path(__file__).parent; INPUT=ROOT/'Loop514'; OUTPUT=ROOT/'Temporal516'
NUM_EPS=1e-9

def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return (a[0]-b[0],a[1]-b[1])
def lerp(a,b,t):return(a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))
def winding(point,edges):
    x,y=point;v=0
    for e in edges:
        a,b=e['a'],e['b'];c=cross(sub(b,a),(x-a[0],y-a[1]))
        if a[1]<=y<b[1]and c>0:v+=1
        elif b[1]<=y<a[1]and c<0:v-=1
    return v

def fragments(rings):
    original=[]
    for ring,p in enumerate(rings):
        for seg,(a,b)in enumerate(zip(p,p[1:]+p[:1])):
            if a!=b:original.append({'ring':ring,'segment':seg,'a':a,'b':b,'cuts':[0.,1.]})
    intersections=0
    for i,e in enumerate(original):
        a=e['a'];r=sub(e['b'],a)
        for f in original[i+1:]:
            q=f['a'];s=sub(f['b'],q);den=cross(r,s)
            if abs(den)<1e-20:
                if abs(cross(sub(q,a),r))<1e-20:
                    rr=r[0]*r[0]+r[1]*r[1];ss=s[0]*s[0]+s[1]*s[1]
                    if rr and ss:
                        for point in [f['a'],f['b']]:
                            v=sum(x*y for x,y in zip(sub(point,a),r))/rr
                            if 0<v<1:e['cuts'].append(v)
                        for point in [e['a'],e['b']]:
                            v=sum(x*y for x,y in zip(sub(point,q),s))/ss
                            if 0<v<1:f['cuts'].append(v)
                continue
            delta=sub(q,a);t=cross(delta,s)/den;u=cross(delta,r)/den
            if 0<=t<=1 and 0<=u<=1:
                if 0<t<1:e['cuts'].append(t)
                if 0<u<1:f['cuts'].append(u)
                if 0<t<1 and 0<u<1:intersections+=1
    active=[];uncertain=0
    for e in original:
        cuts=sorted(set(e['cuts']));vector=sub(e['b'],e['a']);length=math.hypot(*vector)
        for t0,t1 in zip(cuts,cuts[1:]):
            if t1-t0<1e-12:continue
            a,b=lerp(e['a'],e['b'],t0),lerp(e['a'],e['b'],t1);mid=lerp(a,b,.5)
            normal=(-vector[1]/length,vector[0]/length)
            # Find distance along this normal to every other supporting segment.
            # Probe less than one quarter of the nearest actual crossing. This
            # is numerical side classification, not an artistic width threshold.
            reach=min(math.dist(a,b)/1024.,1e-4)
            for f in original:
                if f is e:continue
                v=sub(f['b'],f['a']);den=cross(normal,v)
                if abs(den)<1e-20:continue
                delta=sub(f['a'],mid);s=cross(delta,v)/den;u=cross(delta,normal)/den
                if 0<=u<=1 and abs(s)>1e-12:reach=min(reach,abs(s)/4.)
            if reach<1e-12:uncertain+=1;continue
            left=winding((mid[0]+normal[0]*reach,mid[1]+normal[1]*reach),original)
            right=winding((mid[0]-normal[0]*reach,mid[1]-normal[1]*reach),original)
            if (left>0)==(right>0):continue
            forward=left>0
            active.append({'ring':e['ring'],'segment':e['segment'],'t0':t0,'t1':t1,'a':a if forward else b,'b':b if forward else a,'forward':forward,'leftWinding':left if forward else right,'rightWinding':right if forward else left})
    # Coincident union boundaries retain all source lineage and invalidate a
    # singular history match. They are not counted twice as separate boundaries.
    unique={}
    for e in active:
        key=tuple(round(v,8)for p in[e['a'],e['b']]for v in p)
        lineage=[e['ring'],e['segment'],e['t0'],e['t1']]
        if key in unique:unique[key]['lineages'].append(lineage)
        else:e['lineages']=[lineage];unique[key]=e
    active=list(unique.values())
    # Retain incidence diagnostics rather than inventing a path at junctions.
    key=lambda p:(round(p[0],8),round(p[1],8))
    nodes={}
    for n,e in enumerate(active):
        for end in ['a','b']:nodes.setdefault(key(e[end]),[]).append((n,end))
    junctions={p:xs for p,xs in nodes.items()if len(xs)!=2}
    for e in active:e['junctionA']=key(e['a'])in junctions;e['junctionB']=key(e['b'])in junctions
    return active,{'properIntersections':intersections,'uncertainSideTests':uncertain,'activeFragments':len(active),'unbalancedNodes':sum(abs(sum(1 if end=='a'else-1 for _,end in xs))for xs in nodes.values()),'junctionNodes':len(junctions)}

def read_mask(i):
    b=gzip.decompress((INPUT/f'{i:03d}_MASK.bin.gz').read_bytes());w,h,_,_=struct.unpack_from('<4i',b)
    return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)[:,:,1]>.5
def boundary(mask):
    h,w=mask.shape;out=[]
    def on(x,y):return 0<=x<w and 0<=y<h and mask[y,x]
    for y,x in zip(*np.where(mask)):
        x,y=int(x),int(y)
        for condition,a,b in [(not on(x,y-1),(x,y),(x+1,y)),(not on(x+1,y),(x+1,y),(x+1,y+1)),(not on(x,y+1),(x+1,y+1),(x,y+1)),(not on(x-1,y),(x,y+1),(x,y))]:
            if condition:out.append({'a':a,'b':b,'inside':[x,y]})
    return out

def descriptor(edge,active,rings,packet):
    """Whole directed unit edge to active curve candidates, with side/order checks.

    Candidate radius is the cell diagonal: either endpoint can be a corner of
    a cell intersected by its source curve. It is not a new shape permission;
    unmatched old cuts are reported, not stretched to pass this radius.
    """
    p=np.array([edge['a'],edge['b']],float);a=np.array([e['a']for e in active]);b=np.array([e['b']for e in active]);d=b-a;length2=(d*d).sum(1)
    t=np.clip(((p[:,None,:]-a)*d).sum(2)/length2,0,1);q=a+t[:,:,None]*d
    distances=((p[:,None,:]-q)**2).sum(2);score=distances.mean(0)
    # Dot>=0 ensures the candidate boundary carries the filled region on the
    # same side. Stair edges perpendicular to a smooth curve are allowed.
    direction=p[1]-p[0];oriented=(d*direction).sum(1)>=-1e-12
    candidates=np.where((distances.max(0)<=2+1e-9)&oriented)[0]
    if len(candidates)==0:return {**edge,'valid':False,'reason':'NO_ACTIVE_EDGE_IN_CELL_CORRIDOR'}
    ordered=sorted(candidates,key=lambda n:(score[n],active[n]['ring'],active[n]['segment'],active[n]['t0']))
    best=ordered[0];e=active[best];mid=(p[0]+p[1])/2;u=float(np.clip(np.dot(mid-a[best],d[best])/length2[best],0,1));sourceT=e['t0']+u*(e['t1']-e['t0'])if e['forward']else e['t1']-u*(e['t1']-e['t0'])
    # Exact competing branches do not acquire identity by array/tie order.
    ambiguous=[n for n in ordered[1:]if abs(score[n]-score[best])<=1e-10 and (active[n]['ring'],active[n]['segment'])!=(e['ring'],e['segment'])]
    junction=(u<=1e-10 and e['junctionA'])or(u>=1-1e-10 and e['junctionB'])
    xy=tuple(edge['inside']);pk=packet.get(xy)
    geometryValid=not ambiguous and not junction and len(e.get('lineages',[]))<=1
    foreground=pk is not None and pk.get('bodyForeground',False)
    valid=geometryValid and pk is not None and not foreground
    ref=rings[e['ring']];reference=lerp(ref[e['segment']],ref[(e['segment']+1)%len(ref)],sourceT)
    tangent=sub(ref[(e['segment']+1)%len(ref)],ref[e['segment']]);norm=math.hypot(*tangent);tangent=[v/norm for v in tangent]
    return {**edge,'valid':valid,'geometryValid':geometryValid,'packetKnown':pk is not None,'bodyForeground':foreground,'reason':'MATCH'if valid else'AMBIGUOUS_BRANCH'if ambiguous else'JUNCTION_RESET'if junction else'MULTIPLE_SOURCE_LINEAGE'if not geometryValid else'PACKET_NOT_CAPTURED'if pk is None else'CURRENT_FOREGROUND_RESET','ring':e['ring'],'segment':e['segment'],'u':sourceT,'reference':reference,'tangent':tangent,'squaredFit':float(score[best]),'activeIndex':int(best),'insidePacket':None if pk is None else{key:pk[key]for key in ['submesh','primitive','world','depth']},'candidateCount':len(candidates)}

def spans(descriptors):
    # Splitting a collinear run at a persistent source segment is intentional:
    # source intervals stay explicit when projected branches split or merge.
    groups={};invalid=[]
    for e in descriptors:
        if not e['valid']:invalid.append(e);continue
        dx=e['b'][0]-e['a'][0];dy=e['b'][1]-e['a'][1];line=e['a'][1]if dx else e['a'][0]
        groups.setdefault((e['ring'],e['segment'],dx,dy,line),[]).append(e)
    out=[]
    for key,es in groups.items():
        ring,segment,dx,dy,line=key;es.sort(key=lambda e:e['a'][0]*dx+e['a'][1]*dy);run=[]
        def emit():
            if not run:return
            centre=[sum((e['a'][k]+e['b'][k])*.5 for e in run)/len(run)for k in [0,1]]
            samples=[{'q':[(e['a'][k]+e['b'][k])*.5 for k in[0,1]],'u':e['u'],'reference':e['reference'],'tangent':e['tangent']}for e in run]
            samples.sort(key=lambda e:(e['u'],e['q']))
            out.append({'ring':ring,'segment':segment,'direction':[dx,dy],'length':len(run),'a':run[0]['a'],'b':run[-1]['b'],'centre':centre,'u':sum(e['u']for e in run)/len(run),'uRange':[min(e['u']for e in run),max(e['u']for e in run)],'reference':np.mean([e['reference']for e in run],axis=0).tolist(),'samples':samples,'edges':len(run)})
        for e in es:
            if run and run[-1]['b']!=e['a']:emit();run=[]
            run.append(e)
        emit()
    return sorted(out,key=lambda e:(e['ring'],e['segment'],e['u'],e['direction'])),invalid

def correspondence(previous,current,currentRings,currentActive):
    out=[]
    for old in previous:
        key=(old['ring'],old['segment']);u=old['u']
        active=[e for e in currentActive if(e['ring'],e['segment'])==key and e['t0']-1e-10<=u<=e['t1']+1e-10]
        if not active:out.append({'ring':key[0],'segment':key[1],'valid':False,'reason':'ACTIVE_INTERVAL_ENDED'});continue
        candidates=[s for s in current if(s['ring'],s['segment'])==key]
        if not candidates:out.append({'ring':key[0],'segment':key[1],'valid':False,'reason':'NO_CURRENT_VISIBLE_SPAN'});continue
        ring=currentRings[key[0]];now=lerp(ring[key[1]],ring[(key[1]+1)%len(ring)],u);motion=sub(now,old['reference'])
        # This records candidate correspondences, not an identity proof based
        # only on proximity. Temporal DP will preserve the source u ordering.
        out.append({'ring':key[0],'segment':key[1],'valid':True,'previousU':u,'continuousMotion':motion,'candidateCount':len(candidates),'currentU':[s['u']for s in candidates]})
    return out

def main():
    OUTPUT.mkdir(exist_ok=True);allrows=[];previous=[];start=time.perf_counter();shape=None
    for i in range(81):
        doc=json.loads((INPUT/f'{i:03d}_curves.json').read_text());rings=[[(v['x'],v['y'])for v in r['points']]for r in doc['curves']]
        lengths=[len(r)for r in rings]
        if shape is None:shape=lengths
        assert lengths==shape,'Persistent control order changed'
        active,stats=fragments(rings);assert stats['unbalancedNodes']==0 and stats['uncertainSideTests']==0,stats
        packets={tuple((p['x'],p['y'])):p for p in json.loads((INPUT/f'{i:03d}_packets.json').read_text())['packets']}
        refs=json.loads((INPUT/f'{i:03d}_ALT_bodyrefs512.json').read_text())['references']
        for ref in refs:
            key=(ref['x'],ref['y'])
            if key in packets:packets[key]['bodyForeground']=ref['kind']in[1,2]and ref['depth']<ref['hairDepth']-.0001
        m=read_mask(i);descriptors=[descriptor(e,active,rings,packets)for e in boundary(m)];ss,invalid=spans(descriptors);matches=correspondence(previous,ss,rings,active)if i else[]
        reasons={reason:sum(e['reason']==reason for e in invalid)for reason in sorted(set(e['reason']for e in invalid))}
        row={'target':i,'phase':i/80,'ringLengths':lengths,'geometry':stats,'boundaryEdges':len(descriptors),'validEdges':sum(e['valid']for e in descriptors),'invalidReasons':reasons,'spans':ss,'invalidEdges':invalid,'previousCorrespondence':matches,'active':active}
        (OUTPUT/f'{i:03d}_ACTIVE.json').write_text(json.dumps(row,separators=(',',':'))+'\n');allrows.append({k:v for k,v in row.items()if k not in ['spans','invalidEdges','previousCorrespondence','active']});previous=ss
        if i%20==0:print(json.dumps({'frame':i,'validEdges':row['validEdges'],'edges':row['boundaryEdges'],'invalid':reasons}),flush=True)
    out={'mode':'OFFLINE_ACTIVE_BOUNDARY_SPAN_AUDIT','frames':len(allrows),'seconds':time.perf_counter()-start,'rows':allrows,'allSideAndIncidenceChecksPassed':True,'correspondenceScope':'Source-parameter ordered candidates; actual correspondence costs not yet optimized. Missing selected packets/foreground/junction/active-interval events explicitly invalidate history.','notCaptured':'Novel cell visibility against source renderer1 and native world are not certified by this audit.','runtimeChanged':False,'newCaptures':0}
    (OUTPUT/'ACTIVE_AUDIT516.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='rows'}),flush=True)
if __name__=='__main__':main()
