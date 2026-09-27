"""Validate actual source/depth/gameplay observations; never artistic approval."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
errors=[]
def require(ok,why):
    if not ok:errors.append(why)
cal=read('docs/artifacts/building34/calibration.json')
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
require(obs.get('newErrors')==0,'new Console errors')
require(obs.get('frameLeakPixels')==0,'alpha frame leakage')
require(obs.get('roofLeakPixels')==0,'opaque fixture above roof')
require(obs.get('pixelScale',0)>=1 and abs(obs['pixelScale']-round(obs['pixelScale']))<.001,'integer source texel display')
for path in obs.get('screenshots',[]):require((ROOT/path).is_file(),'missing '+path)
require(len(obs.get('screenshots',[]))>=2,'interior/exterior actual captures')
result={'technical_delivery':not errors,'scope':'one authored interior, source preservation, geometry/depth and actual gameplay observations','artistic_approval':'not claimed','errors':errors}
(ROOT/'docs/artifacts/building34/delivery-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False));sys.exit(2 if errors else 0)
