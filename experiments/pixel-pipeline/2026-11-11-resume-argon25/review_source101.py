"""Validate actual source-view selection and final-owner-aware LUT coverage."""
from pathlib import Path
import json,collections,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def main():
 root=H/'face101/source32';r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];frames=r['stream77']['frames'];assert len(frames)==32 and r['stream77']['actualConsecutive'];counts=collections.Counter();roles=collections.Counter();examples=[];board=Image.new('RGB',(780,3*286),'#20252c');pictures=0;palette=np.fromfile(root/'capture/RUNTIME_PALETTE89.rgb',np.uint8).reshape(-1,3,3)
 for f in frames:
  a,_,_=packet(root,f);encoded=a[14,:,:,0].astype(int);assert np.array_equal(encoded.astype(np.float32),a[14,:,:,0]);flags=encoded&511;kind=encoded//512;assert(kind<=3).all();owner=a[14,:,:,3];assert np.array_equal(owner,owner.astype(int).astype(np.float32));known=a[14,:,:,2]==1;valid=(a[4,:,:,3]==1)&(a[4,:,:,0]>0);assert np.array_equal(known,flags==0)and np.array_equal(valid,known);rgb=np.flipud(np.asarray(srgb(a[5])))[:,:,:3];fam=a[4,:,:,0].astype(int)-1;q=a[4,:,:,2].astype(int);assert np.array_equal(rgb[valid],palette[fam[valid],q[valid]])
  rawFace=(a[0,:,:,1]==f['mappedRole100'])&(a[0,:,:,0]>0)&(a[13,:,:,2]==1);actualFace=(owner==f['mappedRole100'])&(a[13,:,:,2]==1);ordinary=actualFace&((flags&1)==0);alternative=valid&(kind>=2);counts['rawFaceSourcesOverVisibleActor']+=int(rawFace.sum());counts['actualVisibleFaceOwner']+=int(actualFace.sum());counts['ordinaryVisibleFaceOwner']+=int(ordinary.sum());counts['ordinaryVisibleFaceWithLUT']+=int((ordinary&valid).sum());counts['ordinaryVisibleFaceWithoutLUT']+=int((ordinary&~valid).sum());counts['alternativeMainViewCells']+=int(alternative.sum());counts['unknownEyeDomain']+=int((actualFace&~valid&((flags&1)!=0)).sum())
  hidden=rawFace&~actualFace;counts['rawFaceButDifferentActualOwner']+=int(hidden.sum())
  for value in owner[hidden]:roles[int(value)]+=1
  for y,x in np.argwhere(alternative):
   if len(examples)<16:examples.append({'frame':f['frame'],'sourceId':f['sourceId'],'xy':[int(x),int(y)],'sourceKind':int(kind[y,x]),'sourceMetaInHeadDepth':a[0,y,x].tolist(),'originalUV':a[1,y,x,:2].tolist(),'selectedQ':a[4,y,x].tolist(),'actualOwnerRole':int(owner[y,x]),'RGB':rgb[y,x].tolist()})
  pruned=a[8,:,:,3]==2;assert np.array_equal(a[7][~pruned],a[12][~pruned])and np.array_equal(a[7][pruned],a[5][pruned]);assert np.array_equal(a[12][a[3,:,:,0]==3],a[9][a[3,:,:,0]==3])
  if f['ordinal']in[0,8,16]:
   row=pictures*286;d=ImageDraw.Draw(board);d.text((8,row+6),f"Actual GPU frame {f['frame']}   final owner + source camera receipt",fill='white');mask=np.zeros((*flags.shape,3),np.uint8);mask[actualFace&valid]=[60,185,100];mask[actualFace&~valid]=[80,130,255];mask[hidden]=[185,90,225];mask[alternative]=[255,190,50]
   for i,(im,title)in enumerate([(srgb(a[11]),'Native'),(srgb(a[7]),'private101 candidate'),(Image.fromarray(np.flipud(mask)),'green faceLUT / purple raw face hidden')]):
    board.paste(im,(8+258*i,row+30));board.paste(im.resize((208,208),Image.Resampling.NEAREST),(8+258*i,row+64));d.text((42+258*i,row+34),title,fill='white')
   pictures+=1
 out={'actualFrames':len(frames),'sameFrameSourceViewAndFinalOwnerRecorded':True,'knownGatesAndFiniteLUTExactEveryCell':True,'lineControlUnknownContractsExact':True,'counts':dict(counts),'nonFaceOwnerRolesOverRawFace':dict(roles),'alternativeExamples':examples,'mainAlternativeExercised':bool(counts['alternativeMainViewCells']),'product77DefaultChanged':False,'generalColourSegmentationOrArtCompleted':False};(root/'SOURCE_VIEW101.json').write_text(json.dumps(out,indent=2));board.save(root/'SOURCE_VIEW101.png');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
