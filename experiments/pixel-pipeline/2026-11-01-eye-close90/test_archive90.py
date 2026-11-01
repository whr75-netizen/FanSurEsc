"""No Unity calls, no writes, no full89 re-analysis required."""
from pathlib import Path
import hashlib,json
from test90 import main as regression
from validate_gpu90 import main as gpu
HERE=Path(__file__).resolve().parent
def main():
 manifest=HERE/'ARTIFACTS90.json'
 if manifest.exists():
  d=json.loads(manifest.read_text())
  for f in d['files']:
   path=HERE/f['path'];assert path.stat().st_size==f['bytes']and hashlib.sha256(path.read_bytes()).hexdigest()==f['SHA256'],f['path']
 r=regression(write=False);g=gpu(write=False);assert r['passed']==15 and g['changedNativePixels']==4 and g['outsideTargetChanged']==0
 print(json.dumps({'portableTests':r['passed'],'GPUFloatError':g['maxGPUExpectedError'],'changedNativePixels':g['changedNativePixels'],'outsideChanged':0,'otherUnresolvedPixels':g['otherUnresolved89Selections'],'productIntegrated':False},indent=2))
if __name__=='__main__':main()
