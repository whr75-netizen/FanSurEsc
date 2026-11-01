"""Independent screen-ray/triangle verification of the actual occlusion witness.
Uses same-source current vertices/rest/UV and actual query view/projection.
No inferred backing, current Unity call, colour modification or projection fit.
"""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer
from analyse_capture68 import plane
def main():
    cap='capture-final';state=load(sorted((H/cap).glob('STATE107-*'))[-1]);entry=next(e for e in state['sequencePackets']if e['testStage82']=='closed-turn'and e['stageIndex82']==4)
    p=Path(entry['output']);m=load(p/'RAW_MANIFEST.json');view=np.array(m['grid102']['queryPhysicalView107']).reshape(4,4,order='F');projection=np.array(m['grid102']['queryPhysicalProjection107']).reshape(4,4,order='F');results=[]
    for label,scale in [('normal',4),('dense',8)]:
        w,h=m['forward102']['canonicalSize']if scale==4 else m['forward102']['denseSize'];q=buffer(p/(label+'-skin-query-proof.f32')).reshape(h,w,2,4)
        geometry=load(p/(label+'-query-geometry107.json'));assert geometry['sameSourceId']==m['sourceId']and geometry['frame']==m['frameIndex'];triangles=geometry['triangles'];byId={t['triangle']:t for t in triangles};sourceByPrim={t['source'][2]:t for t in triangles if t['source'][:2]==[1,6]}
        if scale==4:
            layers=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);rest=layers[3,2];uv=layers[3,3]
        else:rest=np.flipud(plane(p/'D-lid-rest.plane')[1]);uv=np.flipud(plane(p/'D-lid-uv.plane')[1])
        def screen(world):
            v=(view@np.asarray(world).T).T;c=(projection@v.T).T
            return np.c_[(c[:,0]/c[:,3]*.5+.5)*480,(.5-c[:,1]/c[:,3]*.5)*272],-v[:,2],c[:,3]
        for cy,cx in [(4,4),(4,5),(5,4),(6,3),(6,4)]:
            for sy in range(scale):
                for sx in range(scale):
                    y,x=cy*scale+sy,cx*scale+sx;proof,hit=q[y,x]
                    if proof[0]<=0:continue
                    target=byId[round(float(proof[0]))-1];source=sourceByPrim[round(float(uv[y,x,2]))];sr=np.asarray(source['rest'])[:,:3];point=rest[y,x,:3]
                    ba=np.linalg.lstsq(np.c_[sr[1]-sr[0],sr[2]-sr[0]],point-sr[0],rcond=None)[0];sb=np.r_[1-ba.sum(),ba];world=sb@np.asarray(source['world']);queryXY,sourceDepth,_=screen([world]);queryXY=queryXY[0]
                    xy,z,cw=screen(target['world']);ab=np.linalg.solve(np.c_[xy[1]-xy[0],xy[2]-xy[0]],queryXY-xy[0]);bary=np.r_[1-ab.sum(),ab];perspective=bary/cw;perspective/=perspective.sum();zz=float(perspective@z);hitUV=perspective@np.asarray(target['uv']);bound=32*np.finfo(np.float32).eps*max(1,abs(zz),abs(float(hit[3])))
                    errorDepth=abs(zz-float(proof[1]));errorUV=float(np.max(abs(hitUV-hit[:2])));margin=float(hit[3])-zz
                    row={'scale':scale,'canonicalXY':[cx,cy],'sampleXY':[x,y],'blockerSource':target['source'],'blockerMaterial':target['material'],'blockerTriangle':target['triangle'],'querySourcePrimitive':source['source'][2],'rayInsideBarycentric':bary.tolist(),'sourceRestBarycentric':sb.tolist(),'blockerDepth':zz,'candidateDepth':float(hit[3]),'frontMargin':margin,'float32DepthBound':bound,'GPUCPUBlockerDepthError':errorDepth,'GPUCPUHitUVError':errorUV,'actualAlphaBounds':[float(proof[3]),float(hit[2])],'alphaMode':target['atlas'][3],
                         'certainGeometricBlock':bool(min(bary)>=-2e-5 and margin>3e-5+bound and errorDepth<=bound and errorUV<2e-4 and proof[3]==1 and hit[2]==1 and target['source'][:2]==[1,3])}
                    results.append(row)
    summary={'sourceId':m['sourceId'],'frame':m['frameIndex'],'queryOrthographic':m['grid102']['queryOrthographic107'],'witnesses':len(results),'certainGeometryAndOpaqueBound':sum(r['certainGeometricBlock']for r in results),'maxDepthError':max(r['GPUCPUBlockerDepthError']for r in results),'maxUVError':max(r['GPUCPUHitUVError']for r in results),'normalCells':sorted({tuple(r['canonicalXY'])for r in results if r['scale']==4 and r['certainGeometricBlock']}),'denseCells':sorted({tuple(r['canonicalXY'])for r in results if r['scale']==8 and r['certainGeometricBlock']}),'rows':results,
             'limit':'actual GPU texture alpha bounds; no claim of reproducing all native derivative/AA compositing outside these witnesses'}
    encoded=json.dumps(summary,indent=2,default=lambda x:x.item()if isinstance(x,np.generic)else list(x));(H/'RAY_PROOF107.json').write_text(encoded+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in summary.items()if k!='rows'}))
if __name__=='__main__':main()
