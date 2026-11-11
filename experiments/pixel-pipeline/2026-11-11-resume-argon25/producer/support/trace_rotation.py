"""Same-frame CPU geometry audit of remaining rotated destination rejection."""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'resume-20261111'))
from replay_phase25 import FaceWithOneOriginalAlpha,NativeAlpha,geometry,plane,buffer,read
os.environ['PIXEL111_FROZEN_INPUTS']='1';sys.path.insert(0,str(R/'support-contract112'))
from source112 import Source,load,packet_list
from support112 import Support

def main():
 target=H/'native-proof'if '--native-proof'in sys.argv else H
 run=target/'motion-run'if target!=H else H/'gate-alpha/motion-run'
 info=read(R/'aperture-runtime111/inputs/ALPHA111.json');src=next(v for v in info['images']if v['renderer']==1 and v['submesh']==3)
 ip=R/'aperture-runtime111/inputs'/src['file'];assert hashlib.sha256(ip.read_bytes()).hexdigest()==src['sha256']
 im=Image.open(ip);alphaImage=np.asarray(im.convert('RGBA'))[:,:,3].astype(float)/255;im.close()
 base=np.array(read(R/'argon23-runtime113/SOURCE113.json')['ownSkinMask'],np.uint32);extra=np.array(read(H/'SHARED_SOURCE_MASK26.json')['additionalBits'],np.uint32)
 _,oldPackets=packet_list();affiliation=Support(Source(),load(oldPackets[3]));assert affiliation.key==read(H/'SHARED_SOURCE_MASK26.json')['sourceCacheKey']
 s=read(run/'STATE113-0060-finished.json');pack={v['sourceId']:Path(v['output'])for v in s['sequencePackets']};d=read(target/'GPU_MOTION26.json');rows=[]
 for neg in d['negativeRows']:
  p=pack[neg['sourceId']];m=read(p/'RAW_MANIFEST.json');c=geometry(p,m);mi=np.unique(c['triangles'][(c['sources'][:,0]==1)&(c['sources'][:,1]==3),3]);assert len(mi)==1
  alpha=NativeAlpha.__new__(NativeAlpha);alpha.ctx=c;alpha.images={int(mi[0]):alphaImage};alpha.sources={int(mi[0]):src};face=FaceWithOneOriginalAlpha(c,base|extra,alpha)
  x,y=neg['physicalROI'];w,h=m['grid102']['eyeTopLeftROI'][2:];q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4)[y,x];v=buffer(p/'ASSIGNED-visibility24.f32').reshape(h,w,16,4)[y,x,:,:2]
  proof=face.query(q[:,:2],q[:,2],2,limit=m['runtime24']['socketDiameters'][1]);assert np.array_equal(np.array([a['faceInterval']for a in proof]),v)
  hits={hit['sourcePrimitive']:hit for sample in proof for hit in sample['hits']if not hit['exempt113']}
  classified=[]
  for k,hit in hits.items():
   owners=c['owners'][hit['triangle'],:3];verts=affiliation.tri[k-1]
   sums={eye:float(np.linalg.norm(affiliation.deltas[eye][verts].astype(float),axis=1).sum())for eye in [1,2]};reasons=[]
   if np.sum(owners==2)<2:reasons.append('contralateral_vertex_majority')
   if sums[2]<sums[1]:reasons.append('other_eye_source_blink_dominates')
   if hit['depthGapMetres']>m['runtime24']['socketDiameters'][1]:reasons.append('beyond_current_socket_depth_limit')
   assert reasons,'Unclassified missing affiliation must not be called legitimate external occlusion'
   classified.append(dict(hit,vertexOwners=owners.tolist(),sourceBlinkMagnitudeSums=sums,baseBits=int(base[k-1]),sharedBits=int(extra[k-1]),reasons=reasons))
  rows.append({'sourceId':m['sourceId'],'frame':m['frameIndex'],'sourceCertificateAlreadyVerified':True,'sameFrameGPUFaceSamplesExact':16,
   'faceVisible16':v.sum(0).tolist(),'unexemptHits':classified})
 result={'actualQuerySamplesCPUExact':16*len(rows),'rows':rows,'newGPUExecuted':False,'allUnexemptHitsFailIpsilateralOrSocketRule':True,
  'statusMeaning':'-117 is definite destination face exposure below8/16, not an unknown interval. Whether that surface should co-transport requires source affiliation evidence.'}
 (target/'ROTATION_REJECTIONS26.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'exactQueries':result['actualQuerySamplesCPUExact'],'hits':[[(v['sourcePrimitive'],v['vertexOwners'],v['depthGapMetres'],v['sharedBits'])for v in row['unexemptHits']]for row in rows]}))
if __name__=='__main__':main()
