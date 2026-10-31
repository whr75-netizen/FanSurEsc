"""Read immutable49/47 evidence. Generate only independent experiment50."""
from pathlib import Path
import ast,collections,difflib,hashlib,json,math,sys,types
import numpy as np
from PIL import Image,ImageDraw
from candidate50 import native_lid_from_source,compose_part_ids
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49'
sys.path.insert(0,str(B))
from candidate49 import CachedCell,StateBoundCluster,place_visible,projected_anchor
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def scalar(o):
    if isinstance(o,np.generic):return o.item()
    if isinstance(o,np.ndarray):return o.tolist()
    raise TypeError(type(o).__name__)
def dump(n,a):(R/n).write_text(json.dumps(a,ensure_ascii=False,indent=2,default=scalar),encoding='utf8')
def defs(p,name,initial=None):
    mod=types.ModuleType(name);sys.modules[name]=mod
    mod.__dict__.update(dict(np=np,math=math,Path=Path,json=json,hashlib=hashlib,collections=collections));mod.__dict__.update(initial or {})
    tree=ast.parse(p.read_text(encoding='utf8'));tree.body=[a for a in tree.body if isinstance(a,(ast.FunctionDef,ast.ClassDef))]
    exec(compile(tree,str(p),'exec'),mod.__dict__);return mod
e=defs(B/'lib/eye_cache42.py','eye50_old')
old=defs(B/'lib/counts47.py','counts50_old',{'classify':e.classify})
old_test=defs(B/'verify49.py','test50_old')
checks=[]
def check(n,v):
    if not bool(v):raise AssertionError(n)
    checks.append(n)
manifest=load(B/'PACKAGE_MANIFEST.json')
for f in manifest['files']:check('immutable49 '+f['path'],hashlib.sha256((B/f['path']).read_bytes()).hexdigest()==f['sha256'])
meta=load(B/'fixtures/frames.json');arrays=np.load(B/'fixtures/replay-inputs.npz')
t=load(B/'fixtures/template43.json');cells=[CachedCell(c['cellId'],c['eye'],c['role'],tuple(c['referenceXY']),tuple(c['rgba8']))for c in t['cells']]
cluster=StateBoundCluster('frozen49','open-probe',t['referenceAnchorCellCentre'],cells,meta[0]['styleJson'])
records=[];plates=[];line_regressions=[];line_fixed=[];source_lid_onsets=[]
for i,m in enumerate(meta):
    d={k.split('_',1)[1]:arrays[k]for k in arrays.files if k.startswith(f'f{i:02}_')and not k.endswith('_GPU')}
    gpu=arrays[f'f{i:02}_GPU'];_,depth=old.replay_packets(m,d)
    rows,shift,anchor,_=place_visible(cluster,'frozen49','open-probe',m,d,True)
    record=dict(frame=m['frame'],sourceId=m['sourceId'],shift=shift.tolist(),anchor=anchor.tolist(),eyes={},ablations={},cells=rows)
    source_plans={};wrong_plans={}
    for ix,c in enumerate(m['centres']):
        eye=round(c['w']);source_iris=old.allocator(gpu,m,ix,old.final_gate(d,depth[ix]))[0]
        cached={(c['xy'][0]-m['x'],c['xy'][1]-m['y'])for c in rows if c['eye']==eye and c['role']==1 and c['visible']}
        baseline=old_test.native_line(gpu,m,ix,set(source_iris))
        wrong=old_test.native_line(gpu,m,ix,cached)
        corrected,area=native_lid_from_source(gpu,m,ix,set(source_iris));source_plans[eye]=corrected;wrong_plans[eye]=wrong
        check('source lid replay matches original source-only decision',corrected==baseline)
        check('source iris / source lid mutually exclusive before cache',not(set(source_iris)&corrected))
        # Choosing source lid first commutes with original iris selection, at every pixel.
        for y in range(m['height']):
            for x in range(m['width']):
                a='iris'if(x,y)in source_iris else'lid'if(x,y)in baseline else'other'
                b='lid'if(x,y)in corrected else'iris'if(x,y)in source_iris else'other'
                check('baseline part-order equivalence',a==b)
        ids=lambda pts:[[x+m['x'],y+m['y']]for x,y in sorted(pts)]
        record['eyes'][str(eye)]=dict(sourceLid=ids(corrected),bad49Lid=ids(wrong),sourceLineArea=area,
            sourceIris=ids(source_iris),cachedIris=ids(cached),lineBudget=math.floor(float(np.float32(area+.5))))
        source_lid_onsets.append(dict(frame=m['frame'],eye=eye,area=area,budget=record['eyes'][str(eye)]['lineBudget']))
        if wrong!=baseline:line_regressions.append([m['frame'],eye]);line_fixed.append(dict(frame=m['frame'],eye=eye,fromBad=ids(wrong),restoredSource=ids(corrected)))
    composed=compose_part_ids(rows,m,source_plans)
    check('native-lid composition only removes conflicting cache pixels',{r['cellId']for r in composed if r['visible']}<={r['cellId']for r in rows if r['visible']})
    check('literal cached role/colour never changed by composition',all(r['rgba8']==a['rgba8']and r['role']==a['role']and r['xy']==a['xy']for r,a in zip(composed,rows)))
    check('known final hair/body blocked cell never restored',all(not r['visible']for r in composed if r['knownFinalBlocks']))
    record['composedCells']=composed
    # Ablations are causal diagnostics only. S0 bypass is never adopted.
    for channel in ['S0META','S3META','S4META']:
        altered=dict(d);altered[channel]=np.zeros_like(d[channel])
        trial,*_=place_visible(cluster,'frozen49','open-probe',m,altered,True)
        restored=[r['cellId']for r,a in zip(trial,rows)if r['visible']and not a['visible']]
        record['ablations'][channel]=dict(restoredIds=restored,iris=sum(r['role']==1 and r['visible']for r in trial),sclera=sum(r['role']==4 and r['visible']for r in trial),adopted=False)
    check('upper-lid source omission does not explain prior sclera loss',not record['ablations']['S3META']['restoredIds'])
    record['whiteZeroRows']=[r for r in rows if r['role']==4 and not r['visible']]
    records.append(record)
    w,h=m['width'],m['height']
    def mask(points):
        im=Image.new('RGBA',(w*2,h*2));draw=ImageDraw.Draw(im)
        for eye,pts in points.items():
            colour=(250,210,80,255)if eye==1 else(80,205,230,255)
            for x,y in pts:draw.rectangle((x*2,y*2,x*2+1,y*2+1),fill=colour)
        return im
    def rgb_layer(rr):
        im=Image.new('RGBA',(w*2,h*2));draw=ImageDraw.Draw(im)
        for r in rr:
            if not r['visible']:continue
            x,y=r['xy'][0]-m['x'],r['xy'][1]-m['y'];draw.rectangle((x*2,y*2,x*2+1,y*2+1),fill=tuple(r['rgba8']))
        return im
    plates.append([Image.open(B/f'fixtures/actual-{m["frame"]}.png').convert('RGBA'),mask(wrong_plans),mask(source_plans),rgb_layer(rows),rgb_layer(composed)])

check('only known wrong feedback case reproduces',line_regressions==[[101,1]])
check('frame101 upper lid kept at source position',records[-1]['eyes']['1']['sourceLid']==[[222,52]])
check('frame100 cache improvement not lost by source lid priority',sum(r['role']==1 and r['eye']==1 and r['visible']for r in records[4]['composedCells'])==4)
check('frame101 iris still incomplete; not silently passed',sum(r['role']==1 and r['eye']==1 and r['visible']for r in records[5]['composedCells'])==3)
check('actual fully-open key form still rejects blink',all(m['blinkWeight']==0 for m in meta))

# A minimal, baseline-equivalent GPU preparation diff. It is NOT imported or compiled.
base=(B/'patches/EyeFeature348_visibility_gate47.compute').read_text(encoding='utf8')
new=base.replace('bool IrisAllocated19(int2 p,int eye){','bool SourceIrisAllocated19(int2 p,int eye){',1)
check('one iris source helper definition renamed',new!=base)
at=new.index('bool SourceWhiteNeighbour19(')
new=new[:at]+'// Registered cache occupancy can later replace this wrapper only.\nbool IrisAllocated19(int2 p,int eye){return SourceIrisAllocated19(p,eye);}\n\n'+new[at:]
a=new.index('bool NativeLineAllocated19(');b=new.index('int ChooseLayers19(',a)
native=new[a:b];check('two native-line iris dependencies isolated',native.count('IrisAllocated19(')==2)
new=new[:a]+native.replace('IrisAllocated19(','SourceIrisAllocated19(')+new[b:]
check('native-line cannot refer to logical cache wrapper', '||IrisAllocated19('not in new[a:new.index('int ChooseLayers19(',a)])
first='  if(IrisAllocated19(p,eye)){if(c[4]>=4)return 4;return c[2]>=c[3]?2:3;}\n  if(NativeLineAllocated19(p,eye))return 5;'
second='  if(NativeLineAllocated19(p,eye))return 5;\n  if(IrisAllocated19(p,eye)){if(c[4]>=4)return 4;return c[2]>=c[3]?2:3;}'
# Existing source has one-space indentation; retain exact matching rather than fuzzy edits.
if first not in new:first=first.replace('\n  ','\n ').lstrip();second=second.replace('\n  ','\n ').lstrip()
check('one layer-order hunk found',new.count(first)==1)
new=new.replace(first,second,1)
(R/'EyeFeature348_source_parts50.compute').write_text(new,encoding='utf8')
(R/'SOURCE_PARTS_ONLY.diff').write_text(''.join(difflib.unified_diff(base.splitlines(True),new.splitlines(True),fromfile='gate47-not-product',tofile='source-parts50-not-GPU-compiled')),encoding='utf8')
dump('RESULTS.json',records)
summary=dict(sequenceId=meta[0]['sequenceId'],baselineCommit='d0ca21f4ac87e82151357253582f9ce079596a2d',
    frame101LidCause='NativeLineAllocated19 excludes new cached iris occupancy and re-ranks into a spare tiny source fragment; not anchor change',
    anchorConstant=[2,-26],lineFeedbackRegressions=line_regressions,lineFixed=line_fixed,
    lineIndependentAfter50=True,whiteCauseIndependent=True,
    actualID1Iris=[2,2,2,2,1,2],cache49ID1Iris=[4]*6,
    candidate50ID1Iris=[sum(c['eye']==1 and c['role']==1 and c['visible']for c in r['composedCells'])for r in records],
    scleraStrict49=[sum(c['role']==4 and c['visible']for c in r['cells'])for r in records],
    scleraS0BypassNotAdopted=[r['ablations']['S0META']['sclera']for r in records],
    sourceNativeLineBudget=source_lid_onsets,checks=len(checks),GPUCompiled=False,productModified=False,newUnityCalls=0,
    fullEyeSolved=False,remaining='upper-lid source budget still switches at .5; full registered lid/iris/sclera form and ordinary face-skin vs actual lid split missing; no through-skin fill adopted')
dump('SUMMARY.json',summary);dump('TESTS.json',dict(passed=len(checks),checks=checks))
W,H=plates[0][0].size;im=Image.new('RGB',(6*W,5*H),(28,32,39))
for x,rows in enumerate(plates):
    for y,pic in enumerate(rows):
        bg=Image.new('RGBA',pic.size,(28,32,39,255));im.paste(Image.alpha_composite(bg,pic).convert('RGB'),(x*W,y*H))
im.save(R/'comparison-1x.png');im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).save(R/'comparison-8x.png')
print(json.dumps({k:v for k,v in summary.items()if k!='sourceNativeLineBudget'},ensure_ascii=False,indent=2))
