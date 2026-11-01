"""Same-frame source controls and current-vs-cached typed backing evidence."""
from pathlib import Path
import json,sys,hashlib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));sys.path.insert(0,str(ROOT/'eye-close90'))
from analyse89 import packet,rgb8
from metadata90 import decode_independent_meta

def error(a,b):
 diff=np.abs(a.astype(float)-b.astype(float));at=np.unravel_index(np.argmax(diff),diff.shape)
 return {'max':float(diff.max(initial=0)),'changed1e5':int((diff.max(-1)>1e-5).sum()),'sampleYXchannel':list(map(int,at)),'a':a[at[:2]].tolist(),'b':b[at[:2]].tolist()}
def main(run='capture91'):
 root=HERE/run;state=json.loads(sorted(root.glob('STATE91*.json'))[-1].read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError')and state['current91Disposed'];assert len(state['sequencePackets'])==8;rows=[];pairs=[];backings=[]
 for entry in state['sequencePackets']:
  d=packet(Path(entry['output']));a=d['a'];m=d['m'];frame=entry['frame'];valid=a['S3-meta'][...,0]>0
  assert all(d['heads'][f'current91-g{g}-{ch}']['frameIndex']==frame for g in range(4)for ch in range(8 if g<2 else 4))
  controls={name:error(a[f'current91-g{group}-{channel}'],a[f'S{source}-{suffix}'])for name,group,channel,source,suffix in [('backingRGBA',3,0,0,'rgba'),('backingMeta',3,1,0,'meta'),('backingPoint',3,2,0,'point'),('backingUV',3,3,0,'uv'),('originalProbeRGBA',0,0,3,'rgba'),('originalProbeMeta',0,1,3,'meta'),('originalProbePoint',0,2,3,'point'),('originalProbeUV',0,3,3,'uv'),('originalProbeShade',0,4,3,'shade'),('retargetProbeShade',1,4,3,'shade')]}
  if valid.any():
   diff=np.abs(a['current91-g1-4'][...,0]-a['S3-shade'][...,0]);y,x=np.unravel_index(np.argmax(diff),diff.shape);world={'sourceId':m['sourceId'],'frame':frame,'serial':m['mainSerial'],'sampleMemoryXY':[int(x),int(y)],'primitiveUV':a['S3-uv'][y,x].tolist(),'originalProductShade':a['S3-shade'][y,x].tolist(),'originalProbeShade':a['current91-g0-4'][y,x].tolist(),'retargetProbeShade':a['current91-g1-4'][y,x].tolist(),'originalNormal':a['current91-g0-5'][y,x].tolist(),'retargetNormal':a['current91-g1-5'][y,x].tolist(),'originalSH':a['current91-g0-6'][y,x].tolist(),'retargetSH':a['current91-g1-6'][y,x].tolist(),'originalTotals':a['current91-g0-7'][y,x].tolist(),'retargetTotals':a['current91-g1-7'][y,x].tolist()};pairs.append(world)
  # Same sample barycentric/source coordinates, not the old frame140 sample.
  sameProbe={name:error(a[f'current91-g0-{field}'],a[f'current91-g1-{field}'])for name,field in [('normal',5),('SH',6),('lightTotals',7),('shade',4)]}
  sourceMeta=a['current91-g2-1'];sourceColour=a['current91-g2-0'];sourceValid=(sourceMeta[...,0]>0)&(sourceMeta[...,1]==4)&(sourceMeta[...,3]>=.999);assert sourceMeta.shape[0]==d['m']['eyeFeature']['roiTopLeft'][3]*2
  vertices=(d['path']/'eye-evaluated.mesh').read_bytes();rx,ry,rw,rh=d['roi'];sx,top,sw,sh=m['eyeFeature']['roiTopLeft'];cachedMissing=[]
  for yy in range(sh):
   for xx in range(sw):
    hx,hy=sx+xx,271-(top+yy);i,j=hy-ry,hx-rx
    if not(0<=i<rh and 0<=j<rw):continue
    base=decode_independent_meta(a['base-meta'][i,j]);backing=decode_independent_meta(a['backing-meta'][i,j]);oldMissing=not any(q and q['role']==3 and q['alpha']>=.999 for q in [base,backing]);patch=sourceValid[(sh-1-yy)*2:(sh-yy)*2,xx*2:xx*2+2]
    oldOwner=a['old-eye-owner'][i,j];intrinsic=a['old-intrinsic'][i,j];oldFeature=(round(float(oldOwner[0]))==2 and intrinsic[0]>0)or round(float(oldOwner[0]))==7
    if oldMissing and oldFeature and patch.all():cachedMissing.append({'headCellTopLeft':[hx,top+yy],'typedCurrentSkinPixels':4,'oldFeatureOwner':oldOwner.tolist(),'RGB8':rgb8(sourceColour[(sh-1-yy)*2:(sh-yy)*2,xx*2:xx*2+2,:3]).tolist(),'sourceMeta':sourceMeta[(sh-1-yy)*2:(sh-yy)*2,xx*2:xx*2+2].tolist(),'oldOriginalFullMeta':a['original-full-meta'][i,j].tolist()})
  row={'sourceId':m['sourceId'],'frame':frame,'serial':m['mainSerial'],'stageIndex':entry['stageIndex82'],'getterClose':m['eyeFeature']['closeMorphs']['Fcl_EYE_Close'],'meshSHA256':hashlib.sha256(vertices).hexdigest(),'controls':controls,'sameProbe':sameProbe,'current2xSkinPixels':int(sourceValid.sum()),'oldMissingButCurrentOpaqueSkinCells':len(cachedMissing),'cachedMissingCurrentSkin':cachedMissing,'newProbeProductActivation':False};rows.append(row);backings.append({'sourceId':m['sourceId'],'frame':frame,'index':entry['stageIndex82'],'nativeCurrent2xSkin':int(sourceValid.sum()),'cachedMissingCurrentSkinCells':len(cachedMissing)})
 report={'status':'NEW_SOURCE91_CAPTURE_ANALYSED_CONTROLS_PENDING_REVIEW','newSourceSequence':state['sequencePackets'][0]['sourceId'].rsplit('-frame',1)[0],'frames':rows,'maxSameFramePairs':pairs,'backingSummary':backings,'sameFrameContract':True,'old140SamplesNotMixed':True,'productIntegration':False};(HERE/('CAPTURE_ANALYSIS'+run.removeprefix('capture').upper()+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'frames':len(rows),'controls':[{k:v['max']for k,v in r['controls'].items()}for r in rows],'sameProbe':[ {k:v['max']for k,v in r['sameProbe'].items()}for r in rows],'pairs':pairs[:1],'backing':backings},indent=2))
if __name__=='__main__':main(sys.argv[1]if len(sys.argv)>1 else'capture91')
