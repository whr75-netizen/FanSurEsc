"""Portable final54 frozen GPU verifier. No Unity calls or rendering.
Run python -B recheck107.py (numpy required; no installation performed).
Checks the implemented rule, not artistic correctness;107 remains rejected.
"""
from pathlib import Path
import io,json,struct,hashlib,zipfile
import numpy as np
from joint_reference107 import apply,tests,contributions
from curve_reference106 import apply as old_apply
H=Path(__file__).resolve().parent
def buf(b,stride=16):
 n,s=struct.unpack_from('<ii',b);assert s==stride and len(b)==8+n*s
 return np.frombuffer(b,offset=8,dtype='<f4').reshape(n,s//4)
class Reader:
 def __init__(self,b):self.f=io.BytesIO(b)
 def i(self):return struct.unpack('<i',self.f.read(4))[0]
 def s(self):
  n=0;shift=0
  while True:
   b=self.f.read(1)[0];n|=(b&127)<<shift
   if not b&128:break
   shift+=7;assert shift<35
  assert n<4096;return self.f.read(n).decode('utf-8')
def plane(b):
 r=Reader(b);assert r.i()==0x34365052 and r.i()==1
 h={'sourceId':r.s(),'viewId':r.s(),'frameIndex':r.i(),'renderSerial':r.i()}
 for _ in range(4):r.s()
 r.i();r.i();roi=[r.i()for _ in range(4)];a=np.frombuffer(r.f.read(),dtype='<f4').reshape(roi[3],roi[2],4);return h,a
def main():
 index=json.loads((H/'RAW107_INDEX.json').read_text(encoding='utf-8'));cells=0;frames=0;proofs=0;hashes=0;planes=0
 with zipfile.ZipFile(H/'RAW107.zip')as z:
  assert set(z.namelist())=={r['file']for r in index}
  for r in index:
   b=z.read(r['file']);assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];hashes+=1
  manifests=[n for n in z.namelist()if n.startswith('final54/')and n.endswith('/RAW_MANIFEST.json')]
  for name in manifests:
   m=json.loads(z.read(name));folder=name.rsplit('/',1)[0];assert z.read(folder+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(z.read(name)).hexdigest();assert m['jointInputSampleScale107']==8 and m['frameUnchangedDuringReadback']and m['curveCPUUploadEqualsGPU106']
   def b(n):return buf(z.read(folder+'/'+n+'.f32'))
   arrays={}
   for p in z.namelist():
    if p.startswith(folder+'/')and p.endswith('.plane'):
     h,a=plane(z.read(p));assert h['sourceId']==m['sourceId']and h['frameIndex']==m['frameIndex']and h['renderSerial']==m['mainSerial'];arrays[p.rsplit('/',1)[1][:-6]]=a;planes+=1
   assert len(arrays)==25
   w,h=m['forward102']['canonicalSize'];dw,dh=m['forward102']['denseSize'];normal=b('canonical-layers').reshape(4,5,h,w,4);vis=b('canonical-visibility').reshape(4,h,w,4)
   ls=np.zeros((4,5,dh,dw,4),np.float32);dv=np.zeros((4,dh,dw,4),np.float32)
   for p in [1,2]:ls[p,1]=np.flipud(arrays['D-part'+str(p)+'-meta'])
   for c,n in enumerate(['rgba','meta','rest','uv']):ls[3,c]=np.flipud(arrays['D-lid-'+n])
   dv[1:4]=b('dense-three-part-visibility').reshape(3,dh,dw,4)
   source=buf(z.read(folder+'/curve-segments106.f32'),32).reshape(-1,2,4);base=[b('canonical-'+n)for n in ['colour','identity','decision']]
   ref=apply(source,ls,dv,*base,scale=8);old=old_apply(source,normal,vis,*base)
   for prefix,want in [('curve-',ref),('legacy106-',old)]:
    got=[b(prefix+n)for n in ['colour','identity','decision','audit']]
    assert all(np.array_equal(got[j],want[j])for j in [0,1,2])and np.array_equal(got[3][:,0],want[3][:,0])
   for k in np.flatnonzero(ref[3][:,0]==3):
    q=round(float(ref[3][k,2]))-1;y,x=divmod(q,dw);lo,hi=contributions(ls,dv,y,x);assert lo[2]>max(hi[0],hi[1],hi[3])and np.array_equal(ref[0][k,:3],ls[3,0,y,x,:3]);proofs+=1
   cells+=len(base[0]);frames+=1
 assert frames==54 and cells==7959 and planes==1350
 result={'frozenActualGPUFrames':frames,'cells':cells,'planeSourceChecks':planes,'CPUGPUMismatch':0,'nativeFrontPigmentProofs':proofs,'rawFileHashes':hashes,'synthetic':tests(),'candidateAccepted':False,'UnityExecutedByThisScript':False};print(json.dumps(result));return result
if __name__=='__main__':main()
