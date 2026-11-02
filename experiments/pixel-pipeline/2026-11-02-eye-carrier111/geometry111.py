"""Direct same-frame111 source arrays. No reconstruction or cross-frame morph."""
from pathlib import Path
import sys,json,os,zipfile
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
P110=R/'joint-resolver110'if(R/'joint-resolver110').exists()else R/'2026-11-01-joint-resolver110';sys.path.insert(0,str(P110))
from stored110 import plane,P109
from io109 import Reader,buffer,joint_arrays
def read(p):
    if isinstance(p,Path)and not p.exists()and p.parent==H and(H/'ANALYSIS111.zip').exists():
        with zipfile.ZipFile(H/'ANALYSIS111.zip')as z:return json.loads(z.read(p.name))
    return json.loads(p.read_text(encoding='utf8'))
def matrix(v):return np.array(v,float).reshape(4,4,order='F')
class Frozen111:
    def __init__(self,name):self.name=name.strip('/')
    def __truediv__(self,name):return Frozen111(self.name+'/'+str(name))
    @property
    def parent(self):return Frozen111(self.name.rsplit('/',1)[0])
    def read_bytes(self):
        with zipfile.ZipFile(H/'RAW111.zip')as z:return z.read(self.name)
    def read_text(self,encoding='utf8'):return self.read_bytes().decode(encoding)
def load(p):
    p=p if isinstance(p,Frozen111)else Path(p);m=read(p/'RAW_MANIFEST.json');t=read(p/'SOURCE_TRANSFORMS111.json');r=Reader(p/'SOURCE_GEOMETRY111.bin');assert r.s()=='feature-source-geometry111/v1';sid=r.s();frame=r.i();serial=r.i();scope=r.s();assert sid==m['sourceId']==t['sourceId']and frame==m['frameIndex']==t['frame']and serial==m['mainSerial']==t['serial'];assert scope==m['forward102']['scope'];n=r.i();assert 0<n<=131072;world4=r.a(n*4).reshape(n,4).astype(float);rest4=r.a(n*4).reshape(n,4).astype(float);uv=r.a(n*2).reshape(n,2).astype(float);nt=r.i();assert 0<nt<=262144
    raw=r.take(nt*48);dtype=np.dtype([('ints','<i4',8),('eye','<f4',4)]);tr=np.frombuffer(raw,dtype=dtype).copy();inds=tr['ints'][:,:4];sources=tr['ints'][:,4:];owners=tr['eye'];assert inds[:,:3].min()>=0 and inds[:,:3].max()<n
    nm=r.i();materials=r.a(nm*12).reshape(nm,3,4);stride=r.i();count=r.i();assert count==4*stride;parts=r.a(count,'<i4').reshape(4,stride);r.end();reg=read(p.parent/'REGISTRATION_CURRENT102.json');px={e['owner']:np.array(e['x'])for e in reg['projection']};py={e['owner']:np.array(e['y'])for e in reg['projection']};head=matrix(t['headMatrix']);view=matrix(t['currentPhysicalView']);proj=matrix(t['currentPhysicalProjection']);nr=m['forward102']['nativeRegistration'];anchor=np.array(nr['anchor']);bounds=np.array(nr['bounds']);hom={int(round(e[3])):matrix(v)for e,v in zip(t['eyeCentres'],t['authoredToHead'])};headPos=world4@np.linalg.inv(head).T;maps={}
    for owner in px:
        q=np.c_[headPos@px[owner],headPos@py[owner],np.ones(n),np.zeros(n)]@hom[owner].T;maps[owner]=q[:,:2]/q[:,2,None]-anchor-bounds[:2]
    vv=world4@view.T;clip=vv@proj.T;physicalXY=np.c_[(clip[:,0]/clip[:,3]*.5+.5)*480,(.5-clip[:,1]/clip[:,3]*.5)*272]
    return {'path':p,'manifest':m,'transforms':t,'sourceId':sid,'frame':frame,'serial':serial,'scope':scope,'world':world4[:,:3],'world4':world4,'rest':rest4[:,:3],'rest4':rest4,'uv':uv,'triangles':inds,'sources':sources,'triOwners':owners,'materials':materials,'partMap':parts,'maps':maps,'view':view,'projection':proj,'physicalXY':physicalXY,'physicalW':clip[:,3],'depth':-vv[:,2],'projectionX':px,'projectionY':py,'size':np.array(m['forward102']['canonicalSize'])//4,'offset':anchor+bounds[:2]}
def packet_list(kind='original'):
    if os.environ.get('PIXEL111_FROZEN_INPUTS')=='1':
        index=read(H/'CAPTURE_INDEX111.json');state=index['states'][kind];return state,[Frozen111(v['archivePrefix'])for v in index['packets']if v['kind']==kind]
    if kind=='geometry':
        root=H/'gpu-carrier';state=read(sorted(root.glob('STATE111G-*.json'))[-1]);return state,[Path(v['output'])for v in state['sequencePackets']]
    root=H/'capture';state=read(sorted(root.glob('STATE111-*.json'))[-1]);assert state['PlayExited']and not state.get('error')and not state.get('restorationError');return state,[Path(v['output'])for v in state['sequencePackets']]
if __name__=='__main__':
    s,paths=packet_list();c=load(paths[3]);print(json.dumps({'identity':[c['sourceId'],c['frame'],c['serial']],'vertices':len(c['world']),'triangles':len(c['triangles']),'partMaterials':{str(p):[{'material':int(mi),'properties':c['materials'][mi].tolist()}for mi in np.unique(c['triangles'][c['partMap'][i][c['partMap'][i]>=0],3])]for i,p in enumerate([3,1,4,6])}}))
