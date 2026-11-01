"""Portable rebuild + CPU/GPU equality from saved fixture. No Unity calls."""
from pathlib import Path
import json,struct,io,numpy as np
from feature_layer88 import *
HERE=Path(__file__).resolve().parent
class R:
 def __init__(self,p):self.f=p.open('rb')
 def i(self):return struct.unpack('<i',self.f.read(4))[0]
 def a(self,n):return np.frombuffer(self.f.read(n*4),'<f4').copy()
 def s(self):
  n=shift=0
  while True:
   b=self.f.read(1)[0];n|=(b&127)<<shift
   if not b&128:break
   shift+=7
  return self.f.read(n).decode()
 def end(self):assert self.f.read()==b'';self.f.close()
def packet(path):
 r=R(path);assert r.s()=='feature-layer88/v1';source=r.s();frame,serial,w,h=[r.i()for _ in range(4)];scale,ox,oy,ax,ay=r.a(5);n=r.i();cells=r.a(n*8).reshape(n,8);palette=r.a(r.i()*4).reshape(-1,4);rx,ry,rw,rh=[r.i()for _ in range(4)];meta=r.a(5*rw*4*rh*4*4).reshape(5,rh*4,rw*4,4);ray=r.a(12).reshape(4,3);planes=r.a(8).reshape(2,4);owners=[r.i(),r.i()];r.end();return dict(sourceId=source,frame=frame,serial=serial,w=w,h=h,scale=scale,origin=np.array([ox,oy]),anchor=np.array([ax,ay]),cells=cells,palette=palette,roi=[rx,ry,rw,rh],meta=meta,ray=ray,planes=planes,owners=owners)
def run():
 fixture=json.loads((HERE/'SOURCE_FIXTURE88.json').read_text());src=[SourcePixel(**p)for p in fixture['source']];cache=FeatureCache();count=0;maxerr=0
 for f in fixture['frames']:
  inp=packet(HERE/f"validated/frame{f['frame']}/INPUT88.bin");expected=np.load(HERE/f"validated/frame{f['frame']}/EXPECTED88.npz");s=cache.update(src,{int(k):np.array(v)for k,v in f['H'].items()},tuple(f['scope']));cells=np.array([[*r['xy'],r['owner'],r['part'],r['palette'],r['sourceIndex'],r['foregroundArea'],r['partArea']]for r in s['rows']],np.float32);assert np.array_equal(cells,inp['cells']);assert np.array_equal(s['anchor'].astype(np.float32),inp['anchor']);assert inp['sourceId']==f['sourceId']
  # Existing expected values use the original double camera ray construction.
  # GPU files independently validate all binaryfloat32 inputs and outputs.
  for ch,name in enumerate(['colour','identity','coverage']):
   p=HERE/f"gpu-output/frame{f['frame']}-{ch}.bin"
   if not p.exists():
    info=json.loads((HERE/'gpu88/GPU_RESULT88.json').read_text());p=Path(info['output'])/p.name
   r=R(p);assert r.s()=='feature-layer88-GPU/v1'and r.s()==f['sourceId'];assert [r.i(),r.i(),r.i(),r.i()]==[inp['frame'],inp['serial'],inp['w'],inp['h']];a=r.a(inp['w']*inp['h']*4).reshape(inp['h'],inp['w'],4);r.end();err=float(abs(a-expected[name]).max());maxerr=max(maxerr,err);assert err==0
  count+=1
 assert count==24;print(json.dumps({'sourceRebuildsVerified':count,'GPUOutputFieldsCompared':count*3,'maxDifference':maxerr,'UnityCalls':0,'productActivated':False},indent=2))
if __name__=='__main__':run()
