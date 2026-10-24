"""One fixed-pitch stored-input prototype, never a render or product patch."""
from pathlib import Path
import json,struct,math,collections
import numpy as np
ROOT=Path(__file__).parent;PREV=ROOT.parent/'RegionContract571';CAP=ROOT.parent/'HairContract570/Full570'
env={'__file__':str(PREV/'audit571.py')};exec((PREV/'audit571.py').read_text().split('\nrows=[]')[0],env)
N4=((1,0),(-1,0),(0,1),(0,-1))

def parts(cells):
    remaining=set(cells);out=[]
    while remaining:
        start=min(remaining);remaining.remove(start);q=[start]
        for x,y in q:
            for dx,dy in N4:
                z=x+dx,y+dy
                if z in remaining:remaining.remove(z);q.append(z)
        out.append(q)
    return out

def exterior(mask):
    h,w=mask.shape;outside={(x,y)for y in range(h)for x in range(w)if not mask[y,x]and(x in(0,w-1)or y in(0,h-1))};q=list(outside)
    for x,y in q:
        for dx,dy in N4:
            z=x+dx,y+dy
            if 0<=z[0]<w and 0<=z[1]<h and not mask[z[1],z[0]]and z not in outside:outside.add(z);q.append(z)
    return outside

def source_branches(frame):
    d=(ROOT/f'Stored572/{frame:03}_SOURCE_AXES.bin').read_bytes();at=0
    def get(fmt):
        nonlocal at
        q=struct.unpack_from('<'+fmt,d,at);at+=struct.calcsize('<'+fmt);return q[0]if len(q)==1 else q
    def text():
        nonlocal at
        n=0;shift=0
        while True:
            q=get('B');n|=(q&127)<<shift
            if q<128:break
            shift+=7
        s=d[at:at+n].decode();at+=n;return s
    def geo():return [get('6d2q')for _ in range(get('i'))]
    assert get('2i')==(572,frame)
    result={}
    for _ in range(get('i')):
        transpose=get('?');key=text();geometry=geo();ports=[]
        for side in ['start','end']:
            port={'side':side,'kind':text(),'values':get('3d2q')};port['neighbours']=[text()for _ in range(get('i'))];ports.append(port)
        result[key]={'geometry':geometry,'ports':ports,'transpose':transpose}
    assert at==len(d);return result

def local_cells(geometry,lo_limit,hi_limit):
    cells=set()
    for lo,hi,l0,l1,r0,r1,*_ in geometry:
        a,b=max(lo,lo_limit),min(hi,hi_limit)
        if b<=a:continue
        ta,tb=(a-lo)/(hi-lo),(b-lo)/(hi-lo)
        left0,left1=l0+(l1-l0)*ta,l0+(l1-l0)*tb;right0,right1=r0+(r1-r0)*ta,r0+(r1-r0)*tb
        y=math.floor((a+b)*.5)
        for x in range(math.floor(min(left0,left1)),math.ceil(max(right0,right1))):
            size=(b-a)*(max(0,min(x+1,right0)-max(x,left0))+max(0,min(x+1,right1)-max(x,left1)))*.5
            if size>0:cells.add((x,y))
    return cells

rows=[]
def decisions(frame):
    data=(ROOT/f'Stored572/{frame:03}_DECISIONS.bin').read_bytes();pos=0
    def get(fmt):
        nonlocal pos
        q=struct.unpack_from('<'+fmt,data,pos);pos+=struct.calcsize('<'+fmt);return q[0]if len(q)==1 else q
    def text():
        nonlocal pos
        n=0;shift=0
        while True:
            q=get('B');n|=(q&127)<<shift
            if q<128:break
            shift+=7
        s=data[pos:pos+n].decode();pos+=n;return s
    assert get('2i')==(572,frame);result=[]
    for _ in range(get('i')):
        d={k:text()for k in['sourceBranch','axis','mode','splitRule']}
        d.update(zip(['pitch','sourceLo','sourceHi','fillLo','fillHi','keepLo','keepHi'],get('7d')));d['insertedRing']=get('i')
        for k in['positiveLeftBoundary','positiveRightBoundary']:d[k]=[get('q')for _ in range(get('i'))]
        for k in['sourceStart','sourceEnd']:
            port={'kind':text()};port.update(zip(['level','left','right','leftId','rightId'],get('3d2q')));d[k]=port
        result.append(d)
    assert pos==len(data);return result
for frame in [16,51,62,71,72,73,77]:
    base=ROOT/f'Stored572/{frame:03}';d=base.with_name(base.name+'_LAYOUT.bin').read_bytes();magic,f,x,y,w,h=struct.unpack_from('<6i',d);assert(magic,f)==(572,frame)
    area=np.frombuffer(d,'<f4',offset=24,count=w*h).reshape(h,w);m=np.frombuffer(d,'?',offset=24+4*w*h).reshape(h,w)
    mx,my,old=env['mask'](CAP/f'{frame:03}_OFF_MASK.bin');old=old[y-my:y-my+h,x-mx:x-mx+w]
    outer=exterior(m);holes=parts({(xx,yy)for yy in range(h)for xx in range(w)if not m[yy,xx]and(xx,yy)not in outer})
    records=json.loads(base.with_name(base.name+'_CONTRACT.json').read_text());records['decisions']=decisions(frame);branches=source_branches(frame)
    def empty(xx,yy):return 0<=xx-x<w and 0<=yy-y<h and not bool(m[yy-y,xx-x])
    def isouter(q):return(q[0]-x,q[1]-y)in outer
    checks=[]
    for decision in records['decisions']:
        branch=branches[decision['sourceBranch']];ports=[];transpose=decision['axis']=='x'
        def cells(lo,hi):
            raw=local_cells(branch['geometry'],lo,hi)
            return {(v,u)for u,v in raw}if transpose else raw
        source_domain=cells(decision['sourceLo'],decision['sourceHi'])
        for source_port in branch['ports']:
            if source_port['kind']!='open-mouth':continue
            level,left,right,lid,rid=source_port['values'];toward=-1 if source_port['side']=='start'else 1
            yy=(math.ceil(level)-1)if toward>0 else math.floor(level);mapping=[]
            for xx in range(math.floor(left),math.ceil(right)):
                if min(xx+1,right)<=max(xx,left):continue
                cx,cy=(yy,xx)if transpose else(xx,yy)
                if not empty(cx,cy):continue
                for dx,dy in N4:
                    to=(cx+dx,cy+dy)
                    if to in source_domain or not empty(*to)or not isouter(to):continue
                    mapping.append({'from':[cx,cy],'to':list(to),'sourcePort':source_port,'positiveLeftBoundary':lid,'positiveRightBoundary':rid})
            ports.extend(mapping)
        if not ports and not any(p['kind']=='open-mouth'for p in branch['ports']):continue
        domain=cells(decision['keepLo'],decision['keepHi'])if decision['mode']=='FILL_CAP_KEEP_REMAINDER'else set()
        active={q for q in domain if empty(*q)};components=parts(active);mapped={tuple(z['from'])for z in ports}
        orphan=[c for c in components if not any(isouter(q)for q in c)]
        decision['selectedPortStatus']='MAPPED_EXISTING_GRID_EDGE'if ports else'NO_SELECTED_PORT'
        decision['selectedPortCells']=[(z['from'][1]-y)*w+z['from'][0]-x for z in ports]
        decision['selectedPortMappings']=ports
        checks.append({'branch':decision['sourceBranch'],'axis':decision['axis'],'mode':decision['mode'],'selectedMode':'KEEP_WITH_FILLED_CAP'if active else'FILL_BY_CAP_AND_EXISTING_SPATIAL_CUT','fillRange':[decision['fillLo'],decision['fillHi']],'keepRange':[decision['keepLo'],decision['keepHi']],'mappedPorts':ports,'retainedNegativeCells':sorted(active),'retainedIsolatedComponents':orphan,'allRetainedComponentsMeetMappedPort':all(any(q in mapped for q in c)for c in components)})
    # Every old continuous source ring must still occur unchanged, at its old index.
    curves=base.with_name(base.name+'_CURVES.bin').read_bytes();at=0
    def r(fmt):
        global at
        q=struct.unpack_from('<'+fmt,curves,at);at+=struct.calcsize('<'+fmt);return q[0]if len(q)==1 else q
    newrings=[np.array([r('2d')for _ in range(r('i'))])for _ in range(r('i'))]
    orig=(CAP/f'{frame:03}_ON_CURVES.bin').read_bytes();k=0
    def rr(fmt):
        nonlocal_dummy=None
        global k
        q=struct.unpack_from('<'+fmt,orig,k);k+=struct.calcsize('<'+fmt);return q[0]if len(q)==1 else q
    oldrings=[np.array([rr('2f')for _ in range(rr('i'))])for _ in range(rr('i'))]
    assert all(np.array_equal(a,b)for a,b in zip(oldrings,newrings))
    added=np.argwhere(m&~old);removed=np.argwhere(old&~m)
    row={'frame':frame,'addedRings':records['addedRings'],'addedPoints':records['addedPoints'],'oldSourceRingsUnchanged':True,'addedCells':[[int(xx+x),int(yy+y)]for yy,xx in added],'removedCells':[[int(xx+x),int(yy+y)]for yy,xx in removed],'holes4':[[[xx+x,yy+y]for xx,yy in c]for c in holes],'forelock232_45':empty(232,45)==False if frame in[71,72,73]else None,'canonicalOpenCapContracts':checks,'allAxisDecisionRecords':records['decisions']}
    rows.append(row)
    print(json.dumps({key:row[key]for key in['frame','addedRings','addedPoints','addedCells','removedCells','holes4','forelock232_45']},ensure_ascii=False))
(ROOT/'REVIEW572.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
