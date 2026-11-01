from pathlib import Path
import hashlib,json,zipfile
import numpy as np
from reader68 import plane
HERE=Path(__file__).resolve().parent
def main():
    checks=[]
    def ck(n,v):assert v,n;checks.append(n)
    a=json.loads((HERE/'ARTIFACTS96.json').read_text());ck('all archived bytes match manifest',all(hashlib.sha256((HERE/r['path']).read_bytes()).hexdigest()==r['SHA256']for r in a['files']))
    raw=zipfile.Path(zipfile.ZipFile(HERE/'RAW96.zip'));s=json.loads((HERE/'SUMMARY96.json').read_text());rows=json.loads((HERE/'LIVE_COMPARISON96.json').read_text())['rows']
    for row in rows:
        f=row['frame'];p=raw/f'frame-{f}';m=(p/'RAW_MANIFEST.json').read_bytes();ck(f'{f}: complete same source',hashlib.sha256(m).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text()and json.loads(m)['sourceId']==row['sourceId']);z=np.load(HERE/f'oracle/candidate-source-cache-actual96/frame{f}.npz')
        for i,name in enumerate(['colour','owner','depth']):
            h,v=plane(p/f'live96-final{i}.plane');ck(f'{f}/{name}: actual GPU result equals independently computed CPU',h['sourceId']==row['sourceId']and np.array_equal(v,z[name]));b=plane(p/(['native-final-rgba','native-final-owner','native-final-depth'][i]+'.plane'))[1];ck(f'{f}/{name}: original lid and outside scope preserved',np.array_equal(v[z['protected']],b[z['protected']])and np.array_equal(v[~z['scope']],b[~z['scope']]))
    ck('restored current Edit/input/dirty/native content',s['PlayExited']and s['nativeResourcesDirectExact']==47 and s['dirtyBefore']==s['dirtyAfter']==31 and s['publicStateDifferences']==[]and s['inputSameNativeIdAndJSON'])
    ck('RT count and globals restored',s['RTBefore']==s['RTAfter']==30 and not s['globalRestoreErrors'])
    ck('isolation remains explicit',s['product']==77 and s['liveSelectionNotReplay']and s['runtimeReadbacks']==0 and s['liveFinalCalledAtCapturedStatesOnly'])
    print(json.dumps({'passed':len(checks),'UnityCalls':0,'writes':0,'checks':checks},indent=2))
if __name__=='__main__':main()
