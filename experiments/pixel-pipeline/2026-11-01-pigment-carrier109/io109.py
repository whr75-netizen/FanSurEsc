"""Bounded linear binary readers for existing aux-mesh67 and f32 packets.
No Unity JSON parser or reserialization. All declared lengths stay in input.
"""
import struct,json,zipfile,numpy as np
from pathlib import Path,PurePosixPath
class ZipNode:
    def __init__(self,archive,name):
        self.archive=Path(archive);self.name=str(PurePosixPath(name));assert '..'not in PurePosixPath(name).parts
    def __truediv__(self,name):return ZipNode(self.archive,str(PurePosixPath(self.name)/name))
    def read_bytes(self):
        with zipfile.ZipFile(self.archive)as z:return z.read(self.name)
    def read_text(self,encoding='utf8'):return self.read_bytes().decode(encoding)
def entries(root,kind,legacy):
    index=root/'RAW_INPUT109_INDEX.json'
    if index.exists():return json.loads(index.read_text(encoding='utf8'))['entries'+kind]
    return legacy()
def packet(root,entry,kind):
    if(root/'RAW109.zip').exists():return ZipNode(root/'RAW109.zip',kind+'/frame'+str(entry['frame']))
    return Path(entry['output'])
class Reader:
    def __init__(self,path):self.b=memoryview(path.read_bytes());self.at=0
    def take(self,n):
        assert n>=0 and self.at+n<=len(self.b);q=self.b[self.at:self.at+n];self.at+=n;return q
    def i(self):return struct.unpack('<i',self.take(4))[0]
    def s(self):
        n=0;shift=0
        while True:
            b=self.take(1)[0];n|=(b&127)<<shift
            if not b&128:break
            shift+=7;assert shift<35
        return bytes(self.take(n)).decode('utf8')
    def a(self,n,dtype='<f4'):return np.frombuffer(self.take(n*np.dtype(dtype).itemsize),dtype=dtype).copy()
    def mat(self):return self.a(16).reshape(4,4,order='F').astype(float)
    def identity(self):return {'sourceId':self.s(),'viewId':self.s(),'frameIndex':self.i(),'renderSerial':self.i()}
    def end(self):assert self.at==len(self.b)
def mesh(p):
    r=Reader(p);assert r.s()=='aux-mesh67/v1';identity=r.identity();matrix=r.mat();v=r.a(r.i()*3).reshape(-1,3);r.a(r.i()*3);uv=r.a(r.i()*2).reshape(-1,2);indices=[r.a(r.i(),'<i4').reshape(-1,3)for _ in range(r.i())];r.end()
    assert len(uv)==len(v)and all(not len(t)or t.min()>=0 and t.max()<len(v)for t in indices)
    return identity,matrix,v,uv,indices
def buffer(p):
    b=p.read_bytes();n,stride=struct.unpack_from('<ii',b);assert n>=0 and stride==16 and len(b)==8+n*16;return np.frombuffer(b,offset=8,dtype='<f4').reshape(n,4)
def intersects(a,b,x,y):
    lo=0.;hi=1.;delta=b-a
    for axis,start in enumerate((x,y)):
        if delta[axis]==0:
            if not start<=a[axis]<=start+1:return False
        else:
            t0=(start-a[axis])/delta[axis];t1=(start+1-a[axis])/delta[axis];lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
    return hi>=lo

def joint_arrays(layers,vis):
    """Unchanged float32 contribution policy from export108; reusable pure IO
    reference here avoids importing the older scene-analysis entry points."""
    a=vis[1:4,...,0].copy();b=vis[1:4,...,1].copy();z=layers[1:4,1,...,0];lo=a.copy();hi=b.copy()
    for p in range(3):
        for q in range(3):
            if p==q:continue
            valid=(z[q]>0)&(b[q]>0);front=valid&(z[q]<z[p]-np.float32(3e-5));tie=valid&(abs(z[q]-z[p])<=np.float32(3e-5));lo[p]*=np.where(front|tie,1-b[q],1);hi[p]*=np.where(front,1-a[q],1)
    clo=np.ones(a.shape[1:],np.float32);chi=clo.copy()
    for p in range(3):clo*=1-b[p];chi*=1-a[p]
    allhi=np.concatenate([hi,chi[None]]);dominant=np.array([lo[p]>np.max(allhi[np.arange(4)!=p],axis=0)for p in range(3)])
    return lo,hi,clo,chi,dominant
