"""CPU native colour-direction refinement; do not adopt on address count alone."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from chromatic_value92 import build
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face92'
def main():
 G.mkdir(exist_ok=True);native=np.load(H/'face28/SOURCE_NATIVE28.npz');part=np.load(H/'face86/REGIONS86.npz');base=np.load(H/'face88/SOURCE_VALUE88.npz');scalar=np.load(H/'face90/SOURCE_VALUE90.npz');rgb=native['rgba'][:,:,:3];mask=part['mask'];regions=part['regions'];colours,inv,counts=np.unique(rgb[mask],axis=0,return_inverse=True,return_counts=True);assert np.array_equal(colours,base['colours']);index=np.full(mask.shape,-1,int);index[mask]=inv;critical=set();profile=set()
 for x,y,x0,y0,x1,y1,sign in base['accepted']:
  for xx,yy in [(x0,y0),(x1,y1)]:profile.add(tuple(sorted((int(index[y,x]),int(index[yy,xx])))))
 critical|=profile
 # Source-region channel-range witnesses, not additional semantic labels.
 for k in np.unique(regions[mask]):
  ids=np.unique(index[mask&(regions==k)]);c=colours[ids]
  for axis in range(3):
   lo=int(ids[np.argmin(c[:,axis])]);hi=int(ids[np.argmax(c[:,axis])])
   if lo!=hi:critical.add(tuple(sorted((lo,hi))))
 tree=build(colours,counts,scalar['colourAddress'],critical);refs=colours[tree['referenceIndices']];mapped=refs[tree['colourAddress'][inv]];out=rgb.copy();out[mask]=mapped;labels=np.full(mask.shape,-1,np.int32);labels[mask]=tree['colourAddress'][inv];py=luminance(refs);assert all(py[tree['colourAddress'][a]]<py[tree['colourAddress'][b]]for a,b in base['orders']);rgb_delta=colours[np.array(sorted(profile))[:,0]].astype(np.int64)-colours[np.array(sorted(profile))[:,1]];pairs=np.array(sorted(profile));out_delta=refs[tree['colourAddress'][pairs[:,0]]].astype(np.int64)-refs[tree['colourAddress'][pairs[:,1]]];profile_bad=int(np.count_nonzero((rgb_delta*out_delta).sum(1)<=0));result={'CPUOnly':True,'initialMinimumScalarStrata':tree['initialStrata'],'addressesAfterObservedChromaRefinement':tree['addresses'],'old88Addresses':len(base['referenceIndices']),'allConstraintsComplete':tree['complete'],'profilePairs':len(profile),'profileAndChannelRangePairs':len(critical),'profileRGBVectorReversals':profile_bad,'unresolvedPairs':len(tree['unresolvedPairs']),'all88SourceLuminanceOrdersPreserved':True,'sourceRGBMSE':float(np.mean((mapped.astype(float)-rgb[mask])**2)),'maximumRGBChannelError':int(np.max(abs(mapped.astype(int)-rgb[mask]))),'singletonColourDomainsNotUVRegions':tree['singletonColourDomains'],'sameRGBSameAddressAcrossUVAndMaterials':True,'observedRGBReferencesOnly':True,'semanticSupportOrPixelsChanged':False,'GPUOrArtAdopted':False,'globalMinimumPaletteClaimed':False};(G/'SOURCE_VALUE92.json').write_text(json.dumps(result,indent=2));(G/'REFINEMENT92.json').write_text(json.dumps(tree['history'],indent=2));np.savez_compressed(G/'SOURCE_VALUE92.npz',labels=labels,mask=mask,colours=colours,counts=counts,colourAddress=tree['colourAddress'],referenceIndices=tree['referenceIndices'],pairs=tree['pairs'],profilePairs=np.asarray(sorted(profile),int));print(json.dumps(result),flush=True)
 board=Image.new('RGB',(1260,800),(27,29,35));draw=ImageDraw.Draw(board);scalar_refs=scalar['colours'][scalar['referenceIndices']];old=rgb.copy();old[mask]=scalar_refs[scalar['colourAddress'][inv]]
 for j,(a,title)in enumerate([(rgb,'Original source'),(old,'Rejected scalar90'),(out,'CPU92 source colour-direction refinement')]):
  draw.text((j*420+4,4),title,fill='white');board.paste(Image.fromarray(a[620:740,300:440]).resize((420,360),Image.Resampling.NEAREST),(j*420,28));board.paste(Image.fromarray(a).resize((360,360),Image.Resampling.NEAREST),(j*420+4,405))
 draw.text((4,780),'Source value only; support identity unchanged. No palette RGB8, GPU, projection or artistic success implied.',fill='white');board.save(G/'SOURCE_VALUE92.png')
if __name__=='__main__':main()
