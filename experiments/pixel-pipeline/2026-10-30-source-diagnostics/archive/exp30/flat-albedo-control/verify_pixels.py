from pathlib import Path
import base64,hashlib,json
from pngio import read
R=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));data=load(R/'INPUT.json');results=load(R/'RESULTS.json');summary=load(R/'SUMMARY.json');original=base64.b64decode(data['originalRGBA']);mask=base64.b64decode(data['hairMask']);checks=[]
def check(name,yes):
 assert yes,name
 checks.append({'name':name,'pass':True})
for name,out in results['outputs'].items():
 w,h,rgba=read(R/(name+'-1x.png'));zw,zh,z=read(R/(name+'-8x.png'))
 check(name+' raw PNG exactly equals direct emitter',list(rgba)==out['pixels'])
 check(name+' outside mask and alpha preserved',rgba[3::4]==original[3::4]and all(rgba[i*4:i*4+4]==original[i*4:i*4+4]for i,m in enumerate(mask)if not m))
 check(name+' no AA/mixing within logical2x2',all(rgba[((y*2+dy)*w+x*2+dx)*4:((y*2+dy)*w+x*2+dx)*4+3]==bytes(out['rows'][y*32+x]['rgb'])for y in range(40)for x in range(32)if out['rows'][y*32+x]for dy in range(2)for dx in range(2)))
 check(name+' exact integer8x',zw==w*8 and zh==h*8 and all(z[(y*zw+x)*4:(y*zw+x)*4+4]==rgba[((y//8)*w+x//8)*4:((y//8)*w+x//8)*4+4]for y in range(zh)for x in range(zw)))
 if not out['settings'].get('legacyFallback'):check(name+' no off-recipe colours',summary[name]['offExpectedPaletteCells']==0)
origin=data['constant']['origin'];p=R.parent/'model-source'/f"image-{origin['imageId']}.png";w,h,rgba=read(p);at=(origin['y']*w+origin['x'])*4
check('constant exactly original native texel and image SHA',list(rgba[at:at+3])==data['constant']['RGB8']and hashlib.sha256(p.read_bytes()).hexdigest()==origin['imageSHA256'])
check('all source GPU/native sampler RGB8 errors at most1',data['nativeSamplerCheck']['maxRGB8Error']<=1)
for control in ['flat-unlit','flat-legacy','flat-distinct']:
 check(control+' fixed g/Q regions are identical',summary[control]['QRegionCount4']==11 and summary[control]['QRegionCount8']==8 and summary[control]['QSingleton4']==6)
existing=load(R/'CURRENT_PIPELINE_AUDIT.json');check('actual main colourRegion/Q still one RGB per label, featureDomain not confused',all(v['colourRegion_Q_to_RGB']['multiRGB']==0 and v['knownOffPaletteCells']==0 and not v['QErrorsAgainstFrozenGeometry']for v in existing.values()))
result={'checks':checks,'passed':len(checks),'scope':'saved-frame offline diagnostic; no claim about live Unity AA/composite/cache or temporal behaviour'};(R/'PIXEL_VERIFIED.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'passed':len(checks)}))
