"""One bounded spatial mapping gate; not a product selector or temporal code.

Extract ordered return excursions with subcell minor-axis prominence. A
monotone other coordinate identifies a candidate progress span. Test the
explicit OMIT mapping before any graph-cut or Unity integration.
"""
from pathlib import Path
import struct,json,math
import numpy as np
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;D=O/'Order529';D.mkdir(exist_ok=True)
def geometry(f):
    b=(O/'FullLoopB'/f'{f:03d}_ALT_GEOMETRY.bin').read_bytes();at=0;groups=[]
    for _ in range(2):
        count=struct.unpack_from('<i',b,at)[0];at+=4;rings=[]
        for _ in range(count):
            n=struct.unpack_from('<i',b,at)[0];at+=4;rings.append(np.frombuffer(b,'<f4',n*2,at).reshape(n,2).astype(float));at+=n*8
        groups.append(rings)
    return groups[1]
def area(r):return sum(float(a[0]*b[1]-a[1]*b[0])for a,b in zip(r,np.roll(r,-1,axis=0)))*.5
def returns(ring):
    r=np.array(ring,float);n=len(r);out=[];seen=set();sg=1 if area(r)>0 else -1
    for axis in [0,1]:
        for sign in [1,-1]:
            v=r[:,axis]*sign
            for i in range(n):
                if not(v[i]<=v[(i-1)%n]+1e-10 and v[i]<=v[(i+1)%n]+1e-10 and min(v[(i-1)%n]-v[i],v[(i+1)%n]-v[i])>=-1e-10 and max(v[(i-1)%n]-v[i],v[(i+1)%n]-v[i])>1e-10):continue
                peaks=[]
                for direction in [-1,1]:
                    k=i
                    for _ in range(n-1):
                        q=(k+direction)%n
                        if v[q]<v[k]-1e-10:break
                        k=q
                    peaks.append(v[k])
                level=min(peaks);depth=level-v[i]
                if not(1e-9<depth<1):continue
                paths=[]
                for direction in [-1,1]:
                    path=[r[i]];k=i
                    for _ in range(n):
                        q=(k+direction)%n
                        if v[q]>=level-1e-10:
                            t=(level-v[k])/(v[q]-v[k]);path.append(r[k]+t*(r[q]-r[k]));break
                        path.append(r[q]);k=q
                    else:raise AssertionError('No bounded return')
                    paths.append(path)
                arc=list(reversed(paths[0]))+paths[1][1:]
                q=np.array(arc);d=np.diff(q[:,1-axis]);progress=bool(np.all(d>=-1e-9)and np.any(d>1e-9)or np.all(d<=1e-9)and np.any(d<-1e-9))
                if not progress:continue
                ear=area(q)
                if ear*sg<=1e-9:continue # region OMIT, no arbitrary inward filling
                key=(axis,tuple(np.round(q[0],8)),tuple(np.round(q[-1],8)))
                if key in seen:continue
                seen.add(key)
                out.append({'axis':axis,'sign':sign,'minorDepth':float(depth),'majorExtent':float(np.ptp(q[:,1-axis])),
                            'earArea':abs(ear),'arc':q.tolist(),'shortcut':[q[0].tolist(),q[-1].tolist()],
                            'mapping':'OMIT_SUBCELL_RETURN','rule':'depth<1 logicalcell; other-axis ordered progress; region-side ear; no time/history'})
    return out
def relevant(e,box):
    p=np.array(e['arc']);return bool(p[:,0].max()>=box[0]and p[:,0].min()<=box[2]and p[:,1].max()>=box[1]and p[:,1].min()<=box[3])
actual=[]
for f in [42,43,44]:
    candidates=[e for ring in geometry(f)for e in returns(ring)]
    picked=[e for e in candidates if relevant(e,(200,98,201,100))]
    actual.append({'frame':f,'totalReturnSpans':len(candidates),'target43Spans':picked})
diagonal=[]
for f in [43,44,45]:
    picked=[e for ring in geometry(f)for e in returns(ring)if relevant(e,(230.8,77.9,232.1,79.1))]
    diagonal.append({'frame':f,'target44Spans':picked})
# A stable, intentional thin appendage attached to a broad garment. Its
# visible projected end has .75cell width and 3cell height (2.25cell area),
# rather than being an isolated texel or a tiny polygon component.
thin=np.array([[0,0],[4,0],[4,8],[0,8],[0,5],[-.75,5],[-.75,2],[0,2]],float)
thinCandidates=[e for e in returns(thin)if relevant(e,(-.8,1.9,0,5.1))]
tests=[]
for turns in range(4):
    c,s=math.cos(turns*math.pi/2),math.sin(turns*math.pi/2);m=np.array([[c,-s],[s,c]])
    r=thin@m.T;cs=returns(r)
    # Collinear subdivision is geometrically identical and must not provide
    # missing feature significance. No phase/model exception is used.
    sub=np.array([p for a,b in zip(r,np.roll(r,-1,axis=0))for p in [a,(a+b)*.5]])
    tests.append({'quarterTurns':turns,'originalSpanCount':len(cs),'subdividedSpanCount':len(returns(sub)),
                  'intendedThinEndWouldBeOmitted':any(abs(e['earArea']-2.25)<1e-6 for e in cs)})
paired=np.array([[0,0],[4,0],[4,11],[0,11],[0,10],[-.75,10],[-.75,7],[0,7],[0,4],[-.75,4],[-.75,1],[0,1]],float)
pairedCandidates=returns(paired)
pairedTests=[]
for turns in range(4):
    c,s=math.cos(turns*math.pi/2),math.sin(turns*math.pi/2);m=np.array([[c,-s],[s,c]]);r=paired@m.T;cs=returns(r)
    sub=np.array([p for a,b in zip(r,np.roll(r,-1,axis=0))for p in [a,(a+b)*.5]])
    pairedTests.append({'quarterTurns':turns,'originalSpanCount':len(cs),'subdividedSpanCount':len(returns(sub)),
                        'intendedThinEndWouldBeOmitted':any(abs(e['earArea']-2.25)<1e-6 for e in cs)})
thinFailed=any(t['intendedThinEndWouldBeOmitted']for t in tests+pairedTests)
result={'status':'MINIMAL_MAPPING_GATE_FAILED_NORMAL_THIN_END'if thinFailed else'MINIMAL_MAPPING_GATE_PASS_NEEDS_PIXEL_SELECTOR_VALIDATION','newUnityCalls':0,'newCaptures':0,'productChange':False,
        'reused':'ordered Vector2 closed rings; HeadRegion502.Boundaries orientation/cycle convention; no arc-DP/time bank',
        'candidate':'curve return span -> explicit OMIT chord;1logicalcell resolution bound, not fitted to frame43',
        'actual43':actual,'actual44':diagonal,'thinEnd':{'polygon':thin.tolist(),'candidateSpans':thinCandidates,'orientationAndSubdivisionTests':tests},
        'pairedThinEnds':{'polygon':paired.tolist(),'candidateSpans':pairedCandidates,'orientationAndSubdivisionTests':pairedTests},
        'checks':{'actual43TargetMapped':all(x['target43Spans']for x in actual),
                  'actual44Unmodified':all(not x['target44Spans']for x in diagonal),
                  'normalThinPreserved':not thinFailed},
        'noPixelSelectorProduced':'normal-thin precondition failed, so no graphcut/product application or Unity capture',
        'missingInformation':'ordered curve alone has no protected-feature/endcap provenance or explicit keep/omit design decision; passing direction alone still admits source return'}
(D/'MINIMAL_GATE529.json').write_bytes(json.dumps(result,indent=2).encode())
# Small mathematical evidence plot; this is not an edited game capture.
img=Image.new('RGB',(1050,430),'white');draw=ImageDraw.Draw(img)
cases=[('actual Walk43 / candidate omitted arc',geometry(43)[0],actual[1]['target43Spans'],(198,95,204,103)),
       ('normal Walk44 / monotone staircase',geometry(44)[0],[],(229,76,235,83)),
       ('two normal thin ends / rule FAILS',paired,pairedCandidates,(-1.3,1,4.7,10))]
for k,(title,r,es,box)in enumerate(cases):
    x0,y0,x1,y1=box;sc=36;ox=k*350+34;oy=50
    xy=lambda p:(ox+(p[0]-x0)*sc,oy+(p[1]-y0)*sc)
    for x in range(math.ceil(x0),math.floor(x1)+1):draw.line([xy((x,y0)),xy((x,y1))],fill='#eeeeee')
    for y in range(math.ceil(y0),math.floor(y1)+1):draw.line([xy((x0,y)),xy((x1,y))],fill='#eeeeee')
    for a,b in zip(r,np.roll(r,-1,axis=0)):
        if min(a[0],b[0])<=x1 and max(a[0],b[0])>=x0 and min(a[1],b[1])<=y1 and max(a[1],b[1])>=y0:draw.line([xy(a),xy(b)],fill='#1762a0',width=3)
    for e in es:
        for a,b in zip(e['arc'],e['arc'][1:]):draw.line([xy(a),xy(b)],fill='#bb4444',width=4)
        draw.line([xy(e['shortcut'][0]),xy(e['shortcut'][1])],fill='#cc8800',width=3)
    draw.rectangle((k*350,0,(k+1)*350,45),fill='white');draw.text((k*350+10,8),title,fill='black')
draw.text((10,405),'blue=current vector; red=identified return; orange=OMIT shortcut. Not a product output.',fill='black')
img.save(D/'THREE_CASE_GATE529.png')
print(json.dumps({'status':result['status'],'checks':result['checks'],'actual43':[{'frame':r['frame'],'spans':len(r['target43Spans']),'areas':[e['earArea']for e in r['target43Spans']]}for r in actual],'actual44':[len(r['target44Spans'])for r in diagonal],'singleThinTests':tests,'pairedThinTests':pairedTests}))
