from pathlib import Path
import hashlib,json,sys,time
import numpy as np
from PIL import Image,ImageDraw
from uv_features64 import extract,RULE_VERSION
R=Path(__file__).resolve().parent;S=R.parent/'source-regions62';P=R.parent/'renderer-family59'
if not S.exists():S=R.parent/'2026-10-31-source-regions62'
if not P.exists():P=R.parent/'2026-10-31-renderer-family59'
T=Path('C:/Users/15352/Documents/Codex/2026-10-30/task/model-source')
reg=json.loads((P/'SOURCE_REGISTRY59.json').read_text());cells=json.loads((S/'CELLS62.json').read_text());output=[];bindings=[]
for b in reg['bindings']:
 if b['rendererOrdinal']!=2:continue
 mid=b['materialId'];p=R/f'NATIVE_SOURCE64-{mid}.png'
 if not p.exists():p=T/f"image-{b['imageIndex']}.png"
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==b['imageSHA256'];rgba=np.array(Image.open(p).convert('RGBA'));sourceHash=hashlib.sha256(rgba.tobytes()).hexdigest();support=np.load(S/f'source-{mid}-regions62.npz')['support']&(rgba[:,:,3]>0)
 print('extracting original source',mid,'image',b['imageIndex'],flush=True);start=time.perf_counter();e=extract(rgba[:,:,:3],support)
 assert hashlib.sha256(rgba.tobytes()).hexdigest()==sourceHash
 np.savez_compressed(R/f'SOURCE64-{mid}.npz',support=support,coarse=e['coarse'],fine=e['fine'],persistentX=e['x']['persistent'],persistentY=e['y']['persistent'],fineX=e['x']['fine'],fineY=e['y']['fine'],emergentX=e['x']['scaleEmergentUncertain'],emergentY=e['y']['scaleEmergentUncertain'],thinRidgeX=e['thinRidgeX'],thinRidgeY=e['thinRidgeY'])
 counts={axis:{'persistent':int(e[axis]['persistent'].sum()),'fineOnly':int(e[axis]['fineOnly'].sum()),'scaleEmergentUncertain':int(e[axis]['scaleEmergentUncertain'].sum()),'inconsistentScaleOrSideModel':int(e[axis]['inconsistentScales'].sum()),'scales':e[axis]['counts']}for axis in ['x','y']}
 row={'materialId':mid,'imageIndex':b['imageIndex'],'imageSHA256':b['imageSHA256'],'sourceRGBAHash':sourceHash,'cacheKey':e['cacheKey'],'ruleVersion':RULE_VERSION,'sourceShape':list(rgba.shape),'supportTexels':int(support.sum()),'coarseRegions':e['coarseRegions'],'fineRegions':e['fineRegions'],'fineToCoarse':e['parents'],'contourHierarchy':e['contourHierarchy'],'counts':counts,'thinRidgeCells':int((e['thinRidgeX']|e['thinRidgeY']).sum()),'seconds':time.perf_counter()-start,'sourceChanged':False,'meaning':'source jump/gradient evidence hierarchy, not semantic strand IDs or screen-ready correction'};output.append(row)
 debug=np.zeros_like(rgba);debug[:,:,:3]=rgba[:,:,:3]//3;debug[:,:,3]=np.where(support,255,0);debug[e['x']['scaleEmergentUncertain']|e['y']['scaleEmergentUncertain'],:3]=[70,135,230];debug[e['x']['fineOnly']|e['y']['fineOnly'],:3]=[225,165,45];debug[e['x']['persistent']|e['y']['persistent'],:3]=[45,225,155];debug[e['thinRidgeX']|e['thinRidgeY'],:3]=[225,70,195]
 (R/f'NATIVE_SOURCE64-{mid}.png').write_bytes(raw);Image.fromarray(debug).save(R/f'NATIVE_EVIDENCE64-{mid}.png')
 ids=np.zeros_like(rgba);labels=e['coarse'];ids[:,:,0]=(labels*73)%251;ids[:,:,1]=(labels*131+29)%251;ids[:,:,2]=(labels*193+41)%251;ids[:,:,3]=np.where(support,255,0)
 board=Image.new('RGB',(768,550),(24,26,31));draw=ImageDraw.Draw(board)
 for x,im,title in [(0,Image.fromarray(rgba),'Native source preview 1/2'),(256,Image.fromarray(debug),'green stable / blue coarse uncertain'),(512,Image.fromarray(ids),'coarse evidence regions / not palette')]:
  im=im.resize((256,512),Image.Resampling.NEAREST);board.paste(im,(x,32),im);draw.text((x,5),title,fill='white')
 board.save(R/f'SOURCE64-{mid}.png')
 for i,r in enumerate(cells['rows']):
  if r['materialId']!=mid:continue
  x,y=r['nativeTexel'];assert rgba[y,x,:3].tolist()==cells['sourceRGB8'][i],'source point binding mismatch';bindings.append({'x':r['x'],'y':r['y'],'materialId':mid,'sourceImageSHA256':b['imageSHA256'],'nativeTexel':[x,y],'sourceRGB8':cells['sourceRGB8'][i],'sourceCoarseRegionId':e['cacheKey']+'/'+str(int(e['coarse'][y,x])),'sourceFineRegionId':e['cacheKey']+'/'+str(int(e['fine'][y,x])),'oldRangeRegionId':r['sourceRegionId'],'QUnchanged':r['Q'],'thinRidgeCandidate':bool(e['thinRidgeX'][y,x]or e['thinRidgeY'][y,x]),'childToParentValid':e['parents'][int(e['fine'][y,x])]==int(e['coarse'][y,x]),'semanticMeaning':'unresolved; evidence is source-native, not projected footprint'})
 del e,rgba,debug,ids
 assert len(bindings)<=373
assert len(bindings)==373 and all(b['childToParentValid']for b in bindings)
(R/'SOURCE_RESULTS64.json').write_text(json.dumps({'sourceModelSHA256':reg['modelSHA256'],'scalesNativeTexels':[2,4,8],'ruleVersion':RULE_VERSION,'materials':output,'visibleCellsBound':373,'sourceMutations':0,'newUnityCalls':0,'paletteCreated':False,'renderedRGBChanged':False,'semanticOrArtisticAcceptance':False},ensure_ascii=False,indent=2),encoding='utf8')
(R/'CELL_BINDING64.json').write_text(json.dumps({'sourceId':cells['sourceId'],'cells':bindings,'projectionNotYetVerified':True},ensure_ascii=False,indent=2),encoding='utf8');print('source64 completed; source unchanged, no palette or render output',flush=True)
