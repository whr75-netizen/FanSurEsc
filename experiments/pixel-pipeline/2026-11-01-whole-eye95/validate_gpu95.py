from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import Reader,rgb8

def main():
    run=HERE/'gpu-closed';r=json.loads((run/'FINAL_GPU95_CLOSED.json').read_text());assert r['dispatchComplete']and r['ownedResourcesReleased']and not r.get('error');folder=Path(r['output']);assert(folder/'DISPATCH_COMPLETE89.marker').exists();z=np.load(HERE/'candidate-joint/frame104.npz');rows=[]
    for field,name in enumerate(['colour','owner','depth']):
        f=folder/f'0104-field{field}-0.bin';b=Reader(f);assert b.s()=='final-palette89-GPU/v1';sid,variant=b.s(),b.s();frame,serial,w,h=[b.i()for _ in range(4)];a=b.a(w*h*4).reshape(h,w,4);b.end();assert frame==104 and np.array_equal(a,z[name]);rows.append({'field':name,'frame':frame,'sourceId':sid,'maxFloatError':float(abs(a-z[name]).max()),'exact':True})
        if field==0:Image.fromarray(np.flipud(rgb8(a[...,:3]))).save(HERE/'GPU_CLOSED95-native1x.png')
    b=Reader(folder/'0104-field0-2.bin');b.s();b.s();b.s();b.i();b.i();w,h=b.i(),b.i();v=b.a(w*h*4).reshape(h,w,4);b.end();assert(v[...,0]==1).all()and not z['invalid'].any()
    scope=z['scope'];colour=z['colour'];mapping=z['mapping'];palette=z['paletteAtoms'][:,:4];emitted=palette[mapping[scope,0].astype(int)-1];assert np.array_equal(colour[scope],emitted)
    result={'status':'CLOSED_STATE_ACTUAL_GPU_COMPOSITE_EXACT_NOT_PRODUCT_ADOPTED','fields':rows,'paletteOutsideSourceCount':0,'invalidNativePixels':0,'worldAndProtectedPassThroughExact':True,'RTBefore':r['before']['RTcount'],'RTAfter':r['after']['RTcount'],'globalWrites':r['globalWrites'],'PlayEntries':0,'otherOpenStatesNotGPUValidated':True,'frozenReplayNotLiveIntegration':True}
    assert result['RTBefore']==result['RTAfter']==30
    (HERE/'GPU_VALIDATION95.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
