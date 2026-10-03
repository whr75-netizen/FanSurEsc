"""Consume actual native display observations; do not infer artistic acceptance."""
import argparse, hashlib, json, math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/artifacts/building37'
RUN=BASE/'R6'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b): return isinstance(a,(int,float)) and not isinstance(a,bool) and math.isfinite(a) and abs(a-b)<.01
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=['representative','final'],required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args()
    if a.output.exists(): raise FileExistsError('Preserve existing evidence')
    errors=[]; evidence={}
    def check(ok,code,detail=''):
        if not ok: errors.append({'code':code,'detail':detail})
    try:
        manifest=read(BASE/'slices/manifest.json'); cells={c['id']:c for c in manifest['cells'] if c['role']=='object'}
        check(len(cells)==18,'SOURCE_SET')
        check(sha(BASE/'native-final/native.png')==manifest['native_sha256'],'CANONICAL_CHANGED')
        for c in cells.values():
            p=Path(c['output']); asset=ROOT/'Assets/Art/NativeSheet37'/f"{c['id']}.png"
            check(sha(p)==sha(asset)==c['sha256'],'SOURCE_CHANGED',c['id'])
        plan=read(RUN/'support-plan.json'); q=plan['displayMultiplier']
        check(q>=1 and q<=6 and close(plan['ppu'],127/q),'DISPLAY_DENSITY')
        if a.phase=='representative':
            report=read(RUN/'experiment.json'); samples=report['samples']
            check(report['playMode'] and report['scene']=='Assets/Scenes/GameMap1.unity','ACTUAL_PLAY')
            check(close(report['cameraPitch'],30) and close(report['cameraYaw'],350),'CAMERA')
            check(close(report['pixelScale'],q) and close(report['ppu'],plan['ppu']),'PIXEL_SCALE')
            check({s['id'] for s in samples}=={'stock_shelf','detail_clock'} and len(samples)==2,'REPRESENTATIVES')
            for s in samples:
                c=cells[s['id']]; check([s['width'],s['height']]==c['canvas_px'],'SAMPLE_DIMENSIONS',s['id'])
                check(s['roofOverflowTexels']==0,'ROOF_OVERFLOW',s['id'])
                for key,expected in [('screenU',[q,0]),('screenV',[0,q])]: check(all(close(x,y) for x,y in zip(s[key],expected)),'TEXEL_BASIS',s['id'])
            paths=['support-plan.json','experiment.json','play-interior.png','overview-interior.png']
        else:
            binding=read(RUN/'binding.json'); live=read(RUN/'live.json'); outside=read(RUN/'live-outside.json'); obs=read(RUN/'final/play-observation.json')
            check(len(binding['bindings'])==len(live['samples'])==26,'ALL_BINDINGS')
            check(live['playMode'] and live['orthographic'],'ACTUAL_CAMERA')
            check(close(live['cameraPitch'],30) and close(live['cameraYaw'],350),'CAMERA')
            check(live['playerEntityId']==outside['playerEntityId'] and live['cameraEntityId']==outside['cameraEntityId'],'RUNTIME_IDENTITY')
            check(obs['roofHiddenInside'] and obs['roofRestoredOutside'],'ROOF_VISIBILITY')
            for b in binding['bindings']:
                for field in ['entityId','position','rotation','scale','collider']:
                    check(b['before'][field]==b['after'][field],'PRESERVED_'+field,b['instance'])
            shared={}
            for s in live['samples']:
                check(s['rgbaMismatches']==0,'LIVE_RGBA',s['instance']); check(s['boundsOverflowCorners']==0,'LIVE_BOUNDS',s['instance'])
                check([s['width'],s['height']]==cells[s['asset']]['canvas_px'],'LIVE_DIMENSIONS',s['instance'])
                for key,expected in [('screenU',[q,0]),('screenV',[0,q])]: check(all(close(x,y) for x,y in zip(s[key],expected)),'LIVE_TEXEL_BASIS',s['instance'])
                pair=(s['mesh'],s['material']); check(s['asset'] not in shared or shared[s['asset']]==pair,'SHARED_ASSET',s['instance']); shared[s['asset']]=pair
            check(len(shared)==18,'SHARED_COUNT')
            paths=['binding.json','live.json','live-outside.json','final/play-interior.png','final/play-exterior.png','final/overview-interior.png','final/overview-exterior.png','final/play-observation.json']
        for name in paths:
            p=RUN/name; evidence[name]={'sha256':sha(p)}
            if p.suffix=='.png':
                with Image.open(p) as im: evidence[name]['dimensions']=list(im.size); im.verify()
        evidence['q']=q; evidence['canonical_sha256']=manifest['native_sha256']
    except (OSError,KeyError,ValueError,TypeError) as e: errors.append({'code':'MISSING_OR_INVALID_OBSERVATION','detail':str(e)})
    result={'scope':a.phase,'exit_code':2 if errors else 0,'failures':errors,'evidence':evidence,'artApprovalClaimed':False,
            'unverified':['Handheld keyboard traversal (unchanged colliders reuse prior evidence)','Photorealistic/volumetric occlusion: representation is 2D planar art','Exact generated shape and semantic details versus physical diagram']}
    if a.phase=='representative' and not errors:
        result.update(planHash=sha(RUN/'support-plan.json'),experimentHash=sha(RUN/'experiment.json'),authoringCodeHash=sha(ROOT/'Assets/Editor/NativeSheetDisplay36.cs'))
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result,ensure_ascii=False)); return result['exit_code']
if __name__=='__main__': raise SystemExit(main())
