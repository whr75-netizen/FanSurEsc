from pathlib import Path
import array,ast,bisect,collections,json,math,struct,zipfile
R=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34');bindings=load(R/'BUDGET_BINDINGS.json');old=load(R.parent/'palette-v3/BINDINGS.json')
geo=load(Path(r'C:\Users\15352\Desktop\작업폴더\아트검토\35_특징영역_공유경계후보\CANDIDATE_GEOMETRY_RELATIONS.json'))['candidateRelations'];categories={tuple(sorted([e['aIndex'],e['bIndex']])):e['candidateCategory']for e in geo};packets=load(B/'ribbon-path/GEOMETRY_PACKETS.json')
def npz(path):
 out={}
 with zipfile.ZipFile(path)as z:
  for fn in ['base.npy','colour.npy','charts.npy','valid.npy','uncertain.npy']:
   raw=z.read(fn);n=struct.unpack_from('<H',raw,8)[0];h=ast.literal_eval(raw[10:10+n].decode());v=array.array({'<i8':'q','<f8':'d','|b1':'b'}[h['descr']]);v.frombytes(raw[10+n:]);out[fn[:-4]]=v
 return out
fields=npz(B/'shared-v5/NATIVE_FEATURE_FIELDS.npz')
def lablinear(rgb):
 r,g,b=rgb;l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3);m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3);s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
 return(.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s)
cache={}
def lab(rgb):
 t=tuple(rgb)
 if t not in cache:
  v=[x/255 for x in rgb];cache[t]=lablinear([x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4 for x in v])
 return cache[t]
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def neighbours(i):
 x,y=i%32,i//32
 return[(y+dy)*32+x+dx for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]if 0<=x+dx<32 and 0<=y+dy<40]
def domains(rows):
 by={r['index']:r for r in rows if r and not r.get('unresolved')};ids=[-1 if r is None else -2 for r in rows];seen=set();k=0
 for i,a in by.items():
  if i in seen:continue
  q=[i];seen.add(i)
  for j in q:
   ids[j]=k
   for h in neighbours(j):
    if h not in by or h in seen or by[h]['appearance']!=a['appearance']or packets[h]['chart']!=packets[i]['chart']:continue
    if categories.get(tuple(sorted([j,h])))!='same front source chart throughout':continue
    seen.add(h);q.append(h)
  k+=1
 return ids,k
maps={};result={};all_variants={'v3':{k:v['rows']for k,v in old['variants'].items()},**bindings['variants']}
for key,variants in all_variants.items():
 result[key]={}
 for name,rows in variants.items():
  by={r['index']:r for r in rows if r and not r.get('unresolved')};ids,count=domains(rows)
  if name not in maps:maps[name]={'featureRegionIds':ids,'featureRegionCount':count,'definition':'connected existing appearance on same measured front source chart; palette colour IDs never create feature regions'}
  assert maps[name]['featureRegionIds']==ids,'Palette changed feature domains'
  singles=[];visible=0;extra_v2=0;merged_v2=0;sameAQpairs=0
  for i,r in by.items():
   ns=[j for j in neighbours(i)if j in by]
   for j in ns:
    if j<i:continue
    q=by[j]
    if r['appearance']==q['appearance']and r['shadeK']==q['shadeK']:
     sameAQpairs+=1;different=r['rgb']!=q['rgb'];previous=r['oldRGB8']!=q['oldRGB8'];visible+=different;extra_v2+=different and not previous;merged_v2+=previous and not different
   if any(by[j]['rgb']==r['rgb']for j in ns):continue
   actual=min((dist(r['sourceLab'],by[j]['sourceLab'])for j in ns),default=0);display=min((dist(lab(r['rgb']),lab(by[j]['rgb']))for j in ns),default=0)
   interior=len(ns)==4 and all(by[j]['appearance']==r['appearance']and by[j]['shadeK']==r['shadeK']and packets[j]['chart']==packets[i]['chart']and categories.get(tuple(sorted([i,j])))=='same front source chart throughout'for j in ns)
   sameAQ=len(ns)==4 and all(by[j]['appearance']==r['appearance']and by[j]['shadeK']==r['shadeK']for j in ns)
   source_between=bool(ns)and min(by[j]['sourceLab'][0]for j in ns)<=r['sourceLab'][0]<=max(by[j]['sourceLab'][0]for j in ns)
   out_between=bool(ns)and min(lab(by[j]['rgb'])[0]for j in ns)<=lab(r['rgb'])[0]<=max(lab(by[j]['rgb'])[0]for j in ns)
   singleton={'cell':[i%32,i//32],'appearance':r['appearance'],'Q':r['shadeK'],'nativeMinNeighbourDeltaE':actual,'outputMinNeighbourDeltaE':display,'extraIsolatedContrast':max(0,display-actual),
    'interiorSameFeatureSurfaceQ':interior,'allFourNeighboursSameAQ':sameAQ,'sourceLWithinNeighbours':source_between,'outputLWithinNeighbours':out_between,
    'classification':'smooth-tone division, not a new feature domain'if interior and source_between else'feature/geometry/shade edge or source local extremum; meaning not certified by size'}
   if key in ['v3','64-protected']:
    x,y=i%32,i//32;native=[yy*512+xx for yy in range(y*16,(y+1)*16)for xx in range(x*16,(x+1)*16)if fields['valid'][yy*512+xx]and not fields['uncertain'][yy*512+xx]and fields['charts'][yy*512+xx]==packets[i]['chart']]
    supported=[h for h in native if fields['colour'][h]==r['appearance']];ls=sorted(lablinear(fields['base'][h*3:h*3+3])[0]for h in supported)
    singleton['nativeFootprint']={'validSameFrontChartSamples':len(native),'sameAppearanceSamples':len(supported),
     'sameAppearanceFraction':len(supported)/len(native)if native else None,'sourceLRange':[ls[0],ls[-1]]if ls else None,
     'meaning':'support only; a thin real feature need not occupy the majority, and size is not a deletion rule'}
   singles.append(singleton)
  ordered=sorted(s['extraIsolatedContrast']for s in singles);result[key][name]={'sameAQPairs':sameAQpairs,'totalVisibleSameAQEdges':visible,'additionalVsV2':extra_v2,'v2EdgesMerged':merged_v2,'singleCells':len(singles),
   'smoothToneInteriorSingles':sum(s['interiorSameFeatureSurfaceQ']and s['sourceLWithinNeighbours']for s in singles),
   'sameAQSampledSingletons':sum(s['allFourNeighboursSameAQ']for s in singles),
   'sameAQSmoothToneSingles':sum(s['allFourNeighboursSameAQ']and s['sourceLWithinNeighbours']for s in singles),
   'sameAQInventedLPeaks':sum(s['allFourNeighboursSameAQ']and s['sourceLWithinNeighbours']and not s['outputLWithinNeighbours']for s in singles),
   'inventedInteriorLPeaks':sum(s['interiorSameFeatureSurfaceQ']and s['sourceLWithinNeighbours']and not s['outputLWithinNeighbours']for s in singles),
   'medianExtraIsolatedContrast':ordered[len(ordered)//2]if ordered else 0,'maxExtraIsolatedContrast':max(ordered,default=0),'singles':singles,
   'featureDomains':count,'paletteColourEdgesAreNotFeatureDomains':True}
(R/'FRAGMENT_AUDIT.json').write_text(json.dumps(result,indent=2));(R/'SOURCE_DOMAIN_MAP.json').write_text(json.dumps({'sourceId':old['sourceId'],'sourceFeatureId':None,'inferredDomains':maps,'unchangedAcrossAllBudgets':True},indent=2))
print(json.dumps({k:{n:{a:b for a,b in v.items()if a!='singles'}for n,v in w.items()}for k,w in result.items()},indent=2))
