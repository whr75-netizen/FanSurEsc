from pathlib import Path
import base64,collections,hashlib,json,math
from pngio import read
R=Path(__file__).resolve().parent;B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34');load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=load(B/'source-export/bundle/prelight-source.json');frame=load(B/'source-export/bundle/frame-source-data.json');binding=load(B/'ribbon-path/PALETTE_V2_BINDING.json');packets=load(B/'ribbon-path/GEOMETRY_PACKETS.json');palette=load(R/'PALETTE_LEGACY.json')
assert source['sourceId']==frame['sourceId']==binding['sourceId']==palette['sourceId']
assert source['modelSHA256']==binding['modelSHA256']==palette['modelSHA256']
assert sha(B/'ribbon-path/GEOMETRY_PACKETS.json')==binding['geometryPacketsSHA256']
families=set(palette['originalMaterialIds']);textures={};hist=collections.Counter();origin={};cache={}
def lin(x):
 x/=255;return x/12.92 if x<=.04045 else((x+.055)/1.055)**2.4
def enc(x):return round(255*(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055))
def lab(rgb):
 if rgb not in cache:
  r,g,b=map(lin,rgb);l=(.4122214708*r+.5363325363*g+.0514459929*b)**(1/3);m=(.2119034982*r+.6806995451*g+.1073969566*b)**(1/3);s=(.0883024619*r+.2817188376*g+.6299787005*b)**(1/3)
  cache[rgb]=(.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s)
 return cache[rgb]
for m in source['materials']:
 if m['materialId']not in families:continue
 p=R.parent/'model-source'/f"image-{m['imageId']}.png";assert sha(p)==m['imageSHA256'];assert m['baseColorFactorLinear']==[1,1,1,1];w,h,rgba=read(p);textures[m['materialId']]=(w,h,rgba)
 for y in range(h):
  for x in range(w):
   rgb=tuple(rgba[(y*w+x)*4:(y*w+x)*4+3]);hist[rgb]+=1;origin.setdefault(rgb,{'materialId':m['materialId'],'imageId':m['imageId'],'x':x,'y':y,'imageSHA256':m['imageSHA256']})
n=sum(hist.values());s=[sum(w*lab(rgb)[j]for rgb,w in hist.items())for j in range(3)];chosen=min(hist,key=lambda rgb:(n*sum(v*v for v in lab(rgb))-2*sum(v*t for v,t in zip(lab(rgb),s)),rgb));constant={'RGB8':chosen,'RGBAlinear':[*(lin(v)for v in chosen),1],'origin':origin[chosen],
 'selectionRule':'exact observed native texel weighted OKLab medoid over all pixels of verified visible-hair material images, unit native-texel weights; arithmetic moments evaluate medoid cost, no RGB mean is output',
 'nativePixelCount':n,'nativeUniqueRGB8':len(hist),'chosenRGBNativeSupport':hist[chosen],'scope':'explicit diagnostic albedo override, not product default or claimed original uniform hair colour'}
mask=base64.b64decode(frame['hairMask']);cells=[];uvErrors=[]
for i,p in enumerate(packets):
 x,y=i%32,i//32;visible=bool(mask[(y*2*64+x*2)])
 assert visible==(p is not None)
 if not p:cells.append(None);continue
 assert p['role']in families
 for dy in range(2):
  for dx in range(2):assert mask[((y*2+dy)*64+x*2+dx)]
 # Independent original sampler check; source export is GPU half precision.
 w,h,rgba=textures[p['role']];u,v=p['uv'];xx=u*w-.5;yy=(1-v)*h-.5;x0,y0=math.floor(xx),math.floor(yy);fx,fy=xx-x0,yy-y0;sample=[0.,0.,0.]
 for dx,wx in [(0,1-fx),(1,fx)]:
  for dy,wy in [(0,1-fy),(1,fy)]:
   at=(((y0+dy)%h)*w+(x0+dx)%w)*4
   for k in range(3):sample[k]+=lin(rgba[at+k])*wx*wy
 uvErrors.append({'index':i,'maxRGB8Error':max(abs(enc(a)-enc(b))for a,b in zip(sample,p['baseRGBAlinear'][:3])),'maxLinearError':max(abs(a-b)for a,b in zip(sample,p['baseRGBAlinear'][:3]))})
 previous=binding['variants']['preserve'][i];q=sum(p['g']>=t for t in frame['thresholds']);assert previous is not None
 if not previous.get('unresolved'):assert previous['shade']==q
 cells.append({'index':i,'materialId':p['role'],'uv':p['uv'],'sourceRGBAlinear':p['baseRGBAlinear'],'g':p['g'],'Q':q,'chart':p['chart'],'primitive':p['primitive'],'depth':p['depth'],
  'originalFeatureUnknown':bool(previous.get('unresolved')),'sourceFamilyId':0,'sourcePolicy':'geometry-selected actual unlit source sample; no feature/ribbon resampling in either branch'})
context={'primarySourceId':source['sourceId'],'modelSHA256':source['modelSHA256'],'frame':frame['frame'],'packetSHA256':sha(B/'ribbon-path/GEOMETRY_PACKETS.json'),
 'frameJSON_SHA256':sha(B/'source-export/bundle/frame-source-data.json'),'sourceJSON_SHA256':sha(B/'source-export/bundle/prelight-source.json'),'paletteSHA256':sha(R/'PALETTE_LEGACY.json'),
 'geometryAndGPolicy':'same frozen geometry-selected frame95 samples for every branch; frame original centre g is not substituted','shaderGSource':'ActualIrradiance22 ambient+direct(normal,lights,shadow), then dot(E, Rec709); baseColor.rgb not multiplied into g',
 'shaderSHA256':sha(B.parent/'unity-compare/Author33DiffuseRamp.shader')}
data={'context':context,'bindingReceipt':{'sourceId':binding['sourceId'],'modelSHA256':binding['modelSHA256'],'packetSHA256':binding['geometryPacketsSHA256']},'width':32,'height':40,'displayWidth':64,'displayHeight':80,'cell':frame['cell'],'hairCells':frame['hairCells'],'thresholds':frame['thresholds'],'originalRGBA':frame['originalRGBA'],'hairMask':frame['hairMask'],'constant':constant,'cells':cells,
 'sourceFeaturePolicy':'known hair geometry mask all368; original feature unknown flags kept as metadata, no original-colour passthrough in diagnostic branch',
 'nativeSamplerCheck':{'samples':len(uvErrors),'maxRGB8Error':max(e['maxRGB8Error']for e in uvErrors),'maxLinearError':max(e['maxLinearError']for e in uvErrors),'errors':uvErrors}}
assert len([c for c in cells if c])==frame['hairCells']
(R/'INPUT.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');(R/'CONSTANT_SOURCE.json').write_text(json.dumps(constant,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'constant':constant,'nativeSamplerMaxRGB8Error':data['nativeSamplerCheck']['maxRGB8Error'],'QCounts':dict(collections.Counter(c['Q']for c in cells if c))},ensure_ascii=True))
