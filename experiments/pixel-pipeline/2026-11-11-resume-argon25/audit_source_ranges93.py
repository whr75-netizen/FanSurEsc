"""Audit source92 against observed support ranges, not inferred semantic labels.

An original constant support is a strict counterexample to replacing its RGB
by a different source-region representative. A nonconstant range is only an
observed gamut envelope; respecting it does not classify AA/paint/lighting.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;G=H/'face93'

def main():
 n=np.load(H/'face28/SOURCE_NATIVE28.npz');s=np.load(H/'face86/REGIONS86.npz');v=np.load(H/'face92/SOURCE_VALUE92.npz');rgb=n['rgba'][:,:,:3];mask=s['mask'];regions=s['regions'];mapped=rgb.copy();mapped[mask]=v['colours'][v['referenceIndices'][v['labels'][mask]]];rows=[];bad=np.zeros(mask.shape,bool);constant=np.zeros_like(bad)
 for k in np.unique(regions[mask]):
  m=mask&(regions==k);c=rgb[m].astype(int);out=mapped[m].astype(int);lo=c.min(0);hi=c.max(0);escape=np.maximum(lo-out,0)+np.maximum(out-hi,0);invalid=(escape>0).any(1);bad[m]=invalid;is_constant=bool(np.array_equal(lo,hi));constant[m]=is_constant
  rows.append({'supportId':int(k),'texels':len(c),'sourceMin':lo.tolist(),'sourceMax':hi.tolist(),'sourceConstant':is_constant,'outsideRangeTexels':int(invalid.sum()),'maximumChannelRangeExcursion':int(escape.max()),'sourceMSE':float(np.mean((out-c)**2))})
 d=(mapped[mask].astype(float)-rgb[mask]);result={'CPUOnly':True,'source92Addresses':len(v['referenceIndices']),'observedSupportComponents':len(rows),'nativeSourceColours':len(v['colours']),'sourceMSE':float(np.mean(d*d)),'maximumChannelError':int(abs(d).max()),'absoluteChannelErrorQuantiles':np.quantile(abs(d),[.5,.95,.99,1]).tolist(),'componentsWithRangeEscape':sum(x['outsideRangeTexels']>0 for x in rows),'rangeEscapeTexels':int(bad.sum()),'constantComponentsChanged':sum(x['sourceConstant']and x['outsideRangeTexels']>0 for x in rows),'constantTexelsChanged':int((bad&constant).sum()),'semanticRegionTruthClaimed':False,'rangeIsSufficientQualityCriterion':False,'rows':rows};(G/'SOURCE_RANGE_AUDIT93.json').write_text(json.dumps(result,indent=2));heat=rgb.copy();heat[bad]=[255,0,255];board=Image.new('RGB',(1050,380),(25,28,34));draw=ImageDraw.Draw(board)
 for j,(im,title)in enumerate([(rgb,'Original source'),(mapped,'Source92 representatives'),(heat,'Magenta: outside original support range')]):
  draw.text((j*350+4,5),title,fill='white');board.paste(Image.fromarray(im).resize((340,340),Image.Resampling.NEAREST),(j*350+4,27))
 board.save(G/'SOURCE_RANGE_AUDIT93.png');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
