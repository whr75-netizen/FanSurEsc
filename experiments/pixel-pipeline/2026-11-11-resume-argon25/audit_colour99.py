"""Actual GPU RGB versus the unchanged original material/UV point texel.
CPU source reconstruction is checked against uploaded GPU family addresses.
Adjacent same-primitive cells are not claimed to have identical UV footprints.
"""
from pathlib import Path
import json,hashlib,sys,numpy as np
from actor_visibility96 import packet
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def main():
 root=H/'face99'/sys.argv[1];r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['packetComplete'];source=H/'face99/original99/details';info=json.loads((source/'COMPLETE.json').read_text());raw=(source/'ORIGINAL99.rgba').read_bytes();assert hashlib.sha256(raw).hexdigest()==info['rgbaSHA256'];assert info['currentImageHash']==r['sourcePalette67']['sourceValue89']['liveOriginalImageHash'];texture=np.frombuffer(raw,np.uint8).reshape(info['height'],info['width'],4);address=np.fromfile(H/'face92/ADDRESS92.r32','<f4').reshape(info['height'],info['width']);assert hashlib.sha256((H/'face92/ADDRESS92.r32').read_bytes()).hexdigest()==r['sourcePalette67']['sourceValue89']['sourceContract']['addressSHA'];part=np.load(H/'face86/REGIONS86.npz')['regions'];crop=np.load(H/'face28/SOURCE_NATIVE28.npz')['rgba'];meta=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=meta['cropOffset'];assert np.array_equal(np.flipud(texture)[oy:oy+crop.shape[0],ox:ox+crop.shape[1]],crop)
 previous=None;allPairs=0;stableRGB=0;unexpected=[];changes=[];lookup=0;unknownCrop=0;faceFrames=0;faceCells=0
 for f in r['stream77']['frames']:
  a,_,_=packet(root,f);uv=a[1,:,:,:2];sx=np.floor(uv[:,:,0]*np.float32(info['width'])).astype(int)%info['width'];sy=np.floor(uv[:,:,1]*np.float32(info['height'])).astype(int)%info['height'];valid=(a[4,:,:,3]==1)&(a[4,:,:,0]>0);lookup+=int(valid.sum());assert np.array_equal(a[4,:,:,0][valid],address[sy,sx][valid]);original=texture[sy,sx,:3].astype(int);output=np.flipud(np.asarray(srgb(a[5])))[:,:,:3].astype(int);tx=sx-ox;ty=info['height']-1-sy-oy;inside=(tx>=0)&(ty>=0)&(tx<part.shape[1])&(ty<part.shape[0]);regions=np.zeros(valid.shape,int);regions[inside]=part[ty[inside],tx[inside]];faceCells+=int(valid.sum());faceFrames+=int(valid.any());unknownCrop+=int((valid&~inside).sum())
  if previous is not None:
   before,oldOriginal,oldOutput,oldValid,oldRegions=previous;mask=valid&oldValid&inside&(regions==oldRegions)&(regions>0)&(a[0,:,:,1]==before[0,:,:,1])&(a[0,:,:,3]==before[0,:,:,3])&(a[4,:,:,2]==before[4,:,:,2]);allPairs+=int(mask.sum())
   for y,x in np.argwhere(mask):
    sourceStep=original[y,x]-oldOriginal[y,x];rgbStep=output[y,x]-oldOutput[y,x]
    if not sourceStep.any():
     stableRGB+=1
     if rgbStep.any():unexpected.append({'frame':f['frame'],'xy':[int(x),int(y)],'RGBStep':rgbStep.tolist(),'sourceRGB':original[y,x].tolist(),'oldUV':before[1,y,x,:2].tolist(),'newUV':a[1,y,x,:2].tolist()})
    elif rgbStep.any():changes.append({'frame':f['frame'],'xy':[int(x),int(y)],'sourceStep':sourceStep.tolist(),'actualGPUColourStep':rgbStep.tolist(),'gain':float(np.linalg.norm(rgbStep)/np.linalg.norm(sourceStep)),'sourceRegion':int(regions[y,x]),'familyBefore':int(before[4,y,x,0]),'familyAfter':int(a[4,y,x,0]),'selectedShade':int(a[4,y,x,2])})
  previous=a,original,output,valid,regions
 changes.sort(key=lambda x:-x['gain']);out={'actualGPUFrames':len(r['stream77']['frames']),'sourceTexelMethod':'CPU floor(float32(UV)*size), same verified original material image, no guessed/screenshot/mean colour','sourceCropRGBAExact':True,'actualGPUFamilyLookupsMatched':lookup,'framesWithKnownFaceColour':faceFrames,'knownFaceCells':faceCells,'unavailableSourceCropCells':unknownCrop,'adjacentSameCellPrimitiveSupportSelectedQPairs':allPairs,'sameSourceRGBPairs':stableRGB,'sameSourceRGBButColourChanged':len(unexpected),'unexpected':unexpected[:20],'changingSourceAndGPUColourPairs':len(changes),'maximumPointSourceStepGain':max((v['gain']for v in changes),default=0),'largestStepExamples':changes[:10],'adjacentCellPairIsNotIdenticalSurfaceFootprintProof':True,'sourceGradientAAPigmentSemanticsInferred':False,'paletteOrArtCandidateAdopted':False};(root/'COLOUR_CAUSALITY99.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
