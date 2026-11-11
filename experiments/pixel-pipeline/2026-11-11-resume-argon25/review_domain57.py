"""Verify actual native pixels, and test ordinary carriers separately from eye domains."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from native_contour42 import coordinates,native_min,oracle
from surface_paths34 import native
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face57';C=G/'capture';O=G/'analysis'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors']
 assert len(r['frames'])==1 and r['temporalStabilityValidated'] is False
 O.mkdir(exist_ok=True);surface,binding=native();f=r['frames'][0]
 def read(name):
  ps=[p for p in r['planes']if p['frame']==f['frame']and p['sourceId']==f['sourceId']and p['name']==name]
  assert ps and all(p['format']=='linear RGBAFloat32 little-endian; bottom-left storage'for p in ps)
  out=np.full((ps[0]['height'],ps[0]['width'],4),np.nan,np.float32);seen=np.zeros(out.shape[:2],bool)
  for p in ps:
   y=p['bottomRow'];n=p['rows'];a=np.fromfile(C/p['file'],dtype='<f4');assert a.nbytes==p['bytes']and a.nbytes<=262144 and not seen[y:y+n].any();out[y:y+n]=a.reshape(n,p['width'],4);seen[y:y+n]=True
  assert seen.all()and np.isfinite(out).all();return out
 w=f['QROI'][2];h=f['QROI'][3];a=read('atlas40');assert a.shape==(h,16*w,4);fields=[a[:,i*w:(i+1)*w]for i in range(16)]
 b=read('ownerReceipts47');back=[b[:,i*w:(i+1)*w]for i in range(4)];e=read('featureProducer49');eyes=[e[:,i*w:(i+1)*w]for i in range(4)]
 info=f['frameInfo']['nativeComposite42'];reg=f['frameInfo']['sourceCarrier48'];assert reg['triangleCount']==len(surface.indices)and reg['rendererOrdinal']==binding['rendererOrdinal']and reg['subMesh']==binding['subMesh']
 assert info['sourceId']==f['sourceId']and info['sameFrame']==f['frame']and info['presentSerialExecuted']>info['presentSerialBeforeGraphExecute']
 q,p,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);assert info['nativeROI'][:2]==native_min(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']).tolist()
 ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);expected,gate=oracle(fields[3],fields[4],fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink)
 assert expected.tobytes()==fields[10].tobytes()and gate.tobytes()==fields[11].tobytes()
 before=read('nativeBefore42');after=read('nativeAfter42');assert np.array_equal(before,np.repeat(np.repeat(fields[9],2,0),2,1))and np.array_equal(after,np.repeat(np.repeat(expected,2,0),2,1))
 owner=back[0];raw=back[2];visible=fields[14][:,:,2]==1;designed=back[3][:,:,0]==-4;good=back[3][:,:,0]==4
 assert not(good&designed).any();assert np.all((fields[15][:,:,0][designed&visible])==4)
 candidate=visible&inside&(fields[14][:,:,:2]==q).all(2)&(raw[:,:,0]==owner[:,:,2])&(raw[:,:,1]==owner[:,:,0])&(raw[:,:,2]==owner[:,:,1])&(raw[:,:,1]==reg['registeredRole'])&(raw[:,:,3]>0)&(raw[:,:,3]<=len(surface.indices))&(raw[:,:,3]==np.rint(raw[:,:,3]))
 assert np.array_equal(good,candidate&~designed)
 # Transported eye domain must be a real producer domain, not a fabricated mesh point.
 assert np.array_equal(designed,eyes[2][:,:,0]>=.5)
 geo=geometry(C/f"geometry-frame{f['frame']}.bin");assert geo['sourceId']==f['sourceId'];bad=[];residuals=[]
 for y,x in np.argwhere(good):
  t=int(round(raw[y,x,3]))-1;uv=back[1][y,x,:2].astype(float);v=surface.inv[t]@(uv-surface.tri[t,0]);bary=np.r_[1-v.sum(),v];world=bary@geo['points']['world'][surface.indices[t]].astype(float)
  depth=-float(geo['view'][2,:3]@world+geo['view'][2,3])+info['depthOffset'];error=abs(depth-float(owner[y,x,2]));residuals.append(error)
  if not surface.good[t]or bary.min()<-2e-7 or error>=2e-5:bad.append({'localPixel':[int(x),int(y)],'sourceQ':q[y,x].tolist(),'primitive':t+1,'UV':uv.tolist(),'minBarycentric':float(bary.min()),'depthResidualMetres':error})
 use=gate[:,:,3]==1;source=gate[:,:,0]==1;current=read('currentColour47')
 row={'actualSourceId':f['sourceId'],'frame':f['frame'],'actualGPUCaptured':True,'CPUCompositeByteExact':True,'actualNativeBeforeAfterByteExact':True,'sourceLineCells':int(source.sum()),'finalSelected':int(use.sum()),'styleRejected':int((source&(gate[:,:,1]==0)).sum()),'worldRejected':int((source&(gate[:,:,2]==0)).sum()),'unselectedNativeRGBChanged':int((fields[10][~use]!=fields[9][~use]).any(1).sum()),'selectedInkMismatch':int((fields[10][use,:3]!=ink).any(1).sum()),'designedDomainCells':int(designed.sum()),'visibleDesignedDomainCells':int((designed&visible).sum()),'designedPointClaims':int((good&designed).sum()),'ordinaryCarrierClaims':int(good.sum()),'ordinaryGeometryInvalid':bad,'ordinaryGeometryPass':not bad,'maxOrdinaryDepthResidualMetres':max(residuals,default=0),'originalCarrierCandidateWithinDesignedDomain':int((candidate&designed).sum()),'currentVsNativeRGBDifferent':int((visible&(current[:,:,:3]!=fields[9][:,:,:3]).any(2)).sum()),'borrowedBuffersReleased':False,'product77Changed':False,'temporalStabilityValidated':False,'fullFacePaletteOrVariableWidthComplete':False,'restorationChecksPass':True,'ownResourcesReleased':True}
 (O/'ACTUAL_DOMAIN57.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
 def image(z):
  z=np.clip(z[::-1,:,:3],0,1);z=np.where(z<=.0031308,12.92*z,1.055*np.power(z,1/2.4)-.055);return Image.fromarray(np.uint8(np.rint(z*255)))
 mask=np.zeros((h,w,3),np.float32);mask[designed]=[.12,.55,1];mask[good]=[.1,.8,.2]
 for y,x in [(z['localPixel'][1],z['localPixel'][0])for z in bad]:mask[y,x]=[1,0,.1]
 pictures=[('Actual Native395',image(before)),('GPU curve candidate',image(after)),('Blue: eye domain / green: carrier',image(mask))]
 board=Image.new('RGB',(1080,340),(28,30,35));draw=ImageDraw.Draw(board)
 for i,(title,im)in enumerate(pictures):
  draw.text((i*360+10,10),title,fill='white');board.paste(im,(i*360+10,36));board.paste(im.resize((224,224),Image.Resampling.NEAREST),(i*360+100,36))
 draw.text((10,285),'One actual source frame; native pixel scale + nearest zoom. Product77 unchanged.',fill='white')
 draw.text((10,310),f"Geometry-invalid ordinary claims: {len(bad)}. Full face palette/width/time stability incomplete.",fill='white')
 board.save(G/'FACE_SOURCE_DOMAIN57.png');print(json.dumps(row))
if __name__=='__main__':main()
