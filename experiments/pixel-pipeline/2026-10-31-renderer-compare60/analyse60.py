"""No Unity execution. Inspect the actual frozen-frame buffers, not a packet replay."""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent
S59=R.parent/'renderer-family59'
if not S59.exists():S59=R.parent/'2026-10-31-renderer-family59'
d=json.loads((R/'RESULT60.json').read_text(encoding='utf8'))
assert d['stage']=='finished',d['stage']
assert (R/'CANDIDATE_FULL60.float4').exists(),d.get('error')
def read(n,w=480,h=272):return np.fromfile(R/n,dtype='<f4').reshape(h,w,4)
def encode(a):
 a=np.maximum(a,0).astype(np.float64)
 return np.clip(np.floor(np.where(a<=.0031308,12.92*a,1.055*np.power(a,1/2.4)-.055)*255+.5),0,255).astype(np.uint8)
a=read('CONTROL_FULL60.float4',960,544);b=read('CANDIDATE_FULL60.float4',960,544)
am=read('CONTROL_META60.float4');bm=read('CANDIDATE_META60.float4');au=read('CONTROL_UV60.float4');bu=read('CANDIDATE_UV60.float4')
ao=read('CONTROL_OWNER60.float4');bo=read('CANDIDATE_OWNER60.float4');al=read('CONTROL_LOCAL60.float4');bl=read('CANDIDATE_LOCAL60.float4')
an=read('CONTROL_NATIVE_OWNER60.float4',960,544);bn=read('CANDIDATE_NATIVE_OWNER60.float4',960,544)
role=np.floor(bm[:,:,1]+.5).astype(int)-1
hair=(bm[:,:,0]>0)&(role>=11)&(role<=14)
nativeRole=np.floor(bn[:,:,0]+.5).astype(int)-1
nativeHair=(bn[:,:,2]>0)&(nativeRole>=11)&(nativeRole<=14)
nativeOldRole=np.floor(an[:,:,0]+.5).astype(int)-1
nativeOldHair=(an[:,:,2]>0)&(nativeOldRole>=11)&(nativeOldRole<=14)
inside=hair.copy()
for dy in [-1,0,1]:
 for dx in [-1,0,1]:
  neighbour=np.roll(hair,(dy,dx),(0,1));
  if dy<0:neighbour[dy:]=False
  if dy>0:neighbour[:dy]=False
  if dx<0:neighbour[:,dx:]=False
  if dx>0:neighbour[:,:dx]=False
  inside &= neighbour
boundary=hair&~inside
palettes={p['draw']:np.array(p['palette']['rgb8'],dtype=np.uint8)for p in d['palettes']}
localRGB=encode(bl[:,:,:3]);baseRGB=encode(al[:,:,:3]);fullRGB=encode(b[:,:,:3]);oldFullRGB=encode(a[:,:,:3])
cells={}; rows=[];qErrors=0;sourceUVStats={'insideTriangle':0,'outsideTriangle':0,'degenerateUV':0}
registry=json.loads((S59/'SOURCE_REGISTRY59.json').read_text())
uvs={};indices={}
for c in d.get('cells',[]):
 x,y=c['x'],c['yBottom'];draw=c['draw'];p=palettes[draw]
 # PreparedUV.z is reused by eye/layer composition. It is not an invariant Q
 # channel (nine recorded cells contain integer provenance tags here).
 c['rawPreparedUVZ']=c['q'];assert c['centreSourceExact'],'No exact selected source class; do not invent Q'
 c['q']=c['centreClass'][0];assert 0<=c['q']<=1 and c['q']==c['centreMask'][0]
 k=int(math.floor(c['q']*(len(p)-1)+.5));rgb=localRGB[y,x];expected=p[k]
 c['finalRGB8']=rgb.tolist();c['expectedRGB8']=expected.tolist();c['paletteIndex']=k;c['familyPaletteMember']=bool(np.any(np.all(p==rgb,axis=1)));c['expectedIndexExact']=bool(np.array_equal(rgb,expected));c['geometryBoundary']=bool(boundary[y,x]);cells[x,y]=c
 c['initialRGB8']=encode(np.array(c['centreInitial'][:3])).tolist();c['initialIndexExact']=c['initialRGB8']==expected.tolist()
 binding=registry['bindings'][draw];renderer=binding['rendererOrdinal']+1;sub=binding['subMesh'];
 if renderer not in uvs:uvs[renderer]=np.fromfile(S59/f'source-{renderer}.uv.f32',dtype='<f4').reshape(-1,2)
 if (renderer,sub)not in indices:indices[renderer,sub]=np.fromfile(S59/f'source-{renderer}-sub-{sub}.indices.u32',dtype='<u4').reshape(-1,3)
 t=c['triangle'];ix=indices[renderer,sub]
 if 0<=t<len(ix):
  tri=uvs[renderer][ix[t]].astype(float);q=np.array(c['uv']);m=np.column_stack([tri[1]-tri[0],tri[2]-tri[0]])
  if abs(np.linalg.det(m))<1e-10:sourceUVStats['degenerateUV']+=1;c['uvTriangleTest']='degenerate-UV'
  else:
   v=np.linalg.solve(m,q-tri[0]);bary=[1-v.sum(),*v];ok=min(bary)>=-1e-3 and max(bary)<=1+1e-3
   sourceUVStats['insideTriangle'if ok else'outsideTriangle']+=1;c['uvBarycentric']=bary;c['uvTriangleTest']='inside'if ok else'outside'
 if c['centreSourceExact']:
  g=c['g'];expectedK=sum(g>=(i+.5)/(len(p)-1)for i in range(len(p)-1));c['unmodifiedQfromG']=expectedK;c['boundaryChangedQ']=expectedK!=k
 rows.append(c)
nativeTests=[];origin=d['candidatePose']['origin'];delta=d['candidatePose']['delta'];scale=d['candidatePose']['cellScale']
for y,x in np.argwhere(nativeHair):
 qx=math.floor((x+.5-origin[0])/scale-delta[0]);qy=math.floor((y+.5-origin[1])/scale-delta[1]);cell=cells.get((qx,qy));entry={'nativeX':int(x),'nativeYBottom':int(y),'cellX':qx,'cellYBottom':qy}
 if cell:
  p=palettes[cell['draw']];rgb=fullRGB[y,x];entry.update({'draw':cell['draw'],'RGB8':rgb.tolist(),'paletteMember':bool(np.any(np.all(p==rgb,axis=1))),'indexExact':rgb.tolist()==cell['expectedRGB8'],'boundary':cell['geometryBoundary']})
 else:entry['unresolvedSelectedCell']=True
 nativeTests.append(entry)
changed=np.any(a!=b,axis=2);changedRGB=np.any(oldFullRGB!=fullRGB,axis=2);outside=changed&~(nativeHair|nativeOldHair)
def summarize_native(bound):
 s=[v for v in nativeTests if v.get('boundary')==bound and'paletteMember'in v]
 return {'samples':len(s),'outsideFamilyPalette':sum(not v['paletteMember']for v in s),'differentSelectedIndex':sum(not v['indexExact']for v in s)}
summary={'sourceId':d['sourceId'],'frameIndex':d['frameIndex'],'poseAndGeometryExact':d.get('poseAndGeometryExact'),
 'fullFinalChangedFloatPixels':int(changed.sum()),'fullFinalChangedRGB8Pixels':int(changedRGB.sum()),'nonHairChangedFloatPixels':int(outside.sum()),
 'fullAlphaChangedPixels':int(np.count_nonzero(a[:,:,3]!=b[:,:,3])),
 'preparedMetaChangedCells':int(np.count_nonzero(np.any(am!=bm,axis=2))),'selectedUVQChangedCells':int(np.count_nonzero(np.any(au!=bu,axis=2))),
 'ownerChangedCells':int(np.count_nonzero(np.any(ao!=bo,axis=2))),'nativeOwnerDepthVisibilityChangedPixels':int(np.count_nonzero(np.any(an!=bn,axis=2))),
 'hairCells':int(hair.sum()),'hairInteriorCells':int(inside.sum()),'hairGeometryBoundaryCells':int(boundary.sum()),'visibleNativeHairPixels':int(nativeHair.sum()),
 'knownVisibleHairSourceCells':d.get('knownVisibleHairSourceCells'),'unknownVisibleHairSourceCells':d.get('unknownVisibleHairSourceCells'),'uvProvenance':sourceUVStats,
 'localInteriorOutsideFamilyPalette':sum(not c['familyPaletteMember']for c in rows if not c['geometryBoundary']),
 'localGeometryBoundaryOutsideFamilyPalette':sum(not c['familyPaletteMember']for c in rows if c['geometryBoundary']),
 'initialSelectedSourcePaletteMismatches':sum(not c['initialIndexExact']for c in rows),'spatialQCorrectionsInThisFrame':sum(c.get('boundaryChangedQ',False)for c in rows),
 'nativeInterior':summarize_native(False),'nativeGeometryBoundary':summarize_native(True),'nativeUnresolvedSelectedCells':sum(v.get('unresolvedSelectedCell',False)for v in nativeTests),
 'selectedGExactCells':sum(c['centreSourceExact']for c in rows),'noMeasuredGCells':sum(not c['centreSourceExact']for c in rows),
 'preparedUVZNotQCells':sum(c['rawPreparedUVZ']<0 or c['rawPreparedUVZ']>1 for c in rows),'Qsource':'Same-frame source class.x == shadeMask.x; exact selected role/primitive/UV match. PreparedUV.z not used as Q.',
 'ownedClonesReleased':d.get('allOwnedClonesReleased'),'optionsRestored':d.get('optionsRestored'),'pipelineRestored':d.get('pipelineRestored'),'timeRestored':d.get('timeRestored'),
 'dirtyListEqualityAgainstLatest25':d.get('originalDirtyExact'),'fileListEquality':d.get('diskFilesExact'),
 'latest25OriginalDirtySubsetExact':all(v in d['after']['dirty']for v in d['before']['dirty']),
 'originalFilesContentUnchanged':all(v in d['after']['files']for v in d['before']['files']),
 'listEqualityLimit':'False list equality includes newly dirty assets/newly included unchanged disk paths; use subset/hash checks to distinguish content damage.',
 'error':d.get('error'),'restorationError':d.get('restorationError'),
 'limits':['Existing role scope retained; source-bound palettes are per material, not automatic painted-feature segmentation','Palette endpoint ratios .55/.6 are inherited diagnostic parameters, not aesthetic optima','Geometry boundary means an 8-neighbour hair silhouette boundary; not inferred semantic curves','Single static frame, current-frame capture policy; not temporal, blink, rotation or eye-backing validation','No screen/UI screenshot; PNG encodes actual linear native output once as sRGB8']}
(R/'ANALYSIS60.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8');(R/'CELL_AUDIT60.json').write_text(json.dumps({'cells':rows,'nativePixels':nativeTests},ensure_ascii=False,indent=2),encoding='utf8')
# Actual full and logical crops. PNG rows are top-left; raw GPU arrays are bottom-left.
x0,y0,w,h=d['hairRectBottomLeft'];crop=(x0*2,544-(y0+h)*2,(x0+w)*2,544-y0*2)
for tag,arr in [('CONTROL',al),('CANDIDATE',bl)]:
 rgb=encode(arr[:,:,:3]);alpha=np.clip(np.floor(arr[:,:,3]*255+.5),0,255).astype('uint8');im=Image.fromarray(np.flipud(np.dstack([rgb,alpha])),mode='RGBA');im.crop((x0,272-y0-h,x0+w,272-y0)).save(R/(tag+'_HAIR_LOGICAL60.png'))
 Image.open(R/(tag+'_FULL60.png')).crop(crop).resize((w*8,h*8),Image.Resampling.NEAREST).save(R/(tag+'_HAIR_NEAREST60.png'))
debug=np.zeros((272,480,4),dtype=np.uint8);paletteDebug=debug.copy();unknown=debug.copy()
colours=np.array([[62,140,255],[245,83,83],[66,219,164],[213,122,247]],dtype=np.uint8)
for c in rows:
 x,y=c['x'],c['yBottom'];debug[y,x,:3]=colours[(c['draw']-11)%4];debug[y,x,3]=255;paletteDebug[y,x,:3]=c['expectedRGB8'];paletteDebug[y,x,3]=255
 if not c['sourceKnown'] or c.get('uvTriangleTest')=='outside':unknown[y,x]=[255,0,255,255]
for name,img in [('SOURCE_FAMILY60',debug),('PALETTE_EXPECTED60',paletteDebug),('UNKNOWN_SOURCE60',unknown)]:
 im=Image.fromarray(np.flipud(img),mode='RGBA');im.save(R/(name+'.png'));im.crop((x0,272-y0-h,x0+w,272-y0)).resize((w*8,h*8),Image.Resampling.NEAREST).save(R/(name+'_ZOOM.png'))
canvas=Image.new('RGB',(1920,544+60+max(h*8,120)),(24,26,31));pen=ImageDraw.Draw(canvas)
for col,tag in enumerate(['CONTROL','CANDIDATE']):
 canvas.paste(Image.open(R/(tag+'_FULL60.png')).convert('RGB'),(960*col,24));pen.text((960*col+12,5),tag+' actual native960; identical frozen frame',fill='white')
 canvas.paste(Image.open(R/(tag+'_HAIR_NEAREST60.png')).convert('RGB'),(960*col+12,590));pen.text((960*col+12,570),'Hair nearest integer enlargement; no resampling blend',fill='white')
canvas.save(R/'COMPARE60.png')
print(json.dumps(summary,ensure_ascii=False,indent=2))
