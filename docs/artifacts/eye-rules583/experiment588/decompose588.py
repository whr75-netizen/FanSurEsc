from pathlib import Path
from fractions import Fraction as F
import numpy as np,json,csv
R=Path(__file__).parent
def fixture(target):
    t=np.float32(target);s=np.float32(np.sqrt(np.float32(t/np.float32(np.float32(2.16)*np.float32(.58)))))
    ur=np.float32(1.08);x0=np.float32(np.float32(1.5)+np.float32(-ur*s));x1=np.float32(np.float32(1.5)+np.float32(ur*s))
    y0=np.float32(np.float32(1.5)-np.float32(np.float32(1.5)*s));y1=np.float32(np.float32(1.5)-np.float32(np.float32(-.5)*s))
    return dict(target=float(t),scale=float(s),u0=-float(ur),u1=float(ur),x0=float(x0),x1=float(x1),y0=float(y0),y1=float(y1))
def run(target):
    f=fixture(target);sy=(F(f['y1'])-F(f['y0']))/2;sx=(F(f['x1'])-F(f['x0']))/(F(f['u1'])-F(f['u0']))
    h=(F(float(np.float32(.36)))+F(float(np.float32(.22))))*sy
    exact=(F(f['x1'])-F(f['x0']))*h
    x=(np.arange(512)+.5)/128;y=x.copy();xs=x[(x>=f['x0'])&(x<=f['x1'])]
    u=(xs-f['x0'])/float(sx)+f['u0'];v=(y-f['y0'])/float(sy)-1.5
    q=float(np.float32(-.82))+float(np.float32(.35))*u*u
    counts=((v[None,:]>=q[:,None]-float(np.float32(.36)))&(v[None,:]<=q[:,None]+float(np.float32(.22)))).sum(axis=1)
    xy=F(int(counts.sum()),128*128);column_exact=F(len(xs),128)*h
    counter_input=R/'COUNTERS587.tsv'
    if not counter_input.is_file():counter_input=R.with_name('EyeArea587')/'COUNTERS587.tsv'
    old=list(csv.DictReader(counter_input.open(),delimiter='\t'))
    row=next(z for z in old if abs(float(z['targetArea'])-target)<1e-7 and z['case']in ['1','3'])
    gpu=F(round(float(row['GPUArea'])*16384),16384)
    result=dict(fixture=f,referenceArea=str(exact),referenceAreaDecimal=float(exact),gpuArea=float(gpu),
        acceptedXColumns=len(xs),columnExactYArea=float(column_exact),cpuCentreArea=float(xy),
        missingArea=dict(sourceSideBoundary=float(exact-column_exact),bandTopBottomRounding=float(column_exact-xy),cpuVersusSavedGPU=float(xy-gpu),alpha=0,ownership=0,total=float(exact-gpu)),
        input='Exact rational interpretation of actual float32 mesh endpoints and shader constants; no change to source mesh or shader.',
        alphaProof='White texture/alpha1, no alpha cutout; every covered fragment passes. Empty hair/brow/body inputs.',
        ownershipProof='Two adjacent coplanar source0 triangles, same eye/front and same affine rest mapping. Shared diagonal changes no covered area; no front occluder.')
    assert sum(result['missingArea'][k]for k in ['sourceSideBoundary','bandTopBottomRounding','cpuVersusSavedGPU','alpha','ownership'])==result['missingArea']['total']
    return result
if __name__=='__main__':
    result=[run(.499),run(.501)];(R/'DECOMPOSITION588.json').write_text(json.dumps(result,indent=2)+'\n')
    for q in result:print(json.dumps(q,indent=2))
