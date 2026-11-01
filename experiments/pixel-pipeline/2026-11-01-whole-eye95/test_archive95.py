"""Read-only archive recheck; no Unity, Play, extraction, file writes or UI."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
try:from reader68 import Reader,plane
except ImportError:
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'apply-capture66'))
    from analyse_capture68 import Reader,plane
HERE=Path(__file__).resolve().parent

def main():
    checks=[]
    def ck(name,v):assert v,name;checks.append(name)
    manifest=json.loads((HERE/'ARTIFACTS95.json').read_text())
    ck('selected artifact SHA256 exact',all(hashlib.sha256((HERE/x['path']).read_bytes()).hexdigest()==x['SHA256']for x in manifest['files']))
    summary=json.loads((HERE/'SUMMARY95.json').read_text());raw=zipfile.Path(zipfile.ZipFile(HERE/'RAW95.zip'));gpu=zipfile.Path(zipfile.ZipFile(HERE/'GPU95.zip'))
    result=json.loads((HERE/'RESULT95-source-cache-audit.json').read_text())
    for row in result['frames']:
        f=row['frame'];p=raw/f'frame-{f}';m=(p/'RAW_MANIFEST.json').read_bytes();ck(f'{f}: raw completion and source',hashlib.sha256(m).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text()and json.loads(m)['sourceId']==row['sourceId'])
        planes=[x for x in p.iterdir()if x.name.endswith('.plane')];ck(f'{f}:110 finite same-frame planes',len(planes)==110 and all((lambda h,a:h['sourceId']==row['sourceId']and h['frameIndex']==f and np.isfinite(a).all())(*plane(x))for x in planes))
        z=np.load(HERE/f'candidate-source-cache-audit/frame{f}.npz')
        for channel,name,base in [(0,'colour','base'),(1,'owner','baseOwner'),(2,'depth','baseDepth')]:
            r=Reader(gpu/f'{f:04d}-field{channel}-0.bin');ck(f'{f}/{name}:GPU header',r.s()=='final-palette89-GPU/v1');sid,v=r.s(),r.s();frame,serial,w,h=[r.i()for _ in range(4)];a=r.a(w*h*4).reshape(h,w,4);r.end();ck(f'{f}/{name}:actual GPU exact',sid==row['sourceId']and frame==f and np.array_equal(a,z[name]))
            scope=z['scope'];ck(f'{f}/{name}:finite source table and native protection',np.array_equal(a[scope],z['paletteAtoms'][:,channel*4:channel*4+4][z['mapping'][scope,0].astype(int)-1])and np.array_equal(a[z['protected']],z[base][z['protected']]))
        ck(f'{f}: no invalid or missing output',not z['invalid'].any()and not z['missing'].any())
    ck('all restoration checks exact',summary['nativeExact']==summary['nativeTotal']==47 and not summary['publicDifferences']and summary['dirtyBefore']==summary['dirtyAfter']==31 and not summary['newConsoleErrors'])
    ck('retained product, no live integration claim',summary['productDefault']==77 and summary['AssetsModified']==0 and summary['coldTieRemainsUndecided'])
    print(json.dumps({'passed':len(checks),'UnityCalls':0,'writes':0,'product':77,'checks':checks},indent=2))

if __name__=='__main__':main()
