"""Validate only the metric tray correction; reuse prior unaffected movement evidence."""
import argparse,collections,json
from pathlib import Path
import numpy as np
from PIL import Image

parser=argparse.ArgumentParser();parser.add_argument('--dir',default='docs/artifacts/building35/tray-size-correction');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/args.dir
read=lambda name:json.loads((OUT/name).read_text(encoding='utf-8-sig'))
errors=[]; manifest=read('production-manifest.json')
for asset in manifest['assets']:
    r=json.loads((ROOT/asset['receipt']).read_text())
    rgba=np.array(Image.open(ROOT/asset['folder']/'native.png').convert('RGBA'))
    xyz=np.fromfile(ROOT/asset['folder']/'positions.rgba32f',dtype='<f4').reshape(r['height'],r['width'],4)[::-1]
    if not np.array_equal(rgba[...,3]>.1*255,xyz[...,3]>.5):errors.append('mask')
    if r['ppu']!=127 or not np.isfinite(xyz).all():errors.append('density/positions')
    if 'fruit_count' in r and (r['minimum_fruit_centre_distance_m']<r['fruit_diameter_m']-1e-7 or r['fruit_sphere_top_y_m']>r['collider_size_xyz_m'][1]):errors.append('fruit physical bounds')
p=read('play-observation.json');b=read('unity-build.json')
for k in ['frameLeakPixels','roofLeakPixels','sourceDepthMismatches']:
    if p[k]!=0:errors.append(k)
if b['instances']!=3 or b['assetTypes']!=1:errors.append('existing three trays')
if p['pixelScale']!=1 or not p['noDoublePixelation']:errors.append('native screen pixel mapping')
if p['playerBefore']!=p['playerAfter'] or p['cameraBefore']!=p['cameraAfter']:errors.append('same shell objects')
def logs(file):return collections.Counter(json.dumps(x,sort_keys=True) for x in read(file)['data']['logs'])
before=logs('console-before.json');after=logs('console-after.json');new=after-before
if new or before-after:errors.append('console changed')
result={'status':'technical_pass' if not errors else 'technical_fail','errors':errors,
        'instances_changed':3,'new_console_errors':sum(new.values()),'reused_routes':'docs/artifacts/building35/details/play-observation.json',
        'art_status':'awaiting_user_observation','scope':'Actual imported sources/depth/native screen mapping; movement not rerun for smaller same-position colliders; not perfect art or 3D fruit proof.'}
(OUT/'delivery-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False));raise SystemExit(bool(errors))
