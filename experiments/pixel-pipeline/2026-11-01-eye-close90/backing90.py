from pathlib import Path
import json,sys,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'native-feature89'))
from analyse89 import packet,rgb8
from metadata90 import decode_independent_meta,clean_skin_underlay
def positions(d,mask):
 m=d['m'];yy,xx=np.where(mask);r=m['nativeFinalReference89'];origin=np.asarray(r['origin']);offset=np.asarray(m['trace86']['headJoinOffset']);delta=np.asarray(m['camera86']['deliveredDelta'][:2]);xy=(np.c_[xx+r['nativeROI'][0]+.5,yy+r['nativeROI'][1]+.5]-origin)/r['scale']-offset-delta;return np.floor(xy).astype(int)

def inspect_cell(d,cx,cy):
 a=d['a'];x,y,w,h=d['roi'];i,j=cy-y,cx-x;rx,ry,rw,rh=d['eyeROI'];sample={};candidates=[]
 for prefix in ['base','backing']:
  c=clean_skin_underlay(a[prefix+'-rgba'][i,j],a[prefix+'-meta'][i,j]);sample[prefix]={'meta':a[prefix+'-meta'][i,j].tolist(),'decoded':decode_independent_meta(a[prefix+'-meta'][i,j]),'rgba':a[prefix+'-rgba'][i,j].tolist()}
  if c:candidates.append({'layer':prefix,'RGB8':rgb8(np.asarray(c['rgba'][:3])).tolist(),'source':c})
 sources={};ii,jj=cy-ry,cx-rx
 if 0<=ii<rh and 0<=jj<rw:
  for part in [0,3]:
   meta=a[f'S{part}-meta'][ii*4:ii*4+4,jj*4:jj*4+4];rgba=a[f'S{part}-rgba'][ii*4:ii*4+4,jj*4:jj*4+4];col=rgb8(rgba[...,:3]);sources[str(part)]={'sourceRole':3 if part==0 else 6,'presentSamples':int((meta[...,0]>0).sum()),'opaqueSamples':int(((meta[...,0]>0)&(rgba[...,3]==1)).sum()),'uniqueRGB8':np.unique(col.reshape(-1,3),axis=0).tolist(),'minAlpha':float(rgba[...,3].min()),'maxAlpha':float(rgba[...,3].max()),'meaning':'current native skin is not automatically native eyeline'if part==0 else'actual native eyeline has its own role6/alpha/depth'}
 return {'headCellTopLeft':[int(cx),int(271-cy)],'baseline348Before':{'rgba':d['baseline'][i,j,0].tolist(),'ownerTags':d['baseline'][i,j,1].tolist(),'rawPreparedMeta':d['baseline'][i,j,2].tolist(),'meaning':'already after333 eye composition; cannot treat as clean backing'},'layers':sample,'cleanSkinCandidates':candidates,'currentNativeSources4x':sources,'originalFullMeta':a['original-full-meta'][i,j].tolist(),'originalFullDecoded':decode_independent_meta(a['original-full-meta'][i,j]),'originalFullColourCaptured':False,'backgroundOwnerSelectionComplete':False}

def main():
 old=ROOT/'native-feature89';s=json.loads(sorted((old/'capture89f').glob('STATE89*.json'))[-1].read_text());index=json.loads((old/'final-input89/INPUT_INDEX89.json').read_text());cache={};rows=[];focus=[]
 for entry in index:
  if not entry['missingBackingNativePixels']:continue
  frame=entry['frame']
  if frame not in cache:cache[frame]=packet(Path(next(e['output']for e in s['sequencePackets']if e['frame']==frame)))
  d=cache[frame];data=np.load(old/'final-input89'/(Path(entry['file']).stem+'-expected.npz'));mask=data['scope']&(data['colour'][...,3]==0);cells=positions(d,mask);byCell={tuple(k):inspect_cell(d,*k)for k in np.unique(cells,axis=0)};wrong=sum(bool(byCell[tuple(k)]['cleanSkinCandidates'])for k in cells);rows.append({'frame':frame,'variant':entry['variant'],'oldMissingNativePixels':len(cells),'schemaFalseMissingNativePixels':wrong,'remainingBaseBackingMissingNativePixels':len(cells)-wrong,'eligibilityOnlyNotFinalComposite':True})
  if frame==140 and entry['variant']=='ray-visible':focus=list(byCell.values())
 assert len(focus)==9;assert sum(bool(x['cleanSkinCandidates'])for x in focus)==5
 report={'status':'INDEPENDENT333_ROLE_PLUS_ONE_DECODE_CORRECTED_OFFLINE','oldMissingNativePixels':sum(x['oldMissingNativePixels']for x in rows),'schemaFalseMissingNativePixels':sum(x['schemaFalseMissingNativePixels']for x in rows),'remainingBaseBackingMissingNativePixels':sum(x['remainingBaseBackingMissingNativePixels']for x in rows),'countUnit':'over32 actual frames and2 variants, not unique screen coordinates','focus140':{'cells':9,'cleanSkinAlreadyRenderedCells':5,'genuinelyAbsentBaseBackingCells':4,'baselineClean':False,'cellsDetails':focus},'rows':rows,'cause':'89 build_final89 compared Independent333.meta.y against literal roleIDs; producer writes role+1. Encoded4 is skin3, not sclera4.','sourceProducer':'FullFeature367.Eyes uses ph.face for8 and ph.backing for8/10; Independent333 writes(depth,role+1,owner,alpha).','stateMismatch':'Full319View335.PrepareCurrent chooses phases by evaluatedFrame/2.5 and head matrix, updates body/hair, but not cached ph.face/nativeFace/backing from current Close deformation. For the4 absent cells, original-full meta remains iris1 or translucent eye role2 while current S0 has16 opaque skin samples.','dataPresentButNotEquivalent':'S0 actual current skin4x RGBA exists for these cells, but it is not a captured1x/2x final backing P with owner. S3 native eyeline is separate. No averaging or inferred skin colour is used.','nextConnection':'Reuse or render actual current-deformed skin source as a typed backing producer at the target raster; preserve source role/owner/depth/UV and resolve native line separately. Do not reuse the333-contaminated pre348 colour or stale open-face cache as hidden skin.','newCaptureRequiredForThisAudit':False,'productChanged':False};(HERE/'BACKING_RESULT90.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['focus140','rows']},indent=2))
if __name__=='__main__':main()
