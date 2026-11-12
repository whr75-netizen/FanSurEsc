from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from audit_polarity76 import luminance
from region_order79 import feasible
H=Path(__file__).resolve().parent;G=H/'face79'

def main():
 source=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=source['rgba'][:,:,:3];mask=source['mask'];labels=np.load(H/'face76/SOURCE_REGIONS76.npz')['labels'];pairs=json.loads((G/'ACTUAL_LABEL_POLARITY79.json').read_text())['rows'];domains={int(n):np.unique(luminance(rgb[mask&(labels==n)]))for n in np.unique(labels[mask])};orders=[];witness=[]
 for row in pairs:
  if row['nativePolarity']==0:continue
  fg=row['actualForegroundRegion']
  for k,bg in enumerate(row['actualFlankRegions']):
   edge=(fg,bg)if row['nativePolarity']<0 else(bg,fg);orders.append(edge)
   if edge[0]==edge[1]:witness.append({'region':fg,'nativeForegroundXY':row['nativeForegroundXY'],'nativeFlankXY':row['nativeFlankXY'][k],'nativeForegroundRGB':row['nativeForegroundRGB'],'nativeFlankRGB':row['nativeFlankRGB'][k],'requiredOrder':row['nativePolarity']})
 result=feasible(domains,orders);result.update(sourceRegionCount=len(domains),nativeStrictOrders=len(orders),uniqueNativeStrictOrders=len(set(orders)),sameLabelWitnesses=witness,allFaceLUTActivationAllowed=result['feasible'],GPUExecuted=False,partitionRefinementRequired=not result['feasible']);(G/'REGION_ORDER79.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in['sameLabelWitnesses','order','leastNativeLuminance','predecessor','sameLabelOrders','cyclicOrDependentRegions']}));print('same-label',len(result['sameLabelOrders']),'cycle/dependent',len(result['cyclicOrDependentRegions']))
 board=Image.new('RGB',(900,600),(27,29,35));draw=ImageDraw.Draw(board)
 for i,r in enumerate(witness[:6]):
  x,y=r['nativeForegroundXY'];crop=rgb[max(0,y-8):y+9,max(0,x-8):x+9];im=Image.fromarray(crop).resize((170,170),Image.Resampling.NEAREST);xx=(i%3)*300;yy=(i//3)*300;draw.text((xx+5,yy+5),f"region{r['region']} same-label conflict",fill='white');draw.text((xx+5,yy+25),f"native {r['nativeForegroundXY']} vs {r['nativeFlankXY']}",fill='white');board.paste(im,(xx+5,yy+50));draw.text((xx+5,yy+225),f"{r['nativeForegroundRGB']} | {r['nativeFlankRGB']}",fill='white')
 board.save(G/'SAME_LABEL_WITNESSES79.png')
if __name__=='__main__':main()
