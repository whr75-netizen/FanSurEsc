"""Audit frozen62 first fragmentation; no renderer, palette or threshold edits."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;S=R.parent/'source-regions62';B=R.parent/'author33/feature34'
if not S.exists():S=R.parent/'2026-10-31-source-regions62'
sys.path.insert(0,str(S))
from region62 import lab
load=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
dump=lambda n,v:(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
data=load(S/'CELLS62.json');cache=load(S/'CACHE62.json');profiles=load(S/'SOURCE_PROFILE_AUDIT62.json');legacy=load(S/'LEGACY_INPUT62.json');legacyLabels=load(S/'LEGACY_CELLS62.json')
byregion={f"material{m['materialId']}/uv-region{q['localId']}":q for m in cache['materials']for q in m['regions']}
profile={(r['x'],r['yBottom']):r for r in profiles['rows']}
def components(rows,key):
 pts={(r['x'],r['y']):i for i,r in enumerate(rows)};seen=set();out=[]
 for xy,i in pts.items():
  if i in seen:continue
  todo=[xy];seen.add(i);group=[]
  while todo:
   x,y=todo.pop();j=pts[x,y];group.append(j)
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    k=pts.get((x+dx,y+dy))
    if k is not None and k not in seen and key(rows[k])==key(rows[j]):seen.add(k);todo.append((x+dx,y+dy))
  out.append(group)
 return out
groups=defaultdict(list)
for row in data['rows']:groups[row['sourceRegionId']].append(row)
regions=[]
for key,rows in groups.items():
 src=byregion[key];parts=components(rows,lambda r:0);structures=Counter(r['sourceStructureId']for r in rows)
 regions.append({'rangeRegionId':key,'sourceDefinition':'connected quantized source-Lab box; NOT a detected feature domain','visibleCells':len(rows),'sourceTexelCount':src['texelCount'],'screenComponents':len(parts),'sourceTopologyStructures':dict(structures),'separateStructuresObserved':len(structures)>1,'sameStructureScreenSplit':any(len(components([r for r in rows if r['sourceStructureId']==s],lambda r:0))>1 for s in structures),'certificateSeedInThisRangeRegion':src['hasCertificateSeed'],'certificateProvesWholeRegionFeature':False,'affineCompatiblePointSamples':sum(profile[r['x'],r['y']]['bothAxesAffineCompatible']for r in rows),'colourRangeCutOrigin':'measured diagnostic box width, not physical geometry or semantic ID','occlusionCauseOfScreenSplit':'unresolved: frame60 evaluated/projection-contour correspondence not saved','cells':[[r['x'],r['y']]for r in rows]})
regions.sort(key=lambda r:r['rangeRegionId'])
for r in regions:
 r['exclusiveDisplaySplitClass']='UV-region-spans-distinct-source-structures'if r['separateStructuresObserved']else'same-structure-disconnected-on-screen-cause-unresolved'if r['sameStructureScreenSplit']else'single-visible-fragment-of-a-colour-range'

# Four independent edge facts; a colour-range cut is not made a geometry cut.
currentEdges=[];byxy={(r['x'],r['y']):i for i,r in enumerate(data['rows'])}
for xy,i in byxy.items():
 a=data['rows'][i]
 for dx,dy in [(1,0),(0,1)]:
  j=byxy.get((xy[0]+dx,xy[1]+dy))
  if j is None:continue
  b=data['rows'][j];different=a['sourceRegionId']!=b['sourceRegionId']
  currentEdges.append({'a':list(xy),'b':[xy[0]+dx,xy[1]+dy],'rangeCut':different,'sourceTopologyDifferent':(a['materialId'],a['sourceStructureId'])!=(b['materialId'],b['sourceStructureId']),'ownerDifferent':a['occlusionOwnerBufferUnchanged'][0:2]!=b['occlusionOwnerBufferUnchanged'][0:2],'QDifferent':a['Q']!=b['Q'],'nativePointRGBEqual':data['sourceRGB8'][i]==data['sourceRGB8'][j],'outputRGBDifferent':data['beforeLineRGB8'][i]!=data['beforeLineRGB8'][j],'sameTriangle':a['materialId']==b['materialId']and a['primitive']==b['primitive'],'geometryVisibility':'unknown for this exact frame; topology/owner difference alone is not occlusion','rangeCutProvesHardFeature':False})

# The legacy140 are another source, with actual matched evaluated geometry.
frozen=load(R/'EDGE_SOURCE_INPUT63.json');packet={int(k):v for k,v in frozen['packet'].items()};packetHash=frozen['packetSHA256']
geo=frozen;relations={tuple(sorted([e['aIndex'],e['bIndex']])):e for e in geo['candidateRelations']}
assert all([packet[e['aIndex']]['chart'],packet[e['bIndex']]['chart']]==e['candidateCharts']for e in geo['candidateRelations'])
known=set(legacy['knownIndices']);rows={r['index']:r for r in legacy['rows']if r['index']in known};cand={r['index']:r for r in legacyLabels['cells']if r['sourceKnown']}
certs=load(S/'FEATURE_TESTS62.json');protected={v['id']for v in certs if v['protect']}
# The region40 certificate mapping retains the ORIGINAL screen index pair;
# sourcePair UV witnesses alone do not contain an index field.
rawMap=frozen['certificateIndexPairs']
certEdge={tuple(sorted([v['a'],v['b']])):v['id']for v in rawMap if v['id']in protected}
edges=[];rebound=[]
for i,a in rows.items():
 p=packet[i];assert a['sample']['materialId']==p['role']
 if a['sample']['uv']!=p['uv']:rebound.append({'index':i,'colourSampleUV':a['sample']['uv'],'geometryUV':p['uv'],'sourceBindingGeometryUV':a.get('geometryUV'),'classification':'colour-reference UV differs from selected surface UV; not assumed corrupt or equivalent'})
reboundIds={v['index']for v in rebound}
for i,a in rows.items():
 p=packet[i]
 for j in [i+1 if i%32<31 else -1,i+32]:
  if j not in rows:continue
  b=rows[j]
  if a['appearance']!=b['appearance']or a['shadeK']!=b['shadeK']or a['oldRGB8']!=b['oldRGB8']or cand[i]['outputRGB8']==cand[j]['outputRGB8']:continue
  relation=relations[tuple(sorted([i,j]))];category=relation['candidateCategory'];nativeGap=abs(a['sourceLab'][0]-b['sourceLab'][0]);outputGap=float(abs(lab([cand[i]['outputRGB8']])[0,0]-lab([cand[j]['outputRGB8']])[0,0]));c=certEdge.get(tuple(sorted([i,j])))
  reason='colour-reference-UV-rebound-needs-bridge'if i in reboundIds or j in reboundIds else'certified-source-feature-pair'if c is not None else'actual-occlusion-or-gap'if category in ['front/back occlusion','projected uncovered hair gap']else'surface-ownership-or-overlap'if category in ['depth-continuous ownership change','depth-tied chart overlap']else'continuous-front-surface-colour-range-cut'
  edges.append({'aIndex':i,'bIndex':j,'a':[i%32,i//32],'b':[j%32,j//32],'reason':reason,'sourceFeatureCertificate':c,'actualGeometryCategory':category,'chartA':p['chart'],'chartB':packet[j]['chart'],'sourceRGBLinearA':a['sample']['baseRGBAlinear'],'sourceRGBLinearB':b['sample']['baseRGBAlinear'],'sourceDeltaL':nativeGap,'outputDeltaL':outputGap,'outputRGB8':[cand[i]['outputRGB8'],cand[j]['outputRGB8']],'rangeRegionIds':[cand[i]['sourceRegion'],cand[j]['sourceRegion']],'sameQ':a['shadeK'],'artificialHardFeaturePromotion':c is None,'meaning':'range/palette boundary cause is confirmed; undesired artistic edge or removal permission is NOT inferred from count or size','geometryEvents':relation['geometry']['events']})
assert len(edges)==140
summary={'currentSourceId':data['sourceId'],'current373':{'visibleRangeRegions':len(regions),'screenComponents':sum(v['screenComponents']for v in regions),'regionsAcrossDifferentStructures':sum(v['separateStructuresObserved']for v in regions),'sameStructureScreenSplitRegions':sum(v['sameStructureScreenSplit']for v in regions),'certificateSeedMemberRegions':sum(v['certificateSeedInThisRangeRegion']for v in regions),'edges':len(currentEdges),'rangeCutEdges':sum(e['rangeCut']for e in currentEdges),'rangeCutEdgesWithSameTriangle':sum(e['rangeCut']and e['sameTriangle']for e in currentEdges),'samePointRGBButDifferentOutputSameQ':sum(e['nativePointRGBEqual']and e['outputRGBDifferent']and not e['QDifferent']for e in currentEdges)},'legacySourceId':legacy['sourceId'],'legacy140':{'edges':len(edges),'classification':dict(Counter(e['reason']for e in edges)),'geometryCategory':dict(Counter(e['actualGeometryCategory']for e in edges)),'packetSHA256':packetHash,'geometryEndpointChartMatches':672,'colourSampleUVRebindings':rebound,'sameSourceAs373':False},'firstFragmentation':'region62.build_regions Lab bin cuts before any actual source feature-domain/curve stage','missingStages':['actual source feature boundaries/key IDs beyond hair membership and sparse contrast witnesses','source-colour shared boundary correction before shade lookup','frame60 source-guided boundary geometry'],'paletteSharingIsRegionCorrection':False,'labelsOrRGBChanged':0}
summary['current373']['exclusiveDisplaySplitClass']=dict(Counter(r['exclusiveDisplaySplitClass']for r in regions))
summary['legacy140']['evaluatedGeometryCorrespondence']=frozen['geometrySourceMatch']
summary['noActiveFeatureBoundaryLockExistedIn62']=True
summary['minimalAdapterChange']='remove unsupported feature-name promotion; expose separate source/colour/structure/shade layers and shared edges. This does not claim a spatial correction.'
dump('REGIONS66.json',regions);dump('CURRENT_EDGES63.json',currentEdges);dump('LEGACY_140_EDGES63.json',edges);dump('AUDIT63.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
