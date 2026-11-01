"""Recover the observed canonical projective map; project actual native ring.

No eye size target or design form is introduced. The reference is the existing
registered native source skin-ring upper arc, evaluated in this captured pose.
It is NOT automatically the native lash pigment contour. Their agreement is
tested, never inferred from sharing an eye ID.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent
if '--direct' in sys.argv:H=H/'direct'
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer,font
from analyse_capture68 import Reader,plane

def mesh(path):
    r=Reader(path);assert r.s()=='aux-mesh67/v1';identity=r.identity();matrix=r.mat()
    points=r.a(r.i()*3).reshape(-1,3);r.a(r.i()*3);uv=r.a(r.i()*2).reshape(-1,2)
    indices=[r.a(r.i(),'<i4').reshape(-1,3)for _ in range(r.i())];r.end()
    return identity,matrix,points,uv,indices

def apply(H,points):
    out=np.column_stack([points,np.ones(len(points))])@H.T
    return out[:,:2]/out[:,2:3]

def fit_homography(source,target):
    centre=source.mean(0);scale=np.max(np.ptp(source,axis=0))
    q=(source-centre)/scale;x,y=q.T;u,v=target.T;zero=np.zeros(len(q));one=np.ones(len(q))
    A=np.stack([np.column_stack([x,y,one,zero,zero,zero,-u*x,-u*y]),np.column_stack([zero,zero,zero,x,y,one,-v*x,-v*y])],axis=1).reshape(-1,8)
    value=np.linalg.lstsq(A,target.reshape(-1),rcond=None)[0]
    P=np.r_[value,1].reshape(3,3);N=np.array([[1/scale,0,-centre[0]/scale],[0,1/scale,-centre[1]/scale],[0,0,1.]])
    return P@N

def upper_arc(row):
    q=np.asarray(row['authoredParent']);n=len(q);left=int(np.argmin(q[:,0]));right=int(np.argmax(q[:,0]))
    chains=[]
    for direction in (1,-1):
        chain=[];i=left
        for _ in range(n+1):
            chain.append(i)
            if i==right:break
            i=(i+direction)%n
        p=q[chain];w=np.linalg.norm(np.diff(p,axis=0),axis=1)
        score=float(np.dot(w,(p[:-1,1]+p[1:,1])*.5)/w.sum());chains.append((score,chain))
    return min(chains,key=lambda a:a[0])[1]

def intersects(a,b,x,y):
    lo=0.;hi=1.;delta=b-a
    for axis,start in enumerate((x,y)):
        if delta[axis]==0:
            if not start<=a[axis]<=start+1:return False
        else:
            t0=(start-a[axis])/delta[axis];t1=(start+1-a[axis])/delta[axis]
            lo=max(lo,min(t0,t1));hi=min(hi,max(t0,t1))
    return hi>=lo

def main():
    state=load(sorted(H.glob('STATE102-*'))[-1]);reg=load(R/'native-feature89/REGISTRATION89.json');results=[]
    board=Image.new('RGB',(1100,700),'#20252c');draw=ImageDraw.Draw(board)
    draw.text((20,12),'105 · 실제 native upper arc와 안검 색소의 대응 검사',font=font(24),fill='white')
    for j,e in enumerate(state['sequencePackets']):
        p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');identity,model,points,uv,indices=mesh(p/'current-face105.mesh')
        assert identity['sourceId']==m['sourceId']
        w,h=m['forward102']['canonicalSize'];a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);vis=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
        head=np.array(m['headMatrix105']).reshape(4,4,order='F');world=np.column_stack([points,np.ones(len(points))])@model.T
        currentHead=world@np.linalg.inv(head).T;rows=[]
        for row in reg['eyes']:
            eye=row['eye'];q=currentHead@np.array(row['nativeToAuthoredProjection'])
            source=[];target=[]
            for y,x in np.argwhere((a[3,1,:,:,0]>0)&(np.rint(a[3,1,:,:,2])==eye)):
                primitive=int(round(float(a[3,3,y,x,2])))-1;ids=indices[6][primitive]
                A=(uv[ids[1:]]-uv[ids[0]]).T.astype(float)
                if abs(np.linalg.det(A))<1e-14:continue
                bc=np.linalg.solve(A,a[3,3,y,x,:2]-uv[ids[0]])
                pos=np.array([1-bc.sum(),*bc])@q[ids]
                source.append(pos);target.append([(x+.5)/4,(y+.5)/4])
            source=np.asarray(source);target=np.asarray(target)
            fitted=fit_homography(source[::2],target[::2])
            if 'existingEyeInverse105'in m:
                inverse=np.array(next(x for x in m['existingEyeInverse105']if x['eye']==eye)['inverseHomography']).reshape(4,4,order='F')
                inverse[3,3]=1;forward=np.linalg.inv(inverse)[:3,:3]
                info=m['forward102']['nativeRegistration'];offset=np.array(info['anchor'])+np.array(info['bounds'][:2])
                Hmap=np.array([[1,0,-offset[0]],[0,1,-offset[1]],[0,0,1.]])@forward
                mapSource='direct existing public eyeInverse, exact Forward96 embedding/inverse; source contract, not fitted'
            else:Hmap=fitted;mapSource='diagnostic UV reconstructed homography; direct map missing'
            pred=apply(Hmap,source)
            error=np.linalg.norm(pred-target,axis=1);valid=float(error.max())<=5e-4
            # First capture has only diagnostic numerical recovery. The direct
            # capture uses existing public transforms as the curve reference;
            # UV sample reprojection is an independent agreement check. A failed
            # check remains failed rather than increasing the .0005px bound.
            arcIds=np.array(row['nativeRingVertexIds'])[upper_arc(row)];curve=apply(Hmap,q[arcIds])
            logical=np.zeros((h//4,w//4),bool)
            for y in range(h//4):
                for x in range(w//4):
                    logical[y,x]=any(intersects(aa,bb,x,y)for aa,bb in zip(curve,curve[1:]))
            support=vis[3,:,:,0]*((np.rint(a[3,1,:,:,2])==eye))
            area=support.reshape(h//4,4,w//4,4).sum((1,3));supported=logical&(area>0)
            result={'eye':eye,'numericMapValidated':valid,'mapSource':mapSource,'sampleCount':len(source),'heldOutMaxErrorLogicalPixels':float(error[1::2].max()),
                    'directVsFittedSamplesMaxPixels':float(np.linalg.norm(pred-apply(fitted,source),axis=1).max()),
                    'allSampleMaxErrorLogicalPixels':float(error.max()),'reference':'existing registered native skin-ring upper arc, evaluated source mesh; not yet an authored lash-colour contour',
                    'nativeUpperArcVertexIds':arcIds.tolist(),'canonicalCurve':curve.tolist(),'curveTouchedCells':np.argwhere(logical)[:,::-1].tolist(),
                    'sameCellLidPigmentSupported':np.argwhere(supported)[:,::-1].tolist(),'curveCellsWithoutLidPigment':np.argwhere(logical&~supported)[:,::-1].tolist(),
                    'nativeSupportAlphaOnCurveCells':area[logical].tolist()}
            rows.append(result)
            if valid:
                origin=np.array([30+eye*330,110+j*185]);scale=14
                for y,x in np.argwhere(area>0):
                    level=int(min(1,area[y,x]/16)*255);xx,yy=origin+np.array([x,y])*scale
                    draw.rectangle([int(xx),int(yy),int(xx+scale-1),int(yy+scale-1)],fill=(level,level,level))
                pts=[tuple(origin+v*scale)for v in curve];draw.line(pts,fill='#ffc95b',width=2)
                draw.text((int(origin[0]),int(origin[1]-35)),f'Close {m["motion82"]["requestedClose"]} · eye {eye}',font=font(18),fill='white')
        results.append({'frame':e['frame'],'sourceId':m['sourceId'],'Close':m['motion82']['requestedClose'],'eyes':rows})
    (H/'SOURCE_CURVE105.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');board.save(H/'NATIVE_CURVE_MAPPING105.png')
    print(json.dumps([{k:v for k,v in r.items()if k!='eyes'}|{'eyes':[{k:v for k,v in x.items()if k not in ['canonicalCurve','nativeUpperArcVertexIds']}for x in r['eyes']]}for r in results],ensure_ascii=False))
if __name__=='__main__':main()
