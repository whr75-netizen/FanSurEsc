"""Reference coupled source-local raster, real native geometry/depth only.

All native parts use the recovered native3D->authored2D registration, then the
same current authored pose map. Source bank pigments replace native iris/white
pigments only. This reference uses original PNG point texels for geometry/alpha
diagnosis, NOT a claim of equivalence to Unity's material/mip/light producer.
"""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'feature-audit86'));from analyse87 import load,texture
sys.path.insert(0,str(ROOT/'feature-layer88'));from feature_layer88 import project
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import Reader,camera
from registration89 import bary2

def mesh(path):
 r=Reader(path);assert r.s()=='aux-mesh67/v1';identity=[r.s(),r.s(),r.i(),r.i()];matrix=r.mat();v=r.a(r.i()*3).reshape(-1,3);n=r.a(r.i()*3).reshape(-1,3);uv=r.a(r.i()*2).reshape(-1,2);tris=[r.a(r.i(),'<i4').reshape(-1,3)for _ in range(r.i())];r.end();return v,n,uv,tris,matrix

def original_materials():
 src=json.loads(Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json').read_text());out={}
 for role in [3,6]:
  m=next(m for m in src['materials']if m['materialId']==role);out[role]={'pixels':np.asarray(Image.open(m['image']['file']).convert('RGBA')),'alphaMode':m['alphaMode'],'cutoff':m['alphaCutoff'],'factor':np.array(m['baseColorFactorLinear'])}
 return out

def draw(framepath,bounds=None):
 d=load(framepath);m=d['manifest'];v,n,uv,tris,world=mesh(framepath/'eye-evaluated.mesh');rest=np.load(ROOT/'whole-eye52/SOURCE_SURFACES52.npz');reg=json.loads((HERE/'REGISTRATION89.json').read_text());P={e['eye']:np.array(e['nativeToAuthoredProjection'])for e in reg['eyes']};H={int(c[3]):np.linalg.inv(np.array(m['eyeFeature']['inverse'][i]).reshape(4,4,order='F')[:3,:3])for i,c in enumerate(m['eyeFeature']['centres'])};head=np.array(m['eyeFeature']['headMatrix']).reshape(4,4,order='F');headrest=(np.c_[v,np.ones(len(v))]@(np.linalg.inv(head)@world).T)[:,:3];nativeRest=rest['native_xyz_head'];assert len(nativeRest)==len(v)==4060
 centres={e['eye']:nativeRest[e['nativeRingVertexIds']].mean(0)for e in reg['eyes']};owners=np.array([min(centres,key=lambda owner:np.dot(p-centres[owner],p-centres[owner]))for p in nativeRest]);worldv=np.c_[v,np.ones(len(v))]@world.T;cam=camera(framepath/'source.camera');depth=-(worldv@cam['view'].T)[:,2];q0={o:np.c_[nativeRest,np.ones(len(v))]@P[o]for o in P};q1={o:np.c_[headrest,np.ones(len(v))]@P[o]for o in P};parent={e['eye']:np.array(e['authoredParent'])for e in reg['eyes']};src=json.loads((ROOT/'feature-layer88/SOURCE_FIXTURE88.json').read_text())['source'];anchors={o:np.floor((np.array([[p['x'],p['y']]for p in src if p['owner']==o]).min(0)+np.array([[p['x'],p['y']]for p in src if p['owner']==o]).max(0))/2)+.5 for o in P};anchor=np.mean([project(H[o],anchors[o])for o in P],0);xy={o:project(H[o],q1[o])-anchor for o in P};extents=np.concatenate([project(H[o],parent[o])-anchor for o in P]);lo=np.floor(extents.min(0)-2)if bounds is None else np.array(bounds[0]);hi=np.ceil(extents.max(0)+2)if bounds is None else np.array(bounds[1]);w,h=np.rint((hi-lo)*4).astype(int);layers={part:np.zeros((h,w,12),float)for part in [3,1,4,6]};materials=original_materials();_,_,bank=texture('TemplateRole.asset','<f4');_,_,bankP=texture('TemplateRGBA.asset','u1')
 for part in [3,1,4,6]:
  out=layers[part]
  for tid,ix in enumerate(tris[part]):
   own=owners[ix]
   for owner in np.unique(own):
    p=xy[int(owner)][ix];start=np.maximum(np.floor((p.min(0)-lo)*4).astype(int),0);end=np.minimum(np.ceil((p.max(0)-lo)*4).astype(int),[w,h]);
    if np.any(end<=start):continue
    yy,xx=np.mgrid[start[1]:end[1],start[0]:end[0]];samples=np.c_[xx.ravel(),yy.ravel()]/4+lo+.125;valid,b=bary2(np.broadcast_to(p,(len(samples),3,2)),samples);ownerval=b@own;valid&=np.rint(ownerval)==owner
    if not valid.any():continue
    px=xx.ravel()[valid];py=yy.ravel()[valid];b=b[valid];z=b@depth[ix];closer=(out[py,px,0]<=0)|(z<out[py,px,0]);px,py,b,z=px[closer],py[closer],b[closer],z[closer]
    if not len(px):continue
    t=b@uv[ix];reference=b@q0[int(owner)][ix]
    if part in [1,4]:
     k=np.floor(reference).astype(int);inrange=(k[:,0]>=0)&(k[:,0]<480)&(k[:,1]>=0)&(k[:,1]<272);k=np.clip(k,[0,0],[479,271]);roles=bank[k[:,1],k[:,0]];ok=inrange&(roles[:,0]==part)&(roles[:,1]==owner);c=bankP[k[:,1],k[:,0]].astype(float)/255
    else:
     mat=materials[part];pic=mat['pixels'];k=np.floor((t%1)*[pic.shape[1],pic.shape[0]]).astype(int);k[:,1]=pic.shape[0]-1-k[:,1];c=pic[k[:,1],k[:,0]].astype(float)/255;c[:,:3]=np.where(c[:,:3]<=.04045,c[:,:3]/12.92,((c[:,:3]+.055)/1.055)**2.4)*mat['factor'][:3];c[:,3]*=mat['factor'][3];ok=c[:,3]>0
     if mat['alphaMode']=='MASK':ok=c[:,3]>=mat['cutoff'];c[:,3]=ok
    # RGB for authored bank remains encoded here; final table makes its space
    # explicit. It is not combined numerically with native RGB in this stage.
    px,py,z,c,t,b=px[ok],py[ok],z[ok],c[ok],t[ok],b[ok];out[py,px,0]=z;out[py,px,1]=owner;out[py,px,2:6]=c;out[py,px,6:8]=t;out[py,px,8]=tid+1;out[py,px,9:12]=b
 return {'sourceId':m['sourceId'],'frame':m['frameIndex'],'anchor':anchor,'bounds':[lo,hi],'layers':layers,'pixelsPerCell':4,'manifest':m}

def resolve(data):
 layers=data['layers'];h,w=layers[3].shape[:2];parts=[3,1,4,6];depth=np.stack([np.where(layers[p][...,0]>0,layers[p][...,0],np.inf)for p in parts]);alpha=np.stack([layers[p][...,5]for p in parts]);order=np.argsort(depth,axis=0,kind='stable');weight=np.zeros_like(alpha);T=np.ones((h,w))
 for rank in range(4):
  indices=order[rank];a=np.take_along_axis(alpha,indices[None],axis=0)[0];v=T*a;np.put_along_axis(weight,indices[None],v[None],axis=0);T*=1-a
 # Shared cell owner is selected once; nearly occluded residual loses naturally.
 ch,cw=h//4,w//4;weights=weight.reshape(4,ch,4,cw,4).sum((2,4));winner=np.argmax(weights,axis=0);winweight=weights.max(0);out=np.zeros((ch,cw,8));detail=[]
 for y,x in np.argwhere(winweight>0):
  pi=winner[y,x];part=parts[pi];sub=weight[pi,y*4:y*4+4,x*4:x*4+4];sy,sx=np.unravel_index(np.argmax(sub),sub.shape);s=layers[part][y*4+sy,x*4+sx];out[y,x,:4]=[part,s[1],winweight[y,x]/16,s[8]];out[y,x,4:7]=s[2:5];out[y,x,7]=1 if part in [1,4]else 0
 return out,weight

def main():
 out=HERE/'reference';out.mkdir(exist_ok=False);run=ROOT/'feature-audit86/run87';st=json.loads(sorted(run.glob('STATE87*.json'))[-1].read_text());rows=[]
 for entry in st['sequencePackets']:
  if entry['frame']not in [124,125,132,133,134,135,136,137,138]:continue
  d=draw(Path(entry['output']));result,weights=resolve(d);frame=entry['frame'];np.savez_compressed(out/f'frame{frame}.npz',result=result,**{f'layer{p}':v for p,v in d['layers'].items()});m=d['manifest'];row={'frame':frame,'sourceId':d['sourceId'],'CloseGetter':m['eyeFeature']['closeMorphs']['Fcl_EYE_Close'],'bounds':[q.tolist()for q in d['bounds']],'anchor':d['anchor'].tolist(),'winningCells':{str(p):int((result[...,0]==p).sum())for p in [1,4,6,3]},'literalBankColourEncoding':'sRGB8 normalized before final table','nativeColourEncoding':'originalPNG point->linear RGB; no runtime material/mip/light equivalence claimed'};rows.append(row)
  image=np.zeros(result.shape[:2]+(3,),np.uint8)
  for part,col in [(1,[210,90,60]),(4,[240,240,235]),(6,[110,70,180]),(3,[90,110,130])]:image[result[...,0]==part]=col
  Image.fromarray(image).resize((image.shape[1]*24,image.shape[0]*24),Image.Resampling.NEAREST).save(out/f'frame{frame}-owner-nearest24.png')
 q=out/'RESULT89_REFERENCE.json';q.write_text(json.dumps({'status':'COUPLED_GEOMETRY_REFERENCE_NOT_FINAL_RGB_OR_GPU','frames':rows,'nativeRegistration':str(HERE/'REGISTRATION89.json'),'limitations':['Original PNG point alpha is explicit source-reference policy, not measured Unity material sampling.','No final face composition or valid reopen frame.','Winner coverage alone may drop a thin important part; Native77 readability regression must be evaluated before adoption.']},indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
