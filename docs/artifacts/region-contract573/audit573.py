"""One ownership audit of existing 572 layouts. No new selection or rendering."""
from pathlib import Path
import struct,json,collections,math
import numpy as np
ROOT=Path(__file__).parent;PREV=ROOT.parent/'RegionContract572'
env={'__file__':str(PREV/'review572.py')};exec((PREV/'review572.py').read_text().split('\nrows=[]')[0],env)
EPS=1e-12 # Same zero-width scale as the existing source sweep; tiny cases are flagged.

def polyarea(poly):
    if len(poly)<3:return 0.
    x,y=poly[0];return abs(sum((a[0]-x)*(b[1]-y)-(a[1]-y)*(b[0]-x)for a,b in zip(poly[1:],poly[2:])))*.5

def signed(poly):return sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(poly,poly[1:]+poly[:1]))

def clip(subject,polygon):
    if signed(polygon)<0:polygon=list(reversed(polygon))
    out=subject
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if not out:break
        old=out;out=[]
        def side(p):return(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        p=old[-1];sp=side(p)
        for q in old:
            sq=side(q)
            if(sp>=0)!=(sq>=0):
                t=sp/(sp-sq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
            if sq>=0:out.append(q)
            p,sp=q,sq
    return out

def original_pieces(branches):
    bycell=collections.defaultdict(list);area={}
    for identity,b in branches.items():
        total=0.
        for lo,hi,l0,l1,r0,r1,left,right in b['geometry']:
            total+=(hi-lo)*(r0+r1-l0-l1)*.5;v=math.floor((lo+hi)*.5)
            for u in range(math.floor(min(l0,l1)),math.ceil(max(r0,r1))):
                c=lambda z:max(u,min(u+1,z))
                polygon=[(c(l0),lo),(c(r0),lo),(c(r1),hi),(c(l1),hi)]
                if polyarea(polygon)<=0:continue
                cell=(u,v)
                if b['transpose']:polygon=[(y,x)for x,y in polygon];cell=(v,u)
                bycell[cell].append((identity,polygon))
        area[identity]=total
    return bycell,area

def atoms(frame):
    data=(ROOT/f'Atoms573B/{frame:03}_ATOMS.bin').read_bytes();v,f,x,y,w,h,n=struct.unpack_from('<7i',data);assert(v,f)==(573,frame)and len(data)==28+72*n
    return(x,y,w,h),[struct.unpack_from('<6d2q2i',data,28+72*i)for i in range(n)]

def local_components(nodes):
    parent=list(range(len(nodes)));starts=collections.defaultdict(list)
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,z in enumerate(nodes):starts[(z[8],z[9],z[0])].append(i)
    for i,z in enumerate(nodes):
        for j in starts.get((z[8],z[9],z[1]),[]):
            q=nodes[j]
            if min(z[5],q[4])-max(z[3],q[2])>EPS:parent[root(i)]=root(j)
    groups=collections.defaultdict(lambda:collections.defaultdict(list))
    for i,z in enumerate(nodes):groups[(z[8],z[9])][root(i)].append(i)
    return groups

prior=json.loads((PREV/'REVIEW572.json').read_text());summary=[];witnesses=[];all_records=[]
for saved in prior:
    frame=saved['frame'];(x,y,w,h),nodes=atoms(frame);groups=local_components(nodes)
    layout=(PREV/f'Stored572/{frame:03}_LAYOUT.bin').read_bytes();mask=np.frombuffer(layout,'?',offset=24+4*w*h).reshape(h,w);areas=np.frombuffer(layout,'<f4',offset=24,count=w*h).reshape(h,w)
    branches=env['source_branches'](frame);pieces,original_area=original_pieces(branches)
    remain=collections.defaultdict(float);selected=collections.defaultdict(float);branch_cells=collections.defaultdict(set);parents=[];overlap_overcount=0.;uncertain=0
    for i,z in enumerate(nodes):
        lo,hi,l0,l1,r0,r1,left,right,cx,cy=z;polygon=[(l0,lo),(r0,lo),(r1,hi),(l1,hi)];pa=polyarea(polygon);ownerarea=collections.defaultdict(float)
        for identity,p in pieces.get((cx,cy),[]):
            v=polyarea(clip(polygon,p))
            if 0<v<=EPS:uncertain+=1
            if v>EPS:ownerarea[identity]+=v
        for axis in('x|','y|'):
            overlap_overcount=max(overlap_overcount,sum(v for k,v in ownerarea.items()if k.startswith(axis))-pa)
        parents.append(dict(ownerarea))
        for k,v in ownerarea.items():
            remain[k]+=v
            if not mask[cy-y,cx-x]:selected[k]+=v;branch_cells[k].add((cx,cy))
    conflicted=[];resolved=0;none=0;numeric_cells=[]
    for cy in range(y,y+h):
        for cx in range(x,x+w):
            if mask[cy-y,cx-x]:continue
            components=[]
            for ids in groups[(cx,cy)].values():
                total=sum((nodes[i][1]-nodes[i][0])*(nodes[i][4]+nodes[i][5]-nodes[i][2]-nodes[i][3])*.5 for i in ids)
                trace=sorted(set(v for i in ids for v in nodes[i][6:8]));source=sorted(set(k for i in ids for k in parents[i]))
                components.append({'area':total,'nodeIds':ids,'sourceBoundaryIDs':trace,'sourceBranches':source})
            if not components:none+=1
            elif len(components)==1:resolved+=1
            else:
                row={'frame':frame,'cell':[cx,cy],'positiveArea':float(areas[cy-y,cx-x]),'negativeLocalComponents':components,'sourceSelectedOwner':'UNRESOLVED: disconnected negative pieces merged by one empty output cell'}
                if min(c['area']for c in components)<=EPS or float(areas[cy-y,cx-x])<=EPS:numeric_cells.append(row)
                else:conflicted.append(row)
    event_errors=[];event_kinds=collections.Counter();nonopen=[]
    for d in saved['allAxisDecisionRecords']:
        if'open-mouth'in(d['sourceStart']['kind'],d['sourceEnd']['kind']):continue
        identity=d['sourceBranch'];b=branches[identity];kind='>'.join(p['kind']for p in b['ports']);event_kinds[kind]+=1
        mode='CONTINUOUS_FILL'if remain[identity]<=EPS else'SPATIAL_FILL'if selected[identity]<=EPS else'RETAINED_NEEDS_JUNCTION_OWNER'
        for p in b['ports']:
            for neighbour in p['neighbours']:
                if neighbour not in branches:event_errors.append([identity,'missing neighbour',neighbour]);continue
                level,left,right,*_=p['values'];opposite=[q for q in branches[neighbour]['ports']if q['values'][0]==level and identity in q['neighbours']]
                if not any(min(right,q['values'][2])-max(left,q['values'][1])>EPS for q in opposite):event_errors.append([identity,'nonreciprocal or zero-width event',neighbour])
        nonopen.append({'sourceBranch':identity,'axis':d['axis'],'sourceType':kind,'originalArea':original_area[identity],'postDesignNegativeArea':remain[identity],'selectedNegativeArea':selected[identity],'outputState':mode,'selectedCells':sorted(branch_cells[identity])})
    modes=collections.Counter(r['outputState']for r in nonopen)
    record={'frame':frame,'atomCount':len(nodes),'singleLocalOwnerNegativeCells':resolved,'noSourceNegativeCells':none,'conflictedNegativeCells':len(conflicted),'numericUncertainCells':len(numeric_cells),'nonOpenDecisionRecords':len(nonopen),'nonOpenTypes':dict(event_kinds),'observedModes':dict(modes),'sourceEventErrors':event_errors,'sourceAxisOverlapOvercountMax':overlap_overcount,'tinyIntersectionsFlagged':uncertain}
    summary.append(record);all_records.append({'frame':frame,'nonOpenRecords':nonopen,'firstConflicts':conflicted[:12],'numericUncertainCells':numeric_cells[:3]});witnesses.extend(conflicted[:3]);print(json.dumps(record))
out={'policy':'No new mask or owner-merge rule. Disconnected continuous negative pieces in one empty output cell remain unresolved.','summary':summary,'allNonOpenDecisionRecords':sum(r['nonOpenDecisionRecords']for r in summary),'allSourceEventsReciprocal':not any(r['sourceEventErrors']for r in summary),'allSourceOverlapOvercountMax':max(r['sourceAxisOverlapOvercountMax']for r in summary),'ownershipConflictCells':sum(r['conflictedNegativeCells']for r in summary),'records':all_records,'firstWitnesses':witnesses,'productIntegration':'BLOCKED until disconnected-source region merge/elision ownership is explicitly decided; counts are not visual-error counts.'}
(ROOT/'AUDIT573B.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('TOTAL',json.dumps({k:out[k]for k in['allNonOpenDecisionRecords','allSourceEventsReciprocal','allSourceOverlapOvercountMax','ownershipConflictCells','productIntegration']}))
