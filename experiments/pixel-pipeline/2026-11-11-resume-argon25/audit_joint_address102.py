"""Separate observed feature contrast from base-support channel-range extrema."""
from pathlib import Path
import json,time,numpy as np
from joint_address102 import optimize
H=Path(__file__).resolve().parent;G=H/'face102'

def main():
 z=np.load(H/'face92/SOURCE_VALUE92.npz');original=np.load(H/'face28/SOURCE_NATIVE28.npz')['rgba'][:,:,:3];support=np.load(H/'face86/REGIONS86.npz');mask=z['mask'];rgb=z['colours'];_,inverse=np.unique(original[mask],axis=0,return_inverse=True);index=np.full(mask.shape,-1,int);index[mask]=inverse;profile={tuple(sorted(map(int,v)))for v in z['profilePairs']};pigment=set();base=set()
 for region in np.unique(support['regions'][mask]):
  regionMask=mask&(support['regions']==region);ids=np.unique(index[regionMask]);c=rgb[ids];dest=pigment if support['foreground'][regionMask].all()else base
  for axis in range(3):
   a=int(ids[np.argmin(c[:,axis])]);b=int(ids[np.argmax(c[:,axis])])
   if a!=b:dest.add(tuple(sorted((a,b))))
 hard=np.asarray(sorted(profile|pigment),int).reshape(-1,2);orders=np.load(H/'face88/SOURCE_VALUE88.npz')['orders'];palette=np.fromfile(H/'face99/long960/capture/RUNTIME_PALETTE89.rgb',np.uint8).reshape(-1,3,3);clock=time.monotonic();result=optimize(rgb,z['counts'],z['colourAddress'],z['referenceIndices'],palette,hard,orders);elapsed=time.monotonic()-clock;labels=np.full(mask.shape,-1,np.int32);labels[mask]=result['labels'][inverse];np.savez_compressed(G/'JOINT_ADDRESS102.npz',**{k:v for k,v in result.items()if isinstance(v,np.ndarray)},sourceLabels=labels,referenceIndices=z['referenceIndices'],colours=rgb,hardPairs=hard,orders=orders)
 info={k:v for k,v in result.items()if not isinstance(v,np.ndarray)};info.update(CPUOnly=True,seconds=elapsed,observedProfilePairs=len(profile),detectedForegroundRangePairs=len(pigment),baseRangePairsNotAutomaticallyFeatures=len(base),droppedRangeOnlyPairs=len(base-(profile|pigment)),sourceSupportAndRGBAChanged=False,paletteRGBChanged=False,paletteFamilies=len(palette),sourceRegionMeaningReclassified=False,actualGPUOrArtAdopted=False);(G/'JOINT_ADDRESS102.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
if __name__=='__main__':main()
