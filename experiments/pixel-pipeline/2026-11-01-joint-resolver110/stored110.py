"""Small bounded packet adapters, with no import of Unity/scene executors.
Plane format from capture68; homography calibration from source_curve105.
Paths can use the original workspace or frozen sibling repository snapshots.
"""
from pathlib import Path
import sys,json,zipfile
import os
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
def related(local,snapshot):
    p=R/local
    return p if p.exists()else R/snapshot
P109=related('pigment-carrier109','2026-11-01-pigment-carrier109')
P108=related('joint-model108','2026-11-01-joint-objective108')
P107=related('joint-lid107','2026-11-01-joint-visibility107')
sys.path.insert(0,str(P109))
from io109 import Reader,buffer,ZipNode

class FrozenNode(ZipNode):
    def __truediv__(self,name):return FrozenNode(self.archive,self.name+'/'+name)
    def exists(self):
        with zipfile.ZipFile(self.archive)as z:return self.name in z.namelist()
class Supplement105Node(FrozenNode):
    def __truediv__(self,name):return Supplement105Node(self.archive,self.name+'/'+name)
    def read_bytes(self):
        with zipfile.ZipFile(self.archive)as z:
            if self.name in z.namelist():return z.read(self.name)
        with zipfile.ZipFile(H/'RAW105_S4_110.zip')as z:return z.read(self.name)
    def exists(self):
        with zipfile.ZipFile(self.archive)as z:
            if self.name in z.namelist():return True
        with zipfile.ZipFile(H/'RAW105_S4_110.zip')as z:return self.name in z.namelist()
def source_packet(row):
    p=Path(row['sourcePacket'])
    if p.exists()and os.environ.get('PIXEL110_FROZEN_INPUTS')!='1':return p
    if row['name'].startswith('closed105'):return Supplement105Node(P109/'RAW109.zip','105/frame'+str(row['frame']))
    return FrozenNode(P107/'RAW107.zip','final54/frame'+str(row['frame']))
def plane(path):
    r=Reader(path);assert r.i()==0x34365052 and r.i()==1;h=r.identity();h.update(zip(['producer','channel','encoding','yConvention'],[r.s()for _ in range(4)]));h['size']=[r.i(),r.i()];h['roi']=[r.i()for _ in range(4)];a=r.a(h['roi'][2]*h['roi'][3]*4).reshape(h['roi'][3],h['roi'][2],4);r.end();return h,a
def load_fields(p):
    m=json.loads((p/'RAW_MANIFEST.json').read_text(encoding='utf8'));scale=m.get('jointInputSampleScale107',4)
    if scale==8:
        w,h=m['forward102']['denseSize'];ls=np.zeros((4,5,h,w,4),np.float32);v=np.zeros((4,h,w,4),np.float32)
        for part in [1,2]:ls[part,1]=np.flipud(plane(p/('D-part'+str(part)+'-meta.plane'))[1])
        for ch,n in enumerate(['rgba','meta','rest','uv']):ls[3,ch]=np.flipud(plane(p/('D-lid-'+n+'.plane'))[1])
        v[1:4]=buffer(p/'dense-three-part-visibility.f32').reshape(3,h,w,4)
    else:
        w,h=m['forward102']['canonicalSize'];ls=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);v=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
    return m,scale,ls,v
def fit_homography(source,target):
    centre=source.mean(0);scale=np.max(np.ptp(source,axis=0));q=(source-centre)/scale;x,y=q.T;u,v=target.T;zero=np.zeros(len(q));one=np.ones(len(q));a=np.stack([np.c_[x,y,one,zero,zero,zero,-u*x,-u*y],np.c_[zero,zero,zero,x,y,one,-v*x,-v*y]],axis=1).reshape(-1,8);value=np.linalg.lstsq(a,target.reshape(-1),rcond=None)[0];p=np.r_[value,1].reshape(3,3);n=np.array([[1/scale,0,-centre[0]/scale],[0,1/scale,-centre[1]/scale],[0,0,1.]])
    return p@n
def upper_arc(row):
    q=np.asarray(row['authoredParent']);n=len(q);left=int(np.argmin(q[:,0]));right=int(np.argmax(q[:,0]));chains=[]
    for direction in [1,-1]:
        chain=[];i=left
        for _ in range(n+1):
            chain.append(i)
            if i==right:break
            i=(i+direction)%n
        p=q[chain];w=np.linalg.norm(np.diff(p,axis=0),axis=1);score=float(w@((p[:-1,1]+p[1:,1])*.5)/w.sum());chains.append((score,chain))
    return min(chains,key=lambda a:a[0])[1]
