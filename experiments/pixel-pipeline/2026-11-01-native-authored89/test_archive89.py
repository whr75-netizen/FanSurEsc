"""Portable saved-data audit. No Unity, project path, write or original assets."""
from pathlib import Path
from io import BytesIO
import hashlib,json,struct,zipfile
import numpy as np
class R:
 def __init__(self,data):self.f=BytesIO(data)
 def i(self):return struct.unpack('<i',self.f.read(4))[0]
 def s(self):
  n=0;shift=0
  while True:
   b=self.f.read(1)[0];n|=(b&127)<<shift
   if b<128:break
   shift+=7
  return self.f.read(n).decode()
 def a(self,n):return np.frombuffer(self.f.read(n*4),'<f4').copy()
 def end(self):assert self.f.tell()==len(self.f.getbuffer())
def run(root):
 manifest=json.loads((root/'ARTIFACTS89.json').read_text());assert all(hashlib.sha256((root/x['file']).read_bytes()).hexdigest()==x['sha256']for x in manifest['files'])
 inputs=zipfile.ZipFile(root/'final-inputs89.zip');gpu=zipfile.ZipFile(root/'gpu-final89.zip');raw=zipfile.ZipFile(root/'raw89.zip');count=0;fields=0;outside=0
 for name in inputs.namelist():
  if not name.endswith('.bin'):continue
  r=R(inputs.read(name));assert r.s()=='final-palette89/v1';sid,variant=r.s(),r.s();frame,serial,w,h,n=[r.i()for _ in range(5)];base=r.a(w*h*4).reshape(h,w,4);select=r.a(w*h*4).reshape(h,w,4);palette=r.a(n*4).reshape(n,4);r.end();mask=select[...,0]>0;expected=base.copy();k=select[...,0][mask].astype(int)-1;assert((k>=0)&(k<n)).all();expected[mask]=palette[k];valid=np.zeros_like(base);valid[...,0]=1;bad=select[...,3]<0;valid[bad,0]=0;valid[bad,1]=2
  for ch,value in enumerate([expected,select,valid]):
   stem=Path(name).stem;r=R(gpu.read(stem+f'-{ch}.bin'));assert r.s()=='final-palette89-GPU/v1';assert[r.s(),r.s(),r.i(),r.i(),r.i(),r.i()]==[sid,variant,frame,serial,w,h];actual=r.a(w*h*4).reshape(h,w,4);r.end();assert np.array_equal(actual,value);fields+=1
   if ch==0:outside+=int(np.any(actual[~mask]!=base[~mask],axis=1).sum())
  count+=1
 packets=0;planes=0;bankSamples=0;reg=json.loads((root/'REGISTRATION89.json').read_text());projections={e['eye']:np.asarray(e['nativeToAuthoredProjection'])for e in reg['eyes']};bank={(c['eye'],c['role'],*c['sourceXY']):c['sourceRGBA8'][:3]for c in reg['cells']}
 def readplane(data):
  r=R(data);assert[r.i(),r.i()]==[0x34365052,1];identity=[r.s(),r.s(),r.i(),r.i()]
  for _ in range(4):r.s()
  size=[r.i(),r.i()];roi=[r.i()for _ in range(4)];a=r.a(roi[2]*roi[3]*4).reshape(roi[3],roi[2],4);r.end();return identity,a
 for name in raw.namelist():
  if not name.endswith('/RAW_MANIFEST.json'):continue
  prefix=name.rsplit('/',1)[0]+'/';data=raw.read(name);m=json.loads(data);assert raw.read(prefix+'RAW_COMPLETE76.marker').decode()==hashlib.sha256(data).hexdigest()
  for entry in m['planes']:
   r=R(raw.read(prefix+entry['file']));assert[r.i(),r.i()]==[0x34365052,1];assert[r.s(),r.s(),r.i(),r.i()]==[entry['sourceId'],entry['viewId'],entry['frameIndex'],entry['renderSerial']];planes+=1
  for part,role in [(1,1),(2,4)]:
   _,c=readplane(raw.read(prefix+f'retarget-part{part}-0.plane'));_,meta=readplane(raw.read(prefix+f'retarget-part{part}-1.plane'));_,point=readplane(raw.read(prefix+f'retarget-part{part}-2.plane'));valid=meta[...,0]>0
   for owner,P in projections.items():
    take=valid&(np.rint(meta[...,2])==owner);q=np.c_[point[take,:3],np.ones(take.sum())]@P;k=np.floor(q).astype(int);linear=np.clip(c[take,:3],0,1);actual=np.rint(np.where(linear<=.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)*255).astype(np.uint8);expected=np.asarray([bank[(owner,role,int(x),int(y))]for x,y in k],np.uint8);assert np.array_equal(actual,expected);bankSamples+=len(k)
  packets+=1
 assert count==64 and fields==192 and packets==32 and outside==0 and bankSamples==11714
 v=json.loads((root/'VALIDATION89.json').read_text());assert v['status'].startswith('NOT_ADOPTED');assert v['sourceBank']['maxRGB8Error']==0;assert v['canonicalSweep']['identitySignatures']==1
 return {'manifestFiles':len(manifest['files']),'actualRawPackets':packets,'sameFramePlaneHeaders':planes,'actualBankSamples':bankSamples,'bankRGB8MaxError':0,'GPUreplayPackets':count,'GPUfieldsCompared':fields,'GPU_CPUFloatDifferences':0,'outsideScopeChanges':outside,'candidateAccepted':False}
if __name__=='__main__':print(json.dumps(run(Path(__file__).resolve().parent),indent=2))
