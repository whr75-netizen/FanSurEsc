"""Frozen frame100/101 joint allocation, composited diagnostic PNGs.

Only writes this experiment directory. Does not invoke Unity or any UI.
"""
from pathlib import Path
import collections,copy,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
from joint53 import enumerate_joint,glyph_signature,connected_components
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';F=R.parent/'whole-eye52';L=R.parent/'lid-evidence51'
sys.path[:0]=[str(B),str(F)]
from candidate49 import known_final_occlusion,projected_anchor
from whole52 import native_representative,barycentric
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def default(v):return v.tolist()if isinstance(v,np.ndarray)else v.item()
def dump(n,d):(R/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=default),encoding='utf8')
checks=[]
def check(n,v):
    if not v:raise AssertionError(n)
    checks.append(n)
for f in load(F/'OUTPUT_MANIFEST.json')['files']:check('immutable52 '+f['path'],sha(F/f['path'])==f['sha256'])
for f in load(B/'PACKAGE_MANIFEST.json')['files']:check('immutable49 '+f['path'],sha(B/f['path'])==f['sha256'])
metas=load(B/'fixtures/frames.json');arrays=np.load(B/'fixtures/replay-inputs.npz');old=load(L/'APERTURE_RESULTS.json')
whole=load(F/'WHOLE_KEYFORM52.json');surfaces=np.load(F/'SOURCE_SURFACES52.npz')
data={m['frame']:{k.split('_',1)[1]:arrays[k]for k in arrays.files if k.startswith(f'f{i:02}_')and not k.endswith('_GPU')}for i,m in enumerate(metas)}
by_frame={m['frame']:m for m in metas};probe_frames=[100,101]
record_by_frame={r['frame']:r for r in old}
known_sources={by_frame[f]['sourceId']for f in probe_frames}
eye=1;reference_frame=101;mref=by_frame[reference_frame]
source_line=load(R.parent/'eye-composition50'/'RESULTS.json')[-1]['eyes']['1']['sourceLid']
check('registered source lid is measured, not an invented global size',len(source_line)>0)
check('reference source is fully open actual mode',mref['blinkWeight']==0 and mref['layerMode19'])
# Use the observed native role/colour only where the independent eye identity
# actually says native-upper-lid. This is cached FINAL reference colour, not a
# reconstructed unlit source or a guessed S3 shader result.
native=[]
for xy in source_line:
    x,y=xy[0]-mref['x'],xy[1]-mref['y'];visible=data[101]['eye-visible'][y,x]
    check('source pigment is observed native part',round(float(visible[0]))==5 and round(float(visible[1]))==eye)
    im=Image.open(B/f'fixtures/actual-{reference_frame}.png').convert('RGBA')
    rgba=list(im.getpixel((x*2,y*2)))
    row=dict(xy=xy,eye=eye,role=6);rep=native_representative(data[101],mref,row,known_final_occlusion)
    check('native reference has actual surviving source geometry',rep.get('support',False))
    k=rep['k'];xx=x*4+k%4;yy=y*4+3-k//4
    raw=(R.parent/'continuous47-counts'/'frames'/'05'/'S3UV.bin').read_bytes();w,h=struct.unpack_from('<ii',raw)
    u=np.frombuffer(raw,'<f4',offset=8).reshape(h,w,4)[::-1][yy,xx]
    primitive=round(float(u[2]))-1;ids=surfaces['native_role6_tri'][primitive]
    p=data[101]['S3POINT'][yy,xx,:3];bary,err=barycentric(p,surfaces['native_xyz_head'][ids])
    check('native reference triangle proof',err<1e-6 and bary.min()>-1e-4)
    native.append(dict(id=f'eye1:native6:source101:primitive{primitive+1}',eye=eye,role=6,part='upper-lid',xy=xy,
        rgba8=rgba,provenance=dict(kind='measured native part, cached final reference pigment',sourceId=mref['sourceId'],
            outputXY=xy,feature=5,sourceLayer=3,primitive=primitive+1,UV=u[:2].tolist(),barycentric=bary.tolist(),
            restHeadPoint=p.tolist(),pointError=err,pigmentFrame=101,pigmentIsUnlit=False,sourceWeight=rep['weight'])))

template=whole['states']['existing-open-reference']['cells']
input_rows=[copy.deepcopy(r)for r in record_by_frame[101]['registered51']if r['eye']==eye]
glyphs={'iris':[],'sclera':[],'upper-lid':native}
for row in input_rows:
    src=next(v for v in template if v['cellId']==row['cellId'])
    glyphs[src['part']].append(dict(id=row['cellId'],eye=eye,role=row['role'],part=src['part'],xy=row['xy'],
        rgba8=row['rgba8'],provenance=src['source']))

# Both frozen source frames have the same registered style/open state and
# common anchor translation. This offline cohort is explicit, not a claim of
# a causal runtime optimiser or a key form for unknown poses.
root_shifts=[];source_visible={};depths={};native_reps={}
for frame in probe_frames:
    m=by_frame[frame];check('open registered source frame',m['blinkWeight']==0 and m['styleJson']==mref['styleJson'])
    anchor,_=projected_anchor(m);shift=np.floor(anchor-np.array(whole['referenceAnchor'])+.5).astype(int);root_shifts.append(shift)
    rows=record_by_frame[frame]['registered51'];vis={};dep={}
    for r in rows:
        if r['eye']!=eye:continue
        vis[r['cellId']]=r['visible'];rep=r['representative'];dep[r['cellId']]=float(rep.get('depth',0))
    native_reps[frame]=[]
    for r in native:
        rep=native_representative(data[frame],m,dict(xy=r['xy'],eye=eye),known_final_occlusion)
        check('registered native part exists in each probe without area-budget rounding',rep.get('support',False))
        native_reps[frame].append(rep);vis[r['id']]=bool(rep.get('support'));dep[r['id']]=float(rep.get('depth',0))
    source_visible[frame]=vis;depths[frame]=dep
check('cohort has one whole-eye anchor shift',all(np.array_equal(root_shifts[0],s)for s in root_shifts))
shift=root_shifts[0]
form=next(e for e in whole['states']['existing-open-reference']['eyes']if e['eye']==eye)
source_paths={
    'iris':dict(points=(np.array(form['iris'])+shift).tolist(),closed=True,region=True),
    'sclera':dict(points=(np.array(form['parent'])+shift).tolist(),closed=True,region=True),
    'upper-lid':dict(points=(np.array(form['nativeUpperPath'])+shift).tolist(),closed=False,region=False)}
original_occupied={tuple(r['xy'])for group in glyphs.values()for r in group}
growth_occlusion_records=[]
def external(frame,r,xy):
    m=by_frame[frame];x,y=xy[0]-m['x'],xy[1]-m['y']
    if not(0<=x<m['width']and 0<=y<m['height']):return ['outside captured ROI']
    depth=depths[frame][r['id']]
    veto=known_final_occlusion(data[frame],m,xy,depth)
    if tuple(xy)not in original_occupied:
        # A new feature cell may look free in the final winner mask while
        # intersecting a real, nearer hair fragment in the saved4x source.
        # Reject new footprint growth over that evidence. This is a scoped
        # offline feasibility constraint, not a new product monitoring pass.
        for key in['S4META','S5META','S6META']:
            a=data[frame][key][y*4:(y+1)*4,x*4:(x+1)*4]
            front=(a[...,0]>0)&(a[...,1]>.5)&(a[...,3]>1e-6)&(a[...,0]<depth)
            if np.any(front):veto.append(f'new-cell source occlusion {key}: {int(front.sum())}/16')
    return veto

zero=enumerate_joint(glyphs,source_paths,0,external,source_visible)
result=enumerate_joint(glyphs,source_paths,1,external,source_visible)
check('zero correction budget reproduces exact collision infeasibility',zero['feasible']==0)
check('bounded joint solution exists',result['feasible']>0)
selected=result['rows'];check('selected part ownership is disjoint',len({tuple(r['xy'])for r in selected})==len(selected))
original={r['id']:r for group in glyphs.values()for r in group}
check('all source part identities preserved, no count minimum or deletion',set(original)=={r['id']for r in selected})
check('pigment provenance not changed',all(r['rgba8']==original[r['id']]['rgba8']and r['provenance']==original[r['id']]['provenance']for r in selected))
check('whole glyph remains connected',len(connected_components([r['xy']for r in selected]))==1)
for part,rows in glyphs.items():
    source_edges={tuple(np.array(a['xy'])-b['xy'])for a in rows for b in rows}
    out=[r for r in selected if r['part']==part]
    check('within-part shape exactly retained '+part,source_edges=={tuple(np.array(a['xy'])-b['xy'])for a in out for b in out})
check('one-cell L1 displacement bound is visible',all(sum(abs(v)for v in r['partShift'])<=1 for r in selected))
reordered=enumerate_joint(dict(reversed(list(glyphs.items()))),source_paths,1,external,source_visible)
check('part iteration order has no winner priority',reordered['selected']['shifts']==result['selected']['shifts'])

# A second explicit trade-off keeps the measured lid in place and moves the
# other glyphs jointly. It is NOT an automatic retry/fallback or selected output.
lid_fixed=[t for t in result['trials']if t['feasible']and t['shifts']['upper-lid']==[0,0]]
lid_fixed.sort(key=lambda t:(t['movementPerPart'],t['curveError'],t['relativeCentreError'],t['boundingAreaChange'],sorted(t['shifts'].items())))
alternative=[]
if lid_fixed:
    for p,group in glyphs.items():
        for src in group:
            r=copy.deepcopy(src);r['partShift']=lid_fixed[0]['shifts'][p];r['xy']=(np.array(r['xy'])+r['partShift']).tolist();alternative.append(r)

class FrozenStateReplay53:
    def __init__(self,rows):self.rows=copy.deepcopy(rows)
    def apply(self,m,phase=(0,0)):
        if m['sourceId']not in known_sources or m['blinkWeight']!=0 or m['styleJson']!=mref['styleJson']:
            return dict(status='unregistered source/state',rows=[])
        # One common phase translation AFTER joint state allocation. No part
        # is re-ranked per phase. Real visibility is a separate operation.
        t=np.floor(np.asarray(phase)+.5).astype(int);rows=copy.deepcopy(self.rows)
        for r in rows:r['xy']=(np.array(r['xy'])+t).tolist()
        return dict(status='registered offline state candidate',rows=rows,translation=t.tolist())
cache=FrozenStateReplay53(selected);phase_shapes=set()
for m in[by_frame[f]for f in probe_frames]:
    for x in np.linspace(0,1,17,endpoint=False):
        for y in np.linspace(0,1,17,endpoint=False):
            rows=cache.apply(m,(x,y))['rows'];phase_shapes.add(glyph_signature(rows))
check('joint intrinsic shape remains one shape under578 common phases',len(phase_shapes)==1)
for change in[dict(blinkWeight=50),dict(blinkWeight=100),dict(sourceId='unknown-open-source')]:
    check('unregistered states emit no guessed shape',not cache.apply(dict(mref,**change))['rows'])
# Old pose metadata lacks registered blink/part state and complete external
# visibility. It is a boundary-condition rejection, not an invented open eye.
old_pose_rejections=[]
for p in sorted((R.parent/'final-validation').glob('*/params.json')):
    m=load(p);old_pose_rejections.append(dict(pose=p.parent.name,paramsSHA256=sha(p),source=m['source'],
        state='unregistered for whole native lid joint candidate',
        missing=['explicit blink/state registration','complete hair/brow/body source visibility for this native glyph']))
check('five old poses not silently promoted to registered whole-eye states',len(old_pose_rejections)==5)

rgb_results=[];plates=[];all_paths=[]
def painted(base,m,rows,frame,order=None):
    im=base.copy();draw=ImageDraw.Draw(im)
    if order is not None:rows=sorted(rows,key=lambda r:order.index(r['part']))
    emitted=[]
    for r in rows:
        # Preserve original external occlusion even if a token is moved out of
        # it. Also veto any new front occluder at the destination.
        visible=source_visible[frame][r['id']]and not external(frame,r,r['xy'])
        if not visible:continue
        x,y=(r['xy'][0]-m['x'])*2,(r['xy'][1]-m['y'])*2
        draw.rectangle((x,y,x+1,y+1),fill=tuple(r['rgba8']));emitted.append(r)
    return im,emitted
before_rows=[r for group in glyphs.values()for r in group]
for frame in probe_frames:
    m=by_frame[frame];base=Image.open(B/f'fixtures/actual-{frame}.png').convert('RGBA')
    iris_first,ri=painted(base,m,before_rows,frame,['sclera','upper-lid','iris'])
    lid_first,rl=painted(base,m,before_rows,frame,['sclera','iris','upper-lid'])
    after,emitted=painted(base,m,selected,frame)
    alt=Image.open(R/'logical-gate-only'/f'frame{frame}-joint-A-1x.png').convert('RGBA')
    moved=[r for r in selected if r['xy']!=original[r['id']]['xy']]
    allowed=set()
    for r in before_rows+selected:
        x,y=(r['xy'][0]-m['x'])*2,(r['xy'][1]-m['y'])*2
        allowed.update((x+dx,y+dy)for dx in[0,1]for dy in[0,1])
    aa=np.asarray(after);bb=np.asarray(base);changed=[(int(x),int(y))for y,x in np.argwhere(np.any(aa!=bb,axis=2))]
    check('only bounded eye union pixels changed '+str(frame),set(changed)<=allowed)
    check('source-hidden tokens never rescued '+str(frame),all(source_visible[frame][r['id']]for r in emitted))
    check('no new external occlusion ignored '+str(frame),all(not external(frame,r,r['xy'])for r in emitted))
    check('all final modified opaque pixels are direct assigned colours '+str(frame),all(tuple(aa[(r['xy'][1]-m['y'])*2,(r['xy'][0]-m['x'])*2])==tuple(r['rgba8'])for r in emitted))
    check('both measured native part and existing iris glyph survive '+str(frame),
        sum(r['part']=='iris'for r in emitted)==len(glyphs['iris'])and sum(r['part']=='upper-lid'for r in emitted)==len(glyphs['upper-lid']))
    delta=np.any(np.asarray(after)!=np.asarray(lid_first),axis=2)
    cells_changed=sorted({(int(x//2+m['x']),int(y//2+m['y']))for y,x in np.argwhere(delta)})
    names=['actual','iris-priority','lid-priority','joint-safe','logical-only-A-rejected']
    for name,img in zip(names,[base,iris_first,lid_first,after,alt]):
        path=R/f'frame{frame}-{name}-1x.png';img.save(path);img.resize((img.width*12,img.height*12),Image.Resampling.NEAREST).save(R/f'frame{frame}-{name}-12x.png');all_paths.append(path.name)
    rgb_results.append(dict(frame=frame,sourceId=m['sourceId'],emittedByPart=dict(collections.Counter(r['part']for r in emitted)),
        movedTokens=[dict(id=r['id'],part=r['part'],fromXY=original[r['id']]['xy'],toXY=r['xy'],rgba8=r['rgba8'])for r in moved],
        changesVsLidPriorityCells=cells_changed,changedPhysicalPixelsVsActual=len(changed),outsideEyeUnionChanges=0,
        selectedRows=selected,lidFixedAlternativeRows=alternative,sourceExternalHidden=[r['id']for r in selected if not source_visible[frame][r['id']]]))
    plates.append([base,iris_first,lid_first,alt,after])
W,H=plates[0][0].size;strip=Image.new('RGBA',(2*W,5*H))
for x,group in enumerate(plates):
    for y,im in enumerate(group):strip.alpha_composite(im,(x*W,y*H))
strip.save(R/'comparison-1x.png');strip.resize((strip.width*12,strip.height*12),Image.Resampling.NEAREST).save(R/'comparison-12x.png')
# A short frozen-source preview only, not newly rendered gameplay footage.
anim=[Image.open(R/f'frame{frame}-joint-safe-12x.png').convert('RGB')for frame in probe_frames]
anim[0].save(R/'pair-preview.gif',save_all=True,append_images=anim[1:],duration=450,loop=0)
summary=dict(status='offline bounded joint allocation candidate; not art/GPU/temporal completion',
    sourceFrames=probe_frames,cohortUsesBothFramesOffline=True,targetCounts={p:len(v)for p,v in glyphs.items()},
    targetCountRule='exact retained Template glyph plus independently observed native source part; no global iris/lid count',
    budgetZeroFeasible=zero['feasible'],budgetOneEnumerated=result['enumerated'],budgetOneFeasible=result['feasible'],
    selected=result['selected'],alternativeLidFixed=lid_fixed[0]if lid_fixed else None,
    sourceGrowthOcclusionChecked=True,
    rejectedLogicalOnlyA=load(R/'logical-gate-only'/'SUMMARY.json')['selected'],
    actualNativeSupportPerFrame=native_reps,syntheticPhasePlacements=578,
    frameResults=[{k:v for k,v in r.items()if k not in['candidateA','candidateB']}for r in rgb_results],
    preservedFrame101LidAndReferenceIris=True,fullEyeArtApproved=False,
    oldPosesRegistered=False,unregisteredCloseReused=False,GPUIntegrated=False,productModified=False,
    newUnityCalls=0,newCapture=0,newCommit=False,assertions=len(checks),
    limits=['Only this registered open100/101 source pair; native target derives from observed source101',
        'Cached native colour is observed final frame101 RGB, not unlit or new per-frame lighting',
        'One-cell retarget alters spatial source fidelity and upper contour; assess at original size',
        'Both frames inform offline assignment; no claim of a causal runtime cache',
        'No actual rotation/blink or changed lighting test; no unknown pose/state filling'])
dump('INPUT_GLYPHS53.json',dict(glyphs=glyphs,sourcePaths=source_paths,sourceVisibility=source_visible,sourceDepths=depths,
    registeredSourceIds=sorted(known_sources),sourceWhole52SHA256=sha(F/'WHOLE_KEYFORM52.json')))
dump('JOINT_ENUMERATION53.json',result);dump('ZERO_BUDGET53.json',zero)
dump('FRAME_RESULTS53.json',rgb_results);dump('OLD_POSE_BOUNDARIES53.json',old_pose_rejections)
dump('TESTS.json',dict(assertions=len(checks),allPassed=True,cases=checks));dump('SUMMARY.json',summary)
print(json.dumps({k:v for k,v in summary.items()if k not in['frameResults','actualNativeSupportPerFrame']},ensure_ascii=False,indent=2))
