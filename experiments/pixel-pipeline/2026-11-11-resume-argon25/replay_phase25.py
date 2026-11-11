"""Two existing actual phase packets, CPU oracle only, never a GPU result."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parent
FULL=R/'bounded-form115/runtime24/full-render24'
for p in [FULL,FULL/'carrier-fix24',R/'eye-failures114',R/'aperture-runtime111']:sys.path.insert(0,str(p))
from report_full24 import read,plane,buffer
from trace_carrier24 import origins,points,direct
from trace114 import geometry
from geometry114 import Face114
from ray111 import NativeAlpha,FaceRay
from pairing114 import compose
from prepare_coordinate25 import shift

class FaceWithOneOriginalAlpha(Face114):
    def __init__(self,ctx,mask,alpha):
        # Reuse the existing FaceRay initializer and Face114 query. Only face
        # material alpha is needed: avoid loading unrelated textures repeatedly.
        FaceRay.__init__(self,ctx,alpha)
        self.mask=np.asarray(mask,np.uint32);self.mi=ctx['triangles'][self.tids,3]

def main():
    state=read(next((FULL/'motion24').glob('STATE113-*-finished.json')))
    phase=read(FULL/'carrier-fix24/PHASE_EXPOSURE24.json')
    source=read(R/'argon23-runtime113/SOURCE113.json')
    alphaInfo=read(R/'aperture-runtime111/inputs/ALPHA111.json')
    alphaSource=next(a for a in alphaInfo['images']if a['renderer']==1 and a['submesh']==3)
    imagePath=R/'aperture-runtime111/inputs'/alphaSource['file']
    assert hashlib.sha256(imagePath.read_bytes()).hexdigest()==alphaSource['sha256']
    image=Image.open(imagePath);assert image.width*image.height*8<=128*1024*1024
    alphaImage=np.asarray(image.convert('RGBA'))[:,:,3].astype(float)/255
    image.close();rows=[]
    for pi,packet in enumerate(state['sequencePackets'][:2]):
        p=Path(packet['output']);m=read(p/'RAW_MANIFEST.json');assert packet['sourceId']==phase['rows'][pi]['sourceId']
        sample=next(x for x in phase['rows'][pi]['samples']if x['owner']==2 and x['canonical']==[3,4])
        x,y=sample['tile'];roi=m['grid102']['eyeTopLeftROI'];anchor,carrierOrigin=origins(m,p)
        raw=geometry(p,m);a=NativeAlpha.__new__(NativeAlpha);a.ctx=raw
        faceMaterials=np.unique(raw['triangles'][(raw['sources'][:,0]==1)&(raw['sources'][:,1]==3),3]);assert len(faceMaterials)==1
        mi=int(faceMaterials[0]);assert list(map(int,raw['materials'][mi,0,1:3]))==[alphaImage.shape[1],alphaImage.shape[0]]
        a.images={mi:alphaImage};a.sources={mi:alphaSource};face=FaceWithOneOriginalAlpha(raw,source['ownSkinMask'],a)
        q=buffer(p/'ASSIGNED-depth24.f32').reshape(roi[3],roi[2],16,4)[y,x]
        oldVis=buffer(p/'ASSIGNED-visibility24.f32').reshape(roi[3],roi[2],16,4)[y,x,:,:2]
        observed=face.query(q[:,:2],q[:,2],2,limit=m['runtime24']['socketDiameters'][1]);vv=np.array([r['faceInterval']for r in observed])
        assert float(abs(vv-oldVis).max())==0,'Existing same-frame GPU face query not reproduced'
        delta=shift(np.array([roi[0],272-roi[1]-roi[3],roi[2],roi[3]]),np.array([x,y]),anchor)
        xy=points(roi,x,y)+np.array([delta[0],-delta[1]],np.float32)/np.float32(4)
        cw=m['forward102']['canonicalSize'][0]//4;at=4*cw+3
        ident=buffer(p/'curve-identity.f32').reshape(-1,4)[at];assert tuple(map(int,ident[:2]))==(4,2)
        meta=plane(p/'C-part2-meta.plane')[1][::-1];depth=direct(meta,xy,carrierOrigin,2);known=depth>0
        total=np.float32(0)
        for z in depth:
            if z>0:total=np.float32(total+z)
        lo,hi=m['runtime24']['ringDepthRanges'][2:4]
        fill=np.float32(total/np.float32(known.sum()))if known.any()else ident[2]if lo<=ident[2]<=hi else np.float32(0)
        depth=np.where(known,depth,fill);assert (depth>0).all(),'Carrier unavailable: do not invent a depth'
        query=face.query(xy,depth,2,limit=m['runtime24']['socketDiameters'][1]);vis=np.array([v['faceInterval']for v in query])
        hairMeta=plane(p/'S4-meta.plane')[1];hairColour=plane(p/'S4-rgba.plane')[1]
        hm=[];hc=[];hairSamples=[]
        for i in range(16):
            hx=x*4+i%4+int(delta[0]);hy=y*4+i//4+int(delta[1])
            assert 0<=hx<hairMeta.shape[1]and 0<=hy<hairMeta.shape[0],'Outside capture: unknown, no clamping'
            hxy=np.array([roi[0]+(hx+.5)/4,272-((272-roi[1]-roi[3])+(hy+.5)/4)],np.float32)
            assert np.array_equal(hxy,xy[i]),'Depth/alpha query and hair sample disagree'
            hm.append(hairMeta[hy,hx]);hc.append(hairColour[hy,hx]);hairSamples.append([hx,hy])
        canvas=plane(p/'L0-RGBA.plane')[1][y*4+1,x*4+1];canvasMeta=plane(p/'L0-META.plane')[1][y*4+1,x*4+1]
        selected=buffer(p/'curve-colour.f32').reshape(-1,4)[at]
        case={'fine':[{'fineXY':[i%4,i//4]}for i in range(16)]}
        corrected=compose(case,vis,depth,canvas,canvasMeta,selected,4,2,np.array(hm).reshape(4,4,4),np.array(hc).reshape(4,4,4))
        old=compose(case,oldVis,q[:,2],canvas,canvasMeta,selected,4,2,hairMeta[y*4:y*4+4,x*4:x*4+4],hairColour[y*4:y*4+4,x*4:x*4+4])
        gpu=plane(p/'F-FinalRGBA.plane')[1][y,x];assert np.array_equal(np.array(old['linearRGBA'],np.float32),gpu),'Original final GPU composition not reproduced'
        rows.append({'sourceId':packet['sourceId'],'frame':packet['frame'],'phase':phase['rows'][pi]['phase'],'tile':[x,y],
            'sameFrameGPUFaceComparisons':16,'sameFrameGPUFaceError':0,'originalGPUFinalExact':True,'correctedQueryCoordinates':xy.tolist(),
            'correctedDepth16':depth.tolist(),'correctedHairSamples':hairSamples,'faceInterval':vis.sum(0).tolist(),'old':old,'correctedCPUOnly':corrected})
    report={'scope':'CPU counterfactual on TWO old actual source packets. No new capture/GPU output.', 'rows':rows,
        'originalAlphaSHA256':alphaSource['sha256'],'oldGPUQueriesReproduced':32,'correctedQueryHairCoordinatePairsExact':32,
        'newGPUExecuted':False,'skinOwnershipChanged':False,'sourceBankOrPaletteChanged':False,'product77Changed':False}
    (H/'PHASE25_CPU.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'originalGPUQueriesExact':32,'originalFinalRGBAExact':2,'correctedCoordinatePairsExact':32,
        'oldCoverage':[r['old']['hairInterval']for r in rows],'correctedCPUcoverage':[r['correctedCPUOnly']['hairInterval']for r in rows],
        'newGPUExecuted':False}))
if __name__=='__main__':main()
