from pathlib import Path
import array,base64,collections,hashlib,json,math
from pngio import read,write,zoom
R=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));data=load(R/'INPUT.json');result=load(R/'RESULTS.json');models={'legacy':load(R/'PALETTE_LEGACY.json'),'distinct':load(R/'PALETTE_DISTINCT.json')};mask=[c is not None for c in data['cells']];W,H=data['width'],data['height'];DW,DH=data['displayWidth'],data['displayHeight'];original=base64.b64decode(data['originalRGBA']);visible=[i for i,v in enumerate(mask)if v]
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34');pool=load(B/'coverage-v3/PACKET_POOL.json');fine=collections.defaultdict(list)
for p in pool:
 if p['sampleKind']=='native960':
  x,y=map(math.floor,p['point'])
  if 0<=x<W and 0<=y<H:fine[y*W+x].append(p)
def components(values,connect):
 ids=[-1]*len(mask);sizes=[];groups=[];offsets=[(1,0),(-1,0),(0,1),(0,-1)]+([(1,1),(-1,-1),(1,-1),(-1,1)]if connect==8 else[])
 for i in visible:
  if ids[i]>=0:continue
  k=len(sizes);ids[i]=k;q=[i]
  for j in q:
   x,y=j%W,j//W
   for dx,dy in offsets:
    xx,yy=x+dx,y+dy;n=yy*W+xx
    if 0<=xx<W and 0<=yy<H and mask[n]and ids[n]<0 and values[n]==values[i]:ids[n]=k;q.append(n)
  sizes.append(len(q));groups.append(q)
 return{'ids':ids,'count':len(sizes),'singletons':sizes.count(1),'sizes':sizes,'groups':groups}
def unique(values):return len({json.dumps(values[i],separators=(',',':'))for i in visible})
def relation_violations(keys,rows):
 table=collections.defaultdict(lambda:collections.defaultdict(list))
 for i in visible:table[str(keys[i])][tuple(rows[i]['rgb'])].append(i)
 return{'testedGroups':len(table),'multiRGBGroups':sum(len(v)>1 for v in table.values()),'examples':[{'key':k,'RGBCells':[{'RGB':rgb,'cells':indices}for rgb,indices in v.items()]}for k,v in table.items()if len(v)>1][:8]}
Q=[c['Q']if c else None for c in data['cells']];q4=components(Q,4);q8=components(Q,8);base4=components([0]*len(mask),4);base8=components([0]*len(mask),8);summary={};details={};expected={}
for name,out in result['outputs'].items():
 rows=out['rows'];pixels=bytes(out['pixels']);source=[r['effectiveSourceRGBAlinear'][:3]if r else None for r in rows];source8=[[round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))for v in c]if c else None for c in source];rgb=[r['rgb']if r else None for r in rows];refs=[r['sourceReferenceId']if r else None for r in rows];keys=[r['emissionKey']if r else None for r in rows];r4=components(keys,4);r8=components(keys,8);c4=components(rgb,4);c8=components(rgb,8);src4=components(source8,4);src8=components(source8,8)
 if out['settings'].get('lit',True):
  m=models['distinct'if'distinct'in name else'legacy'];palette={tuple(m['compactPaletteRGB8'][m['perReferenceShadePaletteIndices'][refs[i]][Q[i]]])for i in visible}
 else:palette={tuple(source8[i])for i in visible}
 off=[{'index':i,'Q':Q[i],'RGB':rgb[i],'passthrough':rows[i]['passthrough']}for i in visible if tuple(rgb[i])not in palette]
 insideDisplay={tuple(pixels[(y*DW+x)*4:(y*DW+x)*4+3])for y in range(DH)for x in range(DW)if mask[y//2*W+x//2]}
 relations={'family_Q':relation_violations(Q,rows),'family_Q_QRegion4':relation_violations(q4['ids'],rows),'completeEmissionKey':relation_violations(keys,rows),'completeEmissionRegion4':relation_violations(r4['ids'],rows)}
 summary[name]={'hairLogicalCells':len(visible),'hairDisplayPixels':len(visible)*4,'inputLinearRGBUnique':unique(source),'inputRGB8Unique':unique(source8),'gExactUnique':len({data['cells'][i]['g']for i in visible}),
  'QDefinedBins':len(data['thresholds'])+1,'QOccupiedBins':unique(Q),'QCounts':dict(collections.Counter(Q[i]for i in visible)),'QRegionCount4':q4['count'],'QRegionCount8':q8['count'],'QSingleton4':q4['singletons'],'QSingleton8':q8['singletons'],
  'sourceReferenceUnique':unique(refs),'emissionLabelUnique':unique(keys),'emissionRegionCount4':r4['count'],'emissionRegionCount8':r8['count'],
  'inputRGBComponents4':src4['count'],'inputRGBComponents8':src8['count'],'finalRGBUnique':len(insideDisplay),'finalRGBComponents4':c4['count'],'finalRGBComponents8':c8['count'],'finalRGBSingleton4':c4['singletons'],'finalRGBSingleton8':c8['singletons'],
  'offExpectedPaletteCells':len(off),'offExpectedPaletteRGBUnique':len({tuple(x['RGB'])for x in off}),
  'mappingViolations':{k:v['multiRGBGroups']for k,v in relations.items()},'samePalettePixelsAtDisplayRaster':len(insideDisplay)==unique(rgb)}
 details[name]={'offPalette':off,'relations':relations,'QRegion4':q4['ids'],'QRegion8':q8['ids'],'emissionRegion4':r4['ids'],'emissionRegion8':r8['ids'],'RGBComponents4':c4['ids'],'RGBComponents8':c8['ids']}
 write(R/(name+'-1x.png'),DW,DH,pixels);write(R/(name+'-8x.png'),DW*8,DH*8,zoom(pixels,DW,DH,8));expected[name]=out['pixels']
# Frozen g/Q singleton evidence is independent of albedo override.
spikes=[]
for group in q4['groups']:
 if len(group)!=1:continue
 i=group[0];c=data['cells'][i];packet=load(B/'ribbon-path/GEOMETRY_PACKETS.json')[i];ns=[j for j in visible if abs(j%W-i%W)+abs(j//W-i//W)==1];native=fine[i];same=[p for p in native if p['chart']==c['chart']];selected=[p for p in pool if all(p[k]==packet[k]for k in ['sampleKind','fineX','fineY','role','primitive'])];px,py=packet['point'];x,y=i%W,i//W
 spikes.append({'index':i,'cell':[x,y],'Q':Q[i],'g':c['g'],'chart':c['chart'],'sampleKind':packet['sampleKind'],'selectedProjectedPoint':packet['point'],'selectedSourceSampleFoundInPool':bool(selected),'selectedSourceGExact':bool(selected)and selected[0]['g']==c['g'],
  'distanceOutsideNominalCellPixels':max(0,x-px,px-(x+1),y-py,py-(y+1)),
  'nativeFineCount':len(native),'sameChartFineCount':len(same),
  'sameChartFineQCounts':dict(collections.Counter(sum(p['g']>=t for t in data['thresholds'])for p in same)),
  'neighbours':[{'index':j,'Q':Q[j],'g':data['cells'][j]['g'],'chart':data['cells'][j]['chart']}for j in ns],
  'sourcePatternCanChangeThisQ':False,'fineSupportCaution':'only projected native960 points strictly inside cell are counted; selected centre or border sample may differ, not a proof of invalid coverage'})
shade={'geometryMaskComponents4':base4['count'],'geometryMaskComponents8':base8['count'],'geometryMaskSingleton4':base4['singletons'],'geometryMaskSingleton8':base8['singletons'],
 'QComponents4':q4['count'],'QComponents8':q8['count'],'QSingletons4':q4['singletons'],'QSingletons8':q8['singletons'],'QSingletonEvidence':spikes,
 'connectivityDefinition':'4: edge-sharing; 8: edge or corner-sharing on logical32x40 hair mask; components may share a Q/RGB value without being one connected region',
 'nativeEvidenceSource':'same-source native960 measured packets, matched by projected cell and current chart; no new raster/Unity capture'}
raw=load(B/'source-export/bundle/prelight-source.json');originalQ=[sum(c['g']>=t for t in data['thresholds'])if c else None for c in raw['cells']];raw4=components(originalQ,4);raw8=components(originalQ,8)
shade['priorCentreSamplingAudit']={'sameCaptureSourceId':raw['sourceId']==data['context']['primarySourceId'],'thisIsNotThePairedAlbedoIntervention':True,'originalCentreQCounts':dict(collections.Counter(originalQ[i]for i in visible)),
 'originalCentreComponents4':raw4['count'],'originalCentreComponents8':raw8['count'],'originalCentreSingleton4':raw4['singletons'],'originalCentreSingleton8':raw8['singletons'],'QChangesAtGeometrySampleSelection':sum(originalQ[i]!=Q[i]for i in visible),
 'singletonRows':[{'index':s['index'],'sourceCentreG':raw['cells'][s['index']]['g'],'sourceCentreQ':originalQ[s['index']],'selectedG':s['g'],'selectedQ':s['Q'],'originalCentreRegionSize4':raw4['sizes'][raw4['ids'][s['index']]]}for s in spikes],
 'interpretation':'source-centre vs geometry-selected sampling is a different geometry/sampling stage, not a texture/flat pair or a stale-sourceId finding'}
oldSingle={g[0]for g in raw4['groups']if len(g)==1};newSingle={g[0]for g in q4['groups']if len(g)==1};shade['priorCentreSamplingAudit']['newQSingletonIndices']=sorted(newSingle-oldSingle);shade['priorCentreSamplingAudit']['removedQSingletonIndices']=sorted(oldSingle-newSingle)
(R/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');(R/'MAPPING_AUDIT.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8');(R/'SHADE_FRAGMENTATION.json').write_text(json.dumps(shade,ensure_ascii=False,indent=2),encoding='utf-8');(R/'EXPECTED_PIXELS.json').write_text(json.dumps(expected,separators=(',',':')),encoding='utf-8')
print(json.dumps({'summary':summary,'geometry':{k:v for k,v in shade.items()if k!='QSingletonEvidence'}},indent=2))
