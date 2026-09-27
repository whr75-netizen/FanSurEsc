"""One final technical delivery check. Visual quality remains the user's judgement."""
import collections,json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/artifacts/building35/details'
def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
errors=[]
manifest=read('production-manifest.json')
for a in manifest['assets']:
    receipt=json.loads((ROOT/a['receipt']).read_text())
    rgba=np.array(Image.open(ROOT/a['folder']/'native.png').convert('RGBA'))
    xyz=np.fromfile(ROOT/a['folder']/'positions.rgba32f',dtype='<f4').reshape(receipt['height'],receipt['width'],4)[::-1]
    if receipt['ppu']!=127 or not np.isfinite(xyz).all():errors.append(a['id']+': finite positions/common PPU')
    if not np.array_equal(rgba[...,3]/255.0>.1,xyz[...,3]>.5):errors.append(a['id']+': source/depth mismatch')
play=read('play-observation.json');build=read('unity-build.json')
for key in ['entryReached','wallBlocked','roofHiddenInside','roofRestoredOutside','depthPassConsistent','noDoublePixelation']:
    if not play[key]:errors.append(key)
for key in ['frameLeakPixels','roofLeakPixels','sourceDepthMismatches']:
    if play[key]!=0:errors.append(key)
if play['accessReached']!=3:errors.append('three affected routes')
if play['playerBefore']!=play['playerAfter'] or play['cameraBefore']!=play['cameraAfter']:errors.append('same live shell')
if build['instances']!=6 or play['nativeSurfaceCount']!=46:errors.append('six additive details')
def messages(name):
    obj=read(name)
    return collections.Counter(json.dumps(x,sort_keys=True) for x in obj['data']['logs'])
added=messages('console-after.json')-messages('console-before.json')
if added:errors.append('new console errors')
result={'status':'technical_pass' if not errors else 'technical_fail','errors':errors,
        'added_instances':build['instances'],'unchanged_approved_instances':20,'affected_routes':play['accessReached'],
        'added_console_errors':sum(added.values()),'art_status':'awaiting_user_observation',
        'limits':'API movement and imported depth/alpha checks; not keyboard, build, save/load, GPU depth equality or artistic approval.'}
(OUT/'delivery-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(bool(errors))
