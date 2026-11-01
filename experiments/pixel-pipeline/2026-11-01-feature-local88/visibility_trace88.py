"""Coordinate provenance of remaining visibility changes, not an art classifier."""
from pathlib import Path
import json,numpy as np
from test_saved88 import packet
from validate_gpu88 import read
HERE=Path(__file__).resolve().parent
def main():
 gpu=json.loads((HERE/'gpu88/GPU_RESULT88.json').read_text());folder=Path(gpu['output']);data=[]
 for frame in [124,125]:
  inp=packet(HERE/f'validated/frame{frame}/INPUT88.bin');ids=read(folder/f'frame{frame}-1.bin')[1];cov=read(folder/f'frame{frame}-2.bin')[1];yy,xx=np.where(ids[...,0]>0);data.append((inp,ids,cov,int(xx.min()),int(yy.min())))
 a,b=data;rows=[]
 for y,x in np.argwhere(a[1][...,0]>0):
  yy,xx=y-a[4]+b[4],x-a[3]+b[3]
  assert np.array_equal(a[1][y,x],b[1][yy,xx])and np.array_equal(a[2][y,x,2:],b[2][yy,xx,2:])
  if a[2][y,x,0]==b[2][yy,xx,0]:continue
  row={'localCanonicalXY':a[2][y,x,2:].tolist(),'ownerPartPaletteSourceIndex':a[1][y,x].tolist(),'observations':[]}
  for (inp,ids,cov,ox,oy),px,py in [(a,x,y),(b,xx,yy)]:
   p=inp['origin']+(np.array([px,py])+.5)/inp['scale'];rx,ry,rw,rh=inp['roi'];sx,sy=np.floor([(p[0]-rx)*4,(272-p[1]-ry)*4]).astype(int);plane=inp['planes'][inp['owners'].index(int(ids[py,px,0]))];ray=inp['ray'];near=ray[0]+p[0]*ray[1]+p[1]*ray[2];depth=float(-(np.dot(plane[:3],near)+plane[3])/np.dot(plane[:3],ray[3]));metas=inp['meta'][:,sy,sx]
   row['observations'].append({'sourceId':inp['sourceId'],'frame':inp['frame'],'nativeOutputXY':[int(px),int(py)],'headLogicalSampleTopLeft':p.tolist(),'source4xXY':[int(sx),int(sy)],'featureAnchor':inp['anchor'].tolist(),'visibleFraction':float(cov[py,px,0]),'occluderBits':int(cov[py,px,1]),'virtualAuthoredEyePlaneDepth':depth,'metas_S0_S3_S4_S5_S6':metas.tolist()})
  rows.append(row)
 out={'frames':[124,125],'registeredIntrinsicShapeAndPartIDsIdentical':True,'changedNativeVisibilityFragments':len(rows),'examples':rows,'interpretation':'These are actual saved4x source/depth inputs at different final native sample locations. They do not by themselves label generic face as semantic lid, prove continuous visibility, or justify ignoring skin. No visibility cache was frozen across an unknown occluder state.'};q=HERE/'VISIBILITY_TRACE88.json';assert not q.exists();q.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'changed':len(rows),'first':rows[:1]},indent=2))
if __name__=='__main__':main()
