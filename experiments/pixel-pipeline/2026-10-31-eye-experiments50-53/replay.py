"""Relocatable bounded CPU replay; no Unity, Pillow, external assets or writes.

Original definitions are loaded without CLI/global path assignments. A NumPy
rectangle adapter verifies the original 2x2 diagnostic composition against PNG
pixels; it does not fill the six missing clean-underlay samples.
"""
from pathlib import Path
import ast,collections,copy,dataclasses,hashlib,itertools,json,math,os,struct,sys,types,zlib
import numpy as np
R=Path(__file__).resolve().parent
P=next(p for p in R.parents if (p/'Assets').is_dir()and(p/'experiments').is_dir())
B=P/'experiments/pixel-pipeline/2026-10-30-eye-candidate49'
A=R/'archive'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def guard(event,args):
 if event!='open'or not isinstance(args[0],(str,bytes,os.PathLike)):return
 p=Path(os.fsdecode(args[0])).resolve()
 if not(p.is_relative_to(R)or p.is_relative_to(B)or p.is_relative_to(P/'experiments/pixel-pipeline/2026-10-30-source-diagnostics')or p.is_relative_to(Path(sys.base_prefix).resolve())):raise PermissionError('External data read blocked: '+str(p))
 if isinstance(args[1],str)and any(x in args[1]for x in 'wax+'):raise PermissionError('File write blocked: '+str(p))
sys.addaudithook(guard)
checks=[]
def check(name,v):
 assert bool(v),name
 checks.append(name)
def reject(name,fn):
 try:fn()
 except ValueError:checks.append(name)
 else:raise AssertionError(name)
def defs(path,name,initial=None):
 m=types.ModuleType(name);sys.modules[name]=m;m.__dict__.update(dict(np=np,copy=copy,math=math,Path=Path,json=json,hashlib=hashlib,collections=collections,dataclass=dataclasses.dataclass,product=itertools.product,struct=struct,zlib=zlib))
 m.__dict__.update(initial or {});tree=ast.parse(path.read_text(encoding='utf-8'));tree.body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))];exec(compile(tree,str(path),'exec'),m.__dict__);return m
for n,row in load(R/'DEPENDENCIES.json')['repositoryRelativeFiles'].items():check('versioned dependency '+n,hashlib.sha256((P/n).read_bytes()).hexdigest()==row['sha256'])
old=defs(B/'lib/eye_cache42.py','archive_eye50')
counts=defs(B/'lib/counts47.py','archive_counts50',{'classify':old.classify})
cache49=defs(B/'candidate49.py','archive_cache49')
part50=defs(A/'eye-composition50/candidate50.py','archive_part50')
key51=defs(A/'lid-evidence51/keyform51.py','archive_key51')
ap51=defs(A/'lid-evidence51/registered_aperture51.py','archive_aperture51')
whole52=defs(A/'whole-eye52/whole52.py','archive_whole52')
joint53=defs(A/'joint-eye53/joint53.py','archive_joint53')
meta=load(B/'fixtures/frames.json');z=np.load(B/'fixtures/replay-inputs.npz')
template=load(B/'fixtures/template43.json');bundle51=load(A/'lid-evidence51/KEYFORM_BUNDLE51.json')
cells=[cache49.CachedCell(c['cellId'],c['eye'],c['role'],tuple(c['referenceXY']),tuple(c['rgba8']))for c in template['cells']]
cluster=cache49.StateBoundCluster('fixed','open',template['referenceAnchorCellCentre'],cells,meta[0]['styleJson'])
gold50=load(A/'eye-composition50/RESULTS.json');gold51=load(A/'lid-evidence51/APERTURE_RESULTS.json')
data={m['frame']:{k.split('_',1)[1]:z[k]for k in z.files if k.startswith(f'f{i:02}_')and not k.endswith('_GPU')}for i,m in enumerate(meta)}
for i,m in enumerate(meta):
 d=data[m['frame']];gpu=z[f'f{i:02}_GPU'];_,depth=counts.replay_packets(m,d)
 rows,*_=cache49.place_visible(cluster,'fixed','open',m,d)
 lids={}
 for eye_index,centre in enumerate(m['centres']):
  eye=round(centre['w']);iris=counts.allocator(gpu,m,eye_index,counts.final_gate(d,depth[eye_index]))[0]
  lid,area=part50.native_lid_from_source(gpu,m,eye_index,set(iris));lids[eye]=lid
  ids=sorted([[x+m['x'],y+m['y']]for x,y in lid]);expected=gold50[i]['eyes'][str(eye)]
  check(f"50 frame{m['frame']} eye{eye}: source lid independent of cached iris",ids==sorted(expected['sourceLid'])and area==expected['sourceLineArea'])
 composed=part50.compose_part_ids(rows,m,lids)
 check(f"50 frame{m['frame']}: literal composition matches saved cells",[(c['cellId'],c['xy'],c['rgba8'],c['visible'])for c in composed]==[(c['cellId'],c['xy'],c['rgba8'],c['visible'])for c in gold50[i]['composedCells']])
 registered=ap51.evaluate_registered51(cluster,'fixed','open',m,d,bundle51,{q['sourceId']for q in meta},cache49.representative,cache49.known_final_occlusion,cache49.projected_anchor)
 check(f"51 frame{m['frame']}: registered aperture/visibility/pigment replay",[(c['cellId'],c['xy'],c['rgba8'],c['visible'])for c in registered]==[(c['cellId'],c['xy'],c['rgba8'],c['visible'])for c in gold51[i]['registered51']])
form=key51.KeyForm51(bundle51)
reject('51 unbound source rejected',lambda:form.reference_layer(('wrong',),'existing-open-reference',(0,0)))
reject('51 missing closed pixel state not replaced by open form',lambda:form.reference_layer(form.key,'blink50',(0,0)))
for name,value in bundle51['nativeClosingMorphs'].items():
 for ring in value['nativeRingStates']:
  for weight in [50,100]:check('51 native geometry is not approved pixel keyform '+name+str(ring['eye'])+str(weight),not form.native_lid_geometry(name,ring['eye'],weight)['pixelKeyFormAvailable'])
bundle52=load(A/'whole-eye52/WHOLE_KEYFORM52.json');whole=whole52.WholeEye52(bundle52,bundle52['referenceAnchor'])
reference=whole.request(whole.key,'existing-open-reference',whole.anchor)
_,conflicts=whole52.compose_registered(reference['cells'])
check('52 unresolved reference overlap stays explicit',len(conflicts)>0)
for name,s in bundle52['states'].items():
 if not s['pixelFormAvailable']:check('52 rejects inferred raster '+name,whole.request(whole.key,name,whole.anchor)['cells']==[])
reject('52 stale cache key rejected',lambda:whole.request('stale','existing-open-reference',whole.anchor))
for x,y in itertools.product(range(17),repeat=2):
 out=whole.request(whole.key,'existing-open-reference',whole.anchor,(x/16,y/16));t=np.array(out['translation'])
 assert all(np.array_equal(np.array(c['xy'])-t,c['referenceXY'])for c in out['cells'])
check('52 289 phase translations preserve whole intrinsic cell identity',True)
inp=load(A/'joint-eye53/INPUT_GLYPHS53.json');glyphs=inp['glyphs'];by_frame={m['frame']:m for m in meta}
depths={int(f):v for f,v in inp['sourceDepths'].items()};visibility={int(f):v for f,v in inp['sourceVisibility'].items()}
occupied={tuple(r['xy'])for g in glyphs.values()for r in g}
run53=defs(A/'joint-eye53/run53.py','archive_run53',dict(by_frame=by_frame,data=data,depths=depths,original_occupied=occupied,known_final_occlusion=cache49.known_final_occlusion,known_sources=set(inp['registeredSourceIds']),mref=by_frame[101]))
expected=load(A/'joint-eye53/JOINT_ENUMERATION53.json')
zero=joint53.enumerate_joint(glyphs,inp['sourcePaths'],0,run53.external,visibility)
trial=joint53.enumerate_joint(glyphs,inp['sourcePaths'],1,run53.external,visibility)
check('53 no zero-budget solution; 125 alternatives and two feasible',zero['feasible']==0 and trial['enumerated']==125 and trial['feasible']==2)
check('53 all feasibility/collision/source-growth decisions replay',[(t['shifts'],t['feasible'],t['violations'],t['externalBlocks'])for t in trial['trials']]==[(t['shifts'],t['feasible'],t['violations'],t['externalBlocks'])for t in expected['trials']])
check('53 selected B retains original shifts/cost',trial['selected']['shifts']==expected['selected']['shifts']and abs(trial['selected']['curveError']-expected['selected']['curveError'])<1e-12)
reverse=joint53.enumerate_joint(dict(reversed(list(glyphs.items()))),inp['sourcePaths'],1,run53.external,visibility)
check('53 part ordering cannot change selected allocation',reverse['selected']==trial['selected'])
cache=run53.FrozenStateReplay53(trial['rows']);signatures=set()
for frame in [100,101]:
 for x,y in itertools.product(range(17),repeat=2):
  signatures.add(joint53.glyph_signature(cache.apply(by_frame[frame],(x/16,y/16))['rows']))
check('53 578 common-phase placements keep one intrinsic glyph',len(signatures)==1)
bad=dict(by_frame[100],blinkWeight=1);check('53 missing blink/state cannot output open raster',cache.apply(bad)['rows']==[])
# Run original composition with an array-only equivalent of its solid rectangle
# API. Compare full stored RGBA, including magenta UNKNOWN and untouched pixels.
class Canvas:
 def __init__(self,a):self.a=a
 def copy(self):return Canvas(self.a.copy())
class Draw:
 @staticmethod
 def Draw(im):return Draw(im)
 def __init__(self,im):self.im=im
 def rectangle(self,box,fill):
  x,y,xx,yy=box;self.im.a[y:yy+1,x:xx+1]=fill
compose=defs(A/'joint-eye53/compose53.py','archive_compose53',{'ImageDraw':Draw,'UNKNOWN':(250,0,200,255)})
png=defs(P/'experiments/pixel-pipeline/2026-10-30-source-diagnostics/archive/exp30/flat-albedo-control/pngio.py','replay_png53')
frame_results=load(A/'joint-eye53/FRAME_RESULTS53.json')
total_unknown=0
for frame,want in zip([100,101],frame_results):
 w,h,rgba=png.read(B/f'fixtures/actual-{frame}.png');base=Canvas(np.frombuffer(rgba,np.uint8).reshape(h,w,4).copy())
 im,emitted,missing=compose.partial_context(base,by_frame[frame],data[frame],trial['rows'],visibility[frame],lambda r:run53.external(frame,r,r['xy']))
 ww,hh,saved=png.read(A/f'joint-eye53/frame{frame}-candidateB-1x.png')
 check('53 frame'+str(frame)+': entire partial RGBA equals stored PNG',ww==w and hh==h and im.a.tobytes()==saved)
 check('53 frame'+str(frame)+': unknown backing never filled by guessed skin',missing==want['unknownUnderlayCells']and all(np.all(im.a[(y-by_frame[frame]['y'])*2:(y-by_frame[frame]['y'])*2+2,(x-by_frame[frame]['x'])*2:(x-by_frame[frame]['x'])*2+2]==(250,0,200,255))for x,y in missing))
 total_unknown+=len(missing)
check('53 six clean Base/Backing samples remain missing',total_unknown==6)
print(json.dumps({'suite':'bounded 50-53 CPU/contract/pixel replay','passed':len(checks),'cases':checks,'dependencyFiles':len(load(R/'DEPENDENCIES.json')['repositoryRelativeFiles']),'GPUExecuted':False,'productApplied':False,'missingCleanUnderlaySamples':total_unknown,'PillowRequiredForReplay':False,'Python':sys.version.split()[0],'NumPy':np.__version__},indent=2))
