"""Same-frame source rays against every stored face/body/hair submesh."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));sys.path.insert(0,str(ROOT/'eye-close90'))
from analyse89 import packet,geometry,mesh,PARTS
from analyse_capture68 import camera
from surface_query90 import ProjectedSurface

def main():
    state=json.loads(sorted((HERE/'capture-scale-correct').glob('STATE95B*'))[-1].read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError')
    output=[]; alpha={}; frame_summary=[]
    for entry in state['sequencePackets']:
        d=packet(Path(entry['output'])); layers,physical,checks=geometry(d); cam=camera(d['path']/'source.camera'); surfaces=[];face_signs={}
        for slot,name in [(1,'eye-evaluated.mesh'),(0,'source-evaluated-0.mesh'),(2,'source-evaluated-2.mesh')]:
            v,n,uv,tris,world=mesh(d['path']/name); wp=np.c_[v,np.ones(len(v))]@world.T
            for sm,ix in enumerate(tris):
                if len(ix):
                    surface=ProjectedSurface(wp,uv,ix,cam['view'],cam['projection'],[480,272]);surfaces.append((slot,sm,surface))
                    if slot==1:face_signs[sm]=surface.sign
        queries=[];skin_mode='--skin'in sys.argv or '--skin-focus'in sys.argv;needed=set()
        if '--skin-focus'in sys.argv:
            z=np.load(HERE/f'candidate-joint/frame{entry["frame"]}.npz');yy,xx=np.where(z['missing']);m=d['m'];ref=m['nativeFinalReference89'];bottom=(np.c_[xx+ref['nativeROI'][0]+.5,yy+ref['nativeROI'][1]+.5]-np.asarray(ref['origin']))/ref['scale']-np.asarray(m['trace86']['headJoinOffset'])-np.asarray(m['camera86']['deliveredDelta'][:2]);bottom[:,1]=272-bottom[:,1];local=np.floor(bottom-np.asarray(m['retarget89']['anchor'])-np.asarray(m['retarget89']['bounds'][:2])).astype(int);needed=set(map(tuple,local))
        for part in ([0,1,2,3]if skin_mode else[1,2,3]):
            valid=(layers[part][1][...,0]>0)&(layers[part][0][...,3]>0)
            for sy,sx in np.argwhere(valid):
                if part==0 and '--skin-focus'in sys.argv and (int(sx)//4,int(sy)//4)not in needed:continue
                point=physical[part,sy,sx]; depth=float(layers[part][1][sy,sx,0]); hits=[]
                for slot,sm,surface in surfaces:
                    for hit in surface.hits(point):
                        if hit['depth']>=depth-3e-5:continue
                        uv=np.asarray(hit['uv'],'<f4'); key=f'{slot}-{sm}-'+hashlib.sha256(uv.tobytes()).hexdigest()[:20]
                        hit.update({'rendererSlot':slot,'sourceSubMesh':sm,'queryKey':key}); hits.append(hit)
                        alpha.setdefault(key,{'id':key,'rendererSlot':slot,'sourceSubMesh':sm,'uv':uv.astype(float).tolist()})
                primitive=int(round(float(layers[part][3][sy,sx,2])))-1
                queries.append({'partIndex':part,'sourceRole':PARTS[part],'sample':[int(sx),int(sy)],'candidatePhysicalWinding':int(face_signs[PARTS[part]][primitive]),'candidatePrimitive':primitive+1,'physicalPoint':point.tolist(),'depth':depth,'alpha':float(layers[part][0][sy,sx,3]),'hits':sorted(hits,key=lambda h:h['depth'])})
        output.append({'sourceId':d['m']['sourceId'],'frame':entry['frame'],'serial':entry['serial'],'geometryChecks':checks,'queries':queries})
        frame_summary.append({'frame':entry['frame'],'Close':d['m']['motion82']['getterClose'],'evaluatedError':d['m']['motion82']['evaluatedVsOwnedBakeMax'],'queries':len(queries),'frontHits':sum(len(q['hits'])for q in queries),'allThreeEvaluatedMeshes':True})
    request={'modelAsset':'Assets/EUnityValidation01/VRoidSampleA144/Inputs/AvatarSample_A.vrm','modelSHA256':'0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3','queries':list(alpha.values())}
    assert len(alpha)<=32768,'Bounded source alpha request exceeded; do not silently truncate'
    tag='SKIN_FOCUS'if '--skin-focus'in sys.argv else'SKIN'
    if skin_mode:
        (HERE/('QUERIES_'+tag+'95.json')).write_text(json.dumps({'frames':output},indent=2)+'\n')
        old_ids={q['id']for q in json.loads((HERE/'ALPHA_REQUEST95.json').read_text())['queries']}
        request['queries']=[q for q in request['queries']if q['id']not in old_ids]
        (HERE/('ALPHA_REQUEST_'+tag+'95.json')).write_text(json.dumps(request,indent=2)+'\n')
    else:
        (HERE/'QUERIES_FACING95.json').write_text(json.dumps({'frames':output},indent=2)+'\n')
        assert request==json.loads((HERE/'ALPHA_REQUEST95.json').read_text()),'Source alpha queries changed; do not reuse bounds'
    (HERE/('QUERY_'+tag+'_SUMMARY95.json'if skin_mode else'QUERY_FACING_SUMMARY95.json')).write_text(json.dumps({'frames':frame_summary,'uniqueAlphaQueries':len(alpha),'newAlphaQueries':len(request['queries'])},indent=2)+'\n')
    print(json.dumps({'frames':frame_summary,'uniqueAlphaQueries':len(alpha)},indent=2))

if __name__=='__main__':main()
