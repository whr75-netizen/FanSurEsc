"""Frozen five-pose/six-frame source, state, placement and conflict tests."""
from pathlib import Path
import ast,collections,copy,hashlib,json,math,struct,sys,types
import numpy as np
from PIL import Image,ImageDraw
from whole52 import WholeEye52,barycentric,compose_registered,native_representative
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';L=R.parent/'lid-evidence51'
sys.path[:0]=[str(B),str(L),str(R.parent/'eye-composition50')]
from candidate49 import CachedCell,StateBoundCluster,projected_anchor,representative,known_final_occlusion
from registered_aperture51 import evaluate_registered51
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def scalar(v):return v.tolist()if isinstance(v,np.ndarray)else v.item()
def dump(n,d):(R/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=scalar),encoding='utf8')
def defs(p,name,initial=None):
    mod=types.ModuleType(name);sys.modules[name]=mod
    mod.__dict__.update(dict(np=np,math=math,Path=Path,json=json,hashlib=hashlib,collections=collections,struct=struct))
    mod.__dict__.update(initial or {})
    tree=ast.parse(p.read_text(encoding='utf8'));tree.body=[q for q in tree.body if isinstance(q,(ast.FunctionDef,ast.ClassDef))]
    exec(compile(tree,str(p),'exec'),mod.__dict__);return mod
checks=[]
def check(n,v):
    if not bool(v):raise AssertionError(n)
    checks.append(n)

for f in load(B/'PACKAGE_MANIFEST.json')['files']:check('immutable49 '+f['path'],sha(B/f['path'])==f['sha256'])
binding=load(R/'SOURCE_BINDING52.json')
for file,h in binding['inputs'].items():check('source file unchanged '+file,sha(Path(file))==h)
template=load(B/'fixtures/template43.json')
for file,h in template['productSHA256'].items():check('product disk hash unchanged '+file,sha(Path(file))==h)
bundle=load(R/'WHOLE_KEYFORM52.json');cache=WholeEye52(bundle,bundle['referenceAnchor']);key=cache.key
surfaces=np.load(R/'SOURCE_SURFACES52.npz');frame_meta=load(B/'fixtures/frames.json');z=np.load(B/'fixtures/replay-inputs.npz')
frozen51=load(L/'KEYFORM_BUNDLE51.json');source_ids={m['sourceId']for m in frame_meta}
cells=[CachedCell(c['cellId'],c['eye'],c['role'],tuple(c['referenceXY']),tuple(c['rgba8']))for c in frozen51['cells']]
cluster=StateBoundCluster('52-open-reference','open-reference',template['referenceAnchorCellCentre'],cells,frame_meta[0]['styleJson'])
old=defs(B/'lib/eye_cache42.py','old52')
assoc=load(R/'CARRIER_ASSOCIATION52.json')
check('20 carrier UV samples reproduce literal Template colours',assoc['allLiteralCarrierSamplesAgree'])
check('original GLB/Unity UV flip verified on all4060 vertices',assoc['nativeUVConvention']['vertices']==4060 and assoc['nativeUVConvention']['maxError']==0)
intrinsic=cache.request(key,'existing-open-reference',cache.anchor)
_,reference_conflicts=compose_registered(intrinsic['cells'])
check('two contradictory opaque part assignments are explicit, not deleted',len(reference_conflicts)==2)
check('no invented lower-lid pixel where reference native sample is absent',not any(c['part']=='lower-lid'for c in intrinsic['cells']))
for state in[c for c in bundle['states']if c!='existing-open-reference']:
    result=cache.request(key,state,cache.anchor)
    check(state+' retains native source geometry but emits no guessed open pixels',not result['pixelFormAvailable']and not result['cells']and len(result['nativeGeometry'])==2)
try:cache.request('wrong-key','existing-open-reference',cache.anchor)
except ValueError:check('changed source key rejected',True)
else:raise AssertionError('changed source accepted')
try:cache.request(key,'unknown-expression',cache.anchor)
except ValueError:check('unknown expression rejected',True)
else:raise AssertionError('unknown expression accepted')

# Probe five OLD poses separately from the real six-frame47 sequence. A phase
# sweep does not pretend to be a new rotation/blink render.
pose_inputs=[]
for path in sorted((R.parent/'final-validation').glob('*/params.json')):
    m=load(path);p=dict(m,headInverse=m['worldToHead'])
    anchor,_=projected_anchor(p)
    pose_inputs.append(dict(kind='old-independent-pose',pose=path.parent.name,source=m['source'],
        angle=m['angle'],paramsSHA256=sha(path),anchor=anchor.tolist(),meta=m))
for m in frame_meta:
    anchor,_=projected_anchor(m)
    pose_inputs.append(dict(kind='actual47-frame',frame=m['frame'],sourceId=m['sourceId'],anchor=anchor.tolist(),meta=m))
phase_reports=[]
for probe in pose_inputs:
    baseline=cache.request(key,'existing-open-reference',probe['anchor']);count=0;shape_signatures=set()
    for x in np.linspace(0,1,33,endpoint=False):
        for y in np.linspace(0,1,33,endpoint=False):
            result=cache.request(key,'existing-open-reference',probe['anchor'],(x,y));t=np.array(result['translation'])
            c=result['cells'];signature=tuple((v['cellId'],v['part'],tuple(np.array(v['xy'])-t),tuple(v['rgba8']))for v in c)
            shape_signatures.add(signature)
            check('common part translation',all(np.array_equal(np.array(a['xy'])-b['referenceXY'],t)for a,b in zip(c,baseline['cells'])))
            check('all source IDs UV and pigment invariant under phase',all(a['source']==b['source']and a['rgba8']==b['rgba8']for a,b in zip(c,baseline['cells'])))
            for e,b in zip(result['eyes'],baseline['eyes']):
                bt=np.array(baseline['translation'])
                check('parent iris and both boundary arcs share common anchor',all(np.allclose(np.array(e[f])-t,np.array(b[f])-bt,atol=1e-12,rtol=0)for f in['parent','iris','upperLidPath','lowerLidPath']))
            _,conflicts=compose_registered(c)
            check('intrinsic overlap cannot be hidden by common translation',len(conflicts)==len(reference_conflicts))
            count+=1
    check('one relative whole shape across phase',len(shape_signatures)==1)
    phase_reports.append({k:v for k,v in probe.items()if k!='meta'}|dict(phasePlacements=count,relativeShapes=1,visibilityNotSimulated=True))

def read_uv(path):
    raw=path.read_bytes();w,h=struct.unpack_from('<ii',raw)
    return np.frombuffer(raw,'<f4',offset=8).reshape(h,w,4)[::-1]
original47=R.parent/'continuous47-counts'/'frames'
trace=[];records=[];plates=[];native_visible=[]
source50=load(R.parent/'eye-composition50'/'RESULTS.json')
registered51=load(L/'APERTURE_RESULTS.json')
for i,m in enumerate(frame_meta):
    d={k.split('_',1)[1]:z[k]for k in z.files if k.startswith(f'f{i:02}_')and not k.endswith('_GPU')}
    anchor,_=projected_anchor(m);placed=cache.request(key,'existing-open-reference',anchor)
    actual=evaluate_registered51(cluster,cluster.key,cluster.state,m,d,frozen51,source_ids,representative,known_final_occlusion,projected_anchor)
    check('frozen51 open aperture exact reproduction',actual==registered51[i]['registered51'])
    by_id={c['cellId']:c for c in placed['cells']}
    for c in actual:c['source']=copy.deepcopy(by_id[c['cellId']]['source']);c['part']=by_id[c['cellId']]['part']
    lines=[]
    for row in placed['cells']:
        if row['role']!=6:continue
        c=copy.deepcopy(row);rep=native_representative(d,m,c,known_final_occlusion);c['representative']=rep;c['visible']=bool(rep.get('support'));lines.append(c)
    all_rows=actual+lines
    unambiguous,conflicts=compose_registered([c for c in all_rows if c['visible']])
    # Bind measured source UV/triangle/barycentric for every eligible output.
    # Missing S3RGBA remains missing; never relabel PNG reference as measured RGB.
    uv_buffers={s:read_uv(original47/f'{i:02}'/f'S{s}UV.bin')for s in[1,2,3]}
    for c in all_rows:
        rep=c.get('representative')
        if not rep or not rep.get('support'):continue
        s=3 if c['role']==6 else(2 if c['role']==1 else 1)
        x,y=c['xy'][0]-m['x'],c['xy'][1]-m['y'];k=rep['k'];xx=x*4+k%4;yy=y*4+3-k//4
        sampled=uv_buffers[s][yy,xx];primitive=int(round(float(sampled[2])))-1
        role={1:4,2:1,3:6}[s];tri=surfaces[f'native_role{role}_tri'][primitive]
        point=d[f'S{s}POINT'][yy,xx,:3];w,err=barycentric(point,surfaces['native_xyz_head'][tri])
        uv=w@surfaces['native_uv'][tri];uv_error=float(np.linalg.norm(uv-sampled[:2]))
        check('recorded representative resolves original native triangle',w.min()>-1e-4 and err<1e-6 and uv_error<1e-5)
        trace.append(dict(frame=m['frame'],sourceId=m['sourceId'],cellId=c['cellId'],xy=c['xy'],part=c['part'],sourceLayer=s,
            primitive=primitive+1,triangleVertexIds=tri.tolist(),barycentric=w.tolist(),UV=sampled[:2].tolist(),
            sourcePointError=err,sourceUVError=uv_error,literalRGBA8=c['rgba8'],
            pigmentMeaning='literal registered Template'if s!=3 else'canonical source PNG illustration; actual S3RGBA unavailable'))
    native_visible.append(sum(c['visible']for c in lines))
    record=dict(frame=m['frame'],sourceId=m['sourceId'],translation=placed['translation'],
        sourceNativeLid50=source50[i]['eyes']['1']['sourceLid'],wholeSourceRows=all_rows,unresolvedVisibleConflicts=conflicts,
        allVisibleSourceParts=len([c for c in all_rows if c['visible']]),unambiguousCells=len(unambiguous),
        frame101FullShapeSolved=False)
    records.append(record)
    # Diagnostic layers only. No new eye RGB is pasted onto a saved character.
    W,H=m['width']*2,m['height']*2
    def pic(rows,conflict_points=()):
        im=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(im)
        for c in rows:
            if not c.get('visible',True):continue
            x,y=(c['xy'][0]-m['x'])*2,(c['xy'][1]-m['y'])*2
            draw.rectangle((x,y,x+1,y+1),fill=tuple(c['rgba8']))
        for c in conflict_points:
            x,y=(c['xy'][0]-m['x'])*2,(c['xy'][1]-m['y'])*2
            draw.rectangle((x,y,x+1,y+1),fill=(255,0,200,255))
        return im
    intrinsic_layer=pic(placed['cells'],[dict(xy=(np.array(c['xy'])+np.array(placed['translation'])).tolist())for c in reference_conflicts])
    masks=[]
    for eye,entry in source50[i]['eyes'].items():
        for xy in entry['sourceLid']:masks.append(dict(xy=xy,rgba8=[255,205,60,255]))
    plates.append([Image.open(B/f'fixtures/actual-{m["frame"]}.png').convert('RGBA'),intrinsic_layer,
        pic(actual),pic(lines),pic(unambiguous,conflicts),pic(masks)])

W,H=plates[0][0].size;strip=Image.new('RGBA',(6*W,6*H),(28,32,39,255))
for x,group in enumerate(plates):
    for y,im in enumerate(group):strip.alpha_composite(im,(x*W,y*H))
strip.convert('RGB').save(R/'actual6-layers-1x.png');strip.resize((strip.width*8,strip.height*8),Image.Resampling.NEAREST).save(R/'actual6-layers-8x.png')
# Show the genuine parent/native geometry and source Close states separately
# from pixel availability; blank closed pixel panels are intentionally blank.
im=Image.new('RGB',(720,480),(26,30,37));draw=ImageDraw.Draw(im)
for col,eye in enumerate([2,1]):
    f=next(e for e in intrinsic['eyes']if e['eye']==eye);origin=np.floor(np.array(f['parent']).min(axis=0))-1
    def line(points,row,colour):
        q=(np.array(points)-origin)*22+[col*360+20,row*160+26]
        draw.line(list(map(tuple,np.vstack([q,q[0]]))),fill=colour,width=2)
    draw.text((col*360+20,4),f'eye{eye} OPEN: authored / native',fill='white')
    line(f['parent'],0,(100,210,255));line(f['iris'],0,(245,115,100));line(f['nativeRingReference'],0,(245,210,80))
    for row,weight in enumerate([50,100],1):
        state=cache.request(key,f'Fcl_EYE_Close:{weight}',cache.anchor)
        geom=next(e for e in state['nativeGeometry']if e['eye']==eye)
        draw.text((col*360+20,row*160+4),f'Close{weight}: native geometry ONLY / raster UNKNOWN',fill='white')
        line(geom['referencePoints'],row,(245,210,80))
im.save(R/'source-close-geometry.png')
summary=dict(kind='whole-eye52-offline-result',phasePlacements=sum(p['phasePlacements']for p in phase_reports),
    oldIndependentPoses=5,actualFrozenFrames=[m['frame']for m in frame_meta],relativeWholeShapeVariantsPerProbe=1,
    boundTemplateCells=20,literalSourceCarrierAgreement=20,nativeReferenceLidCells=2,nativeReferenceLowerLidCells=0,
    referenceOpaqueConflicts=reference_conflicts,nativeVisibleCellsPerActualFrame=native_visible,
    actualMeasuredSourceBindings=len(trace),maxActualSourcePointError=max(t['sourcePointError']for t in trace),
    maxActualUVError=max(t['sourceUVError']for t in trace),
    visibleConflictsPerFrame=[len(r['unresolvedVisibleConflicts'])for r in records],
    sourceLid50Frame101=records[-1]['sourceNativeLid50'],
    iris1AfterPreservingSourceLid=[sum(c['eye']==1 and c['role']==1 and c['visible']for c in r['composed51'])for r in registered51],
    wholeShapeSolved=False,fullyClosedPixelFormAvailable=False,GPUApplied=False,productModified=False,
    liveEditorState='unknown; not queried; parent reported instance change',newUnityCalls=0,newCommit=False,
    testAssertions=len(checks),
    limits=['Native reference raster is incomplete/conflicting and is NOT adopted',
        'Common translation proves pure phase invariance, not pose/blink/occlusion invariance',
        'Actual S3RGBA/S3Shade and S0 deformation-control buffer were not captured',
        'No source-free pixel generation or invented replacement cells',
        'Open Template20 lacks a coherent jointly designed lid/iris/sclera raster'])
dump('SUMMARY.json',summary);dump('FRAME_RESULTS52.json',records);dump('ACTUAL_SOURCE_BINDINGS52.json',trace)
dump('PHASE_TESTS52.json',phase_reports);dump('TESTS.json',dict(assertions=len(checks),allPassed=True,
    assertionsByName=dict(collections.Counter(checks)),note='Repeated phase assertions are not independent art-quality criteria'))
print(json.dumps(summary,ensure_ascii=False,indent=2))
