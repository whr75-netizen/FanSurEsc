"""Final bounded technical acceptance. Does not score art or infer user approval."""
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DIR=ROOT/'docs/artifacts/building35'

def main():
    result={'status':'failed','checks':{},'art_status':'requires_user_observation'}
    try:
        read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
        built=read(DIR/'unity-build.json'); played=read(DIR/'play-observation.json')
        assert built['instances']>=18, 'Role-linked object instances missing'
        assert built['commonPpu']==127 and built['sourceDepthMismatches']==0
        assert played['playerBefore']==played['playerAfter'] and played['cameraBefore']==played['cameraAfter']
        assert played['accessReached']>=6 and played['wallBlocked']
        assert played['roofHiddenInside'] and played['roofRestoredOutside']
        assert played['frameLeakPixels']==0 and played['sourceDepthMismatches']==0
        assert played['noDoublePixelation']
        manifest=read(DIR/'production-manifest.json')
        for asset in manifest['assets']:
            r=read(ROOT/asset['receipt'])
            assert r['ppu']==127 and r['opaque_pixels']>0
            assert all(f['reprojection_residual']<1e-4 for f in r['faces'])
            assert (ROOT/asset['folder']/'native.png').exists()
        # Compare actual complete console snapshots; caller supplied zero is never evidence.
        from collections import Counter
        before=read(DIR/'console-before.json');after=read(DIR/'console-after.json')
        def logs(obj):
            if isinstance(obj,dict):
                if isinstance(obj.get('logs'),list): return obj['logs']
                for val in obj.values():
                    got=logs(val)
                    if got is not None:return got
            return None
        a,b=logs(before),logs(after)
        assert a is not None and b is not None,'Missing console logs'
        key=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False)
        ca,cb=Counter(map(key,a)),Counter(map(key,b))
        assert not(ca-cb),'Console history unexpectedly removed'
        assert not(cb-ca),'New console errors require investigation'
        result.update(status='technical_pass',checks={'instances':built['instances'],'asset_count':len(manifest['assets']),
            'routes':played['accessReached'],'new_errors':len(list((cb-ca).elements()))})
    except Exception as e:
        result['error']=str(e)
    (DIR/'delivery-result.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result));return 0 if result['status']=='technical_pass' else 2

if __name__=='__main__':sys.exit(main())
