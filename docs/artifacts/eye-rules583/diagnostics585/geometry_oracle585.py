"""Offline diagnostic only. Continuous extension of recorded triangle/texture inputs.
No runtime renderer, new selection rule, temporal state or image generation.
"""
from pathlib import Path
import json,csv,struct,io,time,sys
import numpy as np
from PIL import Image
R=Path(__file__).parent;OLD=R.with_name('EyeFollow584')/'Runtime584/OneCase5B';G=R/'Runtime585/Geometry5'
P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game')
def table(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def config(p):return {q[0]:np.array(q[1:],float)for l in p.read_text().splitlines()if(q:=l.split('\t'))}
def glb_textures():
 raw=(P/'Assets/EUnityValidation01/VRoidSampleA144/Inputs/AvatarSample_A.vrm').read_bytes();n,_=struct.unpack_from('<II',raw,12);j=json.loads(raw[20:20+n]);bn,kind=struct.unpack_from('<II',raw,20+n);binary=memoryview(raw)[28+n:28+n+bn];out={}
 for mi,m in enumerate(j['materials']):
  tex=m.get('pbrMetallicRoughness',{}).get('baseColorTexture')
  if not tex:continue
  ti=j['textures'][tex['index']]['source'];im=j['images'][ti];b=j['bufferViews'][im['bufferView']];offset=b.get('byteOffset',0);a=np.array(Image.open(io.BytesIO(binary[offset:offset+b['byteLength']])).convert('RGBA'))[:,:,3].astype(float)/255
  out[mi]={'alpha':a,'name':im.get('name'),'mat':m}
 return j,out
GLB,TEXTURES=glb_textures()
def texture_bilinear(uv,mi,flip=True):
 a=TEXTURES[int(mi)]['alpha'];h,w=a.shape;u=np.asarray(uv)[:,0];v=np.asarray(uv)[:,1];x=u*w-.5;y=(1-v if flip else v)*h-.5;ix=np.floor(x).astype(int);iy=np.floor(y).astype(int);fx=x-ix;fy=y-iy
 return (a[iy%h,ix%w]*(1-fx)+a[iy%h,(ix+1)%w]*fx)*(1-fy)+(a[(iy+1)%h,ix%w]*(1-fx)+a[(iy+1)%h,(ix+1)%w]*fx)*fy
class Frame:
 def __init__(self,i,old=OLD,geo=G):
  self.i=i;self.prefix=geo/f'{i:03}_ON';self.old=old/f'{i:03}_ON';self.cfg=config(Path(str(self.old)+'_CONFIG582.tsv'))
  verts={(int(q['renderer']),int(q['vertex'])):np.array([q[k]for k in ['x','y','depth','restX','restY','restZ','owner','u','v']],float)for q in table(Path(str(self.prefix)+'_VERTS585.tsv'))}
  tr=table(Path(str(self.prefix)+'_TRIS585.tsv')); mats={}
  for q in table(Path(str(self.prefix)+'_MATERIAL585.tsv')):mats.setdefault(q['material'],{})[q['property']]=q['value']
  self.mats=mats;v=np.array([[verts[int(q['renderer']),int(q[k])]for k in ['a','b','c']]for q in tr]);xy=v[:,:,:2];det=np.cross(xy[:,1]-xy[:,0],xy[:,2]-xy[:,0]);good=np.abs(det)>1e-10;self.degenerateArea=float(np.abs(det[~good]).sum()/2);v=v[good];tr=[q for q,g in zip(tr,good)if g];det=det[good]
  self.tr=tr;self.v=v;self.sign=np.sign(det);self.xy=v[:,:,:2];mat=np.concatenate([v[:,:,:2].transpose(0,2,1),np.ones((len(v),1,3))],axis=1);self.B=np.linalg.inv(mat)
  self.depth=np.einsum('mji,mj->mi',self.B,v[:,:,2]);self.rest=np.einsum('mji,mjk->mik',self.B,v[:,:,3:6]);self.owner=np.einsum('mji,mj->mi',self.B,v[:,:,6]);self.uv=np.einsum('mji,mjk->mik',self.B,v[:,:,7:9])
  self.s=np.array([int(q['support'])for q in tr]);self.prim=np.array([int(q['primitive'])for q in tr]);self.sm=np.array([int(q['submesh'])for q in tr]);self.cull=np.array([int(float(mats[q['material']]['_M_CullMode']))for q in tr]);self.mode=np.array([int(float(mats[q['material']]['_AlphaMode']))for q in tr]);self.cut=np.array([float(mats[q['material']]['_Cutoff'])for q in tr]);self.alpha=np.array([float(mats[q['material']]['colorAlpha'])for q in tr]);self.mi=np.array([GLB['meshes'][0 if int(q['renderer'])==1 else 1]['primitives'][int(q['submesh'])]['material']for q in tr]);self.box=np.stack([self.xy.min(axis=1),self.xy.max(axis=1)],axis=1)
  self.samples=table(Path(str(self.old)+'_SUBPIXELS582.tsv'));sign=[]
  for q in self.samples:
   if float(q['depth'])<=0 or int(q['support'])!=0:continue
   k=np.flatnonzero((self.s==0)&(self.prim==round(float(q['primitive']))))
   if len(k):sign.append(self.sign[k[0]]*np.sign(float(q['pointValid'])))
  assert len(set(sign))==1,set(sign);self.frontSign=sign[0];self.front=self.sign==self.frontSign
  self.rendered=(self.cull==0)|((self.cull==2)&self.front)|((self.cull==1)&~self.front)
  eye=next(e for e in range(2)if round(self.cfg[f'Centres348.{e}'][3])==2);c=self.cfg[f'Centres348.{eye}'][:3];ax=self.cfg[f'AxesX348.{eye}'];ay=self.cfg[f'AxesY348.{eye}'];rr=self.rest.copy();rr[:,2,:]-=c;self.uc=rr@ax[:3]/ax[3];self.vc=-(rr@ay[:3])/ay[3]
  self.cells={(int(q['cellX']),int(q['cellY']),q['buffer']):np.array([q[k]for k in ['r','g','b','a']],float)for q in table(Path(str(self.old)+'_CELLS582.tsv'))}
  self.global_alpha=np.array([self.tex_bounds(vv[:,7:9].min(axis=0),vv[:,7:9].max(axis=0),mi) for vv,mi in zip(v,self.mi)])
 @staticmethod
 def tex_bounds(lo,hi,mi):
  a=TEXTURES[int(mi)]['alpha'];h,w=a.shape
  # Pillow origin is top-left; Unity texture UV is bottom-left. All queried wrap modes Repeat.
  x0=int(np.floor(lo[0]*w-.5));x1=int(np.floor(hi[0]*w-.5))+1;y0=int(np.floor((1-hi[1])*h-.5));y1=int(np.floor((1-lo[1])*h-.5))+1
  xs=np.arange(x0,min(x1+1,x0+w))%w;ys=np.arange(y0,min(y1+1,y0+h))%h;patch=a[np.ix_(ys,xs)];return float(patch.min()),float(patch.max())
 def point_layer(self,points,s,flip=True):
  points=np.asarray(points);ix=np.flatnonzero((self.s==s)&self.rendered);out=np.full(len(points),-1,int);out_alpha=np.zeros(len(points));best=np.full(len(points),np.inf)
  for start in range(0,len(points),128):
   p=points[start:start+128];b=np.einsum('nd,mid->nmi',np.c_[p,np.ones(len(p))],self.B[ix]);inside=(b>=-1e-7).all(axis=2);row,col=np.nonzero(inside)
   if not len(row):continue
   gi=ix[col];uv=np.einsum('nd,ndk->nk',np.c_[p[row],np.ones(len(row))],self.uv[gi]);a=np.empty(len(row))
   for mi in np.unique(self.mi[gi]):
    m=self.mi[gi]==mi;a[m]=texture_bilinear(uv[m],mi,flip)
   a*=self.alpha[gi];mode=self.mode[gi];a=np.where(mode==0,1,np.where(mode==1,np.where(a>=self.cut[gi],1,0),np.where(a>=6.103515625e-5,a,0)))
   ds=np.sum(np.c_[p[row],np.ones(len(row))]*self.depth[gi],axis=1)
   for k in range(len(row)):
    if a[k]<=0:continue
    dest=start+row[k]
    if ds[k]<=best[dest]:best[dest]=ds[k];out[dest]=gi[k];out_alpha[dest]=a[k]
  return out,best,out_alpha
 def validate(self,flip=True):
  result=[]
  for s in [0,1,2,3,5,6]:
   qs=[q for q in self.samples if int(q['support'])==s];pts=np.array([[float(q['cellX'])+(int(q['k'])%4+.5)/4,float(q['cellY'])+1-(int(q['k'])//4+.5)/4]for q in qs]);tri,depth,a=self.point_layer(pts,s,flip);expected=np.array([float(q['depth'])>0 for q in qs]);cov=tri>=0;bad=int(np.count_nonzero(cov!=expected));both=np.flatnonzero(cov&expected);prim_bad=sum(self.prim[tri[k]]!=round(float(qs[k]['primitive']))for k in both);alphaerr=max([abs(a[k]-float(qs[k]['alpha']))for k in both],default=0);deperr=max([abs(depth[k]-float(qs[k]['depth']))for k in both],default=0)
   result.append({'support':s,'points':len(qs),'coverageMismatch':bad,'primitiveMismatch':int(prim_bad),'maxAlphaError':float(alphaerr),'maxDepthError':float(deperr)})
  return result
 def area4(self):
  x,by,w,h=map(int,self.cfg['ROI348']);top=272-by-h;cells=[(xx,yy)for yy in range(top,top+h)for xx in range(x,x+w)];pts=np.array([(xx+(k%4+.5)/4,yy+1-(k//4+.5)/4)for xx,yy in cells for k in range(16)]);pc=np.c_[pts,np.ones(len(pts))];layers={s:self.point_layer(pts,s)for s in [0,1,2,3,5,6]};ref=np.full(len(pts),-1,int);support=ref.copy()
  for s in [0,1,2,3]:
   ix=layers[s][0];v=ix>=0;own=np.rint(np.sum(pc*self.owner[np.maximum(ix,0)],axis=1));valid=v&(own==2)&self.front[np.maximum(ix,0)];ref[(ref<0)&valid]=ix[(ref<0)&valid]
  for s in [0,3]:
   ix=layers[s][0];v=ix>=0;own=np.rint(np.sum(pc*self.owner[np.maximum(ix,0)],axis=1));valid=v&(own==2)&self.front[np.maximum(ix,0)];support[(support<0)&valid]=ix[(support<0)&valid]
  u=np.sum(pc*self.uc[np.maximum(ref,0)],axis=1);v=np.sum(pc*self.vc[np.maximum(ref,0)],axis=1);a,b=self.cfg['UpperLower348'][:2];g=v-a-b*u*u;weight=((ref>=0)&(support>=0)&(np.abs(u)<=1.08)&(g>=-.36)&(g<=.22)).astype(float);dep=np.sum(pc*self.depth[np.maximum(support,0)],axis=1)
  for k,p in enumerate(cells):
   hm=self.cells[*p,'HairMETA'];sl=slice(16*k,16*k+16)
   if hm[0]>0 and hm[1]>.5 and hm[3]>1e-6:weight[sl]*=np.where(hm[0]<dep[sl],1-np.clip(hm[3],0,1),1)
  bi,bd,ba=layers[5];weight*=np.where((bi>=0)&(bd<dep),1-ba,1);bi,bd,ba=layers[6];weight*=np.where((bi>=0)&(bd<dep),0,1)
  observed=[]
  lookup={(int(q['cellX']),int(q['cellY']),int(q['k']),int(q['support'])):q for q in self.samples}
  # Current584 CPU replay supplies the independent shader-matching support labels.
  sys.path.insert(0,str(R.with_name('EyeFollow584')))
  scope={'__file__':str(R.with_name('EyeSupport582')/'oracle583.py'),'__name__':'definitions_only'};saved=sys.argv;sys.argv=['oracle','unused'];src=Path(scope['__file__']);exec(compile(src.read_text().split("if __name__=='__main__':")[0],str(src),'exec'),scope);sys.argv=saved
  ss=scope['read_samples'](Path(str(self.old)+'_SUBPIXELS582.tsv'));cs=scope['read_cells'](Path(str(self.old)+'_CELLS582.tsv'))
  for p in cells:
   e=next(z for z in scope['evaluate'](p,self.cfg,ss,cs,True)if z['eyeID']==2);observed.extend(s['weight']if s['label']==5 else 0 for s in e['samples'])
  observed=np.array(observed);return {'geometryArea4':float(weight.sum()/16),'savedArea4':float(observed.sum()/16),'weightMismatches':int(np.count_nonzero(np.abs(weight-observed)>2e-4)),'maxWeightError':float(np.max(np.abs(weight-observed))),'candidateUpperLashPoints':int(np.count_nonzero(weight))}
 def weights(self,pts):
  pts=np.asarray(pts);pc=np.c_[pts,np.ones(len(pts))];layers={s:self.point_layer(pts,s)for s in [0,1,2,3,5,6]};ref=np.full(len(pts),-1,int);support=ref.copy()
  for s in [0,1,2,3]:
   ix=layers[s][0];own=np.rint(np.sum(pc*self.owner[np.maximum(ix,0)],axis=1));ok=(ix>=0)&(own==2)&self.front[np.maximum(ix,0)]&(ref<0);ref[ok]=ix[ok]
  for s in [0,3]:
   ix=layers[s][0];own=np.rint(np.sum(pc*self.owner[np.maximum(ix,0)],axis=1));ok=(ix>=0)&(own==2)&self.front[np.maximum(ix,0)]&(support<0);support[ok]=ix[ok]
  u=np.sum(pc*self.uc[np.maximum(ref,0)],axis=1);v=np.sum(pc*self.vc[np.maximum(ref,0)],axis=1);a,b=self.cfg['UpperLower348'][:2];g=v-a-b*u*u;weight=((ref>=0)&(support>=0)&(np.abs(u)<=1.08)&(g>=-.36)&(g<=.22)).astype(float);dep=np.sum(pc*self.depth[np.maximum(support,0)],axis=1)
  for p in np.unique(np.floor(pts).astype(int),axis=0):
   hm=self.cells[int(p[0]),int(p[1]),'HairMETA'];sl=(np.floor(pts[:,0])==p[0])&(np.floor(pts[:,1])==p[1])
   if hm[0]>0 and hm[1]>.5 and hm[3]>1e-6:weight[sl]*=np.where(hm[0]<dep[sl],1-np.clip(hm[3],0,1),1)
  bi,bd,ba=layers[5];weight*=np.where((bi>=0)&(bd<dep),1-ba,1);bi,bd,ba=layers[6];weight*=np.where((bi>=0)&(bd<dep),0,1)
  return weight
 def possible_cells(self):
  x,by,w,h=map(int,self.cfg['ROI348']);top=272-by-h;result=[]
  for yy in range(top,top+h):
   for xx in range(x,x+w):
    ix=np.flatnonzero(np.isin(self.s,[0,1,2,3])&self.rendered&self.front&(self.box[:,0,0]<=xx+1)&(self.box[:,1,0]>=xx)&(self.box[:,0,1]<=yy+1)&(self.box[:,1,1]>=yy))
    if not len(ix):continue
    center=np.array([xx+.5,yy+.5,1]);u=self.uc[ix]@center;du=.5*np.abs(self.uc[ix,:2]).sum(axis=1);v=self.vc[ix]@center;dv=.5*np.abs(self.vc[ix,:2]).sum(axis=1);own=self.owner[ix]@center;do=.5*np.abs(self.owner[ix,:2]).sum(axis=1);ulo,uhi=u-du,u+du;vslo,vshi=v-dv,v+dv;umin2=np.where((ulo<=0)&(uhi>=0),0,np.minimum(ulo*ulo,uhi*uhi));umax2=np.maximum(ulo*ulo,uhi*uhi);a,b=self.cfg['UpperLower348'][:2];glo=vslo-a-b*umax2;ghi=vshi-a-b*umin2
    if np.any((uhi>=-1.08)&(ulo<=1.08)&(ghi>=-.36)&(glo<=.22)&(own+do>=1.5)&(own-do<=2.5)):result.append((xx,yy))
  return result
 def integrate_grid(self,n,offset=(.5,.5)):
  total=0;tiles=self.possible_cells();start=time.perf_counter()
  for x,y in tiles:
   # Crop triangles to the current logical cell before the independent ray calculation.
   yy,xx=np.mgrid[:n,:n];pts=np.stack([x+(xx.ravel()+offset[0])/n,y+(yy.ravel()+offset[1])/n],axis=1)
   all_rendered=self.rendered.copy();self.rendered&=(self.box[:,0,0]<=x+1)&(self.box[:,1,0]>=x)&(self.box[:,0,1]<=y+1)&(self.box[:,1,1]>=y)
   try:total+=float(self.weights(pts).sum())/(n*n)
   finally:self.rendered=all_rendered
  return {'n':n,'offset':list(offset),'area':total,'logicalTiles':len(tiles),'seconds':time.perf_counter()-start}
if __name__=='__main__':
 i=int(sys.argv[1])if len(sys.argv)>1 else 0;f=Frame(i);start=time.perf_counter();out={'frame':i,'triangles':len(f.tr),'frontSign':f.frontSign,'degenerateAreaUpperBound':f.degenerateArea,'validation':{str(flip):f.validate(flip)for flip in [True,False]},'seconds':time.perf_counter()-start};(R/f'GEOMETRY_MODEL_{i:03}_585.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
