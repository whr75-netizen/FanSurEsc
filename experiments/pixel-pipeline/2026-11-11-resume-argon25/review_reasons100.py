"""Classify actual source-address exclusions; never relax a selection gate."""
from pathlib import Path
import json,collections,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_motion64 import srgb
H=Path(__file__).resolve().parent
BITS={1:'eyeDomain',2:'nativeCellNotActor',4:'nativeCellCoordinate',8:'mainSourceVsNativeOwner',16:'selectedRole',32:'selectedVsHeadUV',64:'headVsMainUV',128:'headVsSelectedShade',256:'mainVsSelectedRoleOwnerPrimitive'}

def main():
 root=H/'face100/reasons32';r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];frames=r['stream77']['frames'];assert len(frames)==32 and r['stream77']['actualConsecutive'];groups=collections.Counter();bits=collections.Counter();counts=collections.Counter();examples=[];board=Image.new('RGB',(780,3*286),'#20252c');pictures=0
 for f in frames:
  assert f['rawSourcePlaneCount100']==15;a,world,depth=packet(root,f);flags=a[14,:,:,0].astype(int);assert np.array_equal(flags.astype(np.float32),a[14,:,:,0])and(flags>=0).all()and(flags<=511).all();known=a[14,:,:,2]==1;assert np.array_equal(known,flags==0),'new reason receipt disagrees with unchanged SourceValue89 known gate';palette=(a[4,:,:,3]==1)&(a[4,:,:,0]>0);assert np.array_equal(palette,known),'known source address had no valid LUT/history result'
  native=(a[0,:,:,1]==f['mappedRole100'])&(a[0,:,:,0]>0)&(a[13,:,:,2]==1);missing=native&~palette;counts['nativeVisibleFace']+=int(native.sum());counts['knownLUT']+=int((native&palette).sum());counts['unknown']+=int(missing.sum());counts['unknownEyeDomain']+=int((missing&((flags&1)!=0)).sum());counts['unknownOrdinaryDomain']+=int((missing&((flags&1)==0)).sum())
  for value in flags[missing]:groups[int(value)]+=1
  for bit in BITS:bits[BITS[bit]]+=int((missing&((flags&bit)!=0)).sum())
  if len(examples)<16:
   for y,x in np.argwhere(missing):
    if len(examples)>=16:break
    examples.append({'sourceId':f['sourceId'],'frame':f['frame'],'xy':[int(x),int(y)],'flags':int(flags[y,x]),'reasons':[name for bit,name in BITS.items()if flags[y,x]&bit],'domainX':float(a[14,y,x,1]),'primitive':int(a[0,y,x,3]),'uv':a[1,y,x,:2].tolist()})
  # Original colour operation and unknown appearance remain the98B contract.
  pruned=a[8,:,:,3]==2;assert np.array_equal(a[7][~pruned],a[12][~pruned])and np.array_equal(a[7][pruned],a[5][pruned]);assert np.array_equal(a[12][a[3,:,:,0]==3],a[9][a[3,:,:,0]==3])
  if f['ordinal']in[0,8,16]:
   row=pictures*286;draw=ImageDraw.Draw(board);draw.text((8,row+6),f"Actual GPU frame {f['frame']}  source exclusions, unchanged output",fill='white');mask=np.zeros((*flags.shape,3),np.uint8);mask[native&palette]=[60,185,100];mask[missing&((flags&1)!=0)]=[80,130,255];mask[missing&((flags&1)==0)]=[255,90,50]
   for i,(im,title)in enumerate([(srgb(a[11]),'Native'),(srgb(a[7]),'98B + CPU99C'),(Image.fromarray(np.flipud(mask)),'green LUT / blue domain / orange other')]):
    board.paste(im,(8+258*i,row+30));board.paste(im.resize((208,208),Image.Resampling.NEAREST),(8+258*i,row+64));draw.text((42+258*i,row+34),title,fill='white')
   pictures+=1
 out={'actualFrames':len(frames),'sourceReasonsMatchUnchangedKnownGateEveryCell':True,'knownLUTValidEveryCell':True,'unknownControlAnd98BOutputExact':True,'counts':dict(counts),'countMaskUsesRawFaceRoleAndVisibleActorNotFinalFaceOwner':True,'countsAreNotProofOfMissingVisibleFacePalette':True,'finalOwnerRoleNotInThisPacket':True,'unknownExactFlagGroups':dict(sorted(groups.items())),'cooccurringReasonsNotDisjoint':dict(bits),'firstExamples':examples,'reasonsExplainThisNewSourceOnlyNotOld960Frames':True,'selectionGateRelaxed':False,'artOrSegmentationCompleted':False};(root/'SOURCE_REASONS100.json').write_text(json.dumps(out,indent=2));board.save(root/'SOURCE_REASONS100.png');print(json.dumps({k:v for k,v in out.items()if k!='firstExamples'},indent=2))
if __name__=='__main__':main()
