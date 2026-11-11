"""Old-mask CPU counterfactual against new same-frame GPU queries."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'resume-20261111'))
from replay_phase25 import FaceWithOneOriginalAlpha,NativeAlpha,geometry,plane,buffer,read
def main():
 target=H/'native-proof'if '--native-proof'in sys.argv else H
 run=target/'typed-run'if target!=H else H/'gate-alpha/phase-run'
 info=read(R/'aperture-runtime111/inputs/ALPHA111.json');src=next(v for v in info['images']if v['renderer']==1 and v['submesh']==3);ip=R/'aperture-runtime111/inputs'/src['file'];assert hashlib.sha256(ip.read_bytes()).hexdigest()==src['sha256']
 im=Image.open(ip);image=np.asarray(im.convert('RGBA'))[:,:,3].astype(float)/255;im.close()
 old=np.array(read(R/'argon23-runtime113/SOURCE113.json')['ownSkinMask'],np.uint32);extra=np.array(read(H/'SHARED_SOURCE_MASK26.json')['additionalBits'],np.uint32)
 s=read(run/'STATE113-0012-finished.json');rows=[];tests=0
 for pkt in s['sequencePackets']:
  p=Path(pkt['output']);m=read(p/'RAW_MANIFEST.json');c=geometry(p,m);mi=np.unique(c['triangles'][(c['sources'][:,0]==1)&(c['sources'][:,1]==3),3]);assert len(mi)==1
  alpha=NativeAlpha.__new__(NativeAlpha);alpha.ctx=c;alpha.images={int(mi[0]):image};alpha.sources={int(mi[0]):src}
  before=FaceWithOneOriginalAlpha(c,old,alpha);after=FaceWithOneOriginalAlpha(c,old|extra,alpha)
  rx,ry,w,h=m['grid102']['eyeTopLeftROI'];o=np.array(m['forward102']['headHair25']['origin']);cw,ch=np.array(m['forward102']['canonicalSize'])//4
  ids=buffer(p/'curve-identity.f32').reshape(ch,cw,4);cells=buffer(p/'REGION113-cells.f32').reshape(-1,7,4);q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4);v=buffer(p/'ASSIGNED-visibility24.f32').reshape(h,w,16,4);fo=plane(p/'F-FinalOwner.plane')[1]
  for cx,cy in [(10,3),(10,4),(8,5)]:
   role,eye=ids[cy,cx,:2].astype(int)
   if role!=6 or cells[cy*cw+cx,6,2]==0:continue
   j=np.ceil(o+[cx,cy]-.5).astype(int);x=int(j[0]-rx);y=int(ry+h-1-j[1]);qq=q[y,x];vv=v[y,x,:,:2];limit=m['runtime24']['socketDiameters'][eye-1]
   b=before.query(qq[:,:2],qq[:,2],eye,limit=limit);a=after.query(qq[:,:2],qq[:,2],eye,limit=limit)
   bp=np.array([z['faceInterval']for z in b]);ap=np.array([z['faceInterval']for z in a]);assert np.array_equal(ap,vv);tests+=16
   rows.append({'sourceId':m['sourceId'],'frame':m['frameIndex'],'close':m['motion82']['requestedClose'],'canonical':[cx,cy],'owner':int(eye),
    'sourceWitness':float(cells[cy*cw+cx,6,2]),'sameFrameOldMaskCPUVisible16':bp.sum(0).tolist(),'actualNewGPUVisible16':vv.sum(0).tolist(),'sameFrameNewMaskCPUExact':True,'finalOwner':fo[y,x].tolist()})
 (target/'GATE_CAUSAL26.json').write_text(json.dumps({'actualNewGPUSamplesCPUExact':tests,'rows':rows,'oldMaskIsCPUCounterfactualNotSecondGPUVariant':True},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'sameFrameNewGPUSamplesCPUExact':tests,'counterfactualCases':len(rows)}))
if __name__=='__main__':main()
