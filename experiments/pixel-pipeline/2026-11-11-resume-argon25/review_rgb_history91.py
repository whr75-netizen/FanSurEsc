"""Actual RGB continuity by native carrier, not screen-colour averages.

Current visibility takes precedence. Separate source-address variation from Q
variation. Store compact observed receipts for repository CPU rechecking; these
cannot stand in for a new GPU execution or the locally retained raw atlases.
"""
from pathlib import Path
import json,hashlib,numpy as np
from frame_bytes77 import decode
from selected_light84 import geometry
from shade_history85 import prior_address
H=Path(__file__).resolve().parent;G=H/'face91/bounded192'

def pack(root):
 c=root/'capture';r=json.loads((c/'COMPLETE.json').read_text());previous=None;records=[];reject={};hashes=[];positions=[];rotations=[];visible_frames=0;sim=0
 for f in r['stream77']['frames']:
  w,h=f['QROI'][2:];raw=decode((c/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,22,w,4).transpose(1,0,2,3);geo=geometry(c/f['light84']['sourceGeometryFile']);assert geo['sourceId']==f['sourceId']and geo['frame']==f['frame'];valid=a[20,:,:,3]==1;visible_frames+=int(valid.any());positions.append(f['motion']['avatarPosition']);rotations.append(f['motion']['avatarRotation']);sim+=f['deltaTime'];hashes.append({'frame':f['frame'],'sourceId':f['sourceId'],'rawSHA256':f['rawSHA256'],'file':f['compressedFile'],'geometrySHA256':hashlib.sha256((c/f['light84']['sourceGeometryFile']).read_bytes()).hexdigest()})
  if previous is not None:
   old,oldf,oldg=previous;assert f['frame']==oldf['frame']+1 and f['model']==oldf['model'];assert np.array_equal(f['light84']['projection85'],oldf['light84']['projection85'])
   for y,x in np.argwhere(valid):
    pos,why=prior_address(oldg,int(a[9,y,x,3]),a[11,y,x,:2],oldf['QROI'])
    if pos is None:reject[why]=reject.get(why,0)+1;continue
    px,py=pos
    if old[20,py,px,3]!=1 or not np.array_equal(old[9,py,px,1:],a[9,y,x,1:]):reject['previous-not-currently-visible-same-carrier']=reject.get('previous-not-currently-visible-same-carrier',0)+1;continue
    # Frame, source-address pair, no-history Q pair, actual-history Q pair,
    # current/previous actual RGB and current/previous no-history RGB.
    records.append([f['frame'],a[20,y,x,0]-1,old[20,py,px,0]-1,a[8,y,x,0],old[8,py,px,0],a[16,y,x,0],old[16,py,px,0],*a[19,y,x,:3],*old[19,py,px,:3],*a[18,y,x,:3],*old[18,py,px,:3]])
  previous=a,f,geo
 z=np.asarray(records);assert z.ndim==2 and z.shape[1]==19;np.savez_compressed(root/'RGB_CONTINUITY91.npz',records=z);p=np.asarray(positions);q=np.asarray(rotations);dots=np.clip(abs(q@q[0]),0,1);summary={'actualGPUFrames':len(hashes),'framesWithVisibleFace':visible_frames,'actualSimulationSeconds':sim,'sameCurrentlyVisibleNativeCarrierPairs':len(z),'rejectedCorrespondences':reject,'maximumAvatarDisplacementMetres':float(np.linalg.norm(p-p[0],axis=1).max()),'maximumAvatarQuaternionAngleFromFirstDegrees':float(np.degrees(2*np.arccos(dots)).max()),'pureSubpixelCameraRelativeSweepClaimed':False,'longGameplayStabilityClaimed':False,'sourceAndQAreSeparate':True,'rawAtlasesRemainLocal':str(c),'rawAtlasesIncludedInRepository':False,'frames':hashes};(root/'RGB_CONTINUITY_PROVENANCE91.json').write_text(json.dumps(summary,indent=2));return summary

def verify(root):
 d=np.load(root/'RGB_CONTINUITY91.npz')['records'];same_source=d[:,1]==d[:,2];same_q=d[:,5]==d[:,6];same_rgb=(d[:,7:10]==d[:,10:13]).all(1);nohistory_q=d[:,3]!=d[:,4];qchange=~same_q;colour_change=~same_rgb;source_change=~same_source;assert same_rgb[same_source&same_q].all(),'same palette address and Q must have identical actual RGB';assert not(colour_change&same_source&same_q).any();result={'observedCarrierPairs':len(d),'sameSourceAddressPairs':int(same_source.sum()),'sourceAddressChanges':int(source_change.sum()),'sameAddressNoHistoryQTransitions':int((same_source&nohistory_q).sum()),'sameAddressActualHistoryQTransitions':int((same_source&qchange).sum()),'sameAddressActualRGBTransitions':int((same_source&colour_change).sum()),'sameAddressAndQPairs':int((same_source&same_q).sum()),'unexplainedActualRGBChangesAtSameAddressAndQ':0,'sourceAddressChangesWithSameQ':int((source_change&same_q).sum()),'noRGBTimeAveraging':True,'coverageAndFirstFrameOrBoundaryAmbiguityNotHidden':True,'fixtureIsObservedGPUOutputNotNewExecution':True};(root/'RGB_CONTINUITY91.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':
 import sys
 if '--verify-only'not in sys.argv:pack(G)
 verify(G)
