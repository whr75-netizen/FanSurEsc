"""Same measured colour budget; cover native L support rather than two distant banks."""
from pathlib import Path
import argparse,collections,hashlib,json,sys
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'colour-family'))
from pngio import read
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34\source-export\bundle')
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=B/'prelight-source.json');parser.add_argument('--images',type=Path,default=R.parent/'model-source');parser.add_argument('--family',type=Path,default=R/'SOURCE_FAMILY_INPUT.json');parser.add_argument('--output',type=Path,default=R/'NATIVE_COVERAGE_FIT.json');args=parser.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads(args.source.read_text(encoding='utf-8-sig'));family=json.loads(args.family.read_text(encoding='utf-8-sig'))
assert source['sourceId']==family['sourceId']and source['modelSHA256']==family['modelSHA256'],'Family metadata does not match original source/model; no fallback'
hist=collections.Counter();origin={};cache={}
def lab(rgb):
 if rgb not in cache:
  v=[x/255 for x in rgb];r,g,b=[x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4 for x in v]
  l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3);m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3);s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
  cache[rgb]=(.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s)
 return cache[rgb]
for m in source['materials']:
 if m['materialId'] not in family['materialIds']:continue
 imagepath=args.images/f"image-{m['imageId']}.png";assert sha(imagepath)==m['imageSHA256'],'Original image hash mismatch; no fallback'
 w,h,rgba=read(imagepath)
 for y in range(h):
  for x in range(w):
   rgb=tuple(rgba[(y*w+x)*4:(y*w+x)*4+3]);hist[rgb]+=1
   origin.setdefault(rgb,{'materialId':m['materialId'],'imageId':m['imageId'],'x':x,'y':y})
assert set(family['materialIds']).issubset({m['materialId']for m in source['materials']}),'Missing family source material'
N=family['paletteColourBudget'];assert isinstance(N,int)and N>1
lo=min(lab(r)[0]for r in hist);hi=max(lab(r)[0]for r in hist);width=(hi-lo)/N
bands=[{}for _ in range(N)]
for r,n in hist.items():bands[min(N-1,int((lab(r)[0]-lo)/width))][r]=n
refs=[]
for i,values in enumerate(bands):
 assert values,('empty native band',i)
 n=sum(values.values());s=[sum(count*lab(r)[j]for r,count in values.items())for j in range(3)]
 # Objective uses native support; output is always an actual texel, never the mean.
 rgb=min(values,key=lambda r:(n*sum(v*v for v in lab(r))-2*sum(v*t for v,t in zip(lab(r),s)),r))
 refs.append({'id':i,'anchorRGB8':rgb,'anchorOrigin':origin[rgb],'nativeBandLBounds':[lo+i*width,lo+(i+1)*width],
  'nativeTexelSupport':n,'anchorLab':lab(rgb),'selection':'observed full-OKLab medoid within equal-native-L-support band'})
result={'sourceId':source['sourceId'],'modelSHA256':source['modelSHA256'],'originalMaterialIds':family['materialIds'],'originalAppearanceGroupIds':family['appearanceGroupIds'],
 'references':refs,'nativeLBounds':[lo,hi],'nativeBandWidthL':width,'paletteColourBudget':N,
 'budgetRule':'same as existing palette-v2, not increased','fitRule':'equal width across measured native L support, then actual native OKLab medoid in each band; avoids uncovered large tone intervals',
 'sourceUsed':'full native original material images, no screen or lighting input','RGBMeanUsedAsOutput':False,
 'sourceJSON_SHA256':sha(args.source),'familyInput_SHA256':sha(args.family),'familyStatus':family['status']}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'budget':N,'nativeLBounds':[lo,hi],'bandWidthL':width,'colours':[r['anchorRGB8']for r in refs]}))
