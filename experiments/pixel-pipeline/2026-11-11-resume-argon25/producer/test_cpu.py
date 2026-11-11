"""Exact coordinate/projection tests and bounded two-frame geometry/alpha oracle."""
from pathlib import Path
import hashlib,io,json,struct,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[1];FULL=R/'bounded-form115/runtime24/full-render24'
for p in [FULL,FULL/'carrier-fix24',R/'eye-failures114',R/'aperture-runtime111']:sys.path.insert(0,str(p))
from report_full24 import read,plane,buffer
from trace114 import geometry
from trace_carrier24 import origins,direct
from ray111 import NativeAlpha

def alpha_hair(c):
    registry=read(R/'renderer-family59/SOURCE_REGISTRY59.json')
    model=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')/registry['modelAsset'];data=model.read_bytes()
    assert hashlib.sha256(data).hexdigest()==registry['modelSHA256']
    chunks={};p=12
    while p<len(data):
        n,t=struct.unpack_from('<II',data,p);p+=8;assert p+n<=len(data);chunks[t]=data[p:p+n];p+=n
    g=json.loads(chunks[0x4e4f534a]);blob=chunks[0x004e4942]
    a=NativeAlpha.__new__(NativeAlpha);a.ctx=c;a.images={};a.sources={};used=0
    for mi in np.unique(c['triangles'][c['sources'][:,0]==2,3]):
        ids=np.where(c['triangles'][:,3]==mi)[0];source=np.unique(c['sources'][ids,:2],axis=0);assert len(source)==1 and source[0,0]==2
        row=next(v for v in registry['bindings']if v['rendererOrdinal']==2 and v['subMesh']==int(source[0,1]))
        image=g['images'][row['imageIndex']];view=g['bufferViews'][image['bufferView']];raw=blob[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
        assert hashlib.sha256(raw).hexdigest()==row['imageSHA256']
        im=Image.open(io.BytesIO(raw));used+=im.width*im.height*8;assert used<=128*1024*1024
        a.images[int(mi)]=np.asarray(im.convert('RGBA'))[:,:,3].astype(float)/255;im.close();a.sources[int(mi)]=row
    return a,used

class HairRay:
    def __init__(self,c,a):
        self.c=c;self.alpha=a;self.ids=c['triangles'][c['sources'][:,0]==2,:3];self.mi=c['triangles'][c['sources'][:,0]==2,3]
        self.xy=c['physicalXY'][self.ids];self.z=c['depth'][self.ids];self.w=c['physicalW'][self.ids]
        matrix=np.stack([self.xy[:,1]-self.xy[:,0],self.xy[:,2]-self.xy[:,0]],axis=2);self.det=np.linalg.det(matrix);self.good=abs(self.det)>1e-12
        self.inv=np.zeros_like(matrix);self.inv[self.good]=np.linalg.inv(matrix[self.good])
    def query(self,points,depth):
        out=[]
        for p,z in zip(points,depth):
            ab=np.einsum('tij,tj->ti',self.inv,p-self.xy[:,0]);b=np.c_[1-ab.sum(1),ab]
            weights=b/self.w;weights/=weights.sum(1)[:,None];zz=(weights*self.z).sum(1)
            mask=self.good&(b.min(1)>=-1e-7)&(self.w.min(1)>0)&(zz<z-3e-5)
            cull=self.c['materials'][self.mi,1,2];sign=np.where(self.det>0,1,-1);mask&=~(((cull==2)&(sign!=1))|((cull==1)&(sign!= -1)))
            lo=hi=exact=0.;hits=[]
            for i in np.flatnonzero(mask):
                mi=int(self.mi[i]);uv=weights[i]@self.c['uv'][self.ids[i]];bounds=self.alpha.bounds(mi,[uv])[0]
                values,w=self.alpha.corners(mi,[uv]);value=float((values*w).sum());mode=int(self.c['materials'][mi,0,3]);cut=float(self.c['materials'][mi,1,1])
                opacity=1. if mode==0 else float(value>=cut)if mode==1 else value
                lo=1-(1-lo)*(1-bounds[0]);hi=1-(1-hi)*(1-bounds[1]);exact=1-(1-exact)*(1-opacity)
                hits.append({'material':mi,'UV':uv.tolist(),'depth':float(zz[i]),'alphaInterval':bounds.tolist(),'bilinearAlpha':value,'cutoff':cut})
            out.append({'interval':[float(lo),float(hi)],'exactCutout':exact,'hits':hits})
        return out

def main():
    state=read(next((FULL/'motion24').glob('STATE113-*-finished.json')));rows=[];coordinatePairs=0;alphaBytes=0
    for packet in state['sequencePackets'][:2]:
        p=Path(packet['output']);m=read(p/'RAW_MANIFEST.json');c=geometry(p,m);origin,carrierOrigin=origins(m,p)
        a,n=alpha_hair(c);alphaBytes=max(alphaBytes,n);ray=HairRay(c,a)
        roi=m['grid102']['eyeTopLeftROI'];cw=m['forward102']['canonicalSize'][0]//4;ch=m['forward102']['canonicalSize'][1]//4
        cx,cy=3,4;at=cy*cw+cx;ident=buffer(p/'curve-identity.f32').reshape(-1,4)[at];assert tuple(map(int,ident[:2]))==(4,2)
        q=buffer(p/'ASSIGNED-depth24.f32').reshape(roi[3],roi[2],16,4)
        # Locate this canonical source feature in the physical output grid.
        candidates=[]
        for y in range(roi[3]):
            for x in range(roi[2]):
                centre=np.array([roi[0]+x+.5,roi[1]+roi[3]-y-.5]);cell=np.floor(centre-origin).astype(int)
                if tuple(cell)==(cx,cy):candidates.append((x,y))
        assert len(candidates)==1;x,y=candidates[0]
        old=ray.query(q[y,x,:,:2],q[y,x,:,2]);oldSum=np.sum([v['interval']for v in old],axis=0)
        hm=plane(p/'S4-meta.plane')[1][y*4:y*4+4,x*4:x*4+4];hc=plane(p/'S4-rgba.plane')[1][y*4:y*4+4,x*4:x*4+4]
        actual=float(sum(np.clip(hm[j,i,3],0,1)for j in range(4)for i in range(4)if hm[j,i,0]>0 and hc[j,i,3]>0 and hm[j,i,0]<q[y,x,j*4+i,2]-np.float32(3e-5)))
        assert oldSum[0]<=actual<=oldSum[1],('original GPU coverage outside alpha/geometry bounds',actual,oldSum)
        xy=np.array([origin+[cx+(i%4+.5)/4,cy+1-(i//4+.5)/4]for i in range(16)],np.float32)
        hairTexels=np.array([[cx*4+i%4,(ch-1-cy)*4+i//4]for i in range(16)])
        reconstructed=np.array([origin+[xx/4+.125,ch-yy/4-.125]for xx,yy in hairTexels],np.float32)
        assert np.array_equal(xy,reconstructed);coordinatePairs+=16
        # Crop matches Full319View335.Project, not the mistaken +Y-up wording.
        ox,oy=map(float,origin) # Double algebra test; do not silently round crop coefficients to f32 here.
        crop=np.eye(4);crop[0,0]=480/cw;crop[0,3]=(480-2*ox-cw)/cw;crop[1,1]=272/ch;crop[1,3]=(2*oy+ch-272)/ch
        projected=c['world4']@c['view'].T@c['projection'].T@crop.T
        target=np.c_[(projected[:,0]/projected[:,3]*.5+.5)*cw*4,(projected[:,1]/projected[:,3]*.5+.5)*ch*4]
        expected=np.c_[(c['physicalXY'][:,0]-origin[0])*4,(origin[1]+ch-c['physicalXY'][:,1])*4]
        assert abs(target-expected).max()<1e-8,'crop convention mismatch'
        projected32=c['world4'].astype(np.float32)@(crop.astype(np.float32)@c['projection'].astype(np.float32)@c['view'].astype(np.float32)).T
        target32=np.c_[(projected32[:,0]/projected32[:,3]*.5+.5)*cw*4,(projected32[:,1]/projected32[:,3]*.5+.5)*ch*4]
        hairVertices=np.unique(c['triangles'][c['sources'][:,0]==2,:3]);fp32Error=float(abs(target32[hairVertices]-expected[hairVertices]).max()/4)
        meta=plane(p/'C-part2-meta.plane')[1][::-1];z=direct(meta,xy,carrierOrigin,2);known=z>0;total=np.float32(0)
        for v in z:
            if v>0:total=np.float32(total+v)
        low,high=m['runtime24']['ringDepthRanges'][2:4]
        fill=np.float32(total/known.sum())if known.any()else ident[2]if low<=ident[2]<=high else np.float32(0)
        z=np.where(known,z,fill);assert(z>0).all(),'No carrier; result must remain unknown'
        new=ray.query(xy,z);newSum=np.sum([v['interval']for v in new],axis=0);exact=sum(v['exactCutout']for v in new)
        rows.append({'frame':packet['frame'],'sourceId':packet['sourceId'],'origin':origin.tolist(),'canonicalCell':[cx,cy],
            'oldGPURasterCoverage':actual,'oldCPUInterval':oldSum.tolist(),'headGridCPUInterval':newSum.tolist(),'headGridExactCutout':exact,
            'coordinatePairsExact':16,'fp32VertexProjectionErrorPxVersusDouble':fp32Error,'headQueryXY':xy.tolist(),'headQueryDepth':z.tolist(),'headQueryHits':new,
            'headRelativeProjectedHairBounds':(c['physicalXY'][np.unique(c['triangles'][c['sources'][:,0]==2,:3])]-origin).tolist()})
    # Keep only summary of the large vertex diagnostic, not another geometry dump.
    delta=np.array(rows[1].pop('headRelativeProjectedHairBounds'))-np.array(rows[0].pop('headRelativeProjectedHairBounds'))
    result={'rows':rows,'pairedSavedGPUFrames':2,'newGPUExecuted':False,'coordinatePairsExact':coordinatePairs,'projectionPairsExact':True,
        'headRelativeHairMaxDeltaPx':abs(delta).max(0).tolist(),'alphaArrayBytes':alphaBytes,
        'boundsStable':rows[0]['headGridCPUInterval']==rows[1]['headGridCPUInterval'],
        'exactCutoutStable':rows[0]['headGridExactCutout']==rows[1]['headGridExactCutout'],
        'limit':'Analytic native-geometry/alpha counterfactual. Does not validate new shader raster rules, RGB/shading, final GPU image or temporal motion.'}
    (H/'CPU_PRODUCER.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items()if k not in ['rows','limit']}));print('coverage',[(v['oldGPURasterCoverage'],v['headGridCPUInterval'],v['headGridExactCutout'])for v in rows])
if __name__=='__main__':main()
