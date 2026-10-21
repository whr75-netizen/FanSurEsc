"""Novel selections: stored deformed Hair support and conservative body rays.

This does not certify source renderer1/alpha/cull or native-world visibility.
No Unity query, pose sampling, selector run or production mutation occurs.
"""
from pathlib import Path
import json,struct,collections
import numpy as np
import active516 as G
D=G.OUTPUT;R=G.INPUT

def mesh(path):
    b=path.read_bytes();magic,nr=struct.unpack_from('<2i',b);assert magic==512;at=8;out={}
    for _ in range(nr):
        renderer,nv,ns=struct.unpack_from('<3i',b,at);at+=12;v=np.frombuffer(b,'<f4',offset=at,count=nv*5).reshape(nv,5).astype(float);at+=nv*20;ix=[]
        for sm in range(ns):
            ni=struct.unpack_from('<i',b,at)[0];at+=4;ix.append(np.frombuffer(b,'<i4',offset=at,count=ni).reshape(-1,3));at+=ni*4
        out[renderer]={'world':v[:,:3],'uv':v[:,3:],'indices':ix}
    assert at==len(b);return out
def project(v,view,proj):
    h=np.c_[v,np.ones(len(v))];p=h@view.T;q=p@proj.T;return np.c_[(q[:,0]/q[:,3]*.5+.5)*480,(.5-q[:,1]/q[:,3]*.5)*272,-p[:,2]]
def flatten(m,sp):
    ids=np.concatenate(m['indices']);sm=np.concatenate([np.full(len(a),i)for i,a in enumerate(m['indices'])]);prim=np.concatenate([np.arange(len(a))for a in m['indices']]);return ids,sp[ids],sm,prim
def bary(points,tri):
    a=tri[:,1,:2]-tri[:,0,:2];b=tri[:,2,:2]-tri[:,0,:2];q=np.asarray(points)-tri[:,0,:2];den=a[:,0]*b[:,1]-a[:,1]*b[:,0];ok=abs(den)>1e-20
    v=np.divide(q[:,0]*b[:,1]-q[:,1]*b[:,0],den,out=np.zeros_like(den),where=ok);w=np.divide(a[:,0]*q[:,1]-a[:,1]*q[:,0],den,out=np.zeros_like(den),where=ok)
    return np.c_[1-v-w,v,w],ok,den
def hits(point,tri):
    b,ok,det=bary(point,tri);keep=ok&(b.min(1)>=-1e-5);return np.where(keep)[0],np.sum(b*tri[:,:,2],axis=1),det,b
rows=[];maxProjectionError=0.;counts=collections.Counter();positions=set()
for i in range(81):
    result=json.loads((D/'eta-1.0'/f'{i:03d}.json').read_text());novel=result['selectedNovelPacketUnknownXY']
    if not novel:continue
    cfg=json.loads((R/f'{i:03d}_ALT_projection.json').read_text());view=np.array(cfg['headView']).reshape(4,4);proj=np.array(cfg['headProjection']).reshape(4,4);geo=mesh(R/f'{i:03d}_ALT.raymesh')
    hairsp=project(geo[2]['world'],view,proj);bodysp=project(geo[0]['world'],view,proj);ids,tri,sm,prim=flatten(geo[2],hairsp);bid,btri,bsm,bprim=flatten(geo[0],bodysp)
    raw=(R/f'{i:03d}.hairgeom').read_bytes();nv,ns=struct.unpack_from('<2i',raw);stored=np.frombuffer(raw,'<f4',offset=8,count=nv*3).reshape(nv,3);assert stored.shape==hairsp.shape
    error=float(abs(stored-hairsp).max());maxProjectionError=max(maxProjectionError,error);assert error<1e-4,'Stored pose/projection agreement failed; stop without fallback'
    for x,y in novel:
        positions.add((x,y));point=np.array([x+.5,y+.5]);bar,ok,_=bary(point,tri);q=np.tile(point,(len(tri),1));outside=bar.min(1)<0
        closest=np.full(len(tri),np.inf)
        for e in range(3):
            a=tri[:,e,:2];v=tri[:,(e+1)%3,:2]-a;vv=(v*v).sum(1);t=np.divide(((point-a)*v).sum(1),vv,out=np.zeros(len(vv)),where=vv>0);p=a+np.clip(t,0,1)[:,None]*v;distance=((p-point)**2).sum(1);use=outside&(distance<closest);q[use]=p[use];closest[use]=distance[use]
        bar,ok,_=bary(q,tri);bar=bar*(1-1e-5)+1e-5/3.;q=np.sum(bar[:,:,None]*tri[:,:,:2],1);dist=((q-point)**2).sum(1);z=np.sum(bar*tri[:,:,2],1)
        support=ok&(bar.min(1)>=-.001)&(dist<=1.1**2)
        if not support.any():
            rows.append({'target':i,'xy':[x,y],'geometricDonorSupported':False});counts['noGeometricSupport']+=1;continue
        minDistance=dist[support].min();near=support&(dist<=minDistance+1e-7);at=int(np.where(near)[0][np.argmin(z[near])]);world=bar[at]@geo[2]['world'][ids[at]];uv=bar[at]@geo[2]['uv'][ids[at]];source=project(np.array([world]),view,proj)[0]
        hh,hz,_,_=hits(source[:2],tri);hairFront=[int(k)for k in hh if hz[k]<source[2]-.0001 and k!=at]
        bh,bz,bdet,bb=hits(source[:2],btri);bodyFront=[int(k)for k in bh if bz[k]<source[2]-.0001]
        counts['geometricDonorSupported']+=1
        counts['closestDonorOpaqueHairOccluded']+=bool(hairFront);counts['potentialBodyForegroundBeforeAlphaCull']+=bool(bodyFront)
        rows.append({'target':i,'xy':[x,y],'geometricDonorSupported':True,'donor':{'renderer':2,'submesh':int(sm[at]),'primitive':int(prim[at]),'vertices':ids[at].tolist(),'barycentric':bar[at].tolist(),'world':world.tolist(),'uv':uv.tolist(),'projected':source[:2].tolist(),'depth':float(source[2]),'distanceToDestinationCentre':float(np.sqrt(dist[at]))},'otherOpaqueHairFrontCount':len(hairFront),'potentialBodyForegroundCountBeforeAlphaCull':len(bodyFront),'potentialBodyExamples':[{'renderer':0,'submesh':int(bsm[k]),'primitive':int(bprim[k]),'vertices':bid[k].tolist(),'barycentric':bb[k].tolist(),'depth':float(bz[k]),'bodyMinusHairDepth':float(bz[k]-source[2]),'det':float(bdet[k]),'uv':(bb[k]@geo[0]['uv'][bid[k]]).tolist()}for k in bodyFront[:3]],'actualSourcePacketCertified':False,'reason':'Pre-visibility Hair donor query only. Source renderer1 and original material alpha/cull visibility are not fully stored for this novel ray; CPU donor is not a captured GPU packet.'})
out={'mode':'STORED_DEFORMED_GEOMETRY_SUPPORT_ONLY','novelSelectionObservations':len(rows),'distinctScreenCells':len(positions),'counts':dict(counts),'maxStoredVsWorldProjectionError':maxProjectionError,'rows':rows,'allNovelActualPacketsStillUncertified':True,'noUnityCalls':True,'noNewCaptures':True,'noSelectorRerun':True,'limits':['Same role was not used as surface identity; actual renderer/submesh/primitive/vertices/barycentric/UV/world/depth are recorded.','Body foreground is conservative and includes alpha holes/backfaces until material checks.','A closest source donor hidden by another opaque Hair triangle is not proof that no alternative donor exists.','Native-world visibility and source renderer1 remain out of scope.']}
(D/'SUPPORT516.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['rows','limits']}))
