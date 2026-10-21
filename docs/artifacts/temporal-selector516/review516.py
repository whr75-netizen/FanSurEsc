from pathlib import Path
import json,math,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
import active516 as G,select516 as C

D=G.OUTPUT;R=G.INPUT
original=[G.read_mask(i)for i in range(81)]
def pulses(seq):
    return[{'target':i,'xy':[int(x),int(y)],'labels':[int(seq[k][y,x])for k in[i-1,i,i+1]]}for i in range(1,80)for y,x in zip(*np.where((seq[i-1]==seq[i+1])&(seq[i]!=seq[i-1])))]
baselineQuality=[]
for m in original:baselineQuality.append(C.loop_quality(m))
reports=[]
for eta in [.5,1.,2.]:
    folder=D/('eta-'+str(eta));p=folder/'RESULT516.json'
    if not p.exists():raise RuntimeError(f'Existing run eta{eta} not complete; do not restart')
    result=json.loads(p.read_text());seq=[np.load(folder/f'{i:03d}.npy')for i in range(81)];rows=result['rows']
    summary={'eta':eta,'beta':result['beta'],'fixedGridABAPrevious':pulses(original),'fixedGridABACandidate':pulses(seq),'maskSeamColdStartDifference':int((seq[0]!=seq[80]).sum()),'meanSpatialEnergyDelta':float(np.mean([r['finalSpatial']['total']-r['initialSpatial']['total']for r in rows])),'maxSpatialEnergyDelta':max(r['finalSpatial']['total']-r['initialSpatial']['total']for r in rows),'meanAreaErrorDelta':float(np.mean([r['finalSpatial']['area']-r['initialSpatial']['area']for r in rows])),'meanPerimeterDelta':float(np.mean([r['finalSpatial']['perimeter']-r['initialSpatial']['perimeter']for r in rows])),'meanChangedCellsVsSamePoseStaticCut':float(np.mean([len(r['newFillXY'])+len(r['removedXY'])for r in rows])),'maxChangedCellsVsSamePoseStaticCut':max(len(r['newFillXY'])+len(r['removedXY'])for r in rows),'selectedNovelPacketObservations':result['novelPacketCount'],'meanStairRatioReversalsBaseline':float(np.mean([r['stairRatioReversalsDiagnostic']for r in baselineQuality])),'meanStairRatioReversalsCandidate':float(np.mean([r['quality']['stairRatioReversalsDiagnostic']for r in rows])),'worseStairRatioFrames':[i for i,r in enumerate(rows)if r['quality']['stairRatioReversalsDiagnostic']>baselineQuality[i]['stairRatioReversalsDiagnostic']],'maxBoundaryFit':max(r['boundaryFitMax']for r in rows),'shapeQualityPassed':False,'nativePacketAndColourPassed':False,'scope':'Raw fixed-grid ABA is a screen observation, not correspondence-aware proof that every remaining/removed event is an error or that motion is preserved.'}
    reports.append(summary)

resetCounts=collections.Counter();actualAudit=[]
for i in range(1,81):
    a=json.loads((D/f'{i-1:03d}_ACTIVE.json').read_text());b=json.loads((D/f'{i:03d}_ACTIVE.json').read_text())
    counts=collections.Counter(v['reason']for v in b['previousCorrespondence']if not v['valid']);resetCounts.update(counts);actualAudit.append({'target':i,'invalidPreviousSpanReasons':dict(counts),'activeGeometryJunctions':b['geometry']['junctionNodes']})

# A labelled diagnostic, not a rendered new candidate. Actual current full body
# remains at left; two head panels show only source region/reference boundaries.
selected=[np.load(D/'eta-1.0'/f'{i:03d}.npy')for i in range(81)]
box=(203,29,239,63);scale=6;mw,mh=(box[2]-box[0])*scale,(box[3]-box[1])*scale
def mask_panel(i,m):
    small=Image.fromarray(np.where(m[box[1]:box[3],box[0]:box[2]],190,30).astype('uint8'),'L').convert('RGB').resize((mw,mh),Image.Resampling.NEAREST);d=ImageDraw.Draw(small)
    doc=json.loads((R/f'{i:03d}_curves.json').read_text())
    for ring in doc['curves']:
        pts=[((p['x']-box[0])*scale,(p['y']-box[1])*scale)for p in ring['points']];d.line(pts+pts[:1],fill='#64c8ef',width=1)
    return small
phases=[0,10,20,30,40,51,60,70,80];sheet=Image.new('RGB',(700,len(phases)*240),'#202020');draw=ImageDraw.Draw(sheet)
for row,i in enumerate(phases):
    draw.text((4,row*240+2),f'{i}/80 phase{i/80:.4f} | CURRENT511+512 actual head / static mask / temporal516 MASK ONLY',fill='white')
    pose=json.loads((R/f'{i:03d}_pose.json').read_text());ox,oy=pose['offset']
    actual=Image.open(R/f'{i:03d}_ALT.png').convert('RGB').crop((2*(box[0]+ox),2*(box[1]-oy),2*(box[2]+ox),2*(box[3]-oy))).resize((mw,mh),Image.Resampling.NEAREST)
    sheet.paste(actual,(4,row*240+25));sheet.paste(mask_panel(i,original[i]),(238,row*240+25));sheet.paste(mask_panel(i,selected[i]),(472,row*240+25))
sheet.save(D/'HEAD_DIAGNOSTIC516.png')

# All frame/time preservation. This is explicitly an offline mask diagnostic,
# never presented as an actual Unity render of temporal516.
frames=[];times=[];bodyBox=(332,48,556,358)
for i in range(81):
    times.append(json.loads((R/f'{i:03d}_ALT_projection.json').read_text())['gameTime'])
    if i==80:continue
    im=Image.new('RGB',(690,360),'#181818');d=ImageDraw.Draw(im)
    d.text((4,4),f'516 OFFLINE DESIGN ONLY | {i}/80 {i/80:.4f}',fill='white');d.text((4,20),'CURRENT ACTUAL BODY       STATIC REGION       TEMPORAL REGION (UNRENDERED)',fill='white')
    im.paste(Image.open(R/f'{i:03d}_ALT.png').convert('RGB').crop(bodyBox),(2,46));im.paste(mask_panel(i,original[i]),(238,50));im.paste(mask_panel(i,selected[i]),(472,50));frames.append(im)
ms=np.rint((np.array(times)-times[0])*1000).astype(int);duration=np.diff(ms).tolist();target=D/'FULLBODY_CONTEXT_OFFLINE_MASKS516.webp'
frames[0].save(target,format='WEBP',save_all=True,append_images=frames[1:],duration=duration,loop=0,lossless=True,quality=100,method=4)
out={'status':'OFFLINE_PROTOTYPE_NOT_ADOPTED; actual shape/packet gate not passed','sensitivity':reports,'actualStoredCorrespondenceResetCounts':dict(resetCounts),'actualStoredCorrespondenceResets':actualAudit,'actualOcclusionQualifier':'Current selected boundaries have packet evidence; no newly occluded span is inferred from lack of a novel packet. Novel selections still require real same-ray source validation.','allFramesDiagnostic':{'path':str(target),'bytes':target.stat().st_size,'frames':80,'durationMs':sum(duration),'pixelLossless':True,'body':'unchanged actual current511+512 capture','candidate':'offline region mask only; not new Unity final','endpointStoredSeparately':True},'noProductChangesOrNewCaptures':True,'unresolved':['causal cold-start seam difference','stair rhythm/shape tradeoff','novel packets visibility','colour11 and body1','native world','packet212ms']}
(D/'REVIEW516.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'sensitivity':reports,'actualResetCounts':dict(resetCounts),'diagnostic':out['allFramesDiagnostic']},ensure_ascii=False))
