from pathlib import Path
import ast,collections,hashlib,json,math,sys,types
import numpy as np
from PIL import Image,ImageDraw
from registered_aperture51 import evaluate_registered51
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';F=R.parent/'eye-composition50'
sys.path[:0]=[str(B),str(F)]
from candidate49 import CachedCell,StateBoundCluster,representative,known_final_occlusion,projected_anchor,place_visible
from candidate50 import native_lid_from_source,compose_part_ids
load=lambda p:json.loads(p.read_text(encoding='utf8'))
def default(o):return o.tolist()if isinstance(o,np.ndarray)else o.item()
def dump(n,o):(R/n).write_text(json.dumps(o,ensure_ascii=False,indent=2,default=default),encoding='utf8')
def defs(p,name,initial=None):
    mod=types.ModuleType(name);sys.modules[name]=mod;mod.__dict__.update(dict(np=np,math=math,Path=Path,json=json,hashlib=hashlib,collections=collections));mod.__dict__.update(initial or {})
    tree=ast.parse(p.read_text());tree.body=[q for q in tree.body if isinstance(q,(ast.FunctionDef,ast.ClassDef))];exec(compile(tree,str(p),'exec'),mod.__dict__);return mod
old_eye=defs(B/'lib/eye_cache42.py','eye51_frozen');old=defs(B/'lib/counts47.py','counts51_frozen',{'classify':old_eye.classify})
m=load(B/'fixtures/frames.json');z=np.load(B/'fixtures/replay-inputs.npz');bundle=load(R/'KEYFORM_BUNDLE51.json');sources={f['sourceId']for f in m}
cells=[CachedCell(c['cellId'],c['eye'],c['role'],tuple(c['referenceXY']),tuple(c['rgba8']))for c in bundle['cells']]
cluster=StateBoundCluster('source51','open-reference-trial',[217.5,79.],cells,m[0]['styleJson'])
checks=[]
def check(n,v):
    if not bool(v):raise AssertionError(n)
    checks.append(n)
records=[];plates=[]
for i,meta in enumerate(m):
    d={k.split('_',1)[1]:z[k]for k in z.files if k.startswith(f'f{i:02}_')and not k.endswith('_GPU')}
    skin_hash=hashlib.sha256(d['S0META'].tobytes()).hexdigest()
    rows=evaluate_registered51(cluster,cluster.key,cluster.state,meta,d,bundle,sources,representative,known_final_occlusion,projected_anchor)
    strict,*_=place_visible(cluster,cluster.key,cluster.state,meta,d,True)
    gpu=z[f'f{i:02}_GPU'];_,dep=old.replay_packets(meta,d);lids={}
    for eye,c in enumerate(meta['centres']):
        source=old.allocator(gpu,meta,eye,old.final_gate(d,dep[eye]))[0]
        lids[round(c['w'])]=native_lid_from_source(gpu,meta,eye,set(source))[0]
    composed=compose_part_ids(rows,meta,lids)
    check('input skin samples unchanged',hashlib.sha256(d['S0META'].tobytes()).hexdigest()==skin_hash)
    check('every output role/pigment belongs to exact original template cell',all(q['role']==c.role and tuple(q['rgba8'])==c.rgba8 for q,c in zip(rows,cells)))
    check('no emission without same-eye original feature surface support',all(not q['visible']or(q['representative']['sourceSamples']>0 and q['representative']['source']==(2 if q['role']==1 else 1))for q in rows))
    check('no restoration through final hair/body gate',all(not q['visible']for q in rows if q['knownFinalBlocks']))
    check('source native lid always keeps its footprint',all(not q['visible']for q in composed if q['occludedByNativeLid50']))
    for change in[dict(blinkWeight=50.),dict(blinkWeight=100.),dict(sourceId='unregistered-open-source')]:
        try:evaluate_registered51(cluster,cluster.key,cluster.state,dict(meta,**change),d,bundle,sources,representative,known_final_occlusion,projected_anchor)
        except ValueError:pass
        else:raise AssertionError('Unregistered state accepted')
    hide=dict(d);hide['hair-meta']=d['hair-meta'].copy();hide['hair-meta'][...]=[1,12,1,1]
    hidden=evaluate_registered51(cluster,cluster.key,cluster.state,meta,hide,bundle,sources,representative,known_final_occlusion,projected_anchor)
    check('real front hair can hide whole registered feature',not any(q['visible']for q in hidden))
    other=dict(d);other['S0META']=d['S0META'].copy();other['S0META'][...]=[1,8,1,1];other['S0POINT']=d['S0POINT'].copy();other['S0POINT'][...,3]=1
    reserved=evaluate_registered51(cluster,cluster.key,cluster.state,meta,other,bundle,sources,representative,known_final_occlusion,projected_anchor)
    check('non-face material is never suppressed as generic face underlay',not any(q['visible']for q in reserved if q['eye']==1))
    records.append(dict(frame=meta['frame'],sourceId=meta['sourceId'],strict49=strict,registered51=rows,composed51=composed))
    W,H=meta['width']*2,meta['height']*2
    def image(rows):
        im=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(im)
        for q in rows:
            if not q['visible']:continue
            x,y=(q['xy'][0]-meta['x'])*2,(q['xy'][1]-meta['y'])*2;draw.rectangle((x,y,x+1,y+1),fill=tuple(q['rgba8']))
        return im
    plates.append([Image.open(B/f'fixtures/actual-{meta["frame"]}.png').convert('RGBA'),image(strict),image(rows),image(composed)])
summary=dict(sourceStateScope='six frozen fully-open source IDs only',newUnityCalls=0,productModified=False,newCommit=False,
    strictSclera=[sum(q['role']==4 and q['visible']for q in r['strict49'])for r in records],
    scopedSclera=[sum(q['role']==4 and q['visible']for q in r['registered51'])for r in records],
    afterSourceLidSclera=[sum(q['role']==4 and q['visible']for q in r['composed51'])for r in records],
    afterSourceLidIris1=[sum(q['eye']==1 and q['role']==1 and q['visible']for q in r['composed51'])for r in records],
    afterSourceLidIris2=[sum(q['eye']==2 and q['role']==1 and q['visible']for q in r['composed51'])for r in records],
    policySource='existing EyeCompose333 Compose: eye above generic skin inside authored aperture; only this rule restored, all hair retained',
    nativeClosePixelStateReused=False,fullEyeSolved=False,GPUCompiled=False,checks=len(checks),
    remaining='complete pixel lid key form, source-line budget transition, actual GPU compositor/state validation')
dump('APERTURE_RESULTS.json',records);dump('APERTURE_SUMMARY.json',summary);dump('APERTURE_TESTS.json',checks)
im=Image.new('RGBA',(6*W,4*H),(28,32,39,255))
for x,group in enumerate(plates):
    for y,pic in enumerate(group):im.alpha_composite(pic,(x*W,y*H))
im.convert('RGB').save(R/'aperture-comparison-1x.png');im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).save(R/'aperture-comparison-8x.png')
print(json.dumps(summary,ensure_ascii=False,indent=2))
