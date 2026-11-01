"""Read-only offline regression. No Unity command, extraction, save or rendering."""
from pathlib import Path
import io,json,struct,hashlib,zipfile,sys,numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'eye-close90'))
from surface_query90 import ProjectedSurface,choose_joint_bounds
from resolve91 import alpha_bounds

class Reader:
 def __init__(self,b):self.f=io.BytesIO(b)
 def i(self):return struct.unpack('<i',self.f.read(4))[0]
 def s(self):
  n=shift=0
  while True:
   b=self.f.read(1)[0];n|=(b&127)<<shift
   if b<128:break
   shift+=7;assert shift<35
  return self.f.read(n).decode('utf-8')
 def a(self,n,dtype='<f4'):return np.frombuffer(self.f.read(n*np.dtype(dtype).itemsize),dtype).copy()
 def mat(self):return self.a(16).reshape(4,4,order='F').astype(float)
 def end(self):assert not self.f.read(1)
def plane_bytes(b):
 r=Reader(b);assert r.i()==0x34365052 and r.i()==1;h={'sourceId':r.s(),'view':r.s(),'frame':r.i(),'serial':r.i()}
 for _ in range(4):r.s()
 size=[r.i(),r.i()];roi=[r.i()for _ in range(4)];a=r.a(roi[2]*roi[3]*4).reshape(roi[3],roi[2],4);r.end();assert np.isfinite(a).all();return h,a
def mesh_bytes(b):
 r=Reader(b);assert r.s()=='aux-mesh67/v1';identity=(r.s(),r.s(),r.i(),r.i());world=r.mat();v=r.a(r.i()*3).reshape(-1,3);n=r.a(r.i()*3).reshape(-1,3);uv=r.a(r.i()*2).reshape(-1,2);tri=[r.a(r.i(),'<i4').reshape(-1,3)for _ in range(r.i())];r.end();return identity,world,v,n,uv,tri
def camera_bytes(b):
 r=Reader(b);assert r.i()==0x34365043 and r.i()==1;r.s();r.s();r.i();r.i();r.i();r.a(2);view=r.mat();projection=r.mat();return view,projection
def corners(pic,uv):
 h,w=pic.shape;u,v=np.asarray(uv,np.float32);x=int(np.floor(float(u)*w-.5));y=int(np.floor(float(v)*h-.5));return[pic[h-1-((y+j)%h),(x+i)%w]/255 for j in range(2)for i in range(2)]
def old_frame(frame,name):
 old=HERE.parent/'native-feature89';paths=list((old/'capture89f').glob(f'*/frame-{frame}/{name}'))if old.exists()else[]
 if paths:return paths[0].read_bytes()
 archive=HERE.parent/'2026-11-01-native-authored89/raw89.zip';assert archive.exists(),'Previous89 committed raw archive required for old-surface verification'
 with zipfile.ZipFile(archive)as z:
  choices=[n for n in z.namelist()if n.endswith(f'/frame-{frame}/{name}')or n==f'frame-{frame}/{name}'];assert len(choices)==1;return z.read(choices[0])
def main():
 tests=[];summary=json.loads((HERE/'SUMMARY91.json').read_text());v=json.loads((HERE/'VISIBILITY_RESULT91.json').read_text());source=json.loads((HERE/'ALPHA_SOURCE91.json').read_text());masks=np.load(HERE/'ALPHA_MASKS91.npz');assert v['remainingNativePixels']==v['backingNativePixels']+v['eyelineNativePixels']==56;assert sum(c['nativePixels']for c in v['cells'])==20;tests.append('56 pixels decomposed36 backing/20 eyeline, not56 interchangeable noise cells')
 assert all(not c['decision']['paletteLookupAllowed']for c in v['cells']);assert v['robustBackgroundNativePixels']==4 and v['remainingUncertainNativePixels']==16;tests.append('only current mass-rule no-takeover1cell; other4cells remain unknown; no new palette emission')
 synthetic={'sources':{'3':{'alphaTest':True,'alphaBlend':False,'cutoff':.5}},'queries':[{'id':'mixed','sourceSubMesh':3,'min':.4,'max':.6}]};assert alpha_bounds(synthetic)['mixed']==[0.,1.];tests.append('mixed cutout envelope remains unknown')
 for q in source['queries']:assert np.max(abs(np.asarray(corners(masks['part'+str(q['sourceSubMesh'])],q['UVFloat32']))-q['alphaCorners']))<1e-7
 tests.append('178 native texture alpha queries independently reproduced from immutable alpha masks')
 _,world,vertex,normal,uv,tri=mesh_bytes(old_frame(140,'eye-evaluated.mesh'));view,projection=camera_bytes(old_frame(140,'source.camera'));worldVertex=np.c_[vertex,np.ones(len(vertex))]@world.T;surfaces={p:ProjectedSurface(worldVertex,uv,tri[p],view,projection,[480,272])for p in[1,3,4,6]};q=json.loads((HERE/'QUERIES91.json').read_text())['queries']
 for row in q:
  for part in surfaces:
   actual=surfaces[part].hits(row['actualSourceQuery']);saved=[h for h in row['hits']if h['sourcePart']==part];assert len(actual)==len(saved)
   for a,b in zip(actual,saved):assert a['primitive']==b['primitive']and abs(a['depth']-b['depth'])<1e-7 and np.max(abs(np.asarray(a['uv'])-b['uv']))<1e-7
 tests.append('110 same-frame source queries re-intersected against actual old140 mesh and camera')
 old=json.loads((HERE/'OLD96_RESULT91.json').read_text());assert len(old['rows'])==96 and old['opaqueCurrentSkinAtTarget']==96 and not old['RGBRecovered']
 for row in old['rows']:
  opaque=[h for h in row['actualCurrentSkinHits']if h['definitelyOpaque']];assert opaque and opaque[0]['projectedWinding']==1 and min(corners(masks['part3'],opaque[0]['uv']))>=.5
 tests.append('old96 genuine missing samples have front opaque skin evidence; no new-frame RGB substitution')
 back=json.loads((HERE/'CAPTURE_ANALYSIS91B.json').read_text());assert [r['cachedMissingCurrentSkinCells']for r in back['backingSummary']]==[0,0,0,1,1,4,4,0];assert max(r['controls']['backingRGBA']['max']for r in back['frames'])>.15 and not summary['newBacking']['adopted'];tests.append('current Close/reopen skin availability0/1/4/0 shown; failed RGB control stays unadopted')
 prod=json.loads((HERE/'PRODUCTION_RESULT92.json').read_text());last=prod['frames'][-1];pair=prod['examples'][-1];assert last['actualGeometryIdenticalToOriginalBaseline']and last['gMaxChangeFromBaseline']==0;assert last['producerVsManual']['0']['normalMax']==last['producerVsManual']['0']['SHMax']==0;assert abs(pair['productionLitAvailableMainLit'][1]-pair['manualUnboundTotals'][1])==0;assert pair['productionLitAvailableMainLit'][2]!=pair['manualUnboundTotals'][2];assert last['formulaMaxError']<2e-7;tests.append('normal/SH equality and main-light term difference measured in actual producer, not inferred from final RGB')
 for r in summary['restoration']:assert r['PlayExited']and not r['stateChanges']and r['nativeExact']==47 and r['dirty']==31 and r['RTbeforeAfter']==[30,30]
 tests.append('all5 Play exits retain public/native snapshots47, input, dirty31 and RT30')
 errors=json.loads((HERE/'GRAPH_ERRORS93.json').read_text());assert 'FixedAttachmentArray'in errors['primary']['message']and 'ZBinningJob'in errors['subsequent']['message'];assert not errors['runtimeRetryAfterThis'];tests.append('graph failure and renderer-job safety blocker retained, not counted as captures')
 graph=(HERE/'GraphSources93.cs').read_text();assert'AddUnsafePass<Data>'in graph and'GetNativeCommandBuffer'in graph and'SetRenderAttachment('not in graph;assert'UseTexture(resources.mainShadowsTexture)'in graph and'UseTexture(resources.additionalShadowsTexture)'in graph;assert'new Material[4]'in graph;tests.append('compile-only graph fix declares shadow/owned textures and keeps distinct per-pass material state')
 assert not summary['productIntegrated']and summary['productDefault']==77 and summary['newPlayRequestsPending']==0;tests.append('product77 unchanged; no pending or automatically repeated capture')
 zpath=HERE/'RAW91_92.zip';rawFrames=rawPlanes=0
 if zpath.exists():
  with zipfile.ZipFile(zpath)as z:
   for name in z.namelist():
    if not name.endswith('/RAW_MANIFEST.json'):continue
    prefix=name.rsplit('/',1)[0]+'/';raw=z.read(name);m=json.loads(raw);assert z.read(prefix+'RAW_COMPLETE76.marker').decode()==hashlib.sha256(raw).hexdigest();rawFrames+=1
    for n in z.namelist():
     if not n.startswith(prefix)or not n.endswith('.plane'):continue
     h,a=plane_bytes(z.read(n));assert h['sourceId']==m['sourceId']and h['frame']==m['frameIndex']and h['serial']==m['mainSerial'];rawPlanes+=1
  assert rawFrames==19 and rawPlanes>1000;tests.append('19 accepted raw packets/finite planes validate source,frame,serial and completion marker; failed93 excluded')
 manifest=HERE/'ARTIFACTS91.json'
 if manifest.exists():
  for row in json.loads(manifest.read_text())['files']:
   p=HERE/row['path'];assert p.stat().st_size==row['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==row['SHA256'],row['path']
 print(json.dumps({'passed':len(tests),'tests':tests,'rawFrames':rawFrames,'rawPlanes':rawPlanes,'GPUFixValidated':False,'productIntegrated':False},indent=2))
if __name__=='__main__':main()
