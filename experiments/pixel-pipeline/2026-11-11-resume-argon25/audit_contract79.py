"""Compare native pairs at their actual output labels, never an assumed parent."""
from pathlib import Path
import json,numpy as np
from PIL import Image
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face79'

def main():
 G.mkdir(exist_ok=True);old=json.loads((H/'face76/POLARITY_FAILURE76.json').read_text());partition=np.load(H/'face76/SOURCE_REGIONS76.npz');labels=partition['labels'];refs=json.loads((H/'face76/SOURCE_REFERENCES76.json').read_text());out=np.array(Image.open(H/'face76/FULL_REFERENCE76.png'));rows=[]
 for r in old['rows']:
  x,y=r['nativeForegroundXY'];fg=int(labels[y,x]);bg=[int(labels[yy,xx])for xx,yy in r['nativeFlankXY']];c=out[y,x];flanks=np.array([out[yy,xx]for xx,yy in r['nativeFlankXY']]);assert np.array_equal(c,refs[str(fg)]['RGB8'])and all(np.array_equal(v,refs[str(label)]['RGB8'])for v,label in zip(flanks,bg));v=luminance(c);lo,hi=sorted(luminance(flanks));sign=-1 if v<lo else 1 if v>hi else 0;native=r['nativePolarity'];rows.append({**r,'actualForegroundRegion':fg,'actualFlankRegions':bg,'actualForegroundRGB':c.tolist(),'actualFlankRGB':flanks.tolist(),'actualOutputPolarity':sign,'actualPolarityInverted':bool(native!=0 and sign!=0 and native!=sign),'actualPolarityLost':bool(native!=0 and sign==0)})
 result={'sourcePairs':len(rows),'sourceNonzeroPolarityPairs':sum(r['nativePolarity']!=0 for r in rows),'oldAssumedParentInversions':sum(r['polarityInverted']for r in rows),'actualLabelInversions':sum(r['actualPolarityInverted']for r in rows),'actualLabelLostContrast':sum(r['actualPolarityLost']for r in rows),'foregroundAnchorNotInClaimedChild':sum(r['actualForegroundRegion']!=r['child']for r in rows),'flankNotInClaimedParent':sum(any(l!=r['parent']for l in r['actualFlankRegions'])for r in rows),'GPUExecuted':False,'candidate76StillNotAdopted':True,'rows':rows};(G/'ACTUAL_LABEL_POLARITY79.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
