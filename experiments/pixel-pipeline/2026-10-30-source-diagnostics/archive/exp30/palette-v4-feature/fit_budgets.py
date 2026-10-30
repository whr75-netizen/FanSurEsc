from pathlib import Path
import collections,hashlib,json,math,statistics
from pngio import read
R=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34\source-export\bundle')
source=load(B/'prelight-source.json');family=load(R.parent/'palette-v3/SOURCE_FAMILY_INPUT.json');v3=load(R.parent/'palette-v3/SHARED_NATIVE_PALETTE.json');hist=collections.Counter();origins={};cache={}
def lab(rgb):
 rgb=tuple(rgb)
 if rgb not in cache:
  v=[x/255 for x in rgb];r,g,b=[x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4 for x in v]
  l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3);m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3);s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
  cache[rgb]=(.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s)
 return cache[rgb]
for m in source['materials']:
 if m['materialId']not in family['materialIds']:continue
 p=R.parent/'model-source'/f"image-{m['imageId']}.png";assert sha(p)==m['imageSHA256'];w,h,rgba=read(p)
 for y in range(h):
  for x in range(w):
   rgb=tuple(rgba[(y*w+x)*4:(y*w+x)*4+3]);hist[rgb]+=1;origins.setdefault(rgb,{'materialId':m['materialId'],'imageId':m['imageId'],'x':x,'y':y})
lo=min(lab(r)[0]for r in hist);hi=max(lab(r)[0]for r in hist)
oldL=[lab(r['anchorRGB8'])[0]for r in v3['references']];gap=statistics.median(b-a for a,b in zip(oldL,oldL[1:]));summary=[]
for N in [16,32,64]:
 bins=[{}for _ in range(N)];width=(hi-lo)/N
 for r,n in hist.items():bins[min(N-1,int((lab(r)[0]-lo)/width))][r]=n
 refs=[]
 for i,values in enumerate(bins):
  n=sum(values.values());s=[sum(w*lab(r)[j]for r,w in values.items())for j in range(3)]
  rgb=min(values,key=lambda r:(n*sum(v*v for v in lab(r))-2*sum(v*t for v,t in zip(lab(r),s)),r))
  refs.append({'id':i,'anchorRGB8':rgb,'anchorLab':lab(rgb),'anchorOrigin':origins[rgb],'nativeTexelSupport':n})
 tables=[]
 for i,ref in enumerate(refs):
  target=[ref['anchorLab'][0]-gap,*ref['anchorLab'][1:]];eligible=range(i+1)
  low=min(eligible,key=lambda j:sum((x-y)**2 for x,y in zip(refs[j]['anchorLab'],target)));tables.append([low,low,i,i])
 model={**v3,'kind':'fixed-gap-native-palette-budget-candidate','status':'budget comparison only, no art choice','references':refs,'compactPaletteRGB8':[r['anchorRGB8']for r in refs],
  'perReferenceShadePaletteIndices':tables,'paletteColourBudget':N,'nativeLBounds':[lo,hi],'nativeBandWidthL':width,'fixedShadowTargetGapL':gap,
  'shadeRule':'same measured Lab-L shadow target for all budgets; nearest observed colour below anchor; Q0/1 lower and Q2/3 anchor',
  'intervalRule':v3['intervalRule'],'fitRule':'native equal-L coverage bands with actual observed OKLab medoid; no screen-colour mean'}
 (R/f'PALETTE_{N}.json').write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding='utf-8');summary.append({'budget':N,'shadowTargetGapL':gap,'nativeBandWidthL':width})
(R/'BUDGET_FIT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
