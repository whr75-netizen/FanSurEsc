from pathlib import Path
import base64,collections,json,math
from pngio import write,zoom
R=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
binding=load(R/'BUDGET_BINDINGS.json');v3=load(R.parent/'palette-v3/BINDINGS.json');nine=load(R/'NINE_NATIVE_AUDIT.json');B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34\source-export\bundle');frame=load(B/'frame-source-data.json');original=base64.b64decode(frame['originalRGBA'])
def lab(rgb):
 v=[x/255 for x in rgb];r,g,b=[x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4 for x in v];l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3);m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3);s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
 return(.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s)
def dist(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def components(rows):
 labels={r['index']:tuple(r['rgb'])for r in rows if r and not r.get('unresolved')};seen=set();sizes=[]
 for i,label in labels.items():
  if i in seen:continue
  q=[i];seen.add(i)
  for j in q:
   x,y=j%32,j//32
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    xx,yy=x+dx,y+dy;k=yy*32+xx
    if 0<=xx<32 and 0<=yy<40 and k in labels and k not in seen and labels[k]==label:seen.add(k);q.append(k)
  sizes.append(len(q))
 return{'components':len(sizes),'singles':sizes.count(1)}
summary={};evidence={}
for N,variants in binding['variants'].items():
 summary[N]={};evidence[N]={}
 for name,rows in variants.items():
  out=bytearray(original);eligible=[r for r in rows if r and not r.get('unresolved')];by={r['index']:r for r in eligible}
  for r in eligible:
   i=r['index']
   for dy in range(2):
    for dx in range(2):p=((i//32*2+dy)*64+i%32*2+dx)*4;out[p:p+3]=bytes(r['rgb'])
  write(R/f'{name}-{N}-1x.png',64,80,out);write(R/f'{name}-{N}-8x.png',512,640,zoom(out,64,80,8))
  pairs=[]
  for e in nine:
   a=by[e['a'][1]*32+e['a'][0]];b=by[e['b'][1]*32+e['b'][0]];pairs.append({'id':e['id'],'a':e['a'],'b':e['b'],'sourceGapL':e['sourceGapL'],'sourceGapLab':e['sourceGapLab'],'RGB':[a['rgb'],b['rgb']],'gapL':abs(lab(a['rgb'])[0]-lab(b['rgb'])[0]),'gapLab':dist(lab(a['rgb']),lab(b['rgb'])),'sameShade':e['sameShade']})
  errors=sorted(dist(lab(r['rgb']),r['sourceLab'])for r in eligible);delta=[lab(r['rgb'])[0]-r['sourceLab'][0]for r in eligible];summary[N][name]={**components(rows),'usedColours':len({tuple(r['rgb'])for r in eligible}),'medianErrorLab':errors[len(errors)//2],'p95ErrorLab':errors[int(len(errors)*.95)],'maxPositiveL':max(delta),'nineMerged':sum(p['RGB'][0]==p['RGB'][1]for p in pairs)};evidence[N][name]=pairs
(R/'BUDGET_SUMMARY.json').write_text(json.dumps(summary,indent=2));(R/'BUDGET_NINE.json').write_text(json.dumps(evidence,indent=2));print(json.dumps({'summary':summary,'nine':{N:[(p['id'],round(p['gapL'],5))for p in v['preserve']]for N,v in evidence.items()}},indent=2))
