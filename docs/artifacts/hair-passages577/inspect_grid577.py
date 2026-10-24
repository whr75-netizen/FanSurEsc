from pathlib import Path
import csv,json,collections,struct
R=Path(__file__).parent
T=R/'Trace577B'
rows=list(csv.DictReader((T/'GRID577.tsv').open(),delimiter='\t'))
d=json.loads((T/'TRACE577.json').read_text());x0,y0,w,h=[d[k]for k in ['x','y','w','h']]
def flags(key):return [q[key]=='True'for q in rows]
P,S=flags('protectedPositive'),flags('proposal')
def outside(mask):
    visited=[False]*len(mask);q=collections.deque()
    for i,v in enumerate(mask):
        x,y=i%w,i//w
        if not v and(x in(0,w-1)or y in(0,h-1)):visited[i]=True;q.append(i)
    while q:
        i=q.popleft();x,y=i%w,i//w
        for u,v in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
            if 0<=u<w and 0<=v<h:
                j=v*w+u
                if not mask[j]and not visited[j]:visited[j]=True;q.append(j)
    return visited
def xy(i):return [x0+i%w,y0+i//w]
PO,SO=outside(P),outside(S)
assert SO==flags('exterior')
raw=(R/'CanvasFull260/042_OFF_AREAS.bin').read_bytes();assert struct.unpack_from('<4i',raw)==(x0,y0,w,h)
A=list(struct.unpack_from('<'+'f'*(w*h),raw,16));rootA=[float(q['rootArea'])for q in rows]
aliases=[i for i in range(w*h)if not S[i]and not SO[i]]
added=[]
for i in range(w*h):
    if S[i]and not P[i]:
        trial=S.copy();trial[i]=False;out=outside(trial)
        added.append({'cell':xy(i),'index':i,'sourceSignedArea':A[i],'rootArea':rootA[i],'sourceExterior':PO[i],'reopensAliasCells':[xy(j)for j in aliases if out[j]],'oneRemovalRequiredPositiveViolation':False})
raw=(R/'CanvasFull260/042_OFF_MASK.bin').read_bytes();mw,mh,mx,my=struct.unpack_from('<4i',raw);values=struct.unpack_from('<'+'f'*(mw*mh*4),raw,16);different=[]
for y in range(max(my,y0),min(my+mh,y0+h)):
    for x in range(max(mx,x0),min(mx+mw,x0+w)):
        if(values[((y-my)*mw+x-mx)*4+1]>.5)!=P[(y-y0)*w+x-x0]:different.append([x,y])
local=[{'cell':xy(i),'P':P[i],'proposal':S[i],'P_exterior':PO[i],'proposal_exterior':SO[i],'signedArea':A[i],'rootArea':rootA[i]}for i in range(w*h)if 216<=xy(i)[0]<=224 and 44<=xy(i)[1]<=53]
result={'frame':42,'bounds':[x0,y0,w,h],'P_count':sum(P),'proposalCount':sum(S),'P_closedEmptyCells':[xy(i)for i in range(w*h)if not P[i]and not PO[i]],'proposalAliasCells':[{'cell':xy(i),'P_exterior':PO[i]}for i in aliases],'proposalAdded':added,'sourceAreaToRootAreaDifferences':[{'cell':xy(i),'signedArea':A[i],'rootArea':rootA[i]}for i in range(w*h)if abs(A[i]-rootA[i])>1e-7],'P_OFF_selected_diff':different,'local':local}
spans=list(csv.DictReader((T/'FEATURE_7_SPANS577.tsv').open(),delimiter='\t'))
def feature_area(x,y):
    total=0
    for s in spans:
        lo,hi,l0,l1,r0,r1=[float(s[k])for k in ['lo','hi','l0','l1','r0','r1']]
        if int((lo+hi)//2)!=y:continue
        total+=(hi-lo)*(max(0,min(x+1,r0)-max(x,l0))+max(0,min(x+1,r1)-max(x,l1)))*.5
    return total
bridges=[]
for i in range(w*h):
    if not P[i]or feature_area(*xy(i))<=0:continue
    trial=P.copy();trial[i]=False;out=outside(trial)
    reopened=[j for j in aliases if out[j]]
    if not reopened:continue
    x,y=i%w,i//w;boundary=0
    for dy in [-1,0,1]:
        for dx in [-1,0,1]:
            if not(dx or dy)or not(0<=x+dx<w and 0<=y+dy<h):continue
            f32=lambda z:struct.unpack('<f',struct.pack('<f',z))[0]
            weight=f32(f32(d['boundaryCost'])*f32(.29289322 if dx and dy else .58578644))
            boundary+=(1 if P[(y+dy)*w+x+dx]else-1)*weight
    bridges.append({'cell':xy(i),'sourceArea':A[i],'featureNegativeArea':feature_area(*xy(i)),'areaCostDelta':2*A[i]-1,'boundaryCostDelta':boundary,'totalCostDelta':2*A[i]-1+boundary,'reopened':[xy(j)for j in reopened]})
result['singleCellSourceSupportedBridges']=sorted(bridges,key=lambda b:b['totalCostDelta'])
def face_components(x,y):
    nodes=[]
    for s in spans:
        lo,hi,l0,l1,r0,r1=[float(s[k])for k in ['lo','hi','l0','l1','r0','r1']]
        if int((lo+hi)//2)!=y:continue
        q=(lo,hi,max(x,l0),max(x,l1),min(x+1,r0),min(x+1,r1))
        if(q[4]-q[2]+q[5]-q[3])*(hi-lo)<=1e-12:continue
        face=set();left=(l0+l1)/2;right=(r0+r1)/2
        if left<x<right:face.add('L')
        if left<x+1<right:face.add('R')
        if lo==y and q[4]-q[2]>1e-12:face.add('T')
        if hi==y+1 and q[5]-q[3]>1e-12:face.add('B')
        nodes.append((q,face))
    parent=list(range(len(nodes)))
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    for i,(a,_)in enumerate(nodes):
        for j,(b,_)in enumerate(nodes[:i]):
            if a[1]==b[0]and min(a[5],b[4])-max(a[3],b[2])>1e-12 or b[1]==a[0]and min(b[5],a[4])-max(b[3],a[2])>1e-12:parent[find(i)]=find(j)
    groups={}
    for i,(_,f)in enumerate(nodes):groups.setdefault(find(i),set()).update(f)
    return[sorted(f)for f in groups.values()]
for b in result['singleCellSourceSupportedBridges']:
    b['continuousNegativeFaceComponents']=face_components(*b['cell'])
(T/'GRID_ANALYSIS577.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in ['local','sourceAreaToRootAreaDifferences','proposalAdded']}))
