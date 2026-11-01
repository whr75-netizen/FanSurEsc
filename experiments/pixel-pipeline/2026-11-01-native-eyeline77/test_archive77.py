"""Portable replay of captured final GPU cell allocation; no Unity required."""
from pathlib import Path
import json,numpy as np
from reference77 import components,valid,cov,iris_allocation,supported
R=Path(__file__).resolve().parent
def main():
 z=np.load(R/'fixture77.npz');meta=json.loads((R/'FIXTURE77.json').read_text());checks=0;frames=0;sourceColour=0
 for info in meta['frames']:
  pre=info['prefix'];e=info['eyeFeature'];b=z[pre+'baseline'];rec=z[pre+'records'];c=z[pre+'counts'].copy();old=z[pre+'original'];x,y,w,h=info['roi'];rx,ry,rw,rh=info['eyeROI'];old=old[ry-y:ry-y+rh,rx-x:rx-x+rw];pred=np.zeros((rh,rw),bool);expected=np.zeros_like(pred);tag=np.zeros(c.shape[:3]);a=lambda name:z[pre+name]
  parts,ids=components(z['nativeXYZ'],z['nativeTriangles'],e['centres'],e['axesY'])
  for yy in range(rh):
   for xx in range(rw):
    v=b[yy+ry-y,xx+rx-x];sm=[a(f'S{i}-meta')[yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(7)];pt=[a(f'S{i}-point')[yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(4)];ok,sid,weight=supported(v[0],v[1],v[4],sm,pt,a('old-eye-owner')[yy+ry-y,xx+rx-x]);pred[yy,xx]=ok
    if not ok:continue
    assert np.array_equal(rec[yy,xx,0],v[0]);ei=next(i for i,v in enumerate(e['centres'])if int(v[3])==sid);role=round(float(v[1,0]));kind=2 if role==2 else 3 if role==5 else 1 if parts[ids[round(float(rec[yy,xx,6,2]))-1]]['part']=='upper'else 4;tag[ei,yy,xx]=kind;checks+=1
  assert np.array_equal(pred,rec[...,14,2]>.5);assert np.array_equal(np.where(tag==4,1,tag),c[...,10]);c[...,10]=tag
  m=a('S3-meta');p=a('S3-point');u=a('S3-uv');primitive=np.rint(u[...,2]).astype(int)-1;component=np.where(primitive>=0,ids[np.maximum(primitive,0)],-1)
  for q in parts:
   if q['part']!='upper':continue
   ei=q['eyeIndex'];sid=q['eyeId'];intr=np.where(valid(m,p,sid)&(component==q['component']),np.clip(m[...,3],0,1),0).astype(np.float32);sk=a('S0-meta');intr*=np.where(valid(sk,a('S0-point'),sid)&(sk[...,0]<m[...,0]),1-np.clip(sk[...,3],0,1),1);vis=intr.copy()
   for s in [4,5,6]:
    mm=a(f'S{s}-meta');vis*=np.where(cov(mm)&(mm[...,0]<m[...,0]),0 if s==6 else 1-np.clip(mm[...,3],0,1),1)
   raw=np.float32(0)
   for v in intr.reshape(rh,4,rw,4).sum((1,3)).flat:raw=np.float32(raw+np.float32(v/16))
   budget=max(0,int(np.floor(np.float32(raw+.5)))-int((tag[ei]==1).sum()));blocked=pred|iris_allocation(c[ei]);candidates=[]
   for yy in range(rh):
    for xx in range(rw):
     if blocked[yy,xx]:continue
     weights=vis[yy*4:yy*4+4,xx*4:xx*4+4];total=float(weights.sum())
     if total<=0:continue
     mean=(p[yy*4:yy*4+4,xx*4:xx*4+4,:3]*weights[...,None]).sum((0,1))/total;delta=mean-q['meanRest'];dx=np.dot(delta,e['axesX'][ei][:3])/e['axesX'][ei][3];dy=np.dot(delta,e['axesY'][ei][:3])/e['axesY'][ei][3];candidates.append((float(dx*dx+dy*dy),*mean.tolist(),yy,xx))
   for t in sorted(candidates)[:budget]:expected[t[-2],t[-1]]=True
  assert np.array_equal(expected,rec[...,14,3]==77)
  allowed=expected|np.isin(np.rint(old[...,3,0]),[5,7]);assert np.array_equal(rec[...,0,:][~allowed&~pred],old[...,0,:][~allowed&~pred]);assert np.array_equal(rec[...,0,:][pred],old[...,0,:][pred])
  for yy,xx in np.argwhere(expected):
   r=rec[yy,xx];match=np.argwhere(np.max(abs(u[...,:2]-r[7,:2]),axis=2)<1e-6);errs=[np.max(abs(a('S3-rgba')[sy,sx,:3]*a('S3-shade')[sy,sx,2]-r[0,:3]))for sy,sx in match];assert errs and min(errs)<2e-6;sourceColour+=1
  frames+=1
 cache=json.loads((R/'CACHE_GPU_REVIEW77.json').read_text());assert len(cache['tests'])==7 and all(t['passed']for t in cache['tests']);assert cache['sourceXYZUnchanged'];assert all(i//4==i>>2 for i in range(16))
 print(json.dumps({'frames':frames,'protectedRGBChecks':checks,'sourceNativeColourChecks':sourceColour,'GPUownershipCases':7,'GPUvsOfflinePlacement':'equal','nonNativeRGBChanges':0,'limits':'Same captured model/poses only; no universal style or subpixel-motion guarantee.'}))
if __name__=='__main__':main()
