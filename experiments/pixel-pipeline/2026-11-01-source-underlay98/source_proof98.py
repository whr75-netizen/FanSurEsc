"""Three repaired rays: saved actual mesh/UV + immutable original alpha PNG."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import mesh
sys.path.insert(0,str(ROOT/'eye-close90'));from surface_query90 import ProjectedSurface
from analyse_capture68 import camera
from input98 import packet
def main():
    state=json.loads(sorted((HERE/'capture-c').glob('STATE98C*'))[-1].read_text());changed=json.loads((HERE/'analysis-c/CHANGED_SOURCE98.json').read_text());registry=json.loads((ROOT/'live-joint96/registry/REGISTRY96.json').read_text())['sourceMaterials'];materials={(m['slot'],m['subMesh']):m for m in registry};audit=json.loads(Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json').read_text());by={m['texture']['name']:m for m in audit['materials']};pics={};rows=[]
    for row in changed:
        if not row['fixedNativeROIxy']:continue
        d=packet(Path(next(e['output']for e in state['sequencePackets']if e['frame']==row['frame'])));m=d['m'];cam=camera(d['path']/'source.camera');surfaces=[]
        for slot,name in [(0,'source-evaluated-0.mesh'),(1,'eye-evaluated.mesh'),(2,'source-evaluated-2.mesh')]:
            v,n,uv,tris,world=mesh(d['path']/name);wp=np.c_[v,np.ones(len(v))]@world.T
            for sm,ix in enumerate(tris):
                role=sm+7 if slot==0 else sm if slot==1 else sm+11
                if role in [1,2,4,6]or not len(ix):continue
                surfaces.append((slot,sm,role,ProjectedSurface(wp,uv,ix,cam['view'],cam['projection'],[480,272])))
        ref=m['nativeFinalReference89'];origin=np.array(ref['origin']);join=np.array(m['trace86']['headJoinOffset'])+np.array(m['camera86']['deliveredDelta'][:2]);roi=m['currentSources91']['roiTopLeft'];nr=ref['nativeROI']
        for x,y in row['fixedNativeROIxy']:
            bottom=(np.array([x+nr[0],y+nr[1]])+.5-origin)/ref['scale']-join;point=[bottom[0],272-bottom[1]];hits=[]
            for slot,sm,role,surface in surfaces:
                mat=materials[slot,sm]
                for hit in surface.hits(point):
                    cull=mat['cull'];culled=(cull==2 and hit['projectedWinding']!=1)or(cull==1 and hit['projectedWinding']==1);alpha=1.;corners=[1.]*4
                    if mat['alphaTest']or mat['alphaBlend']:
                        key=mat['texture']
                        if key not in pics:
                            im=by[key]['image'];p=Path(im['file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==im['SHA256'];pics[key]=np.flipud(np.asarray(Image.open(p).convert('RGBA'))[...,3]).astype('f4')/np.float32(255)
                        pic=pics[key];h,w=pic.shape;p=np.asarray(hit['uv'])*[w,h]-.5;ix,iy=np.floor(p).astype(int);fx,fy=p-[ix,iy]
                        def wrap(v,n,mode):return np.clip(v,0,n-1)if mode=='Clamp'else v%n
                        corners=[float(pic[wrap(iy+dy,h,mat['wrapV']),wrap(ix+dx,w,mat['wrapU'])]*mat['factorAlpha'])for dy in range(2)for dx in range(2)];alpha=(corners[0]*(1-fx)+corners[1]*fx)*(1-fy)+(corners[2]*(1-fx)+corners[3]*fx)*fy
                    discarded=mat['alphaTest']and alpha<mat['cutoff'];hits.append({**hit,'slot':slot,'subMesh':sm,'role':role,'alpha':float(alpha),'alphaTexelCorners':corners,'cutoff':mat['cutoff'],'alphaTest':mat['alphaTest'],'culled':culled,'discarded':discarded,'visibleCandidate':not culled and not discarded and alpha>1e-6,'sourceUVTriangle':surface.uv[surface.tri[hit['primitive']-1]].tolist(),'projectedTriangle':surface.xy[surface.tri[hit['primitive']-1]].tolist(),'vertexClipW':surface.w[surface.tri[hit['primitive']-1]].tolist()})
            hits.sort(key=lambda h:h['depth']);px,py=np.floor((bottom-[roi[0],272-roi[1]-roi[3]])*2).astype(int);actual=d['a']['current-non-eye98-1'][py,px];visible=[h for h in hits if h['visibleCandidate']];kind=int(d['a']['live96-final3'][y,x,0]);r={'frame':row['frame'],'sourceId':row['sourceId'],'nativeROIxy':[x,y],'physicalTopLeftXY':list(map(float,point)),'actualNonEyeMeta':actual.tolist(),'restorationKind':kind,'geometricAndAlphaHits':hits}
            if kind==4:
                found=next(h for h in visible if h['role']+1==actual[1]and h['primitive']==int(d['a']['current-non-eye98-2'][py,px,2]));uv=d['a']['current-non-eye98-2'][py,px,:2];r['matchingPrimitiveUVMaxError']=float(abs(np.asarray(found['uv'])-uv).max());r['matchingPrimitiveDepthError']=abs(found['depth']-float(actual[0]));tri=np.asarray(found['sourceUVTriangle']);b=np.linalg.solve(np.stack([tri[1]-tri[0],tri[2]-tri[0]],axis=1),uv-tri[0]);weights=np.r_[1-b.sum(),b];r['GPUUVInsideSameSourceTriangle']=bool(weights.min()>=0);cw=weights*np.asarray(found['vertexClipW']);reproject=cw@np.asarray(found['projectedTriangle'])/cw.sum();r['GPUUVReprojectedPoint']=reproject.tolist();r['CPUvsGPUReprojectionPixelError']=abs(reproject-np.asarray(point)).tolist();r['sameTwoXSampleFootprint']=bool((abs(reproject-np.asarray(point))<.25).all());r['UVNotDoubleBitExact']=True;assert r['GPUUVInsideSameSourceTriangle']and r['sameTwoXSampleFootprint']

            else:assert kind==5 and actual[0]==0 and not visible,r
            rows.append(r)
    assert len(rows)==3
    (HERE/'SOURCE_RAYS98.json').write_text(json.dumps({'sameSourceMeshAndAlpha':True,'originalPNGAlphaPreviouslyUnity4230Verified':True,'notNeighbourColourInference':True,'rows':rows},indent=2,default=lambda v:v.item() if isinstance(v,np.generic)else v)+'\n');print(json.dumps([{k:r[k]for k in ['frame','nativeROIxy','restorationKind']}|{'hits':len(r['geometricAndAlphaHits'])}for r in rows]))
if __name__=='__main__':main()
