"""Actual paired renders; exact LUT proof is separate from artistic judgment."""
from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw
from review_footprint95 import frame
from selected_light84 import geometry
from review_colour89 import linear
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face95/colour64';B=H/'face95/motion64'
def main():
 r=json.loads((G/'capture/COMPLETE.json').read_text());b=json.loads((B/'capture/COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];assert len(r['stream77']['frames'])==len(b['stream77']['frames'])==64;lutbytes=(G/'capture/RUNTIME_PALETTE89.rgb').read_bytes();assert lutbytes==(H/'face95/source/CONSTRAINED92.rgb').read_bytes();palette=linear(np.frombuffer(lutbytes,np.uint8).reshape(-1,3,3));rows=[];images=[];previous=None;examples=[];sample_count=0;exact_geometry=0;exact_raw=0;rgb_gain=[]
 for f,old in zip(r['stream77']['frames'],b['stream77']['frames']):
  a,_=frame(G,f);o,_=frame(B,old);g=geometry(G/'capture'/f['light84']['sourceGeometryFile']);og=geometry(B/'capture'/old['light84']['sourceGeometryFile']);geo_equal=np.array_equal(g['v'],og['v'])and np.array_equal(g['tri'],og['tri'])and np.array_equal(g['view'],og['view']);raw_equal=np.array_equal(a[8:16],o[8:16]);exact_geometry+=geo_equal;exact_raw+=raw_equal;known=a[17,:,:,3]==1;ids=a[17,:,:,0].astype(int)-1;k=a[17,:,:,2].astype(int);assert np.array_equal(a[18][known,:3],palette[ids[known],k[known]]);sample_count+=int(known.sum());sameQ=np.array_equal(a[17,:,:,1:3],o[17,:,:,1:3]);assert np.array_equal(known,o[17,:,:,3]==1);oldRGB=np.flipud(np.asarray(srgb(o[18,:,:,:3])));newRGB=np.flipud(np.asarray(srgb(a[18,:,:,:3])));changed=known&(oldRGB!=newRGB).any(2);rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'baselineSourceId':old['sourceId'],'evaluatedFaceGeometryBitExact':geo_equal,'rawHeadMetaUVBitExact':raw_equal,'QAndHistoryQBitExact':sameQ,'visibleColourSamples':int(known.sum()),'changedCandidateRGBCells':int(changed.sum())})
  if previous is not None:
   prev,oldprev,pf,oldf=previous
   for xy in [(6,7)]:
    x,y=xy
    if known[y,x]and pf[17,y,x,3]==1 and f['frame']in[149,196]:examples.append({'framePair':[f['frame']-1,f['frame']],'localXY':[x,y],'baselineGPU226Delta':(oldRGB[y,x].astype(int)-oldprev[y,x].astype(int)).tolist(),'candidateGPU510Delta':(newRGB[y,x].astype(int)-prev[y,x].astype(int)).tolist(),'candidateAddresses':[int(pf[17,y,x,0]),int(a[17,y,x,0])],'baselineQBeforeAfter':[oldf[17,y,x,1:3].tolist(),o[17,y,x,1:3].tolist()],'candidateQBeforeAfter':[pf[17,y,x,1:3].tolist(),a[17,y,x,1:3].tolist()],'sameQ':bool(a[17,y,x,2]==pf[17,y,x,2]),'sameSourceColourNotAssumed':True})
  previous=newRGB,oldRGB,a,o
  im=Image.new('RGB',(26*4+8,26*2+23),'#22262b');d=ImageDraw.Draw(im);d.text((2,3),'92 / 95 actual ROI',fill='white');im.paste(srgb(o[18,:,:,:3]).resize((52,52),Image.Resampling.NEAREST),(0,22));im.paste(srgb(a[18,:,:,:3]).resize((52,52),Image.Resampling.NEAREST),(60,22));images.append(im)
 result={'actualGPUFrames':64,'simulationSeconds':sum(f['deltaTime']for f in r['stream77']['frames']),'candidateSourceAddresses':len(palette),'actualRuntimeCSharpLUTMatchesCPUBytes':True,'actualFinalLUTSamplesExact':sample_count,'sameEvaluatedFaceGeometryFrames':exact_geometry,'sameRawHeadMetaUVFrames':exact_raw,'sameQAndHistoryQFrames':sum(x['QAndHistoryQBitExact']for x in rows),'sameSourcePointUVRecorded':False,'sourceRGBMSEImprovedIsCPUTextureMetric':True,'completePixelVisibilityOrArtAdopted':False,'examples':examples,'rows':rows};(G/'ACTUAL_COLOUR_COMPARISON95.json').write_text(json.dumps(result,indent=2));images[0].save(G/'ACTUAL_COLOUR_COMPARISON95.webp',save_all=True,append_images=images[1:],duration=[17 if i%3==0 else 16 for i in range(len(images))],loop=0,lossless=True,method=6);indices=[0,3,7,15,23,31,47,63];sheet=Image.new('RGB',(images[0].width*4,images[0].height*2),'white')
 for n,i in enumerate(indices):sheet.paste(images[i],((n%4)*images[0].width,(n//4)*images[0].height))
 sheet.save(G/'ACTUAL_COLOUR_COMPARISON95.png');print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
