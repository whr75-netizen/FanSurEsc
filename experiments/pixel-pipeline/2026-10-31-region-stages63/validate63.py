"""Frozen-input validation and debug images for the missing pipeline stages."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from shared_boundary63 import trace,path_metrics,reference_metrics,separate_layers
R=Path(__file__).resolve().parent;S=R.parent/'source-regions62';B=R.parent/'author33/feature34';F=B/'flat-shade-boundary44'
if not S.exists():S=R.parent/'2026-10-31-source-regions62'
load=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
dump=lambda n,v:(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
d=load(S/'CELLS62.json');rows=d['rows'];audit=load(R/'AUDIT63.json');regions=load(R/'REGIONS66.json');edges=load(R/'LEGACY_140_EDGES63.json');currentEdges=load(R/'CURRENT_EDGES63.json')
ids={s:i for i,s in enumerate(sorted({r['sourceRegionId']for r in rows}))};plan=separate_layers(d['sourceId'],rows,[ids[r['sourceRegionId']]for r in rows]);dump('LAYER_PLAN63.json',plan)
assert len(plan['cells'])==373 and not any(r['nativeColourRangeIsHardFeature']for r in plan['cells'])
assert all(r['childFeatureId']is None for r in plan['cells'])
x0,y0=210,214;w,h=21,27;mask=np.zeros((h,w),bool);labels=np.full((h,w),-1,int);q=labels.copy();structures=labels.copy();structIDs={s:i for i,s in enumerate(sorted({(r['materialId'],r['sourceStructureId'])for r in rows}))}
for r in rows:
 x,y=r['x']-x0,r['y']-y0;mask[y,x]=True;labels[y,x]=ids[r['sourceRegionId']];q[y,x]=r['Q'];structures[y,x]=structIDs[r['materialId'],r['sourceStructureId']]
boundary,paths=trace(labels,mask);qedges,qpaths=trace(q,mask);assert len(boundary)==audit['current373']['rangeCutEdges']
dump('SHARED_BOUNDARIES63.json',{'sourceId':d['sourceId'],'colourRangePaths':paths,'shadePaths':qpaths,'colourEdges':boundary,'shadeEdges':qedges,'coordinateSystem':'local frame60 logical x-right/y-up, origin[210,214]','sourceReferenceAvailable':False,'note':'path geometry measured only; cannot label extreme curvature without independent source curve'})

fixtures=[]
for name,a in [('T-junction',np.array([[0,0,1,1],[0,0,1,1],[2,2,2,2]])),('thin-band',np.array([[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]])),('small-hole',np.array([[0,0,0],[0,1,0],[0,0,0]]))]:
 snapshot=a.copy();es,ps=trace(a,np.ones(a.shape,bool));assert np.array_equal(a,snapshot);assert len({tuple(sorted((e['a'],e['b'])))for e in es})==len(es)
 fixtures.append({'name':name,'sharedEdges':len(es),'paths':len(ps),'inputChanged':False,'holesOrThinFeatureRemoved':False,'sourceScope':'synthetic boundary representation, not automatic semantic identification'})
reference=np.c_[np.linspace(0,4,81),np.linspace(0,4,81)];straight=reference_metrics([[0,0],[4,4]],reference);jagged=reference_metrics([[0,0],[0,1],[1,1],[1,3],[2,3],[2,2],[3,2],[3,4],[4,4]],reference)
assert straight['fixedReferenceArclengthTangent']<1e-12 and jagged['fixedReferenceArclengthTangent']>straight['fixedReferenceArclengthTangent']
reversedRun=reference_metrics([[0,0],[3,3],[2,2],[4,4]],reference)
assert reversedRun['fixedReferenceArclengthTangent']<1e-12 and reversedRun['sourceArclengthBacktracking']>1

# Re-evaluate44's already measured guide/raster; no new fit or runtime sampling.
frozen=np.load(R/'REPLAY44_FROZEN.npz');layers=np.load(R/'REPLAY44_LAYERS.npz');input44=load(R/'REPLAY44_INPUT63.json');curves=input44['curves'];result44=input44['result'];failed44=input44['failed'];path4=next(p for p in curves if p['id']==4)
before4=reference_metrics(path4['raw'],path4['fitted']);after4=reference_metrics(path4['constrainedRaster'],path4['fitted'])
assert abs(before4['fixedReferenceArclengthTangent']-path4['fixedArclengthTangent']['before'])<1e-12
assert abs(after4['fixedReferenceArclengthTangent']-path4['constrainedMetrics']['tangent'])<1e-12
assert np.array_equal(frozen['Q'],layers['Q'])and np.array_equal(frozen['g'],layers['g'])and np.array_equal(frozen['mask'],layers['mask'])
assert np.count_nonzero(layers['Q']!=layers['correctedQ'])==4
assert result44['beforeQRegions']==result44['afterQRegions']==11 and result44['beforeSingletons']==result44['afterSingletons']==6
assert failed44['afterSingletons']==7 and failed44['afterQRegions']==12
replay44={'sourceId':result44['sourceId'],'notFrame60':result44['sourceId']!=d['sourceId'],'sharedPath4Before':before4,'sharedPath4After':after4,'changes':result44['changes'],'regionCounts':[11,11],'singletons':[6,6],'unconstrainedFailure':{'regions':[11,12],'singletons':[6,7],'sourceSupportedThinConnectionCutRejected':curves[0]['reason']},'colourRegionCurvesImplementedBy44':False,'shadeCurvesImplementedBy44':True,'newCurveFitOrThresholdSearch':False}
dump('REPLAY44_METRICS63.json',replay44)
# The three original44 comparison PNGs were frozen once, not regenerated from
# neighbouring colours or used as inferred source geometry.

def colour_id(a):return [(int(a)*73)%251,(int(a)*131+29)%251,(int(a)*193+41)%251]
source=np.zeros((h,w,4),np.uint8);domain=source.copy();rangeIm=source.copy();structureIm=source.copy();shadeIm=source.copy()
for i,r in enumerate(rows):
 x,y=r['x']-x0,h-1-(r['y']-y0);source[y,x]=[*d['sourceRGB8'][i],255];domain[y,x]=[70,103,132,255];rangeIm[y,x]=[*colour_id(ids[r['sourceRegionId']]),255];structureIm[y,x]=[*colour_id(structIDs[r['materialId'],r['sourceStructureId']]),255];shadeIm[y,x]=[*([210]*3 if r['Q']else[50]*3),255]
sheet=Image.new('RGB',(6*280,h*12+60),(25,27,32));draw=ImageDraw.Draw(sheet)
for k,(a,title)in enumerate([(source,'Source unlit'),(rangeIm,'62 colour-range IDs (66)'),(domain,'Known hair domain; child unknown'),(structureIm,'Source topology IDs (45)'),(shadeIm,'Frozen Q; no correction here'),(np.array(Image.open(S/'final62-1x.png')),'RGB unchanged / unresolved')]):
 im=Image.fromarray(a).resize((w*12,h*12),Image.Resampling.NEAREST);im.save(R/f'CURRENT_LAYER63-{k}.png');sheet.paste(im,(k*280,36),im);draw.text((k*280,6),title,fill='white')
sheet.save(R/'CURRENT_LAYERS63.png')

# Current exact-RGB/Q contradictions and distinct structural/UV cases.
currentByXY={(r['x'],r['y']):i for i,r in enumerate(rows)}
contradictions=[]
for e in currentEdges:
 if e['nativePointRGBEqual']and e['outputRGBDifferent']and not e['QDifferent']:
  i,j=[currentByXY[tuple(e[k])]for k in ['a','b']]
  contradictions.append({'a':e['a'],'b':e['b'],'inputRGB8':d['sourceRGB8'][i],'Q':rows[i]['Q'],'anchors':[d['anchorRGB8'][i],d['anchorRGB8'][j]],'outputs':[d['beforeLineRGB8'][i],d['beforeLineRGB8'][j]],'materials':[rows[i]['materialId'],rows[j]['materialId']],'reason':'material-local range/medoid creates a colour difference with equal source point RGB and Q; geometry/feature merge is not implied'})
assert len(contradictions)==18;dump('EQUAL_INPUT_DIFFERENT_OUTPUT63.json',contradictions)

# Small masks for each legacy cause, at ORIGINAL legacy coordinates.
legacyIm=Image.open(S/'LEGACY62-2-1x.png').convert('RGBA');categories=sorted(set(e['reason']for e in edges));example=Image.new('RGB',(len(categories)*320,340),(25,27,32));pen=ImageDraw.Draw(example);exampleRows=[]
for k,category in enumerate(categories):
 e=next(v for v in edges if v['reason']==category);x,y=e['a'];box=(max(0,x-4),max(0,y-4),min(32,x+6),min(40,y+6));im=legacyIm.crop(box).resize(((box[2]-box[0])*24,(box[3]-box[1])*24),Image.Resampling.NEAREST);paint=ImageDraw.Draw(im)
 for xy,colour in [(e['a'],(255,80,80)),(e['b'],(255,230,50))]:
  xx,yy=(xy[0]-box[0])*24,(xy[1]-box[1])*24;paint.rectangle([xx,yy,xx+23,yy+23],outline=colour,width=2)
 example.paste(im,(k*320,65));pen.text((k*320,5),category.replace('-','\n',2),fill='white');pen.text((k*320,310),str(e['a'])+' -> '+str(e['b']),fill='white');exampleRows.append({'category':category,'edge':e,'crop':box})
example.save(R/'LEGACY_CAUSE_MASKS63.png');dump('REPRESENTATIVE_MASKS63.json',exampleRows)

# No fabricated spatial correction: keep62 RGB as explicit unchanged control.
(R/'RGB_UNCHANGED63.png').write_bytes((S/'final62-8x.png').read_bytes())
out={'currentSourceId':d['sourceId'],'sharedColourRangeEdges':len(boundary),'sharedColourPaths':len(paths),'sharedShadeEdges':len(qedges),'sharedShadePaths':len(qpaths),'allEdgesStoredExactlyOnce':True,'colourRangeNotFeatureLocks':373,'realChildFeatureMaskAvailable':False,'equalSourceRGBAndQContradictions':18,'syntheticFixtures':fixtures,'sourceReferenceMetricFixture':{'straight':straight,'jagged':jagged,'parallelReversedRun':reversedRun},'frame60SpatialRGBChanges':0,'reasonForNoSpatialChange':'frame60 has source point samples and hashes, but no independently located source feature contours or matching evaluated geometry/view/projection for native source-boundary reconstruction. Do not fit the quantization staircase as if it were the source shape.','noPaletteOrThresholdChanges':True,'artisticAcceptance':False,'newUnityCalls':0,'productChanges':0,'legacy44MetricsReproduced':True}
dump('VALIDATION63.json',out);print(json.dumps(out,ensure_ascii=False,indent=2))
