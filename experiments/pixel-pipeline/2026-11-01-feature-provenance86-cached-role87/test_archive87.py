"""Portable actual-packet tests, stdlib + NumPy, never contacts Unity."""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile
import json,hashlib,struct,numpy as np
from guard76 import supported
HERE=Path(__file__).resolve().parent
class R:
 def __init__(self,b):self.f=BytesIO(b)
 def i(self):return struct.unpack('<i',self.f.read(4))[0]
 def s(self):
  n=shift=0
  while True:
   b=self.f.read(1)[0];n|=(b&127)<<shift
   if not b&128:break
   shift+=7;assert shift<35
  return self.f.read(n).decode()
 def a(self,n):return np.frombuffer(self.f.read(n*4),'<f4').copy()
 def end(self):assert self.f.read()==b''
def plane(b):
 r=R(b);assert[r.i(),r.i()]==[0x34365052,1];h={'sourceId':r.s(),'viewId':r.s(),'frame':r.i(),'serial':r.i()}
 for _ in range(4):r.s()
 h['size']=[r.i(),r.i()];h['roi']=[r.i()for _ in range(4)];x,y,w,hh=h['roi'];a=r.a(w*hh*4).reshape(hh,w,4);r.end();return h,a
def rgb8(c):
 c=np.clip(c,0,1);return np.rint(np.where(c<=.0031308,c*12.92,1.055*c**(1/2.4)-.055)*255).astype(np.uint8)
def run():
 result=json.loads((HERE/'RESULT87.json').read_text());assert result['sourceRoleMismatchCount']==0 and result['nativeExact']==45 and all(result['restore'].values())and result['RTbeforeAfter']==[30,30]
 bank=np.load(HERE/'source-bank87.npz');role,colour=bank['role'],bank['colour'];n=rgb=guard=planeCount=0
 with ZipFile(HERE/'raw87.zip')as z:
  dirs=sorted({s.rsplit('/',1)[0]for s in z.namelist()if s.endswith('/RAW_MANIFEST.json')},key=lambda p:int(p.split('-')[-1]))
  assert len(dirs)==29
  for folder in dirs:
   payload=z.read(folder+'/RAW_MANIFEST.json');m=json.loads(payload);assert z.read(folder+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(payload).hexdigest();arr={};headers={}
   for name in z.namelist():
    if not name.startswith(folder+'/')or not name.endswith('.plane'):continue
    ph,a=plane(z.read(name));assert ph['sourceId']==m['sourceId']and ph['frame']==m['frameIndex']and ph['serial']==m['mainSerial'];assert np.isfinite(a).all();arr[Path(name).stem]=a;headers[Path(name).stem]=ph;planeCount+=1
   x,y,w,h=headers['old-intrinsic']['roi'];yy,xx=np.mgrid[:h,:w];p=np.stack([xx+x+.5,271-yy-y+.5,np.ones_like(xx),np.zeros_like(xx)],-1).astype(np.float32);pred=np.zeros((h,w,2),np.float32);sourcexy=np.zeros((h,w,2),int)
   for ei,sid in enumerate([int(v[3])for v in m['eyeFeature']['centres']]):
    matrix=np.array(m['eyeFeature']['inverse'][ei],np.float32).reshape(4,4,order='F');q=p@matrix.T;q=q[...,:2]/q[...,2,None];k=np.floor(q).astype(int);valid=(k[...,0]>=0)&(k[...,0]<480)&(k[...,1]>=0)&(k[...,1]<272);ck=np.clip(k,[0,0],[479,271]);sr=role[ck[...,1],ck[...,0]];take=valid&(sr[...,1]==sid)&np.isin(sr[...,0],[1,4])&(pred[...,0]==0);pred[take]=sr[take,:2];sourcexy[take]=k[take]
   intr=arr['old-intrinsic'];owner=arr['old-eye-owner'];native=(pred[...,0]>0)&(intr[...,0]==0)&(np.rint(owner[...,0])==7);assert not(np.any(pred!=intr[...,:2],-1)&~native).any()
   for iy,ix in np.argwhere((owner[...,3]==1)&(intr[...,0]>0)):
    sx,sy=sourcexy[iy,ix];assert np.array_equal(rgb8(arr['old-eye-rgba'][iy,ix,:3]),colour[sy,sx,:3]);rgb+=1
   # Baseline to protected final guard uses actual recorded control flag.
   r=R(z.read(folder+'/baseline76.buffer'));assert r.s()=='baseline76/v1';assert[r.s(),r.s(),r.i(),r.i()]==[m['sourceId'],'head',m['frameIndex'],m['mainSerial']];roi=[r.i()for _ in range(4)];assert roi==[x,y,w,h]and r.i()==96;baseline=r.a(w*h*24).reshape(h,w,6,4);r.end()
   raw=z.read(folder+'/eye-records76.bin.partial');digest=hashlib.sha256(raw).hexdigest();assert z.read(folder+f'/ok-{digest}-{len(raw)}.complete')==b''
   r=R(raw);assert r.s()=='pixel-eye-readback70/v1'and r.s()=='Pixel348:sixteenFloat4InShaderOrder';assert[r.s(),r.s(),r.i(),r.i()]==[m['sourceId'],'head',m['frameIndex'],m['mainSerial']];r.s();rx,ry,rw,rh=[r.i()for _ in range(4)];assert r.i()==256;rec=np.empty((rh,rw,16,4),np.float32)
   for iy in range(rh):assert[r.i(),r.i()]==[ry+iy,(ry+iy)*480+rx];rec[iy]=r.a(rw*64).reshape(rw,16,4)
   r.end();predguard=np.zeros((rh,rw),bool)
   for iy in range(rh):
    for ix in range(rw):
     v=baseline[iy+ry-y,ix+rx-x];sm=[arr[f'S{si}-meta'][iy*4:iy*4+4,ix*4:ix*4+4].reshape(16,4)for si in range(7)];pt=[arr[f'S{si}-point'][iy*4:iy*4+4,ix*4:ix*4+4].reshape(16,4)for si in range(4)];ok,sid,weight=supported(v[0],v[1],v[4],sm,pt,arr['old-eye-owner'][iy+ry-y,ix+rx-x]);predguard[iy,ix]=ok
   assert np.array_equal(predguard,rec[...,14,2]>.5);assert np.array_equal(rec[...,0,:][predguard],baseline[ry-y:ry-y+rh,rx-x:rx-x+rw,0,:][predguard]);guard+=int(predguard.sum())
   assert m['frozenOriginal76']['sameFrame']and m['frameUnchangedDuringReadback'];n+=1
  assert n==29 and rgb==result['directTemplateRGB8Checked']==509 and guard==result['protected76RGBExactCells']==339
 trace=json.loads((HERE/'TRACE87.json').read_text());assert .99<trace['sweepXSpanLogicalCells']<1.01 and trace['sweepReturnDeltaCells']==[0,0]and trace['sameEvaluatedMeshAcrossSweep'];assert min(trace['unoccludedUniqueTranslationNormalisedShapesByEye'])>1
 assert result['exporterManifestPlaneListIssueFrames']==[v['frame']for v in result['frames']]
 tested=(HERE/'TESTED_Capture87.cs').read_text();prepared=(HERE/'prepare87.py').read_text();assert 'report["packetComplete"]=true;report["planes"]=planes;CreateOnly73.Text'in prepared and 'report["packetComplete"]=true;CreateOnly73.Text'in tested
 c=json.loads((HERE/'CANDIDATE87.json').read_text());assert hashlib.sha256((HERE/'CachedSourceRole87.compute').read_bytes()).hexdigest()==c['candidateSHA']
 print(json.dumps({'actualFrames':n,'planeIdentitiesVerified':planeCount,'directSourceRGB8':rgb,'protected76RGBExactCells':guard,'realPhaseSpan':trace['sweepXSpanLogicalCells'],'aliasCounterexampleByEye':trace['unoccludedUniqueTranslationNormalisedShapesByEye'],'productDefaultActivated':False,'UnityCalls':0},indent=2))
if __name__=='__main__':run()
