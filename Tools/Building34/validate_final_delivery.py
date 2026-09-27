"""Validate actual source/depth/gameplay observations; never artistic approval."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
errors=[]
def require(ok,why):
    if not ok:errors.append(why)
cal=read('docs/artifacts/building34/calibration-oriented.json')
build=read('docs/artifacts/building34/unity-build.json')
obs=read('docs/artifacts/building34/play-observation.json')
require(len(build['objects'])==5,'five independent fixtures')
for row in build['objects']:
    require(row['rayMisses']==0,row['id']+' opaque source clipped')
    require(row['minY']>=-1e-4 and row['maxY']<build['roofHeight'],row['id']+' depth outside interior')
require(abs(build['ppu']-cal['ppu'])<.001,'shared native PPU')
for a in read('docs/artifacts/building34/native-summary.json')['assets']:
    p=ROOT/a['native_path']
    require(hashlib.sha256(p.read_bytes()).hexdigest()==a['native_sha256'],a['id']+' native data changed')
require(obs['playerBefore']==obs['playerAfter'],'same Player')
require(obs['cameraBefore']==obs['cameraAfter'],'same Camera')
for key in ['entryReached','wallBlocked','roofHiddenInside','roofRestoredOutside','closedRoof','depthPassConsistent','noDoublePixelation']:
    require(obs.get(key) is True,key)
require(obs.get('accessReached')==6,'six fixture access points')
# Read complete provider snapshots. Do not trust a manually supplied error count.
before=read('docs/artifacts/building34/console-window-before.json')
after=read('docs/artifacts/building34/console-window-after.json')
previous=before['payload']['data']; current=after['payload']['data']
require(before['capturedAt']<after['capturedAt'],'ordered Console observation interval')
require(previous['totalCount']==len(previous['logs']) and current['totalCount']==len(current['logs']),'complete Console snapshots')
signature=lambda row:json.dumps(row,sort_keys=True,ensure_ascii=False)
old=Counter(map(signature,previous['logs'])); new=Counter(map(signature,current['logs']))
require(not (old-new),'Console history retained')
added=sum((new-old).values())
require(added==0,'new errors within actual interior/exterior capture interval')
console_window={'before_utc':before['capturedAt'],'after_utc':after['capturedAt'],'retained_error_entries':current['totalCount'],'added_error_entries':added,'scope':'actual interior/exterior captures only; historical errors are retained, not zeroed','warning':'RunCommand reported opted-in volumetric Spot Lights outside visible additional-light set/local volume limit; this warning is retained.'}
require(obs.get('frameLeakPixels')==0,'alpha frame leakage')
require(obs.get('roofLeakPixels')==0,'opaque fixture above roof')
require(obs.get('pixelScale',0)>=1 and abs(obs['pixelScale']-round(obs['pixelScale']))<.001,'integer source texel display')
for path in obs.get('screenshots',[]):require((ROOT/path).is_file(),'missing '+path)
require({'play-interior.png','play-exterior.png','overview-interior.png','overview-exterior.png'}.issubset({Path(p).name for p in obs.get('screenshots',[])}),'actual interior and exterior captures')
require(cal['ppu']==127 and all(a.get('mirrorU')==(a['id']!='island') for a in cal['assets']),'source facing calibration')
require(obs.get('sourceDepthMismatches')==0,'source and depth masks agree')
result={'technical_delivery':not errors,'scope':'one authored interior, source preservation, geometry/depth and actual gameplay observations','artistic_approval':'not claimed','console_window':console_window,'errors':errors}
(ROOT/'docs/artifacts/building34/delivery-final-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False));sys.exit(2 if errors else 0)
