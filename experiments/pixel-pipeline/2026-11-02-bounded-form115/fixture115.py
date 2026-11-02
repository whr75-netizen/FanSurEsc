"""Frozen F103 source inputs for exactly two owner2 layouts, not winner replay."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,sys
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent;P=R/'argon23-runtime113';F=R/'gpu-form115';T=R/'eye-failures114'
sys.path[:0]=[str(P),str(T)]
from inputs113 import load_packets,buffer
from tie114 import transport
F32=np.float32;MIN=F32(np.finfo(np.float32).tiny)
def exact(x):return np.array([x,x],np.float32)
def down(x):return -MIN if abs(x)<=MIN else np.nextafter(F32(x),F32(-np.inf))
def up(x):return MIN if abs(x)<=MIN else np.nextafter(F32(x),F32(np.inf))
def add(a,b):
    if not np.any(a):return b.copy()
    if not np.any(b):return a.copy()
    return np.array([down(F32(a[0]+b[0])),up(F32(a[1]+b[1]))],np.float32)
def mul(a,b):
    if not np.any(a)or not np.any(b):return np.zeros(2,np.float32)
    values=[F32(x*y)for x in a for y in b];return np.array([down(min(values)),up(max(values))],np.float32)
def main():
    assert not(H/'FIXTURE115.json').exists(),'Frozen fixture must not be overwritten'
    source=json.loads((P/'SOURCE113.json').read_text());reg=json.loads((T/'REGISTRATION_CURRENT102.json').read_text());reference=json.loads((F/'REFERENCE115.json').read_text());row=next(r for r in reference['rows']if r['frame']==103);eye=row['eyes'][1];assert eye['owner']==2 and len(eye['masks'])==2 and eye['selectedIndices']==[1]
    _,packets=load_packets(P);entry,path=next((e,p)for e,p in packets if e['frame']==103);meta=json.loads((path/'RAW_MANIFEST.json').read_text());w,h=(int(x)//4 for x in meta['forward102']['canonicalSize']);n=w*h;k=len(source['keys']);assert(n,k,w,h)==(144,20,18,8)
    keys=np.zeros((k,12),'<f4');lookup={}
    for index,key in enumerate(source['keys']):
        identity=(key['owner'],key['part'],key['x'],key['y']);lookup[identity]=index;keys[index]=[key['x'],key['y'],key['owner'],key['part'],*key['linear'],1,key['componentBit'],*key['RGB8']]
    stats=np.zeros((n,k,2,4),np.float32);exact_stats={}
    for owner in [1,2]:
        _,_,_,records=transport(path,owner,reg,source)
        for r in sorted(records,key=lambda a:(a['fineYX'][0],a['fineYX'][1],a['part'])):
            key=lookup[tuple(r['sourceKeys'][0])];y,x=r['cellYX'];fy,fx=r['fineYX'];cell=y*w+x;weight=Fraction(r['certainWeight']);a=stats[cell,key];p=[Fraction(2*fx+1,16),Fraction(2*fy+1,16)]
            values=[exact(F32(float(weight))),mul(exact(F32(float(weight))),exact(F32(float(p[0])))),mul(exact(F32(float(weight))),exact(F32(float(p[1]))))]
            for d in range(3):v=add(a[:,d],values[d]);a[:,d]=v;a[0,d]=max(a[0,d],0)if d==0 else a[0,d]
            v=exact_stats.setdefault((cell,key),[Fraction(0),Fraction(0),Fraction(0)]);v[0]+=weight;v[1]+=weight*p[0];v[2]+=weight*p[1]
    for (cell,key),values in exact_stats.items():
        for d,v in enumerate(values):assert Fraction(float(stats[cell,key,0,d]))<=v<=Fraction(float(stats[cell,key,1,d]))
    refs=np.zeros((k,2,4),np.float32)
    for key in range(k):
        for cell in range(n):
            for d in range(3):v=add(refs[key,:,d],stats[cell,key,:,d]);refs[key,:,d]=v;refs[key,0,d]=max(v[0],0)if d==0 else v[0]
    # Row-major low4/high4 matches Stat115, not interleaved component intervals.
    frame=buffer(path/'REGION113-frame.f32').view('<u4').reshape(2,32,4)[[1,0]].copy();points=buffer(path/'REGION113-points.f32').view('<u4').reshape(2,24,4)[[1,0]].copy()
    tags=buffer(path/'REGION113-tags.f32').view('<u4').reshape(512,4)[:n].copy();best=buffer(path/'REGION113-best.f32').reshape(2,12)[[1,0]].copy();candidates=np.array([[a,b,0,0]for a,b in eye['masks']],'<u4')
    assert frame[0,0,0]==9 and frame[0,0,1]+frame[0,0,2]==11 and frame[0,0,3]==0
    assert np.all(points[0,:9,0]<n)and int(np.bitwise_or.reduce(candidates[:,:2].ravel()))<(1<<9)
    blobs={'keys':keys,'moments':stats,'references':refs,'frame':frame,'points':points,'tags':tags,'best':best,'candidates':candidates}
    files={}
    for name,a in blobs.items():
        data=a.tobytes();p=H/(name+'.bin')
        with p.open('xb')as f:f.write(data)
        files[name]={'file':p.name,'bytes':len(data),'SHA256':hashlib.sha256(data).hexdigest()}
    expected=[]
    for vector in eye['details']['sourceFormDimensions']:
        expected.append([vector['1'],vector['4'],str(Fraction(vector['1:missingSourcePairs'])*6),vector['1:relativeGeometry'],str(Fraction(vector['4:missingSourcePairs'])*15),vector['4:relativeGeometry']])
    assert all(v is not None for row in expected for v in row)
    fixture={'schema':'bounded-form115/frozen-source/v1','sourceId':entry['sourceId'],'frame':103,'mainSerial':meta['mainSerial'],'originalOwnerId':2,'diagnosticLogicalSlot':0,'slotMap':[2,1],'slotPermutationOnly':True,'sourceGenerationIsCPUReferenceNotGPUPartOfThisTest':True,'originalPointsYX':eye['pointsYX'],'masks':eye['masks'],'CPUReferenceWinners':eye['selectedIndices'],'expectedRationalMetrics':expected,'expectedDoubleMetrics':[[float(Fraction(x))for x in r]for r in expected],'width':w,'height':h,'cells':n,'keyCount':k,'pointCount':9,'candidateCount':2,'files':files,'shaderPath':'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye115.compute','shaderSHA256':hashlib.sha256((F/'ForwardEye115.compute').read_bytes()).hexdigest(),'stages':[{'kernel':'BeginForm115','groups':[2,1,1],'threads':2},{'kernel':'EvaluateForm115','groups':[2,1,1],'threads':2},{'kernel':'Pareto115','groups':[1,1,1],'threads':1}],'noBVHOrEnumerationOrPlay':True,'noWinnerInput':True}
    (H/'FIXTURE115.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'sourceId':entry['sourceId'],'slots':fixture['slotMap'],'points':9,'keys':k,'candidateMasks':eye['masks'],'inputBytes':sum(f['bytes']for f in files.values()),'expectedRationalMetrics':expected,'GPUSubmissions':0},ensure_ascii=False))
if __name__=='__main__':main()
