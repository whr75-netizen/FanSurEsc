"""Old96: test their own stored current geometry/UV; never fill with new-frame RGB."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));sys.path.insert(0,str(ROOT/'eye-close90'))
from analyse89 import packet,mesh
from analyse_capture68 import camera
from surface_query90 import ProjectedSurface
from metadata90 import clean_skin_underlay

def corners(pic,uv):
 h,w=pic.shape;u,v=np.asarray(uv,dtype=np.float32);x=int(np.floor(float(u)*w-.5));y=int(np.floor(float(v)*h-.5));return[pic[h-1-((y+j)%h),(x+i)%w]/255 for j in range(2)for i in range(2)]
def main():
 src=json.loads(Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json').read_text());images={m['materialId']:np.asarray(Image.open(m['image']['file']).convert('RGBA'))[...,3]for m in src['materials']if m['materialId']in[1,3,4,6]};actual=json.loads((HERE/'ALPHA_SOURCE91.json').read_text());errors=[]
 for q in actual['queries']:errors.append(float(abs(np.asarray(corners(images[q['sourceSubMesh']],q['UVFloat32']))-q['alphaCorners']).max()))
 assert max(errors,default=0)<1e-7,'PNG alpha differs from actual Unity source; no offline bound adopted'
 old=ROOT/'native-feature89';state=json.loads(sorted((old/'capture89f').glob('STATE89*.json'))[-1].read_text());index=json.loads((old/'final-input89/INPUT_INDEX89.json').read_text());entries=[];cached={}
 for entry in index:
  if entry['frame']not in[138,139,140,141]:continue
  f=entry['frame']
  if f not in cached:
   d=packet(Path(next(e['output']for e in state['sequencePackets']if e['frame']==f)));v,n,uv,tris,world=mesh(d['path']/'eye-evaluated.mesh');cam=camera(d['path']/'source.camera');surface=ProjectedSurface(np.c_[v,np.ones(len(v))]@world.T,uv,tris[3],cam['view'],cam['projection'],[480,272]);cached[f]=(d,surface)
  d,surface=cached[f];m=d['m'];a=d['a'];saved=np.load(old/'final-input89'/(Path(entry['file']).stem+'-expected.npz'));mask=saved['scope']&(saved['colour'][...,3]==0);ref=m['nativeFinalReference89'];rx,ry,rw,rh=d['roi']
  for yy,xx in np.argwhere(mask):
   bottom=(np.array([xx+ref['nativeROI'][0]+.5,yy+ref['nativeROI'][1]+.5])-np.asarray(ref['origin']))/ref['scale']-np.asarray(m['trace86']['headJoinOffset'])-np.asarray(m['camera86']['deliveredDelta'][:2]);cx,cy=np.floor(bottom).astype(int);i,j=cy-ry,cx-rx
   if any(clean_skin_underlay(a[prefix+'-rgba'][i,j],a[prefix+'-meta'][i,j])for prefix in['base','backing']):continue
   top=[float(bottom[0]),float(272-bottom[1])];hits=surface.hits(top);proof=[]
   for hit in hits:
    alpha=corners(images[3],hit['uv']);proof.append({**hit,'sourceAlphaCorners':alpha,'definitelyOpaque':bool(min(alpha)>=.5),'alphaUncertain':bool(min(alpha)<.5<=max(alpha))})
   entries.append({'sourceId':m['sourceId'],'frame':f,'variant':entry['variant'],'nativePixelBottomLeft':[int(xx),int(yy)],'sourceRayTopLeft':top,'headCellTopLeft':[int(cx),int(271-cy)],'actualCurrentSkinHits':proof,'opaqueCurrentSkinAtTarget':any(q['definitelyOpaque']for q in proof),'RGBRecovered':False})
 assert len(entries)==96,len(entries)
 report={'status':'OLD96_GEOMETRY_ALPHA_ONLY_NO_NEW_RGB_SUBSTITUTION','count':len(entries),'opaqueCurrentSkinAtTarget':sum(q['opaqueCurrentSkinAtTarget']for q in entries),'uncertainOrNoHit':sum(not q['opaqueCurrentSkinAtTarget']for q in entries),'nativeSourceAlphaValidation':{'UnityUVQueries':len(errors),'maxPNGvsUnityAlphaError':max(errors,default=0),'singleMipBilinearVerified':True},'oldAndNewFramesNotMixed':True,'RGBRecovered':False,'rows':entries};(HERE/'OLD96_RESULT91.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))
if __name__=='__main__':main()
