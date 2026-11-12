"""Actual RGB and source-aligned exterior ink receipts over one bounded run.

Counts describe observed transitions. They cannot prove each transition is
legitimate: this capture retains a source/depth witness, not full-cell alpha.
"""
from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from selected_light84 import geometry
from shade_history85 import prior_address
from review_packed93 import ribbon
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face93/motion480'

def main():
 import sys
 partial='--partial-diagnostic'in sys.argv;c=G/'capture';r=json.loads((c/('FAILED.json'if partial else'COMPLETE.json')).read_text());assert r['ownedResourcesReleased']and r['restorationChecksPass'];assert(not r['packetComplete']and r['errors']and not(c/'COMPLETE.json').exists())if partial else(r['packetComplete']and not r['errors']);prefix='INCOMPLETE_'if partial else'ACTUAL_';records=[];line_rows=[];provenance=[];previous=None;reject={};positions=[];rotations=[];animation=[];sim=0.;visible_frames=0
 for i,f in enumerate(r['stream77']['frames']):
  w,h=f['QROI'][2:];raw=decode((c/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,24,w,4).transpose(1,0,2,3);geo=geometry(c/f['light84']['sourceGeometryFile']);sid,frame,width,mapped,anchors,vp,view,data=ribbon(c/f['ribbon93']['file']);assert sid==geo['sourceId']==f['sourceId']and frame==geo['frame']==f['frame'];valid=a[15,:,:,3]==1;visible_frames+=int(valid.any());sim+=f['deltaTime'];positions.append(f['motion']['avatarPosition']);rotations.append(f['motion']['avatarRotation']);provenance.append({'frame':frame,'sourceId':sid,'rawSHA256':f['rawSHA256'],'ribbonSHA256':hashlib.sha256((c/f['ribbon93']['file']).read_bytes()).hexdigest()})
  def aligned(mask):
   return{(int(x+f['QROI'][0]-np.floor(anchors[2])),int(h-1-y+f['QROI'][1]-np.floor(anchors[3])))for y,x in np.argwhere(mask)}
  raw_ink=aligned(a[21,:,:,3]==1);joint_ink=aligned(a[23,:,:,3]==1);pre=aligned(a[16,:,:,3]==1);key=(f['ribbon93']['sourceLocalDeformationSHA256'],tuple(f['ribbon93']['relativeViewLinear']),tuple(vp[:2,:3].ravel()))
  if previous is not None:
   old,oldf,oldg,oldraw,oldjoint,oldpre,oldkey=previous;assert f['frame']==oldf['frame']+1 and f['model']==oldf['model'];assert np.array_equal(f['light84']['projection85'],oldf['light84']['projection85'])
   for y,x in np.argwhere(valid):
    pos,why=prior_address(oldg,int(a[9,y,x,3]),a[10,y,x,:2],oldf['QROI'])
    if pos is None:reject[why]=reject.get(why,0)+1;continue
    px,py=pos
    if old[15,py,px,3]!=1 or not np.array_equal(old[9,py,px,1:],a[9,y,x,1:]):reject['previous-not-visible-same-carrier']=reject.get('previous-not-visible-same-carrier',0)+1;continue
    records.append([frame,a[15,y,x,0]-1,old[15,py,px,0]-1,a[8,y,x,0],old[8,py,px,0],a[13,y,x,0],old[13,py,px,0],*a[14,y,x,:3],*old[14,py,px,:3]])
   line_rows.append({'frame':frame,'rawFinalInkChangedCells':len(raw_ink^oldraw),'jointFinalInkChangedCells':len(joint_ink^oldjoint),'jointPreFinalSourceRasterChangedCells':len(pre^oldpre),'exactLocalDeformationAndViewLinear':key==oldkey,'currentJointInkCells':len(joint_ink),'currentPreFinalCells':len(pre)})
  previous=a,f,geo,raw_ink,joint_ink,pre,key
  canvas=Image.new('RGB',(520,174),(26,29,34));draw=ImageDraw.Draw(canvas)
  for j,(plane,title)in enumerate([(0,'Native'),(14,'Face LUT92'),(20,'Raw ribbon'),(22,'Joint ribbon')]):
   im=srgb(a[plane]);draw.text((j*130+3,4),title,fill='white');canvas.paste(im,(j*130+3,23));canvas.paste(im.resize((w*4,h*4),Image.Resampling.NEAREST),(j*130+3,58))
  draw.text((3,162),f'{"FAILED RUN prefix"if partial else"Actual"} F{frame} ({i+1}/480). Current witness gate.',fill='white');animation.append(canvas)
 z=np.asarray(records);assert z.ndim==2 and z.shape[1]==13;same=z[:,1]==z[:,2];sameq=z[:,5]==z[:,6];samergb=(z[:,7:10]==z[:,10:13]).all(1);assert samergb[same&sameq].all();np.savez_compressed(G/(prefix+'RGB_CONTINUITY93.npz'),records=z);q=np.asarray(rotations);p=np.asarray(positions);exact=[v for v in line_rows if v['exactLocalDeformationAndViewLinear']];result={'completedCapture':not partial,'failedRunDiagnosticPrefixOnly':partial,'plannedFrames':480,'observedGPUFrames':len(animation),'actualSimulationSeconds':sim,'nominalSecondsAt60Hz':len(animation)/60,'framesWithVisibleFace':visible_frames,'sourceCarrierPairs':len(z),'sameAddressAndQPairs':int((same&sameq).sum()),'unexplainedRGBChangesAtSameAddressAndQ':0,'sameAddressNoHistoryQTransitions':int((same&(z[:,3]!=z[:,4])).sum()),'sameAddressActualHistoryQTransitions':int((same&~sameq).sum()),'sourceAddressChanges':int((~same).sum()),'rejectedCorrespondences':reject,'maximumDisplacementMetres':float(np.linalg.norm(p-p[0],axis=1).max()),'maximumRotationDegrees':float(np.degrees(2*np.arccos(np.clip(abs(q@q[0]),0,1))).max()),'allMovementInputsMatch':all(v['motion']['matches']for v in r['stream77']['frames']),'sourceAlignedRawInkChangedCells':sum(v['rawFinalInkChangedCells']for v in line_rows),'sourceAlignedJointInkChangedCells':sum(v['jointFinalInkChangedCells']for v in line_rows),'exactLocalDeformationAndViewLinearPairs':len(exact),'exactInputJointPreFinalChangedCells':sum(v['jointPreFinalSourceRasterChangedCells']for v in exact),'everyInkTransitionCausallyClassified':False,'wholeDestinationCellAlphaOrOwnerProven':False,'longGameplayOrArtSuccessClaimed':False,'product77Changed':False,'lineRows':line_rows};(G/(prefix+'MOTION93.json')).write_text(json.dumps(result,indent=2));(G/(prefix+'PROVENANCE93.json')).write_text(json.dumps(provenance,indent=2));durations=[round((i+1)*1000/60)-round(i*1000/60)for i in range(len(animation))];animation[0].save(G/(prefix+'MOTION93.webp'),save_all=True,append_images=animation[1:],duration=durations,loop=0,lossless=True,method=4);print(json.dumps({k:v for k,v in result.items()if k!='lineRows'}))
if __name__=='__main__':
 import sys
 if '--root'in sys.argv:G=Path(sys.argv[sys.argv.index('--root')+1]).resolve()
 main()
