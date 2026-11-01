from pathlib import Path
import json,struct,hashlib,sys,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
sys.path.insert(0,str(R/'apply-capture66'));from analyse_capture68 import Reader
sys.path.insert(0,str(R/'uv-features64'));from uv_features64 import extract
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def native_mesh(p):
 r=Reader(p);assert r.s()=='aux-mesh67/v1';identity=r.identity();matrix=r.mat();vertices=r.a(r.i()*3).reshape(-1,3);normals=r.a(r.i()*3).reshape(-1,3);uv=r.a(r.i()*2).reshape(-1,2);ix=[r.a(r.i(),'<i4').reshape(-1,3)for _ in range(r.i())];r.end();return identity,uv,ix
def native_image(reg,binding):
 b=(P/reg['modelAsset']).read_bytes();assert hashlib.sha256(b).hexdigest()==reg['modelSHA256'];n,t=struct.unpack_from('<II',b,12);g=json.loads(b[20:20+n]);at=20+n;n2,t2=struct.unpack_from('<II',b,at);chunk=b[at+8:at+8+n2];v=g['bufferViews'][g['images'][binding['imageIndex']]['bufferView']];raw=chunk[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];assert hashlib.sha256(raw).hexdigest()==binding['imageSHA256'];return np.array(Image.open(io.BytesIO(raw)).convert('RGBA'))
def mask_uv(uv,triangles,width,height):
 points=uv.astype(np.float64)*[width,height];points[:,1]=height-points[:,1];mask=np.zeros((height,width),bool)
 # Conservative native-texel/triangle intersection via separating axes. This
 # registers boundary texels actually touched by UV geometry, not a dilation.
 for ids in triangles:
  tri=points[ids];lo=np.maximum(0,np.floor(tri.min(0)).astype(int));hi=np.minimum([width,height],np.ceil(tri.max(0)).astype(int))
  if np.any(hi<=lo):continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0])+.5,np.arange(lo[1],hi[1])+.5);valid=np.ones(xx.shape,bool)
  for a,b in zip(tri,np.roll(tri,-1,axis=0)):
   normal=np.array([-(b-a)[1],(b-a)[0]]);support=.5*abs(normal).sum();proj=tri@normal;centre=xx*normal[0]+yy*normal[1];valid&=(centre+support>=proj.min())&(centre-support<=proj.max())
  mask[lo[1]:hi[1],lo[0]:hi[0]]|=valid
 return mask
def colours(labels,mask):
 out=np.zeros((*mask.shape,4),np.uint8);v=labels[mask].astype(np.uint32)+1;out[mask,:3]=np.stack([(v*73)%223+32,(v*131)%223+32,(v*191)%223+32],axis=-1).astype(np.uint8);out[mask,3]=255;return out
def main():
 reg=load(R/'renderer-family59/SOURCE_REGISTRY59.json');state=load(sorted((R/'forward-eye102/ties').glob('STATE102-*'))[-1]);packet=Path(state['sequencePackets'][0]['output']);identity,uv,indices=native_mesh(packet/'current-face102.mesh');assert identity['sourceId']==state['sequencePackets'][0]['sourceId'];out=[]
 for part in [3,6]:
  binding=next(b for b in reg['bindings']if b['rendererOrdinal']==1 and b['subMesh']==part);rgba=native_image(reg,binding);height,width=rgba.shape[:2];mask=mask_uv(uv,indices[part],width,height);ys,xs=np.nonzero(mask);x0,x1=int(xs.min()),int(xs.max())+1;y0,y1=int(ys.min()),int(ys.max())+1;crop=rgba[y0:y1,x0:x1];domain=mask[y0:y1,x0:x1]&(crop[...,3]>0)
  if domain.size>1100000:raise ValueError('103 one-source image budget exceeded; no implicit reduction')
  data=extract(crop[...,:3],domain,scales=(2,4,8));path=H/f'part{part}';path.mkdir(exist_ok=False)
  Image.fromarray(crop).save(path/'source.png');Image.fromarray((domain*255).astype(np.uint8)).save(path/'uv-domain.png');Image.fromarray(colours(data['coarse'],domain)).save(path/'persistent-regions.png');Image.fromarray(colours(data['fine'],domain)).save(path/'fine-evidence-regions.png');np.savez_compressed(path/'hierarchy.npz',rgba=crop,mask=domain,coarse=data['coarse'],fine=data['fine'],xPersistent=data['x']['persistent'],yPersistent=data['y']['persistent'],xFineOnly=data['x']['fineOnly'],yFineOnly=data['y']['fineOnly'],thinX=data['thinRidgeX'],thinY=data['thinRidgeY'])
  row={'part':part,'sourceId':identity['sourceId'],'modelSHA256':reg['modelSHA256'],'imageSHA256':binding['imageSHA256'],'materialId':binding['materialId'],'fullSize':[width,height],'cropTopLeft':[x0,y0,x1-x0,y1-y0],'maskTexels':int(domain.sum()),'sourceRGB8':len(np.unique(crop[domain,:3],axis=0)),'coarseRegions':data['coarseRegions'],'fineRegions':data['fineRegions'],'fineOnlyEdges':int(data['x']['fineOnly'].sum()+data['y']['fineOnly'].sum()),'thinRidgeCandidates':int(data['thinRidgeX'].sum()+data['thinRidgeY'].sum()),'coarseSizes':np.bincount(data['coarse'][domain]).tolist(),'cacheKey':data['cacheKey'],'contract':'source native UV masked evidence; persistent/fine/ridge are not semantic ground truth; no colour-bin CC or palette yet'};out.append(row);print(json.dumps({k:v for k,v in row.items()if k!='coarseSizes'}),flush=True)
 (H/'SOURCE_EVIDENCE103.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
