"""Saved-input AB factorial test. No Unity, capture, GC or project mutation."""
from pathlib import Path
import ast,collections,hashlib,json,math,sys,types
import numpy as np
from PIL import Image,ImageDraw
from candidate49 import CachedCell,StateBoundCluster,projected_anchor,place_visible,family_shape

R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def defs(path,name,initial=None):
    module=types.ModuleType(name);sys.modules[name]=module
    module.__dict__.update(dict(np=np,math=math,Path=Path,json=json,hashlib=hashlib,collections=collections))
    module.__dict__.update(initial or {})
    tree=ast.parse(path.read_text(encoding='utf8'));tree.body=[a for a in tree.body if isinstance(a,(ast.FunctionDef,ast.ClassDef))]
    exec(compile(tree,str(path),'exec'),module.__dict__)
    return module
eye=defs(R/'lib/eye_cache42.py','frozen49_eye')
old=defs(R/'lib/counts47.py','frozen49_counts',{'classify':eye.classify})
checks=[]
def check(name,ok):
    if not bool(ok):raise AssertionError(name)
    checks.append(name)
def scalar(o):
    if isinstance(o,np.generic):return o.item()
    if isinstance(o,np.ndarray):return o.tolist()
    raise TypeError(type(o).__name__)
def write(name,obj):(R/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=scalar),encoding='utf8')
manifest=load(R/'INPUT_MANIFEST.json')
for f in manifest['inputs']:check('frozen SHA256 '+f['file'],hashlib.sha256((R/f['file']).read_bytes()).hexdigest()==f['sha256'])
meta=load(R/'fixtures/frames.json');arrays=np.load(R/'fixtures/replay-inputs.npz')
want=load(R/'fixtures/expected47.json');template=load(R/'fixtures/template43.json')
cells=[CachedCell(c['cellId'],c['eye'],c['role'],tuple(c['referenceXY']),tuple(c['rgba8']))for c in template['cells']]
key=hashlib.sha256(json.dumps(template['productSHA256'],sort_keys=True).encode()).hexdigest()
state='Template216:open:TRANSLATION_PROBE_ONLY'
cluster=StateBoundCluster(key,state,template['referenceAnchorCellCentre'],cells,meta[0]['styleJson'])
fixed=np.array([c.reference for c in cells]);state_rejections=[]
for bad_key,bad_state in [(key+'source-change',state),(key,state+'blink50'),(key,state+'blink100'),(key,state+'rotation-unregistered')]:
    try:cluster.place(bad_key,bad_state,[219.5,53])
    except ValueError as e:state_rejections.append(str(e))
check('source/style/unregistered lid/rotation reject, no open-eye substitute',len(state_rejections)==4)
reverse=StateBoundCluster(key,state,template['referenceAnchorCellCentre'],list(reversed(cells)))
def as_ids(rows):return {r['cellId']:(tuple(r['xy']),tuple(r['rgba8']))for r in rows}
check('source cell traversal order does not change placement',as_ids(cluster.place(key,state,[219.6,53.1])[0])==as_ids(reverse.place(key,state,[219.6,53.1])[0]))
smaller=StateBoundCluster(key,state,template['referenceAnchorCellCentre'],cells[:-1])
check('no minimum cell count or refill in generic adapter',len(smaller.place(key,state,[219.6,53.1])[0])==len(cells)-1)

def native_line(packet,m,eye,iris):
    """Exact NativeLineAllocated19 decision; curveChoice/complete Evaluate not fabricated."""
    c=packet[eye];I=(c[...,2]+c[...,3])+c[...,4];h,w=I.shape
    white=(c[...,1]>=1)&((np.pad(I,((0,0),(1,1)))[:,:w]>0)|(np.pad(I,((0,0),(1,1)))[:,2:]>0))
    white_count=int(white.sum());area=np.float32(0)
    for y in range(h-1,-1,-1):
        for x in range(w):area=np.float32(area+np.float32(c[y,x,5]/16))
    cand=[(x,y)for y in range(h-1,-1,-1)for x in range(w)if c[y,x,5]>0 and not(white_count==1 and white[y,x])and(x,y)not in iris]
    costs=np.maximum(c[...,1],I)-c[...,5]
    cand.sort(key=lambda p:(float(costs[p[1],p[0]]),-p[1],p[0]))
    return set(cand[:math.floor(float(np.float32(area+.5)))])

def diagram(points,m):
    im=Image.new('RGBA',(m['width']*2,m['height']*2))
    d=ImageDraw.Draw(im)
    for eye,p in points.items():
        colour=(235,110,90,255)if eye==1 else(80,190,220,255)
        for x,y in p:d.rectangle((x*2,y*2,x*2+1,y*2+1),fill=colour)
    return im
def layer(rows,m,visible_only):
    im=Image.new('RGBA',(m['width']*2,m['height']*2));d=ImageDraw.Draw(im)
    for row in rows:
        if visible_only and not row['visible']:continue
        x,y=row['xy'][0]-m['x'],row['xy'][1]-m['y']
        check('cache placement remains within captured ROI',0<=x<m['width']and 0<=y<m['height'])
        d.rectangle((x*2,y*2,x*2+1,y*2+1),fill=tuple(row['rgba8']))
    return im
def checker(im):
    bg=Image.new('RGBA',im.size)
    for y in range(im.height):
        for x in range(im.width):bg.putpixel((x,y),(28,32,39,255)if(x//2+y//2)%2 else(42,47,55,255))
    return Image.alpha_composite(bg,im).convert('RGB')

records=[];max_error=0;gate_changes=[];frame_images=[];phase_shapes=set();phase_count=0
for i,m in enumerate(meta):
    d={k.split('_',1)[1]:arrays[k]for k in arrays.files if k.startswith(f'f{i:02}_')and not k.endswith('_GPU')}
    gpu=arrays[f'f{i:02}_GPU'];replayed,depth=old.replay_packets(m,d)
    error=float(np.abs(replayed-gpu).max());max_error=max(error,max_error)
    check(f"{m['frame']}: full frozen GPU packets exact prior replay tolerance",error==want[i]['maxFullPacketCPUvsGPUError'])
    check(f"{m['frame']}: original open lid is measured",m['blinkWeight']==0 and m['layerMode19'])
    for change in ({'blinkWeight':50.},{'blinkWeight':100.},{'styleJson':m['styleJson']+'changed'}):
        try:place_visible(cluster,key,state,dict(m,**change),d,True)
        except ValueError:pass
        else:raise AssertionError('Changed physical lid/style accepted as registered open state')
    rows,shift,anchor,centres=place_visible(cluster,key,state,m,d,True)
    sample_rows,_,_,_=place_visible(cluster,key,state,m,d,False)
    check(f"{m['frame']}: all cached IDs/relative cells/colours stay literal",all(r['cellId']==c.identity and tuple(np.array(r['xy'])-shift)==c.reference and tuple(r['rgba8'])==c.rgba8 for r,c in zip(rows,cells)))
    check(f"{m['frame']}: source family and eye never borrowed",all(not r['representative']or r['representative']['source']==(2 if r['role']==1 else 1)for r in rows))
    check(f"{m['frame']}: final gate only removes, never refills",{r['cellId']for r in rows if r['visible']}<={r['cellId']for r in sample_rows if r['visible']})
    check(f"{m['frame']}: hidden cached rows never emitted",all(not r['visible']for r in rows if r['knownFinalBlocks']))
    rec=dict(sourceId=m['sourceId'],frame=m['frame'],projectedAnchor=anchor.tolist(),projectedEyeCentres={str(k):v.tolist()for k,v in centres.items()},shift=shift.tolist(),eyes={},cells=rows)
    a={};b={};c={};e={}
    for eye_index in range(2):
        stable=round(m['centres'][eye_index]['w']);actual=d['eye-visible']
        a[stable]=[(int(x),int(y))for y,x in np.argwhere((np.rint(actual[...,1])==stable)&np.isin(np.rint(actual[...,0]),[2,3,4]))]
        original,_,budget,area,I,cost=old.allocator(gpu,m,eye_index)
        gate=old.final_gate(d,depth[eye_index]);trial,*_=old.allocator(gpu,m,eye_index,gate)
        b[stable]=trial
        c[stable]=[(r['xy'][0]-m['x'],r['xy'][1]-m['y'])for r in sample_rows if r['eye']==stable and r['role']==1 and r['visible']]
        e[stable]=[(r['xy'][0]-m['x'],r['xy'][1]-m['y'])for r in rows if r['eye']==stable and r['role']==1 and r['visible']]
        if original!=trial:gate_changes.append([m['frame'],stable])
        line_before=native_line(gpu,m,eye_index,set(original));line_gate=native_line(gpu,m,eye_index,set(trial))
        line_joint=native_line(gpu,m,eye_index,set(c[stable]));line_combined=native_line(gpu,m,eye_index,set(e[stable]))
        line_conflicts=[r['xy']for r in rows if r['eye']==stable and r['visible'] and round(float(actual[r['xy'][1]-m['y'],r['xy'][0]-m['x'],0]))in[5,6,7]]
        ids=lambda p:[[x+m['x'],y+m['y']]for x,y in sorted(p)]
        rec['eyes'][str(stable)]=dict(actualVisibleIris=ids(a[stable]),oldAllocated=ids(original),gateOnly=ids(trial),
            referencePlannedIris=[r['xy']for r in rows if r['eye']==stable and r['role']==1],
            jointAfterSourceVisibility=ids(c[stable]),jointAfterKnownFinalGate=ids(e[stable]),
            budget=budget,area=area,referenceShape=[list(p)for p in family_shape(rows,stable)],
            visibleShape=[list(p)for p in family_shape(rows,stable,True)],
            nativeLineGateSymmetricDifference=ids(line_before^line_gate),nativeLineJointSymmetricDifference=ids(line_before^line_joint),
            nativeLineCombinedSymmetricDifference=ids(line_before^line_combined),
            nativeLineOriginal=ids(line_before),nativeLineGateOnly=ids(line_gate),nativeLineJoint=ids(line_joint),nativeLineCombined=ids(line_combined),
            actualLashOrLowerLidConflicts=line_conflicts)
    # Pure phase is an analytic rigid-translation test. Visibility is a separate experiment.
    for py in range(33):
        for px in range(33):
            out,t,delta=cluster.place(key,state,anchor,np.array([px/32,py/32]))
            q=np.asarray([r['xy']for r in out]);check('phase relative topology invariant',np.array_equal(q-t,fixed))
            check('phase snap maximum half-cell per axis',np.max(abs(t-delta))<=.5000000001)
            phase_shapes.add(tuple(map(tuple,q-q[0])));phase_count+=1
    records.append(rec)
    actual=Image.open(R/f'fixtures/actual-{m["frame"]}.png').convert('RGBA')
    pics=[actual,diagram(a,m),diagram(b,m),layer(rows,m,False),layer(rows,m,True)]
    frame_images.append(pics)
    layer(rows,m,False).save(R/f'frame{m["frame"]}-joint-before-visibility.png')
    layer(rows,m,True).save(R/f'frame{m["frame"]}-joint-known-visible.png')
    # Synthetic full occlusion tests the composition contract, not measured geometry.
    hidden=dict(d);hidden['hair-meta']=d['hair-meta'].copy();hidden['hair-meta'][...]=[1,12,1,1]
    blocked,_,_,_=place_visible(cluster,key,state,m,hidden,True)
    check(f"{m['frame']}: all-front hair hides every supported cached cell without relocation",not any(r['visible']for r in blocked))

check('gate-only reproduces exactly the prior one-eye/frame change',gate_changes==[[100,1]])
check('common snap has one relative layout over every tested phase',len(phase_shapes)==1)
check('template has no upper lash key form; do not claim it was tested',template['role6Absent'])
W,H=frame_images[0][0].size
strip=Image.new('RGB',(6*W,5*H))
for x,pics in enumerate(frame_images):
    for y,im in enumerate(pics):strip.paste(checker(im),(x*W,y*H))
strip.save(R/'comparison-1x.png');strip.resize((strip.width*8,strip.height*8),Image.Resampling.NEAREST).save(R/'comparison-8x.png')
summary=dict(sequenceId=meta[0]['sequenceId'],baselineCommits=['1835f10','6c31438'],frames=[m['frame']for m in meta],
    maxFullPacketError=max_error,gateOnlyChangedEyeFramePairs=gate_changes,purePhasePlacements=phase_count,
    purePhaseRelativeLayouts=len(phase_shapes),referenceCells=len(cells),referenceIrisCellsByEye={str(e):sum(c.eye==e and c.role==1 for c in cells)for e in[1,2]},
    actualIrisCounts={str(e):[len(r['eyes'][str(e)]['actualVisibleIris'])for r in records]for e in[1,2]},
    jointSourceVisibleIrisCounts={str(e):[len(r['eyes'][str(e)]['jointAfterSourceVisibility'])for r in records]for e in[1,2]},
    jointKnownFinalVisibleIrisCounts={str(e):[len(r['eyes'][str(e)]['jointAfterKnownFinalGate'])for r in records]for e in[1,2]},
    referenceScleraCells=sum(c.role==4 for c in cells),
    sourceSupportedScleraCounts=[sum(c['role']==4 and c['visible']for c in r['cells'])for r in records],
    rejectedPhysicalLidStyleTests=18,
    nativeLineIndirectChangedPairs=[dict(frame=r['frame'],eye=e,xy=d['nativeLineCombinedSymmetricDifference'])for r in records for e,d in r['eyes'].items()if d['nativeLineCombinedSymmetricDifference']],
    knownLidConflicts=[dict(frame=r['frame'],eye=e,xy=d['actualLashOrLowerLidConflicts'])for r in records for e,d in r['eyes'].items()if d['actualLashOrLowerLidConflicts']],
    GPUCompiled=False,GPUIntegrated=False,finalCandidateFaceRGBAReconstructed=False,newUnityCalls=0,
    productionReady=False,missing='registered pose/lid design forms; template lacks upper-line role; complete GPU compositor/occlusion A/B',
    checks=len(checks),stateRejections=state_rejections)
write('RESULTS.json',records);write('SUMMARY.json',summary);write('TESTS.json',dict(passed=len(checks),checks=checks))
print(json.dumps(summary,ensure_ascii=False,indent=2,default=scalar))
