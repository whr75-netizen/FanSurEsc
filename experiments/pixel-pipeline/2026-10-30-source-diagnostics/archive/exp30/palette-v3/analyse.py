from pathlib import Path
import base64,collections,hashlib,json,math,sys
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'colour-family'))
from pngio import read,write,zoom
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34')
T=Path(r'C:\Users\15352\Desktop\작업폴더\아트검토\35_특징영역_공유경계후보\tone-boundary')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
binding=load(R/'BINDINGS.json');frame=load(B/'source-export/bundle/frame-source-data.json');diag=load(T/'DIAGNOSIS.json');packets=load(B/'ribbon-path/GEOMETRY_PACKETS.json')
original=base64.b64decode(frame['originalRGBA']);W,H=64,80;cache={}
def linearLab(rgb):
 r,g,b=rgb;l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3);m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3);s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
 return (.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s)
def lab(rgb):
 rgb=tuple(rgb)
 if rgb not in cache:
  v=[x/255 for x in rgb];cache[rgb]=linearLab([x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4 for x in v])
 return cache[rgb]
def d(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def rgb8(rgba):return [round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))for v in rgba[:3]]
def image(rows,field):
 out=bytearray(original)
 for row in rows:
  if not row or row.get('unresolved'):continue
  i=row['index'];rgb=rgb8(row['sample']['baseRGBAlinear'])if field=='source'else row[field]
  for dy in range(2):
   for dx in range(2):p=((i//32*2+dy)*W+i%32*2+dx)*4;out[p:p+3]=bytes(rgb)
 return bytes(out)
def save(name,out):write(R/(name+'-1x.png'),W,H,out);write(R/(name+'-8x.png'),W*8,H*8,zoom(out,W,H,8))
def components(rows,key):
 labels={r['index']:key(r)for r in rows if r and not r.get('unresolved')};seen=set();sizes=[]
 for i,label in labels.items():
  if i in seen:continue
  q=[i];seen.add(i)
  for j in q:
   x,y=j%32,j//32
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    xx,yy=x+dx,y+dy;k=yy*32+xx
    if 0<=xx<32 and 0<=yy<40 and k in labels and k not in seen and labels[k]==label:seen.add(k);q.append(k)
  sizes.append(len(q))
 return {'components':len(sizes),'singleCellComponents':sizes.count(1)}
summary={};checks=[];edge_results={};pixel_examples={}
for name in ['preserve','simplify']:
 rows=binding['variants'][name]['rows'];ablation=binding['existing16Ablation'][name]['rows'];eligible=[r for r in rows if r and not r.get('unresolved')];by={r['index']:r for r in eligible}
 outputs={'old':image(rows,'oldRGB8'),'existing16':image(ablation,'rgb'),'new':image(rows,'rgb'),'source':image(rows,'source')}
 w,h,main=read(T/(name+'-before-1x.png'));assert outputs['old']==main;checks.append(name+' actual latest before PNG exact replay')
 for label,out in outputs.items():
  save(name+'-'+label,out);assert out[3::4]==original[3::4]
  for y in range(H):
   for x in range(W):
    i=(y//2)*32+x//2;p=(y*W+x)*4
    if i not in by:assert out[p:p+4]==original[p:p+4]
  checks.append(name+' '+label+' outside/alpha/unresolved exact')
 edges=[]
 for i,a in by.items():
  x,y=i%32,i//32
  for dx,dy in [(1,0),(0,1)]:
   j=(y+dy)*32+x+dx
   if x+dx>=32 or y+dy>=40 or j not in by:continue
   b=by[j];srcA=a['sourceLab'];srcB=b['sourceLab'];oldGap=abs(lab(a['oldRGB8'])[0]-lab(b['oldRGB8'])[0]);newGap=abs(lab(a['rgb'])[0]-lab(b['rgb'])[0]);srcGap=abs(srcA[0]-srcB[0])
   edges.append({'a':[x,y],'b':[j%32,j//32],'sameShade':a['shadeK']==b['shadeK'],'sameAppearance':a['appearance']==b['appearance'],
    'sameChart':packets[i]['chart']==packets[j]['chart'],'paleRoleBoundary':(a['appearance']==3)!=(b['appearance']==3),
    'sourceGapL':srcGap,'sourceGapLab':d(srcA,srcB),'oldGapL':oldGap,'newGapL':newGap,
    'oldGapLab':d(lab(a['oldRGB8']),lab(b['oldRGB8'])),'newGapLab':d(lab(a['rgb']),lab(b['rgb'])),
    'oldExcessL':max(0,oldGap-srcGap),'newExcessL':max(0,newGap-srcGap),'oldEqual':a['oldRGB8']==b['oldRGB8'],'newEqual':a['rgb']==b['rgb'],
    'oldReferenceIds':[a['oldReferenceId'],b['oldReferenceId']],'newReferenceIds':[a['paletteReferenceId'],b['paletteReferenceId']]})
 same=[e for e in edges if e['sameShade']and e['sameAppearance']]
 newEdges=[e for e in same if e['oldEqual']and not e['newEqual']];lost=[e for e in same if not e['oldEqual']and e['newEqual']]
 stats={}
 for field in ['oldRGB8','rgb']:
  delta=[lab(r[field])[0]-r['sourceLab'][0]for r in eligible];absolute=sorted(map(abs,delta));full=sorted(d(lab(r[field]),r['sourceLab'])for r in eligible);stats[field]={'maxPositiveDeltaL':max(delta),'minDeltaL':min(delta),'medianAbsDeltaL':absolute[len(absolute)//2],'p95AbsDeltaL':absolute[int(len(absolute)*.95)],'medianErrorLab':full[len(full)//2],'p95ErrorLab':full[int(len(full)*.95)],'maxErrorLab':max(full),'usedColours':len({tuple(r[field])for r in eligible})}
 paleEdges=[e for e in edges if e['paleRoleBoundary']]
 summary[name]={'eligibleCells':len(eligible),'unresolvedCells':sum(bool(r and r.get('unresolved'))for r in rows),'sourceError':stats,
  'sameShadeAppearanceEdges':len(same),'maxSourceGapL':max(e['sourceGapL']for e in same),'maxOldOutputGapL':max(e['oldGapL']for e in same),'maxNewOutputGapL':max(e['newGapL']for e in same),
  'maxOldExcessGapL':max(e['oldExcessL']for e in same),'maxNewExcessGapL':max(e['newExcessL']for e in same),
  'newVisibleToneEdges':len(newEdges),'oldVisibleToneEdgesMerged':len(lost),
  'newEdgesWithOriginalSourceColourDifference':sum(e['sourceGapLab']>1e-9 for e in newEdges),
  'newEdgeMaxSourceGapL':max((e['sourceGapL']for e in newEdges),default=0),'newEdgeMaxOutputGapL':max((e['newGapL']for e in newEdges),default=0),
  'paleBoundaryEdges':len(paleEdges),'paleBoundariesOldEqual':sum(e['oldEqual']for e in paleEdges),'paleBoundariesNewEqual':sum(e['newEqual']for e in paleEdges),
  'appearanceBoundaryEdges':sum(not e['sameAppearance']for e in edges),
  'appearanceBoundariesOldEqual':sum(not e['sameAppearance']and e['oldEqual']for e in edges),
  'appearanceBoundariesNewEqual':sum(not e['sameAppearance']and e['newEqual']for e in edges),
  'oldRenderedComponents':components(rows,lambda r:tuple(r['oldRGB8'])),'newRenderedComponents':components(rows,lambda r:tuple(r['rgb'])),
  'newSourceReferenceComponents':components(rows,lambda r:r['paletteReferenceId']),
  'warning':'More tone divisions and single-cell regions may be real gradient quantization or undesirable fragmentation. No art pass follows from these counts.'}
 edge_results[name]={'all':edges,'newEdges':newEdges,'oldEdgesMerged':lost,'appearanceBoundaryRGBMerged':[e for e in edges if not e['sameAppearance']and e['newEqual']and not e['oldEqual']],'largestNewExcess':sorted(same,key=lambda e:e['newExcessL'],reverse=True)[:12]}
 pixel_examples[name]=[]
 for x,y in [(10,25),(11,25),(25,26),(25,27),(6,23)]:
  r=by[y*32+x];pixel_examples[name].append({'cell':[x,y],'sourceRGB8':rgb8(r['sample']['baseRGBAlinear']),'sourceLabL':r['sourceLab'][0],
   'appearance':r['appearance'],'shadeK':r['shadeK'],'geometryG':r['geometryG'],'oldToneClass':r['oldToneClass'],'oldReferenceId':r['oldReferenceId'],
   'oldRGB8':r['oldRGB8'],'oldLabL':lab(r['oldRGB8'])[0],'newReferenceId':r['paletteReferenceId'],'newRGB8':r['rgb'],'newLabL':lab(r['rgb'])[0],
   'existing16RGB8':ablation[y*32+x]['rgb'],'sourceUV':r['sample']['uv'],'geometryUV':r['geometryUV']})
 # Head-only label visualization uses native output as colour, no new colour constants.
 def crop(raw,x0,y0,x1,y1,scale):
  w=x1-x0;h=y1-y0;cut=b''.join(raw[(y*W+x0)*4:(y*W+x1)*4]for y in range(y0,y1));return w*scale,h*scale,zoom(cut,w,h,scale)
 for label in ['old','new','source']:
  cw,ch,cut=crop(outputs[label],8,40,30,68,12);write(R/(name+'-'+label+'-lower-left.png'),cw,ch,cut)
 # Preserve/simplify are rendered independently and are not user-selected here.
 (R/(name+'-pixels.json')).write_text(json.dumps({'old':list(outputs['old']),'new':list(outputs['new'])}),encoding='utf-8')

# Confirm the precise report evidence, not a different earlier frame.
for item in diag['sameShadeToneBoundaryPairs']:
 a=item['a'];b=item['b'];by={r['index']:r for r in binding['variants']['preserve']['rows']if r and not r.get('unresolved')}
 for q in [a,b]:
  x,y=q['cell'];r=by[y*32+x];assert r['oldRGB8']==q['finalRGB8']and r['shadeK']==q['shade'];assert abs(r['sourceLab'][0]-q['sourceL'])<1e-12
 checks.append('main DIAGNOSIS exact source/final pair '+str(a['cell'])+'/'+str(b['cell']))
for fn,value in [('SUMMARY.json',summary),('EDGES.json',edge_results),('PIXEL_EVIDENCE.json',pixel_examples)]:
 (R/fn).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
receipt={'checks':checks,'passed':len(checks),'mainToneManifestSHA256':sha(T/'MANIFEST.json'),'inputMainBindingSHA256':binding['mainBindingSHA256'],
 'scope':'fixed latest before packets, palette-only candidate; tone-boundary one-cell trial not adopted; no art or temporal pass'}
(R/'REPLAY_VERIFIED.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({'summary':summary,'examples':pixel_examples['preserve'],'checks':len(checks)},indent=2))
