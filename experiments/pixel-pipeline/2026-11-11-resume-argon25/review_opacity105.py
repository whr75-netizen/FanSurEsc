"""Actual105 GPU result; keep complete opacity/ownership claims separate."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_motion64 import srgb
import review_rows103
H=Path(__file__).resolve().parent

def main():
 sys.argv=[sys.argv[0],'face105/edge64'];review_rows103.main();root=H/'face105/edge64';r=json.loads((root/'capture/COMPLETE.json').read_text());examples=[];panels=[];pruned=0;ids=set()
 for f in r['stream77']['frames']:
  assert'Only same authored edge'in f['opacity105'];a,_,_=packet(root,f);j={tuple(v[:2]):v for v in f['joint97']['rows']};c={tuple(v[:2]):v for v in f['coupled98']['rows']};mask=a[8,:,:,3]==2;pruned+=int(mask.sum())
  for y,x in np.argwhere(mask):
   primary=j[x,y][3];targets=[];bits=int(c[x,y][2])
   for dy in[-1,0,1]:
    for dx in[-1,0,1]:
     if bits&(1<<((dy+1)*3+dx+1))and a[3,y+dy,x+dx,3]==1 and a[8,y+dy,x+dx,3]!=2:targets.append({'xy':[int(x+dx),int(y+dy)],'primaryEdge':j[x+dx,y+dy][3],'selectedCurveEdge':c[x+dx,y+dy][4]})
   assert targets
   if not any(t['primaryEdge']==primary for t in targets):examples.append({'frame':f['frame'],'xy':[int(x),int(y)],'sourcePrimaryEdge':primary,'targets':targets,'sameEdgeCurveSupportExistsButUniqueFinalPrimaryIdentityNotProven':True})
  if f['ordinal']in[0,38,46,47,63]or mask.any():
   if len(panels)>=12:continue
   im=Image.new('RGB',(780,276),'#20252c');d=ImageDraw.Draw(im);d.text((8,5),f"ACTUAL GPU105 frame {f['frame']}; CPU same-edge paths -> unchanged98B raster; default77 preserved",fill='white')
   diff=np.zeros((*mask.shape,3),np.uint8);diff[mask]=[250,160,40];diff[a[3,:,:,0]==3]=[80,130,220]
   for i,(picture,label)in enumerate([(srgb(a[12]),'actual97 opaque support control'),(srgb(a[7]),'actual105 same-edge candidate'),(Image.fromarray(np.flipud(diff)),'orange removed; blue unknown retained')]):
    im.paste(picture,(8+258*i,30));im.paste(picture.resize((182,182),Image.Resampling.NEAREST),(46+258*i,64));d.text((8+258*i,250),label,fill='white')
   panels.append(im);ids.add(f['frame'])
 board=Image.new('RGB',(780,276*len(panels)),'#20252c')
 for i,p in enumerate(panels):board.paste(p,(0,276*i))
 board.save(root/'ACTUAL_OPACITY105.png');out={'actualGPUFrames':len(r['stream77']['frames']),'runtimeCPUDecisionAndActualGPUColourNotOfflineReplay':True,'newGPUKernelsOrPasses':0,'exactPaletteInkAndUnknownContracts':True,'prunedCellsVersusSameFrame97OpaqueControl':pruned,'sameFrameOld98GPUComparisonPerformed':False,'reviewedFrames':sorted(ids),'differentPrimaryRepresentativeCases':examples,'differentPrimaryEdgeIsNotByItselfProofOfFeatureLoss':True,'completeCoRepresentedFeatureOwnershipProven':False,'generalOpacityContinuousWorldAndArtCompleted':False,'product77DefaultChanged':False,'restored':r['restorationChecksPass']};(root/'ACTUAL_OPACITY105.json').write_text(json.dumps(out,indent=2));print(json.dumps({**out,'differentPrimaryRepresentativeCases':len(examples)},indent=2))

if __name__=='__main__':main()
