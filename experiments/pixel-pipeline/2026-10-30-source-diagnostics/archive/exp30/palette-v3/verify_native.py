from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'colour-family'))
from pngio import read
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34')
T=Path(r'C:\Users\15352\Desktop\작업폴더\아트검토\35_특징영역_공유경계후보\tone-boundary')
source=load(B/'source-export/bundle/prelight-source.json');model=load(R/'SHARED_NATIVE_PALETTE.json');binding=load(R/'BINDINGS.json');frame=load(B/'source-export/bundle/frame-source-data.json')
checks=[]
def check(name,yes):
 assert yes,name
 checks.append({'name':name,'pass':True})
textures={}
for m in source['materials']:
 if m['materialId']not in model['originalMaterialIds']:continue
 p=R.parent/'model-source'/f"image-{m['imageId']}.png";check('native image SHA material'+str(m['materialId']),sha(p)==m['imageSHA256']);textures[m['materialId']]=read(p)
for r in model['references']:
 o=r['anchorOrigin'];w,h,rgba=textures[o['materialId']];p=(o['y']*w+o['x'])*4
 check('palette texel RGB exact '+str(r['id']),list(rgba[p:p+3])==r['anchorRGB8'])
for name,v in binding['variants'].items():
 check(name+' all original Q(g) labels unchanged',all(r['shadeK']==sum(r['geometryG']>=t for t in frame['thresholds'])for r in v['rows']if r and not r.get('unresolved')))
 check(name+' exact358 resolved +10 unresolved +912 outside',sum(bool(r and not r.get('unresolved'))for r in v['rows'])==358 and sum(bool(r and r.get('unresolved'))for r in v['rows'])==10 and v['rows'].count(None)==912)
 for label in ['old','existing16','new','source']:
  w,h,out=read(R/f'{name}-{label}-1x.png');zw,zh,z=read(R/f'{name}-{label}-8x.png')
  check(name+' '+label+' exact integer8x',zw==w*8 and zh==h*8 and all(z[(y*zw+x)*4:(y*zw+x)*4+4]==out[((y//8)*w+x//8)*4:((y//8)*w+x//8)*4+4]for y in range(zh)for x in range(zw)))
check('original main binding not edited',binding['mainBindingSHA256']==sha(B/'ribbon-path/PALETTE_V2_BINDING.json'))
check('main geometry packets not edited',binding['packetSHA256']==sha(B/'ribbon-path/GEOMETRY_PACKETS.json'))
check('tone-boundary manifest not edited',load(R/'REPLAY_VERIFIED.json')['mainToneManifestSHA256']==sha(T/'MANIFEST.json'))
check('self-contained colour math is byte-exact unmodified v2 copy',sha(R/'palette_math.cjs')==sha(R.parent/'palette-v2/palette.cjs'))
files=['SHARED_NATIVE_PALETTE.json','SHARED_EXISTING16_ABLATION.json','NATIVE_COVERAGE_FIT.json','SOURCE_FAMILY_INPUT.json','BINDINGS.json','palette.cjs','palette_math.cjs','SUMMARY.json','EDGES.json','PIXEL_EVIDENCE.json']
result={'checks':checks,'passed':len(checks),'filesSHA256':{n:sha(R/n)for n in files},'scope':'native provenance and fixed-input pixel checks; no art, shape or temporal approval'}
(R/'NATIVE_VERIFIED.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'passed':len(checks)}))
