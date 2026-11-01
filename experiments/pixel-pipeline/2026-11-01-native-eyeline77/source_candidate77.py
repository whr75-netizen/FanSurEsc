"""Source-component diagnosis: intrinsic budget vs externally masked visibility."""
from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent;P76=HERE.parent/'whole-eye76'
sys.path.insert(0,str(P76));from validate_final76 import packet
from analyse77 import valid,cov,area
def components(v,tri,centres,axesY):
 parent=list(range(len(tri)));seen={}
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,t in enumerate(tri):
  for x in t:
   if int(x)in seen:parent[root(i)]=root(seen[int(x)])
   else:seen[int(x)]=i
 groups={}
 for i in range(len(tri)):groups.setdefault(root(i),[]).append(i)
 out=[];ids=np.full(len(tri),-1,int)
 for i,indices in enumerate(groups.values()):
  points=v[tri[indices]];areas=np.linalg.norm(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]),axis=1)/2;mean=(points.mean(1)*areas[:,None]).sum(0)/areas.sum();eye=int(np.argmin([np.linalg.norm(mean-np.array(c[:3]))for c in centres]));vertical=-np.dot(mean-np.array(centres[eye][:3]),axesY[eye][:3])/axesY[eye][3]
  out.append({'component':i,'eyeIndex':eye,'eyeId':int(centres[eye][3]),'part':'upper'if vertical<0 else'lower','meanRest':mean.tolist(),'meanNormalizedV':float(vertical),'primitives':indices});ids[indices]=i
 return out,ids
def main():
 state=json.loads(sorted((P76/'run-j').glob('STATE76-*.json'))[-1].read_text());source=np.load(HERE.parent/'whole-eye52/SOURCE_SURFACES52.npz');e=state['eyeFeature'];desc,ids=components(source['native_xyz_head'],source['native_role6_tri'],e['centres'],e['axesY']);rows=[]
 for entry in state['sequencePackets']:
  d=packet(Path(entry['output']));a=d['arrays'];m=a['S3-meta'];p=a['S3-point'];u=a['S3-uv'];rx,ry,rw,rh=d['eyeROI'];protected=d['records'][...,14,2]>.5;primitive=np.rint(u[...,2]).astype(int)-1;which=np.where(primitive>=0,ids[np.maximum(primitive,0)],-1);per=[]
  for q in desc:
   if q['part']!='upper':continue
   sid=q['eyeId'];ei=q['eyeIndex'];intr=np.where(valid(m,p,sid)&(which==q['component']),np.clip(m[...,3],0,1),0).astype(np.float32);skin=a['S0-meta'];intr*=np.where(valid(skin,a['S0-point'],sid)&(skin[...,0]<m[...,0]),1-np.clip(skin[...,3],0,1),1);visible=intr.copy()
   for s in [4,5,6]:
    mm=a[f'S{s}-meta'];visible*=np.where(cov(mm)&(mm[...,0]<m[...,0]),0 if s==6 else 1-np.clip(mm[...,3],0,1),1)
   budget=int(np.floor(np.float32(intr.sum()/16+.5)));reserve=int(((d['counts'][ei,...,10]>.5)).sum());candidates=[]
   for yy in range(rh):
    for xx in range(rw):
     if protected[yy,xx]:continue
     w=visible[yy*4:yy*4+4,xx*4:xx*4+4];total=float(w.sum())
     if total<=0:continue
     mean=(p[yy*4:yy*4+4,xx*4:xx*4+4,:3]*w[...,None]).sum((0,1))/total;delta=mean-np.array(q['meanRest']);ux=np.dot(delta,e['axesX'][ei][:3])/e['axesX'][ei][3];vy=np.dot(delta,e['axesY'][ei][:3])/e['axesY'][ei][3];score=float(ux*ux+vy*vy);candidates.append({'xy':[xx+rx,271-(yy+ry)],'score':score,'visibleWeight':total,'meanRest':mean.tolist()})
   candidates.sort(key=lambda z:(z['score'],z['xy'][1],z['xy'][0]));per.append({'eye':sid,'intrinsicArea':area(intr),'visibleArea':area(visible),'intrinsicBudget':budget,'reserved':reserve,'selected':candidates[:max(0,budget-reserve)],'candidates':candidates})
  rows.append({'identity':d['identity'],'eyes':per})
 out={'descriptors':desc,'frames':rows,'status':'offline candidate only, no product modification'};(HERE/'SOURCE_CANDIDATE77.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'frame':r['identity']['frameIndex'],'eyes':[{k:e[k]for k in ['eye','intrinsicArea','visibleArea','intrinsicBudget','reserved','selected']}for e in r['eyes']]}for r in rows],indent=2))
if __name__=='__main__':main()
