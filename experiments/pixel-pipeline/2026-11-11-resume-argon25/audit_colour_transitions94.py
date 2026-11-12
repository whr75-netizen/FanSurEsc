"""Separate source-point colour changes from Q and actual GPU RGB changes.

The510-address branch is a saved-input CPU counterfactual, never a GPU image.
Same-carrier correspondence does not imply an identical source UV footprint.
"""
from pathlib import Path
import json,hashlib,numpy as np
from frame_bytes77 import decode
from selected_light84 import geometry
from shade_history85 import prior_address
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face94/held480'
def main():
 c=G/'capture';report=json.loads((c/'COMPLETE.json').read_text());assert report['packetComplete'];native=np.load(H/'face28/SOURCE_NATIVE28.npz')['rgba'];regions=np.load(H/'face86/REGIONS86.npz')['regions'];alternative=np.load(H/'face93/SOURCE_RANGE_CANDIDATE93.npz')['labels'];pal=np.fromfile(H/'face93/range-palette/CONSTRAINED92.rgb',np.uint8).reshape(-1,3,3);info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=info['cropOffset'];tw,th=info['textureSize'];previous=None;rows=[]
 for f in report['stream77']['frames']:
  w,h=f['QROI'][2:];raw=decode((c/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,24,w,4).transpose(1,0,2,3);geo=geometry(c/f['light84']['sourceGeometryFile']);uv=a[10,:,:,:2].astype(float);x=np.floor(uv[:,:,0]*tw).astype(int)-ox;y=np.floor((1-uv[:,:,1])*th).astype(int)-oy;rgb=np.flipud(np.asarray(srgb(a[14])))[:,:,:3]
  if previous is not None:
   old,oldf,oldg,pxs,pys,oldrgb=previous
   for yy,xx in np.argwhere(a[15,:,:,3]==1):
    pos,_=prior_address(oldg,int(a[9,yy,xx,3]),a[10,yy,xx,:2],oldf['QROI'])
    if pos is None:continue
    px,py=pos
    if old[15,py,px,3]!=1 or not np.array_equal(old[9,py,px,1:],a[9,yy,xx,1:]):continue
    cy,cx=y[yy,xx],x[yy,xx];oy0,ox0=pys[py,px],pxs[py,px];k=int(round(a[13,yy,xx,0]*2));ok=int(round(old[13,py,px,0]*2));n=native[cy,cx,:3].astype(int);o=native[oy0,ox0,:3].astype(int);delta=rgb[yy,xx].astype(int)-oldrgb[py,px].astype(int);alt=pal[alternative[cy,cx],k].astype(int)-pal[alternative[oy0,ox0],ok].astype(int);rows.append({'frame':f['frame'],'currentLocalXY':[int(xx),int(yy)],'previousLocalXY':[int(px),int(py)],'primitive':int(a[9,yy,xx,3]),'sameSupport':bool(regions[cy,cx]==regions[oy0,ox0]),'sameQ':k==ok,'sameSourceAddress':bool(a[15,yy,xx,0]==old[15,py,px,0]),'currentSourceRGB':n.tolist(),'previousSourceRGB':o.tolist(),'nativeStep':(n-o).tolist(),'actualGPU226Step':delta.tolist(),'CPU510Step':alt.tolist()})
  previous=a,f,geo,x,y,rgb
 selected=[r for r in rows if r['sameSupport']and r['sameQ']];source=np.array([r['nativeStep']for r in selected]);actual=np.array([r['actualGPU226Step']for r in selected]);alt=np.array([r['CPU510Step']for r in selected]);same=(source==0).all(1);assert(actual[same]==0).all()and(alt[same]==0).all();sn=np.linalg.norm(source,axis=1);an=np.linalg.norm(actual,axis=1);bn=np.linalg.norm(alt,axis=1);ratios=np.divide(an,sn,out=np.zeros_like(an),where=sn>0);order=np.argsort(-ratios);result={'actualGPUFrames':len(report['stream77']['frames']),'observedCarrierPairs':len(rows),'sameObservedSupportAndQPairs':len(selected),'sameNativeRGBPairs':int(same.sum()),'unexpectedRGBChangesAtSameNativeRGBAndQ':0,'nativeRGBChangingPairs':int((sn>0).sum()),'actual226RGBChangingPairs':int((an>0).sum()),'CPU510CounterfactualRGBChangingPairs':int((bn>0).sum()),'actual226MaxChannelStep':int(abs(actual).max()),'CPU510MaxChannelStep':int(abs(alt).max()),'actual226MaxStepGainOverSource':float(ratios.max()),'CPU510IsGPUOrArtResult':False,'sameCarrierNotSameUVFootprint':True,'originalGradientAAPaintSemanticsNotInferred':True,'largestGainExamples':[selected[int(i)]for i in order[:5]],'rows':rows};(G/'COLOUR_TRANSITIONS94.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
