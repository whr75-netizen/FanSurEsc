"""Independent CPU enumeration of captured GPU113 cell proposals; no Unity calls.

This checks the live solver, not semantic correctness of its objective or native
carrier availability. Float32 scores are compared exactly, not with a loose RGB
or geometric tolerance. The input is the captured source table, not a selected
offline layout supplied to the GPU.
"""
from pathlib import Path
import json,sys,hashlib
import numpy as np
H=Path(__file__).resolve().parent
from inputs113 import buffer,load_packets
F=np.float32
K=F(65536)
def read(p):return json.loads(p.read_text(encoding='utf8'))
def bits(v):return int(v).bit_count()
def connected(mask,neighbours):
    if mask==0:return True
    reach=mask&-mask
    while True:
        expand=reach
        for i,n in enumerate(neighbours):
            if reach&(1<<i):expand|=n&mask
        if reach==expand:return reach==mask
        reach=expand
def scopes(cells,tags,owner,width,points):
    out=[]
    for part in range(2):
        for bit in range(8):
            raw=set(np.where((cells[:,3,0]==owner)&((tags[:,part]&(1<<bit))!=0))[0].tolist())
            visited=set();todo=[next(iter(raw))]if raw else []
            while todo:
                cell=todo.pop()
                if cell in visited:continue
                visited.add(cell);x=cell%width
                todo.extend(n for n in [cell-width,cell+width]+([cell-1]if x else [])+([cell+1]if x+1<width else [])if n in raw and n not in visited)
            scope=sum(1<<p for p,c in enumerate(points)if c in raw)if visited==raw else 0
            out.append(scope)
    return out
def subsets(cells,tags,points,part,sc,neighbours):
    eligible=[p for p,c in enumerate(points)if cells[c,0,part*2]>0]
    rows=[]
    for state in range(1<<len(eligible)):
        mask=0;component=0;keys=0;cost=F(0);n=0
        for j,p in enumerate(eligible):
            if state&(1<<j):
                c=points[p];mask|=1<<p;component|=int(tags[c,part]);keys|=int(tags[c,part+2]);n+=1
                m=cells[c,0];cost=F(cost+F(F(F(K-m[0])-m[2])-m[part*2]))
        if any(scope and not connected(mask&scope,neighbours)for scope in sc[part*8:part*8+8]):continue
        rows.append((mask,component,keys,n,cost))
    return rows
def interval(n,lo,hi):return np.maximum(np.maximum(lo-n,n-hi),0).astype(np.float32)
def solve(cells,tags,owner,width,header,frame,eye,gpu):
    points=[c for c in range(len(cells))if cells[c,3,0]==owner and cells[c,5,0]==1 and cells[c,0,0]+cells[c,0,2]>0]
    assert len(points)==int(header[0])
    neighbours=[]
    for c in points:
        x,y=c%width,c//width
        neighbours.append(sum(1<<p for p,n in enumerate(points)if abs(x-n%width)+abs(y-n//width)==1))
    sc=scopes(cells,tags,owner,width,points)
    assert sc==[int(x)for x in frame[eye*32+4:eye*32+20,0].view(np.uint32)]
    aa,bb=(subsets(cells,tags,points,p,sc,neighbours)for p in [0,1])
    mass=frame[eye*32+1];active=frame[eye*32+2].view(np.uint32);canvas=frame[eye*32+3,0]
    bm=np.array([r[0]for r in bb],np.uint32);bc=np.array([r[1]for r in bb],np.uint32);bk=np.array([r[2]for r in bb],np.uint32);bn=np.array([r[3]for r in bb],np.float32);bd=np.array([r[4]for r in bb],np.float32)
    best=None;solutions=[]
    for am,ac,ak,an,ad in aa:
        valid=np.where((bm&am)==0)[0]
        if not len(valid):continue
        penalty=np.array([bits(int(active[0])&~ac)+bits(int(active[1])&~int(c))for c in bc[valid]],np.float32)
        union=interval(F(an)*K+bn[valid]*K,F(mass[0]+mass[2]),F(mass[1]+mass[3]))
        individual=interval(F(an)*K,mass[0],mass[1])+interval(bn[valid]*K,mass[2],mass[3])
        reconstruction=np.maximum(F(canvas+ad)+bd[valid],0)
        keyloss=np.array([bits(int(active[2])&~(ak|int(k)))for k in bk[valid]],np.float32)
        score=np.column_stack([penalty,union,individual,reconstruction,keyloss])
        ix=np.lexsort(tuple(score[:,j]for j in range(4,-1,-1)))[0]
        local=tuple(score[ix].tolist())
        if best is None or local<best:best=local;solutions=[]
        if local==best:
            solutions.extend((am,int(bm[valid[j]]))for j in np.where((score==score[ix]).all(1))[0])
    assert best is not None
    expected_score=np.r_[gpu[0],float(gpu[2].view(np.uint32)[0])]
    score_equal=np.array_equal(np.array(best),expected_score)
    both_i=both_w=(1<<len(points))-1;any_i=any_w=0
    for i,w in solutions:both_i&=i;any_i|=i;both_w&=w;any_w|=w
    masks=[both_i,any_i,both_w,any_w];gpu_masks=gpu[1].view(np.uint32).tolist()
    return {'owner':owner,'CPUScore':best,'GPUScore':expected_score.tolist(),'exactScore':bool(score_equal),'CPUOptima':len(solutions),'GPUOptima':int(gpu[2].view(np.uint32)[1]),'consensusEqual':masks==gpu_masks,'allStatesEnumerated':1<<int(header[1]+header[2]),'filteredConnectedSubsets':[len(aa),len(bb)]}
def main():
    state,packets=load_packets(H);rows=[];cache={}
    for p,path in packets:
        meta=read(path/'RAW_MANIFEST.json');frame=buffer(path/'REGION113-frame.f32').reshape(64,4);cell=buffer(path/'REGION113-cells.f32').reshape(512,7,4);tags=buffer(path/'REGION113-tags.f32').reshape(512,4).view(np.uint32);gpu=buffer(path/'REGION113-best.f32').reshape(2,3,4);width=meta['forward102']['canonicalSize'][0]//4
        digest=hashlib.sha256(cell.tobytes()+tags.tobytes()+frame.tobytes()+gpu.tobytes()).hexdigest()
        if digest not in cache:
            cache[digest]=[solve(cell,tags,e+1,width,frame.view(np.uint32)[e*32],frame,e,gpu[e])for e in range(2)]
        rows.append({'sourceId':p['sourceId'],'frame':p['frame'],'eyes':cache[digest]})
    failures=[(r['frame'],e)for r in rows for e in r['eyes']if not(e['exactScore']and e['consensusEqual']and e['CPUOptima']==e['GPUOptima'])]
    report={'actualFrames':len(rows),'uniqueTableInputs':len(cache),'passes':not failures,'scope':'Independent enumeration from captured current GPU source proposals; no replay injected into live runtime. Does not validate native semantic mapping, visual merit, unsupported footprint, history, or consensus topology.','rows':rows,'failures':failures}
    (H/'ORACLE113.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'frames':len(rows),'unique':len(cache),'passes':not failures,'failures':failures},ensure_ascii=False))
    assert not failures,'CPU/GPU enumeration differs; do not declare solver equivalence'
if __name__=='__main__':main()
