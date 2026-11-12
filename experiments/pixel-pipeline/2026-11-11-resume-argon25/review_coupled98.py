from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def main():
 root=H/'face98'/sys.argv[1];report=json.loads((root/'capture/COMPLETE.json').read_text());assert report['packetComplete']and report['Edit']and report['ownedResourcesReleased']and report['restorationChecksPass']and not report['errors'];assert report['stream77']['sourceAlpha97ManagedBytesAfterRelease']==0
 commonPolicy='CoupledRibbon98B/CoupledRibbon98B.shader'in(root/'capture/RUN.cs.txt').read_text();rows=[];pictures=[];sequence=[];changes=[]
 for f in report['stream77']['frames']:
  a,world,depth=packet(root,f);m=f['coupled98'];assert m['sourceId']==f['sourceId']and m['frame']==f['frame'];w=f['QROI'][2];proof={tuple(v[:2]):v for v in m['rows']};pruned=a[8,:,:,3]==2;assert np.array_equal(a[8,:,:,0],a[3,:,:,0]);assert np.array_equal(a[7][~pruned],a[12][~pruned]);assert np.array_equal(a[7][pruned],a[5][pruned]);assert not np.any(pruned&(a[3,:,:,3]!=1));assert not np.any(pruned&(a[3,:,:,0]!=1));assert np.array_equal(a[7][a[3,:,:,0]==3],a[12][a[3,:,:,0]==3])
  for y,x in np.argwhere(pruned):
   v=proof[x,y];mask=int(v[2]);realized=[];assert mask!=0 and mask&16==0 and a[8,y,x,2]==0
   for dy in range(-1,2):
    for dx in range(-1,2):
     if mask&(1<<((dy+1)*3+dx+1)):
      nx,ny=x+dx,y+dy;assert 0<=nx<w and 0<=ny<w;assert (nx,ny)in proof and proof[nx,ny][2]==0 and proof[nx,ny][4]>=0;realized.append(bool(a[3,ny,nx,3]==1 and not pruned[ny,nx]))
   assert (any(realized)if commonPolicy else all(realized))
   changes.append({'frame':f['frame'],'xy':[int(x),int(y)],'sameSourceNeighbourMask':mask,'old97':a[12,y,x].tolist(),'actual98':a[7,y,x].tolist()})
  rows.append({'frame':f['frame'],'CPUmsIncluding97':m['CPUmsIncluding97'],'maskCandidates':m['maskCandidates'],'centrelineWitnesses':m['centrelineWitnesses'],'continuityChecks':m['continuityChecks'],'actualPrunedCells':int(pruned.sum()),'changedRGB':int((a[7]!=a[12]).any(2).sum()),'unknownRetained':int((a[3,:,:,0]==3).sum())})
  p=Image.new('RGB',(1050,292),'#20252c');d=ImageDraw.Draw(p);d.text((12,8),f"ACTUAL GPU98 frame {f['frame']}: current geometry/alpha -> joint line cells. Product77 default unchanged.",fill='white')
  for i,(plane,label)in enumerate([(11,'Native baseline'),(5,'LUT92'),(12,'Joint97 control'),(7,'Coupled98')]):
   im=srgb(a[plane,:,:,:3]);p.paste(im,(12+i*240,33));p.paste(im.resize((208,208),Image.Resampling.NEAREST),(12+i*240,66));d.text((48+i*240,39),label,fill='white')
  d.text((12,276),f"Certified redundant cells removed {int(pruned.sum())}; unknown retained {rows[-1]['unknownRetained']}.",fill='white');sequence.append(p)
  if len(pictures)==0 or 'actorSource96'in f:pictures.append(p)
 out={'actualGPUFrames':len(rows),'simulatedSeconds':sum(f['deltaTime']for f in report['stream77']['frames']),'sameFrameCPUSelectedGeometryNotOfflineRGBReplay':True,'unchangedCellsExact97':True,'prunedCellsExactCurrentLUT':True,'unknownRetained':True,'actualPrunedCells':sum(v['actualPrunedCells']for v in rows),'maskCandidates':sum(v['maskCandidates']for v in rows),'CPUmsMedian':float(np.median([v['CPUmsIncluding97']for v in rows])),'CPUmsMaximum':max(v['CPUmsIncluding97']for v in rows),'rows':rows,'changes':changes,'generalOpacitySolved':False,'worldContinuousOcclusionProven':False,'artAdopted':False}
 (root/'ACTUAL_COUPLED98.json').write_text(json.dumps(out,indent=2));sheet=Image.new('RGB',(1050,292*len(pictures)), '#20252c')
 for i,p in enumerate(pictures):sheet.paste(p,(0,292*i))
 sheet.save(root/'ACTUAL_COUPLED98.png');sequence[0].save(root/'ACTUAL_SEQUENCE98.webp',save_all=True,append_images=sequence[1:],duration=80,loop=0,lossless=True)
 ids=sorted(set([0,len(sequence)//5,2*len(sequence)//5,3*len(sequence)//5,4*len(sequence)//5,len(sequence)-1]));strip=Image.new('RGB',(1050,292*len(ids)), '#20252c')
 for i,k in enumerate(ids):strip.paste(sequence[k],(0,292*i))
 strip.save(root/'SEQUENCE_REVIEW98.png');print(json.dumps({k:v for k,v in out.items()if k not in ['rows','changes']}))
if __name__=='__main__':main()
