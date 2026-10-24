from pathlib import Path
import sys,json,time
import numpy as np
R=Path(__file__).parent
sys.path.insert(0,str(R.with_name('EyeArea585')))
from geometry_oracle585 import Frame,TEXTURES
from coverage588 import Kernel,Plane,point,fit,area

def main():
    start=time.perf_counter()
    f=Frame(0,R.with_name('EyeFollow584')/'Runtime584/OneCase2',R.with_name('EyeArea585')/'Runtime585/Geometry2')
    print('Existing actual pose loaded; no Unity invocation',flush=True)
    result=[]
    for x,y in f.possible_cells():
        cell=(point(x,y),point(x+1,y),point(x+1,y+1),point(x,y+1))
        ix=np.flatnonzero(f.rendered&(f.box[:,0,0]<=x+1)&(f.box[:,1,0]>=x)&(f.box[:,0,1]<=y+1)&(f.box[:,1,1]>=y))
        rows=[];k=Kernel()
        for t in ix:
            tri=tuple(point(*p)for p in f.xy[t]);poly=k.overlap(tri,cell)
            if not area(poly):continue
            tu=fit(tri,f.v[t,:,7]);tv=fit(tri,f.v[t,:,8]);uv=np.array([[float(tu.at(p)),float(tv.at(p))]for p in poly])
            # Two extra texel taps are deliberately included: this is a constant
            # endpoint certificate, not an approximate alpha boundary solver.
            a=TEXTURES[int(f.mi[t])]['alpha'];h,w=a.shape
            lo=uv.min(axis=0);hi=uv.max(axis=0)
            xs=np.arange(int(np.floor(lo[0]*w-.5))-2,int(np.floor(hi[0]*w-.5))+4)%w
            ys=np.arange(int(np.floor((1-hi[1])*h-.5))-2,int(np.floor((1-lo[1])*h-.5))+4)%h
            taps=a[np.ix_(ys,xs)];amin=float(taps.min());amax=float(taps.max())
            mode=int(f.mode[t]);scale=float(f.alpha[t]);cut=float(f.cut[t]);passed=True if mode==0 else False if amax*scale<cut and mode==1 or amax*scale<6.103515625e-5 and mode==2 else True if mode==1 and amin*scale>=cut else True if mode==2 and amin==amax and amin*scale>=6.103515625e-5 else None
            rows.append(dict(triangle=int(t),layer=int(f.s[t]),primitive=int(f.prim[t]),material=int(f.mi[t]),front=bool(f.front[t]),
                area=float(area(poly)),alphaMin=amin,alphaMax=amax,mode=mode,colorAlpha=scale,cutoff=cut,passed=passed,
                UVRange=[lo.tolist(),hi.tolist()],extraTexelHalo=2))
        result.append(dict(cell=[int(x),int(y)],triangles=rows,hairMETA=f.cells[x,y,'HairMETA'].tolist()))
        print(json.dumps(dict(cell=[int(x),int(y)],triangles=len(rows),unknown=sum(q['passed']is None for q in rows),perLayer={str(s):[sum(q['layer']==s and q['passed']is True for q in rows),sum(q['layer']==s and q['passed']is None for q in rows)]for s in [0,1,2,3,5,6]})),flush=True)
    out=dict(sourceCase=2,sourceFrame=0,pose='Stored actual yaw127.000046 Walk phase.70000434',rows=result,seconds=time.perf_counter()-start,
        scope='Stored real projected triangles/materials; alpha endpoint classification from source texture bytes with halo, not yet live GPU certificate.')
    (R/'INPUT_INVENTORY589.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
