"""Preserve measured support gamut while sharing RGB addresses across UV.

Intersect all observed component ranges at each original RGB key. A source
representative must lie in every member's interval. This avoids promoting
material/support identity to colour identity, or treating AA as authored truth.
"""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from chromatic_value92 import build
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face93'

def main():
 n=np.load(H/'face28/SOURCE_NATIVE28.npz');p=np.load(H/'face86/REGIONS86.npz');v=np.load(H/'face92/SOURCE_VALUE92.npz');scalar=np.load(H/'face90/SOURCE_VALUE90.npz');base=np.load(H/'face88/SOURCE_VALUE88.npz');rgb=n['rgba'][:,:,:3];mask=p['mask'];regions=p['regions'];colours,inv,counts=np.unique(rgb[mask],axis=0,return_inverse=True,return_counts=True);assert np.array_equal(colours,v['colours']);index=np.full(mask.shape,-1,int);index[mask]=inv;lo=np.zeros((len(colours),3),int);hi=np.full_like(lo,255)
 for k in np.unique(regions[mask]):
  m=mask&(regions==k);ids=np.unique(index[m]);lo[ids]=np.maximum(lo[ids],rgb[m].min(0));hi[ids]=np.minimum(hi[ids],rgb[m].max(0))
 bounds=np.stack([lo,hi],1);tree=build(colours,counts,scalar['colourAddress'],v['pairs'],reference_bounds=bounds);refs=colours[tree['referenceIndices']];mapped=refs[tree['colourAddress'][inv]];out=rgb.copy();out[mask]=mapped;old=rgb.copy();old[mask]=colours[v['referenceIndices'][v['colourAddress'][inv]]];labels=np.full(mask.shape,-1,np.int32);labels[mask]=tree['colourAddress'][inv];field_escape=0;constant_changed=0
 for k in np.unique(regions[mask]):
  m=mask&(regions==k);a=rgb[m];b=out[m];invalid=((b<a.min(0))|(b>a.max(0))).any(1);field_escape+=int(invalid.sum());constant_changed+=int(np.array_equal(a.min(0),a.max(0))and invalid.any())
 y=luminance(refs);orders=all(y[tree['colourAddress'][a]]<y[tree['colourAddress'][b]]for a,b in base['orders']);d=mapped.astype(float)-rgb[mask];result={'CPUOnly':True,'originalSupportIsSemanticTruth':False,'oldAddresses':len(v['referenceIndices']),'candidateAddresses':tree['addresses'],'complete':tree['complete'],'unresolvedContrastPairs':len(tree['unresolvedPairs']),'unresolvedRangeColours':len(tree['unresolvedRangeColours']),'outsideObservedSupportRangeTexels':field_escape,'constantComponentsChanged':constant_changed,'oldSourceMSE':float(np.mean((old[mask].astype(float)-rgb[mask])**2)),'candidateSourceMSE':float(np.mean(d*d)),'maximumChannelError':int(abs(d).max()),'absoluteChannelErrorQuantiles':np.quantile(abs(d),[.5,.95,.99,1]).tolist(),'allMeasuredSourceYOrdersPreserved':bool(orders),'sameRGBSameAddress':True,'sourceRepresentativeIsObservedRGB':True,'GPUOrArtAdopted':False,'splitBudget':512};(G/'SOURCE_RANGE_CANDIDATE93.json').write_text(json.dumps(result,indent=2));np.savez_compressed(G/'SOURCE_RANGE_CANDIDATE93.npz',labels=labels,mask=mask,colours=colours,counts=counts,colourAddress=tree['colourAddress'],referenceIndices=tree['referenceIndices'],bounds=bounds);(G/'RANGE_REFINEMENT93.json').write_text(json.dumps(tree['history'],indent=2));board=Image.new('RGB',(1050,380),(25,28,34));draw=ImageDraw.Draw(board)
 for j,(im,title)in enumerate([(rgb,'Original source'),(old,'Current source92'),(out,'CPU observed-range candidate')]):
  draw.text((j*350+4,5),title,fill='white');board.paste(Image.fromarray(im).resize((340,340),Image.Resampling.NEAREST),(j*350+4,27))
 board.save(G/'SOURCE_RANGE_CANDIDATE93.png');print(json.dumps(result))
if __name__=='__main__':main()
