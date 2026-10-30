from pathlib import Path
import base64,hashlib,json
from pngio import read
R=Path(__file__).resolve().parent;load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34\source-export\bundle');source=load(B/'prelight-source.json');frame=load(B/'frame-source-data.json');bindings=load(R/'BUDGET_BINDINGS.json');expected=load(R/'EXPECTED_PIXELS.json');original=base64.b64decode(frame['originalRGBA'])
def check(name,yes):
 assert yes,name
 checks.append({'name':name,'pass':True})
textures={}
for m in source['materials']:
 if m['materialId']not in [11,12,13]:continue
 p=R.parent/'model-source'/f"image-{m['imageId']}.png";check('source image SHA '+str(m['materialId']),sha(p)==m['imageSHA256']);textures[m['materialId']]=read(p)
for N in [16,32,64]:
 model=load(R/f'CONSTRAINED_{N}.json')
 check(str(N)+' actual native colours',all(list(textures[r['anchorOrigin']['materialId']][2][(r['anchorOrigin']['y']*textures[r['anchorOrigin']['materialId']][0]+r['anchorOrigin']['x'])*4: (r['anchorOrigin']['y']*textures[r['anchorOrigin']['materialId']][0]+r['anchorOrigin']['x'])*4+3])==r['anchorRGB8']for r in model['references']))
for key,variants in bindings['variants'].items():
 for name,rows in variants.items():
  eligible={r['index']for r in rows if r and not r.get('unresolved')};w,h,out=read(R/f'{name}-{key}-1x.png');zw,zh,z=read(R/f'{name}-{key}-8x.png')
  check(name+key+' populations358/10/912',len(eligible)==358 and sum(bool(r and r.get('unresolved'))for r in rows)==10 and rows.count(None)==912)
  check(name+key+' alpha/external/unknown unchanged',out[3::4]==original[3::4]and all(out[p:p+4]==original[p:p+4]for y in range(h)for x in range(w)if y//2*32+x//2 not in eligible for p in [(y*w+x)*4]))
  check(name+key+' independent PNG fixture',list(out)==expected[key][name])
  check(name+key+' exact nearest8x',zw==w*8 and zh==h*8 and all(z[(y*zw+x)*4:(y*zw+x)*4+4]==out[((y//8)*w+x//8)*4:((y//8)*w+x//8)*4+4]for y in range(zh)for x in range(zw)))
check('feature domain IDs unchanged all budgets',load(R/'SOURCE_DOMAIN_MAP.json')['unchangedAcrossAllBudgets'])
frag=load(R/'FRAGMENT_AUDIT.json');check('113 is additional not total',frag['v3']['preserve']['additionalVsV2']==113 and frag['v3']['preserve']['totalVisibleSameAQEdges']==140)
result={'checks':checks,'passed':len(checks),'scope':'fixed frame pixel/source contract only, not art/temporal approval'};(R/'PIXEL_VERIFIED.json').write_text(json.dumps(result,indent=2));print(json.dumps({'passed':len(checks)}))
