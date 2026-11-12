"""Check actual pre-Present source samples; retain finite sampling limitations."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from selected_light84 import geometry,barycentric_uv
from review_motion64 import srgb
H=Path(__file__).resolve().parent
def frame(root,f):
 w,h=f['QROI'][2:];b=decode((root/'capture'/f['compressedFile']).read_bytes(),f['bytes']);assert len(b)==259584 and hashlib.sha256(b).hexdigest()==f['rawSHA256'];a=np.frombuffer(b,'<f4').reshape(h,24,w,4).transpose(1,0,2,3);assert np.isfinite(a).all();info=f['sourceFootprint95'];assert info['currentFrame']==f['frame']and info['presentSerial']==f['nativeSerial']and info['worldSerial']==f['worldSerial'];x,y=np.meshgrid(np.arange(w),np.arange(h));first=np.array(info['worldFirst']);raw=a[4:8];head=a[8:12];uv=a[12:16];geo=geometry(root/'capture'/f['light84']['sourceGeometryFile']);assert geo['sourceId']==f['sourceId']and geo['frame']==f['frame'];near,far=info['near'],info['far'];expected=(1-raw[...,1]if info['reversedZ']else raw[...,1])*(far-near)+near;assert np.max(abs(expected-raw[...,0]))<=max(1e-4,abs(far)*2e-7)
 for i in range(4):
  assert np.array_equal(raw[i,:,:,2],first[0]+2*x+(i&1));assert np.array_equal(raw[i,:,:,3],first[1]+2*y+(i>>1))
 point=a[16,:,:,:2];matches=(raw[:,:,:,2:]==point[None]).all(3);assert(matches.sum(0)==1).all()
 address=a[17];known=address[:,:,3]==1;assert not(address[:,:,0]<0).any();used=a[23,:,:,3]==1;assert np.array_equal(a[22][~used],a[18][~used]);assert(a[22][used,3]==1).all();assert np.array_equal(used,(a[23,:,:,:3]==1).all(2))
 source_point_errors=[];shift=np.asarray(info.get('nativeExtraSourceCells',[.25,.25]));shift_measured='nativeExtraSourceCells'in info
 for i,yy,xx in np.argwhere(head[:,:,:,1]==4):
  primitive=int(head[i,yy,xx,3])-1
  if primitive<0 or primitive>=len(geo['tri']):continue
  t=geo['v'][geo['tri'][primitive]].astype(float);bary=barycentric_uv(t[:,3:5],uv[i,yy,xx,:2]);
  if bary is None:continue
  p=bary@t[:,5:7];p[1]=272-p[1];sample=(np.array(info['headFirst'])+[2*xx+(i&1)+.5,2*yy+(i>>1)+.5])*.5-shift;source_point_errors.append(float(np.max(abs(p-sample))))
 z=a[19,:,:,0]+f['depthOffset'];world_front=raw[:,:,:,0]+np.float32(.0001)<z[None];source_front=(head[:,:,:,0]>0)&(head[:,:,:,0]+f['depthOffset']+np.float32(.0001)<z[None]);world_counts=world_front.sum(0);source_counts=source_front.sum(0);rows=[]
 for yy,xx in np.argwhere(used):rows.append({'localXY':[int(xx),int(yy)],'edge':int(a[19,yy,xx,1]),'lineWorldDepth':float(z[yy,xx]),'opaqueOutput':a[22,yy,xx].tolist(),'rawWorldDepths':raw[:,yy,xx,0].tolist(),'rawWorldSamplesInFront':int(world_counts[yy,xx]),'rawHeadSamplesInFront':int(source_counts[yy,xx]),'rawHeadRoles':head[:,yy,xx,1].tolist(),'representativeNativeXY':point[yy,xx].tolist(),'sourcePrimitiveIDs':head[:,yy,xx,3].tolist()})
 return a,{'frame':f['frame'],'sourceId':f['sourceId'],'finitePacket':True,'faceColourSamples':int(known.sum()),'rawWorldCellsWithIndependentRGB':int(np.any(a[:4]!=a[:1],axis=(0,3)).sum()),'rawWorldCellsWithIndependentDepth':int(np.any(raw[:,:,:,0]!=raw[:1,:,:,0],axis=0).sum()),'sourceFaceProjectionSamples':len(source_point_errors),'maxRawHeadUVReprojectionErrorCells':max(source_point_errors,default=None),'nativeExtraSourceCells':shift.tolist(),'nativeShiftMeasuredInFrame':shift_measured,'oneFrameFallbackFromFull319PrepareCurrentExactHalfNativePixelRule':not shift_measured,'candidateLineCells':rows,'fourSourceSamplesNotContinuousCoverage':True,'newSelectionOrOpacityPolicyApplied':False}
def main():
 root=Path(sys.argv[1]);r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];rows=[];panels=[]
 for f in r['stream77']['frames']:
  a,row=frame(root,f);rows.append(row)
  if len(panels)<12:
   images=[srgb(a[p,:,:,:3])for p in [0,1,2,3,18,22]];p=Image.new('RGB',(6*(26*5+8),26*5+32),'#22262b');d=ImageDraw.Draw(p)
   for i,(im,label)in enumerate(zip(images,['Raw world00','Raw world10','Raw world01','Raw world11','LUT92','Joint93'])):p.paste(im.resize((130,130),Image.Resampling.NEAREST),(i*138,24));d.text((i*138,5),label,fill='white')
   panels.append(p)
 out={'actualGPUFrames':len(rows),'sourceSamples':'raw world/depth before Native395.Present and unquantized native head meta/UV','noNewComputeDispatch':True,'rows':rows,'totalCandidateLineCells':sum(len(x['candidateLineCells'])for x in rows),'candidateLineCellsWithRawWorldSamplesInFront':sum(sum(c['rawWorldSamplesInFront']>0 for c in x['candidateLineCells'])for x in rows),'candidateLineCellsWithRawHeadSamplesInFront':sum(sum(c['rawHeadSamplesInFront']>0 for c in x['candidateLineCells'])for x in rows),'continuousFullPixelAlphaVisibilityProven':False,'artAdopted':False};(root/'ACTUAL_FOOTPRINT95.json').write_text(json.dumps(out,indent=2));sheet=Image.new('RGB',(panels[0].width,sum(p.height for p in panels)),'white');y=0
 for p in panels:sheet.paste(p,(0,y));y+=p.height
 sheet.save(root/'ACTUAL_FOOTPRINT95.png');print(json.dumps({k:v for k,v in out.items()if k!='rows'}));print(json.dumps(rows[0]))
if __name__=='__main__':main()
