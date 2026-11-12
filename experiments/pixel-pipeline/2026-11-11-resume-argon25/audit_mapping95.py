from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from refine_colour_mapping95 import refine
H=Path(__file__).resolve().parent;G=H/'face95/source'
def main():
 G.mkdir(parents=True,exist_ok=True);s=np.load(H/'face93/SOURCE_RANGE_CANDIDATE93.npz');old=np.load(H/'face92/SOURCE_VALUE92.npz');base=np.load(H/'face88/SOURCE_VALUE88.npz');n=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=n['rgba'][:,:,:3];mask=s['mask'];colours=s['colours'];r=refine(colours,s['colourAddress'],s['referenceIndices'],s['bounds'],old['pairs'],base['orders']);assert r['converged'];refs=colours[r['referenceIndices']];colour_index=np.searchsorted(colours@np.array([65536,256,1]),rgb[mask]@np.array([65536,256,1]));labels=np.full(mask.shape,-1,np.int32);labels[mask]=r['colourAddress'][colour_index];out=rgb.copy();out[mask]=refs[labels[mask]];before=rgb.copy();before[mask]=colours[s['referenceIndices'][s['colourAddress'][colour_index]]];d=out[mask].astype(float)-rgb[mask];prior=before[mask].astype(float)-rgb[mask]
 a=np.load(H/'face86/REGIONS86.npz')['regions'];constant=0;outside=0
 for k in np.unique(a[mask]):
  m=mask&(a==k);original=rgb[m];value=out[m];outside+=int(((value<original.min(0))|(value>original.max(0))).any(1).sum());constant+=int(np.array_equal(original.min(0),original.max(0))and not np.array_equal(value,original))
 codes=colours@np.array([65536,256,1]);probes=[]
 for value in [[254,239,226],[255,239,226],[209,195,179]]:
  i=int(np.searchsorted(codes,np.array(value)@np.array([65536,256,1])));assert np.array_equal(colours[i],value);probes.append({'nativeRGB':value,'oldSource92':colours[old['referenceIndices'][old['colourAddress'][i]]].tolist(),'sourceRange93':colours[s['referenceIndices'][s['colourAddress'][i]]].tolist(),'nearestConstrained95':refs[r['colourAddress'][i]].tolist()})
 report={'CPUOnly':True,'candidateAddresses':len(refs),'beforeAddresses':len(s['referenceIndices']),'history':r['history'],'originalSourceColourKeys':len(colours),'allMeasuredRGBContrastAndBrightnessPreserved':True,'outsideOriginalSupportRangesTexels':outside,'constantSupportComponentsChanged':constant,'sourceRGBMSEBefore93':float(np.mean(prior*prior)),'sourceRGBMSE95':float(np.mean(d*d)),'maximumChannelErrorBefore93':int(abs(prior).max()),'maximumChannelError95':int(abs(d).max()),'newColoursOrMeanRGB':False,'sourceSupportOrSemanticRegionChanged':False,'samplePhaseOrFullPixelOcclusionFixed':False,'GPUOrArtAdopted':False,'probes':probes};np.savez_compressed(G/'SOURCE_MAPPING95.npz',labels=labels,mask=mask,colours=colours,counts=s['counts'],colourAddress=r['colourAddress'],referenceIndices=r['referenceIndices'],pairs=old['pairs'],bounds=s['bounds']);(G/'MAPPING95.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));board=Image.new('RGB',(1050,380),(25,28,34));draw=ImageDraw.Draw(board)
 for j,(im,title)in enumerate([(rgb,'Original source'),(before,'CPU93 source ranges'),(out,'CPU95 same refs / constrained nearest')]):draw.text((350*j+4,5),title,fill='white');board.paste(Image.fromarray(im).resize((340,340),Image.Resampling.NEAREST),(350*j+4,27))
 board.save(G/'CPU_SOURCE_MAPPING95.png')
if __name__=='__main__':main()
