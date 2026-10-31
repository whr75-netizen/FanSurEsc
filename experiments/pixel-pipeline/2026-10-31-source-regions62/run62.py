from pathlib import Path
from collections import defaultdict,Counter
import hashlib,io,json,math,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from region62 import lab,palette,texel,build_regions,structure_components,frame_metrics
R=Path(__file__).resolve().parent;W=R.parent;S60=W/'renderer-compare60';S59=W/'renderer-family59'
if not S60.exists():S60=R.parent/'2026-10-31-renderer-compare60'
if not S59.exists():S59=R.parent/'2026-10-31-renderer-family59'
T=Path('C:/Users/15352/Documents/Codex/2026-10-30/task');V4=T/'palette-v4-feature';OLD=W/'author33/feature34/region-colour40'
registry=json.loads((S59/'SOURCE_REGISTRY59.json').read_text());done=json.loads((S60/'RESULT60.json').read_text());cells=json.loads((S60/'CELL_AUDIT60.json').read_text())['cells'];certs=json.loads((V4/'FEATURE_CERTIFICATES.json').read_text());constraints=json.loads((V4/'CONSTRAINED_64.json').read_text());band=float(constraints['fixedShadowTargetGapL'])
P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game');raw=(P/registry['modelAsset']).read_bytes();assert hashlib.sha256(raw).hexdigest()==registry['modelSHA256'];n=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+n]);binary=raw[n+28:]
def acc(i):
 a=gltf['accessors'][i];v=gltf['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];item=np.dtype(dt).itemsize
 return np.ndarray((a['count'],dim),dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dim*item),item)).copy()
sources={};cacheRows=[];markerByMaterial=defaultdict(list)
# Same model, source UV certificates; never reuse old screen coordinates as new labels.
for cert in certs:
 if not cert['protect']:continue
 pair=cert['sourcePair']
 if pair[0]['materialId']==pair[1]['materialId']:
  markerByMaterial[pair[0]['materialId']].append((pair[0]['uv'],pair[1]['uv']))
 else:
  for endpoint in pair:markerByMaterial[endpoint['materialId']].append((endpoint['uv'],endpoint['uv']))
for binding in registry['bindings']:
 if binding['rendererOrdinal']!=2:continue
 mid=binding['materialId'];prim=gltf['meshes'][binding['gltfMesh']]['primitives'][binding['gltfPrimitive']];view=gltf['bufferViews'][gltf['images'][binding['imageIndex']]['bufferView']];png=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];assert hashlib.sha256(png).hexdigest()==binding['imageSHA256']
 rgba=np.array(Image.open(io.BytesIO(png)).convert('RGBA'));h,w=rgba.shape[:2];uv=np.fromfile(S59/f'source-3.uv.f32',dtype='<f4').reshape(-1,2);indices=np.fromfile(S59/f"source-3-sub-{binding['subMesh']}.indices.u32",dtype='<u4').reshape(-1,3)
 # UV support is the actual mesh's texel footprint, independent of frame/camera.
 maskIm=Image.new('L',(w,h));pen=ImageDraw.Draw(maskIm)
 for tri in uv[indices]:
  coords=np.column_stack([tri[:,0],1-tri[:,1]])
  for du in range(math.floor(coords[:,0].min()),math.ceil(coords[:,0].max())):
   for dv in range(math.floor(coords[:,1].min()),math.ceil(coords[:,1].max())):
    pen.polygon([((float(a)-du)*w,(float(b)-dv)*h)for a,b in coords],fill=255)
 # A source texel square can intersect a UV triangle even when its centre does not.
 # This one-native-texel footprint support is not a screen silhouette expansion.
 mask=np.array(maskIm.filter(ImageFilter.MaxFilter(3)))>0
 markers=[(texel(a,w,h,True),texel(b,w,h,True))for a,b in markerByMaterial[mid]]
 print('building source regions',mid,flush=True);model=build_regions(rgba,mask,band,markers)
 pos=acc(prim['attributes']['POSITION']);normal=acc(prim['attributes']['NORMAL'])if'NORMAL'in prim['attributes']else None;topo=structure_components(indices,pos,normal)
 model.update({'rgba':rgba,'binding':binding,'topology':topo,'width':w,'height':h});sources[mid]=model
 np.savez_compressed(R/f'source-{mid}-regions62.npz',labels=model['labels'],support=mask,structureByTriangle=topo,anchors=model['anchors'])
 sourceImage=Image.fromarray(rgba);sourceImage.resize((256,512),Image.Resampling.NEAREST).save(R/f'source-{mid}-native62.png')
 ids=model['labels'];debug=np.zeros_like(rgba);valid=ids>0;debug[:,:,3]=np.where(valid,255,0);debug[:,:,0]=ids*73%251;debug[:,:,1]=ids*131%251;debug[:,:,2]=ids*193%251;Image.fromarray(debug).resize((256,512),Image.Resampling.NEAREST).save(R/f'source-{mid}-regions62.png')
 cacheRows.append({'materialId':mid,'imageSHA256':binding['imageSHA256'],'cacheKey':model['key'],'sourceRegionCount':model['regionCount'],'sourceSupportTexels':int(mask.sum()),'sourceTopologyComponents':int(topo.max()+1),'cutsLab':model['cuts'],'anchorConflicts':model['conflicts'],'certificateFissions':model['certificateFissions'],'regions':model['rows']})
def resolve(mid,uv,count,q,structure=None,interval=1):
 s=sources[mid];x,y=texel(uv,s['width'],s['height'],True);region=int(s['labels'][y,x]);
 if not region:return None,{'reason':'source texel outside source-mesh UV support','nativeTexel':[x,y]}
 anchor=s['anchors'][region];table=palette(anchor,count,band,interval);key=f'material{mid}/uv-region{region}';meta={'materialId':mid,'sourceRegionId':key,'sourceRegionKey':registry['modelSHA256']+'/'+s['key']+'/'+str(region),'sourceStructureId':structure,'sourceRegionInstanceId':key+'/'+str(structure),'nativeTexel':[x,y],'anchorRGB8':anchor.tolist(),'paletteReferenceGroup':str(mid)+'/'+s['rows'][region-1]['paletteReferenceGroup'],'paletteRGB8':table.tolist(),'Q':q,'anchorConflict':any(c['region']==region for c in s['conflicts']),'unlitApproximationDeltaE':float(s['error'][y,x]),'semanticFeature':'certified source contrast region'if s['rows'][region-1]['hasCertificateSeed']else'unclassified connected colour-range region; may be a continuous texture gradient band'}
 # Native UV neighbourhood disagreement flags sampling uncertainty; no RGB inference.
 local=s['labels'][max(0,y-1):y+2,max(0,x-1):x+2];meta['nativeBoundarySample']=len(set(local.ravel())-{0})>1
 return table[q],meta
rows=[];anchors=[];output=[];unknown=[];certIds=set()
for c in cells:
 mid=c['materialId'];s=sources[mid];structure=int(s['topology'][c['triangle']]);rgb,meta=resolve(mid,c['uv'],2,c['paletteIndex'],structure)
 if rgb is None:unknown.append({'x':c['x'],'yBottom':c['yBottom'],'materialId':mid,**meta});continue
 tx,ty=meta['nativeTexel'];assert s['rgba'][ty,tx,:3].tolist()==c['sourceRGBA8'][:3],'Source point sampler mismatch'
 rows.append({'x':c['x'],'y':c['yBottom'],'occlusionOwnerBufferUnchanged':c['owner'],'depthUnchanged':c['owner'][2],'primitive':c['triangle'],'g':c['g'],**meta});anchors.append(meta['anchorRGB8']);output.append(rgb)
assert len(rows)==373 and not unknown
anchors=np.array(anchors,dtype=np.uint8);output=np.array(output,dtype=np.uint8);sourceRGB=np.array([c['sourceRGBA8'][:3]for c in cells]);old60=np.array([c['finalRGB8']for c in cells]);old60before=np.array([c['expectedRGB8']for c in cells]);lineMask=np.array([not c['familyPaletteMember']for c in cells]);assert lineMask.sum()==52
def linear(rgb):
 v=np.array(rgb,dtype=float)/255;return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
def srgb(v):return np.clip(np.floor(np.where(v<=.0031308,12.92*v,1.055*np.maximum(v,0)**(1/2.4)-.055)*255+.5),0,255).astype('uint8')
final=srgb(linear(output)*np.where(lineMask[:,None],.55,1))
stats={name:frame_metrics(rows,rgb)for name,rgb in [('source189',sourceRGB),('material60-before-line',old60before),('material60-final',old60),('region62-anchors',anchors),('region62-before-line',output),('region62-final',final)]}
for name,rgb in [('region62-anchors',anchors),('region62-before-line',output),('region62-final',final)]:
 err=np.linalg.norm(lab(rgb)-lab(sourceRGB),axis=1);stats[name].update(sourceDeltaEMedian=float(np.median(err)),sourceDeltaEP95=float(np.quantile(err,.95)),sourceSignedDeltaLMedian=float(np.median(lab(rgb)[:,0]-lab(sourceRGB)[:,0])))
# Same source, immutable material/owner/geometry/g/Q; palette interval changes RGB only.
independence=True
for i,c in enumerate(cells):
 _,m=resolve(c['materialId'],c['uv'],2,c['paletteIndex'],rows[i]['sourceStructureId'],interval=.5)
 independence &= all(m[k]==rows[i][k]for k in ['materialId','sourceRegionId','sourceRegionKey','sourceStructureId','sourceRegionInstanceId','Q'])
featureTests=[]
for cert in certs:
 ep=[]
 for end in cert['sourcePair']:
  mid=end['materialId'];uv=end['uv'];s=sources[mid];x,y=texel(uv,s['width'],s['height'],True);rgb,m=resolve(mid,uv,4,3)
  ep.append({'input':end,'nativeRGB8':s['rgba'][y,x,:3].tolist(),'binding':m,'table':None if rgb is None else m['paletteRGB8']})
 if any(e['table']is None for e in ep):featureTests.append({'id':cert['id'],'unresolved':True});continue
 sign=math.copysign(1,cert['sourcePair'][0]['RGBAlinear'][0]-cert['sourcePair'][1]['RGBAlinear'][0]);oldGap=cert['sourceGapL'];nativeGap=float(lab([ep[0]['nativeRGB8']])[0,0]-lab([ep[1]['nativeRGB8']])[0,0]);table=[]
 for q in range(4):
  a,b=lab([ep[0]['table'][q]])[0],lab([ep[1]['table'][q]])[0];gap=float(a[0]-b[0]);table.append({'Q':q,'RGB8':[ep[0]['table'][q],ep[1]['table'][q]],'signedDeltaL':gap,'sameSourceDirection':gap*nativeGap>0,'nativeContrastAbsError':abs(abs(gap)-abs(nativeGap)),'legacyStrictMinContrast':abs(gap)+1e-12>=oldGap and gap*sign>0,'notCollapsed':ep[0]['table'][q]!=ep[1]['table'][q]})
 featureTests.append({'id':cert['id'],'protect':cert['protect'],'scope':'seven source feature pairs'if cert['id']in[0,2,3,5,6,7,8]else'equal-Q cancellation case'if cert['id']==4 else'weak pair not force protected','recordedBilinearGapL':oldGap,'nativePointSignedGapL':nativeGap,'endpoints':ep,'equalQ':table})
# Preserve original context and exactly the measured line operation; no new Unity render.
native=json.loads((S60/'CELL_AUDIT60.json').read_text())['nativePixels'];full=np.fromfile(S60/'CONTROL_FULL60.float4',dtype='<f4').reshape(544,960,4).copy();original=full.copy();index={(r['x'],r['y']):i for i,r in enumerate(rows)};selected=np.zeros((544,960),bool)
for p in native:
 i=index[p['cellX'],p['cellYBottom']];full[p['nativeYBottom'],p['nativeX'],:3]=linear(final[i]);selected[p['nativeYBottom'],p['nativeX']]=True
assert np.array_equal(full[~selected],original[~selected])and np.array_equal(full[:,:,3],original[:,:,3])
rgba=np.dstack([srgb(full[:,:,:3]),np.clip(np.floor(full[:,:,3]*255+.5),0,255).astype('uint8')]);Image.fromarray(np.flipud(rgba)).save(R/'CURRENT_FULL62.png')
roi=done['hairRectBottomLeft'];x0,y0,w,h=roi
def cell_image(name,rgb):
 a=np.zeros((h,w,4),np.uint8)
 for r,c in zip(rows,rgb):a[h-1-(r['y']-y0),r['x']-x0]=[*c,255]
 im=Image.fromarray(a);im.save(R/(name+'-1x.png'));im.resize((w*8,h*8),Image.Resampling.NEAREST).save(R/(name+'-8x.png'))
for name,rgb in [('source62',sourceRGB),('material60',old60),('regions62',anchors),('preline62',output),('final62',final)]:cell_image(name,rgb)
regionIds={v:i+1 for i,v in enumerate(sorted(set(r['sourceRegionId']for r in rows)))};debug=np.array([[regionIds[r['sourceRegionId']]*73%251,regionIds[r['sourceRegionId']]*131%251,regionIds[r['sourceRegionId']]*193%251]for r in rows],dtype='uint8');cell_image('region-debug62',debug)
canvas=Image.new('RGB',(max(6*(w*8+16),1100),h*8+55),(24,26,31));pen=ImageDraw.Draw(canvas)
for j,(name,title)in enumerate([('source62','Source unlit'),('material60','Material medoid60'),('regions62','UV region anchors'),('preline62','P[region,Q]'),('final62','same line mask .55'),('region-debug62','Region IDs')]):
 im=Image.open(R/(name+'-8x.png')).convert('RGBA');canvas.paste(im,(j*(w*8+16),30),im);pen.text((j*(w*8+16),5),title,fill='white')
canvas.save(R/'COMPARE62.png')
(R/'CACHE62.json').write_text(json.dumps({'modelSHA256':registry['modelSHA256'],'regionDefinition':'material source UV-connected bounded Lab range, optional measured native contrast seeds; not semantic or occlusion identity','bandMeasuredFromOldNativePalette':band,'materials':cacheRows},indent=2),encoding='utf8')
(R/'CELLS62.json').write_text(json.dumps({'sourceId':done['sourceId'],'rows':rows,'sourceRGB8':sourceRGB.tolist(),'anchorRGB8':anchors.tolist(),'beforeLineRGB8':output.tolist(),'finalRGB8':final.tolist()},indent=2),encoding='utf8')
(R/'FEATURE_TESTS62.json').write_text(json.dumps(featureTests,indent=2),encoding='utf8')
report={'sourceId':done['sourceId'],'sourceCells':373,'sourceColours':len(set(map(tuple,sourceRGB.tolist()))),'visibleSourceRegions':len(regionIds),'visibleStructureComponents':len(set((r['materialId'],r['sourceStructureId'])for r in rows)),'visibleSourceRegionInstances':len(set(r['sourceRegionInstanceId']for r in rows)),'paletteRGB8CountVisible':len(set(tuple(c)for r in rows for c in r['paletteRGB8'])),'unresolvedCells':unknown,'samplingBoundaryCells':sum(r['nativeBoundarySample']for r in rows),'certifiedRegionCells':sum(r['semanticFeature'].startswith('certified')for r in rows),'uncertainty':'All unclassified range regions may be continuous gradient bands; no authored semantic IDs or baked-gradient removal inferred. Exact same source point sample, not bilinear footprint reconstruction.','statistics':stats,'paletteIntervalLeavesRegionAndQExact':bool(independence),'outsideHairOrAlphaChanges':0,'lineMaskCellsUnchanged':52,'productOrUnityChanges':0,'temporalValidated':False,'artisticAcceptance':False,'legacyFeatureTestsFile':'FEATURE_TESTS62.json','shadeSpecification':{'QCount':2,'referenceTopNativeTexel':True,'constantOKLabLShadowSpan':band,'preserveHueUnlessGamutReduction':True,'note':'shared measured native-L span, not RGB*g or a whole-image median adjustment'}}
(R/'RESULT62.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2),flush=True)
