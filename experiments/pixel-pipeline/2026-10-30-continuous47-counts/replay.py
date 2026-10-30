"""Offline frozen six-frame CountPacket/rank/final-gate replay. No Unity/Pillow."""
from pathlib import Path
import ast,collections,hashlib,json,math,os,sys,types
import numpy as np

R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def guard(event,args):
 if event!='open' or not isinstance(args[0],(str,bytes,os.PathLike)):return
 p=Path(os.fsdecode(args[0])).resolve()
 if not(p.is_relative_to(R)or p.is_relative_to(Path(sys.base_prefix).resolve())):raise PermissionError('External input read blocked: '+str(p))
 if isinstance(args[1],str)and any(x in args[1]for x in 'wax+'):raise PermissionError('File writes blocked: '+str(p))
sys.addaudithook(guard)
def defs(file,name,initial=None):
 m=types.ModuleType(name);sys.modules[name]=m;m.__dict__.update({'np':np,'math':math,'Path':Path,'json':json,'hashlib':hashlib,'collections':collections})
 m.__dict__.update(initial or {})
 a=ast.parse(file.read_text(encoding='utf-8'));a.body=[x for x in a.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))]
 exec(compile(a,str(file),'exec'),m.__dict__);return m
eye=defs(R/'archive/eye_cache42.py','replay47_eye')
algo=defs(R/'archive/analyse_counts.py','replay47_counts',{'classify':eye.classify})
meta=load(R/'fixtures/frames.json');inputs=np.load(R/'fixtures/replay-inputs.npz')
expected=load(R/'archive/analysis/PACKET_REPLAY_AND_ALLOCATOR.json')
summary=load(R/'archive/analysis/SUMMARY.json');checks=[];changes=[];max_error=0
def check(name,ok):
 assert bool(ok),name
 checks.append(name)
check('new independent sequence and six ordered frames',len(meta)==6 and [m['frame']for m in meta]==[96,97,98,99,100,101]and all(m['sequenceId']==summary['sequenceId']for m in meta))
for i,(m,saved)in enumerate(zip(meta,expected)):
 d={key.split('_',1)[1]:inputs[key]for key in inputs.files if key.startswith(f'f{i:02}_')and not key.endswith('_GPU')}
 gpu=inputs[f'f{i:02}_GPU'];cpu,depth=algo.replay_packets(m,d);error=float(np.max(np.abs(cpu-gpu)));max_error=max(max_error,error)
 check(str(m['frame'])+': complete GPU packet replay',gpu.shape==(2,m['height'],m['width'],12)and error==saved['maxFullPacketCPUvsGPUError']and error<1e-4)
 check(str(m['frame'])+': source binding/flags match frozen record',m['sourceId']==saved['sourceId']and m['layerMode19']and not m['useHairRegion502']and not m['useIrisSurface582']and not m['useLashRegion583']and m['useClosedLash590'])
 for eye_index in range(2):
  stable=round(m['centres'][eye_index]['w']);want=saved['eyes'][str(stable)]
  selected,ranked,budget,area,I,cost=algo.allocator(gpu,m,eye_index)
  gate=algo.final_gate(d,depth[eye_index]);trial,*_=algo.allocator(gpu,m,eye_index,gate)
  ids=lambda a:[[x+m['x'],y+m['y']]for x,y in a]
  visible=d['eye-visible'];count=int(((np.rint(visible[...,1])==stable)&np.isin(np.rint(visible[...,0]),[2,3,4])).sum())
  check(f"{m['frame']}/eye{stable}: original area/budget/rank allocation",budget==want['budget']and area==want['wholeIrisArea']and ids(selected)==want['allocatedCells'])
  check(f"{m['frame']}/eye{stable}: stored final visible iris count",count==want['actualVisibleIrisCount'])
  check(f"{m['frame']}/eye{stable}: offline visibility counterfactual",ids(trial)==want['candidateFinalVisibilityGateCells']and all(gate[y,x]for x,y in trial))
  if selected!=trial:changes.append([m['frame'],stable])
  if stable==1:
   x,y=223-m['x'],52-m['y'];focus=want['focus']
   check(str(m['frame'])+': focus rank/cost/count exact',ranked.index((x,y))==focus['rank0based']and float(I[y,x])==focus['IrisCount']and float(cost[y,x])==focus['cost'])
   if m['frame']==100:
    x2,y2=224-m['x'],52-m['y']
    check('frame100 chosen replacement is actually behind opaque hair', (x2,y2)in selected and not gate[y2,x2]and d['hair-meta'][y2,x2,0]<depth[eye_index,y2,x2]and d['hair-meta'][y2,x2,3]==1)
check('1536 full packets replay at original max error',sum(2*m['width']*m['height']for m in meta)==1536 and max_error==summary['maxCPUvsGPU'])
check('only frame100 eye1 differs in offline gate',changes==[[100,1]])
f99=expected[3]['eyes']['1'];f100=expected[4]['eyes']['1']
check('focus keeps iris5 and budget2 while rank1 becomes rank2',f99['focus']['IrisCount']==f100['focus']['IrisCount']==5 and f99['budget']==f100['budget']==2 and f99['focus']['rank0based']==1 and f100['focus']['rank0based']==2)
rest=load(R/'archive/analysis/RESTORATION.json')
check('frozen restoration scope is explicit, not a live recheck',rest['objectsBefore']==rest['objectsAfter']==3065 and rest['dirtySetExact']and rest['sceneDirtyExact']and not rest['serializedOrDirtyChanges']and not rest['tracked12HashChanges'])
candidate=load(R/'archive/candidate/STATIC_AND_COUNTERFACTUAL_VERIFIED.json')
check('candidate remains unimported and GPU-unverified',candidate['workspaceOnly']and not candidate['GPUCompiled']and not candidate['productImported'])
print(json.dumps({'suite':'frozen continuous47 packet/rank/final-occlusion replay','passed':len(checks),'checks':checks,'frames':6,'packets':1536,'maxCPUvsGPU':max_error,'changedEyeFramePairs':changes,'externalInputReads':0,'newUnityCalls':0,'productIntegrated':False,'candidateGPUValidated':False,'memoryCauseConfirmed':False,'Python':sys.version.split()[0],'NumPy':np.__version__},indent=2))
