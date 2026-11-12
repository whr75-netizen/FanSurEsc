"""Compare actual103/105 at bit-identical line geometry, not identical light."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_packed93 import ribbon
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def main():
 old=H/'face103/rows64C';new=H/'face105/edge64';before=json.loads((old/'capture/COMPLETE.json').read_text())['stream77']['frames'];after=json.loads((new/'capture/COMPLETE.json').read_text())['stream77']['frames'];assert len(before)==len(after)==64;changes=[];panels=[]
 for f,g in zip(before,after):
  a,_,_=packet(old,f);b,_,_=packet(new,g);v=ribbon(old/'capture'/f['ribbon93']['file']);w=ribbon(new/'capture'/g['ribbon93']['file']);assert f['frame']==g['frame']and f['joint97']['rows']==g['joint97']['rows']and all(np.array_equal(v[i],w[i])for i in[2,3,4,5,6,7]);oldMask=a[8,:,:,3]==2;newMask=b[8,:,:,3]==2;assert np.all(~oldMask|newMask)
  for y,x in np.argwhere(oldMask!=newMask):
   row=next(t for t in f['joint97']['rows']if t[:2]==[int(x),int(y)]);assert b[3,y,x,3]==1 and b[13,y,x,2]!=1 and np.array_equal(b[7,y,x],b[5,y,x]);entry={'frame':f['frame'],'sourceBefore':f['sourceId'],'sourceAfter':g['sourceId'],'xy':[int(x),int(y)],'sourceEdge':int(row[3]),'positiveSourceAreaUpper':row[7],'addedRedundantCellRemoved':True,'currentLUTBackingExact':True};changes.append(entry)
   board=Image.new('RGB',(860,330),'#20252c');d=ImageDraw.Draw(board);d.text((8,6),f"ACTUAL GPU paired line geometry frame {f['frame']}; cell ({x},{y}); source edge {int(row[3])}",fill='white')
   for i,(array,title)in enumerate([(a[7],'actual103 previous'),(b[7],'actual105 shared-diagonal path'),(b[5],'actual105 current backing')]):
    im=srgb(array[:,:,:3]);board.paste(im,(8+280*i,30));large=im.resize((260,260),Image.Resampling.NEAREST);mark=ImageDraw.Draw(large);mark.rectangle((int(x)*10,(25-int(y))*10,int(x)*10+9,(25-int(y))*10+9),outline='#40ff60');board.paste(large,(8+280*i,60));d.text((40+280*i,34),title,fill='white')
   d.text((8,318),f"Original source area upper {row[7]:.8f}. Geometry/witness rows exact; separate-run lighting may differ.",fill='white');panels.append(board)
 out={'actualRuns':[str(old.relative_to(H)),str(new.relative_to(H))],'lineGeometryAndWitnessRowsExactlyMatched':64,'allPriorPrunesRetained':True,'additionalActualPrunedCells':changes,'sameInputLightingClaimed':False,'fullArtOrUniqueFeatureOwnerProven':False};(new/'PAIRED_LINE105.json').write_text(json.dumps(out,indent=2));sheet=Image.new('RGB',(860,330*len(panels)))
 for i,p in enumerate(panels):sheet.paste(p,(0,330*i))
 sheet.save(new/'PAIRED_LINE105.png');print(json.dumps(out,indent=2))

if __name__=='__main__':main()
