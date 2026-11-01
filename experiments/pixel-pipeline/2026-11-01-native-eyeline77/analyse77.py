"""Decompose actual native-line sampling/occlusion/budget, without Unity calls."""
from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent;P76=HERE.parent/'whole-eye76'
sys.path.insert(0,str(P76));from validate_final76 import packet
sys.path.insert(0,str(HERE.parent/'apply-capture66'));from analyse_capture68 import geometry,camera
def valid(m,p,sid):return(m[...,0]>0)&(m[...,1]>.5)&(m[...,3]>1e-6)&(np.rint(m[...,2])==sid)&(p[...,3]>.5)
def cov(m):return(m[...,0]>0)&(m[...,1]>.5)&(m[...,3]>1e-6)
def area(w):return float(w.astype(np.float64).sum()/16)
def main():
 state=json.loads(sorted((P76/'run-j').glob('STATE76-*.json'))[-1].read_text());rows=[];previous=None
 for entry in state['sequencePackets']:
  root=Path(entry['output']);d=packet(root);a=d['arrays'];c=d['counts'];rx,ry,rw,rh=d['eyeROI'];bx,by,bw,bh=d['roi'];native=a['S3-meta'];skin=a['S0-meta'];hair=a['hair-meta'][ry-by:ry-by+rh,rx-bx:rx-bx+rw];hair=np.repeat(np.repeat(hair,4,0),4,1);gi,meshes=geometry(root/'evaluated-source.geometry');cam=camera(root/'source.camera');assert gi==d['identity'];face=meshes[1];morphs=face['morphs'];changedMorph=[] if previous is None else[(n,v,dict(previous['morphs'])[n])for n,v in morphs if v!=dict(previous['morphs'])[n]]
  world=(face['matrix']@np.c_[face['vertices'],np.ones(len(face['vertices']))].T).T;clip=(cam['effective']@cam['view']@world.T).T;screen=clip[:,:2]/clip[:,3:4]*np.array([240,136]);tri=face['submeshes'][6]['indices'];v=screen[tri];signed=((v[:,1,0]-v[:,0,0])*(v[:,2,1]-v[:,0,1])-(v[:,1,1]-v[:,0,1])*(v[:,2,0]-v[:,0,0]))/2
  per=[]
  for ei,centre in enumerate(d['manifest']['eyeFeature']['centres']):
   sid=int(centre[3]);w=np.where(valid(native,a['S3-point'],sid),np.clip(native[...,3],0,1),0).astype(np.float32);stages={'rawNativeAlphaArea':area(w)}
   skvalid=valid(skin,a['S0-point'],sid);w*=np.where(skvalid&(skin[...,0]<native[...,0]),1-np.clip(skin[...,3],0,1),1);stages['afterSkin']=area(w)
   for name,mm in [('Hair',a['S4-meta']),('Brow',a['S5-meta']),('Body',a['S6-meta'])]:
    w*=np.where(cov(mm)&(mm[...,0]<native[...,0]),0 if name=='Body'else 1-np.clip(mm[...,3],0,1),1);stages['after'+name]=area(w)
   cells=w.reshape(rh,4,rw,4).sum((1,3));gpu=c[ei,...,5];err=float(abs(cells-gpu).max());assert err<2e-5,(sid,err)
   ids=np.unique(np.rint(a['S3-uv'][...,2][valid(native,a['S3-point'],sid)]).astype(int))-1;ids=ids[ids>=0]
   areas=signed[ids];chosen=[]
   for yy,xx in np.argwhere((np.rint(d['records'][...,3,1])==sid)&np.isin(np.rint(d['records'][...,3,0]),[5,7])):
    z=d['records'][yy,xx];chosen.append({'xy':[int(xx+rx),int(271-(yy+ry))],'reserved':bool(z[14,2]>.5),'primitive':int(round(float(z[6,2]))),'uv':z[6,:2].tolist()})
   per.append({'eye':sid,'areas':stages,'GPUarea':float(gpu.sum()/16),'maxReplayWeightError':err,'sourcePrimitiveSet':ids.tolist(),'sourceVisiblePrimitiveProjectedAreaSum':float(abs(areas).sum()),'sourceVisiblePrimitiveWindingSigns':np.unique(np.sign(areas)).tolist(),'budget':int(np.floor(np.float32(gpu.sum()/16+.5))),'selected':chosen,'cellWeights':[[int(xx+rx),int(271-(yy+ry)),float(gpu[yy,xx])]for yy,xx in np.argwhere(gpu>0)]})
  rows.append({'identity':d['identity'],'sourceFrame':d['manifest']['sourceFrame'],'morphsNonZero':[(n,v)for n,v in morphs if v!=0],'morphChanges':changedMorph,'headMatrix':d['manifest']['eyeFeature']['headMatrix'],'eyes':per});previous={'morphs':morphs}
 out={'frames':rows,'limits':['Projected area sum currently covers only primitives observed by 4x samples; not the complete continuous alpha-weighted eye area','No additional Unity call or capture; different source cohorts are not mixed']};(HERE/'ABLATION77.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{ 'frame':r['identity']['frameIndex'],'sourceFrame':r['sourceFrame'],'morphChanges':r['morphChanges'],'eyes':[{'eye':e['eye'],'areas':e['areas'],'budget':e['budget'],'selected':e['selected']}for e in r['eyes']]}for r in rows],indent=2))
if __name__=='__main__':main()
