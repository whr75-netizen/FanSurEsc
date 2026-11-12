"""Locate actual world sample disagreement without inventing continuous depth.

Reproduce Native395.Present + JointRibbon97 at the recorded cell representative,
then compare the existing four native world tiles and the witness-nearest tile.
All are actual discrete world samples, not a continuous visibility oracle.
"""
from pathlib import Path
import json,sys,collections,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def site(origin,point,delta):
 return np.floor(np.asarray(origin,np.float32)+(np.asarray(point,np.float32)+np.asarray(delta,np.float32))*np.float32(2)).astype(int)

def main():
 root=H/sys.argv[1];r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass'];counts=collections.Counter();examples=[];selected=[]
 for f in r['stream77']['frames']:
  a,world,depth=packet(root,f);w=f['QROI'][2];head=np.array([f['QROI'][0],272-f['QROI'][1]-w]);join=np.asarray(f['join']);first=np.asarray(f['sourceFootprint95']['worldFirst']);delta=np.asarray(f['delta'],np.float32)
  def z_at(npix):
   x,y=np.asarray(npix)-first
   assert 0<=x<depth.shape[1]and 0<=y<depth.shape[0]
   return np.float32(depth[y,x,0])
  for row in f['joint97']['rows']:
   x,y,state,edge,px,py,z,*_=row
   if state!=1:continue
   x,y=int(x),int(y);q=head+join+[x,y];centre=site(f['nativeOrigin'],q+np.float32(.5),delta);witness=site(f['nativeOrigin'],np.array([px,py])+join,delta);line=np.float32(np.float32(z)+np.float32(f['depthOffset']));old=z_at(centre);allowed=old>0 and line<=np.float32(old+np.float32(.0001));actor=a[13,y,x,2]==1;cell=np.array_equal(a[13,y,x,:2],q);expected=bool(allowed and not actor and cell and(q>=0).all()and(q<[480,272]).all());actual=a[3,y,x,3]==1
   assert actual==expected,('representative gate mismatch',f['frame'],x,y,line,old,actual,expected)
   counts['knownLineCells']+=1;counts['representativeGateExactlyReproduced']+=1
   if actor or not cell:counts['actorOrCellGateExcluded']+=1;continue
   counts['worldEligibleLineCells']+=1;counts['representativeWorldRejected']+=int(not allowed);wz=z_at(witness);wpass=wz>0 and line<=np.float32(wz+np.float32(.0001));counts['witnessUsesDifferentNativeTile']+=int(not np.array_equal(witness,centre));counts['nearestWitnessWorldSampleDisagreement']+=int(allowed!=wpass)
   base=site(f['nativeOrigin'],q,delta);tiles=[z_at(base+[dx,dy])for dy in[0,1]for dx in[0,1]];passes=[bool(t>0 and line<=np.float32(t+np.float32(.0001)))for t in tiles];partial=any(passes)and not all(passes);counts['mixedFourTileWorldVisibility']+=int(partial)
   if partial or allowed!=wpass:
    sample={'frame':f['frame'],'sourceId':f['sourceId'],'xy':[x,y],'sourceEdge':int(edge),'pointHead':[px,py],'lineDepthNative':float(line),'cellRepresentativeNative':centre.tolist(),'witnessNearestNative':witness.tolist(),'representativeDepth':float(old),'witnessNearestDepth':float(wz),'representativePassed':bool(allowed),'witnessNearestPassed':bool(wpass),'fourActualTileDepths':list(map(float,tiles)),'fourActualTilePassed':passes,'sourceVisibleAreaUpper':float(row[7]),'noneOfTheseSamplesIsContinuousWitnessDepth':True}
    if len(examples)<32:examples.append(sample)
    if len(selected)<6:selected.append((f,a.copy(),sample))
 out={'CPUOnlySavedActualInput':True,'actualFrames':len(r['stream77']['frames']),'counts':dict(counts),'examples':examples,'representativeGateMatchesActualGPU':True,'continuousWorldOcclusionProven':False,'newWorldGateAdopted':False,'remainingInput':'At selected line support/witness coordinates, same-frame evaluated world geometry + shader deformation/alpha, or a renderer-produced continuous coverage contract. Native 2x2 samples cannot certify between samples.'}
 (root/'WORLD_SAMPLE104.json').write_text(json.dumps(out,indent=2))
 board=Image.new('RGB',(880,max(1,len(selected))*220),'#20252c');d=ImageDraw.Draw(board)
 if not selected:d.text((8,8),'No sampled world disagreement in this captured input. Continuous visibility remains unproven.',fill='white')
 for i,(f,a,s)in enumerate(selected):
  y=i*220;d.text((8,y+6),f"ACTUAL frame {f['frame']} cell {s['xy']}   world sample disagreement, not continuous proof",fill='white');im=srgb(a[7,:,:,:3]);board.paste(im,(8,y+30));board.paste(im.resize((156,156),Image.Resampling.NEAREST),(50,y+30));d.text((230,y+35),f"Representative passed {s['representativePassed']}  witness-nearest passed {s['witnessNearestPassed']}",fill='white');d.text((230,y+65),f"4 native tile decisions: {s['fourActualTilePassed']}",fill='white');d.text((230,y+95),f"line z {s['lineDepthNative']:.8f}; original source edge {s['sourceEdge']}",fill='white');d.text((230,y+125),'Preserve partial support. Do not turn one sample into whole-cell visibility.',fill='white')
 board.save(root/'WORLD_SAMPLE104.png');print(json.dumps({k:v for k,v in out.items()if k!='examples'},indent=2))

if __name__=='__main__':main()
