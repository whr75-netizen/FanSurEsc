"""Direct111 source components -> canonical allocation -> destination exposure.
Frozen110 geometry is NOT used. Output remains labels/visibility, not finalRGB.
"""
from pathlib import Path
import sys,json,math
import numpy as np
from geometry111 import H,R,P109,read,load,packet_list,plane,buffer,joint_arrays
P22=R/'argon22-boundary'if(R/'argon22-boundary').exists()else R/'2026-11-01-argon22-boundary';sys.path.insert(0,str(P22))
from aperture22 import column_rows,component_count
from ray111 import NativeAlpha,FaceRay,carrier_at
from allocate111 import solve

def source_fields(p):
    m=read(p/'RAW_MANIFEST.json');w,h=m['forward102']['denseSize'];a=np.zeros((4,5,h,w,4),np.float32);v=np.zeros((4,h,w,4),np.float32)
    for part in [1,2,3]:
        for ch,name in enumerate(['rgba','meta','rest','uv']):
            s='D-lid-'if part==3 else f'D-part{part}-';meta,data=plane(p/(s+name+'.plane'));assert meta['sourceId']==m['sourceId']and meta['frameIndex']==m['frameIndex'];a[part,ch]=np.flipud(data)
    v[1:]=buffer(p/'dense-three-part-visibility.f32').reshape(3,h,w,4);return m,a,v

def bank_data():
    s=read(P109/'inputs/SOURCE_FIXTURE88.json');palette=s['paletteRGB8'];bank={};groups={}
    for owner in [1,2]:
        for part in [1,4]:
            points={(v['x'],v['y'])for v in s['source']if v['owner']==owner and v['part']==part};left=points.copy();component=0
            while left:
                todo=[left.pop()];component+=1
                while todo:
                    x,y=todo.pop();groups[(owner,part,x,y)]=1<<(component-1)
                    for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                        if q in left:left.remove(q);todo.append(q)
    for v in s['source']:bank[(v['owner'],v['part'],v['x'],v['y'])]=np.array(palette[v['palette']])
    return bank,groups

def source_components(ctx,a,lo,owner,bank,groups):
    hh,ww=lo.shape[1:];h,w=hh//8,ww//8;bits=[np.zeros((h,w),np.uint32)for _ in [1,4]];active=[0,0];records=[];mismatch=[]
    for pi,part in enumerate([1,4]):
        for y,x in np.argwhere((lo[pi]>0)&(np.rint(a[pi+1,1,:,:,2])==owner)):
            rest=a[pi+1,2,y,x,:3];q=np.r_[rest,np.float32(1)].astype(np.float32);p=np.stack([ctx['projectionX'][owner],ctx['projectionY'][owner]]).astype(np.float32);xy=p@q
            # Bound float32 dot rounding, including fused/nonfused order.
            err=8*np.finfo(np.float32).eps*np.sum(abs(p*q),axis=1);xs=range(math.floor(float(xy[0]-err[0])),math.floor(float(xy[0]+err[0]))+1);ys=range(math.floor(float(xy[1]-err[1])),math.floor(float(xy[1]+err[1]))+1);rgb=a[pi+1,0,y,x,:3].astype(float);code=np.rint(np.where(rgb<=.0031308,rgb*12.92,1.055*np.maximum(rgb,0)**(1/2.4)-.055)*255).astype(int);keys=[(owner,part,xx,yy)for xx in xs for yy in ys if(owner,part,xx,yy)in bank and np.array_equal(bank[(owner,part,xx,yy)],code)];gb={groups[k]for k in keys}
            if len(gb)!=1:mismatch.append({'fineYX':[int(y),int(x)],'part':part,'possibleKeys':keys,'RGB8':code.tolist()});continue
            bit=next(iter(gb));bits[pi][y//8,x//8]|=bit;active[pi]|=bit;records.append({'fineYX':[int(y),int(x)],'cellYX':[int(y)//8,int(x)//8],'part':part,'sourceKeys':[list(k)for k in keys],'componentBit':bit,'sourceKeyUnique':len(keys)==1,'certainWeight':float(lo[pi,y,x])/64,'sourceRGB8':code.tolist(),'nativePrimitive':int(round(float(a[pi+1,3,y,x,2]))),'sourceUV':a[pi+1,3,y,x,:2].tolist()})
    return bits,active,records,mismatch

def rest_world(ctx,part,rest,primitive):
    ti=int(ctx['partMap'][part,primitive-1]);assert ti>=0;ids=ctx['triangles'][ti,:3];v=ctx['rest'][ids];basis=np.stack([v[1]-v[0],v[2]-v[0]],axis=1);q=np.linalg.lstsq(basis,np.asarray(rest)-v[0],rcond=None)[0];b=np.r_[1-q.sum(),q];return b@ctx['world'][ids],b,ti

def validate(ctx,alpha,rays):
    p=ctx['path'];w,h=ctx['manifest']['forward102']['denseSize'];v=buffer(p/'carrier-three-part-visibility.f32').reshape(3,h,w,4);maximum=0.;depthError=0.;checks=[]
    for part in [1,2,3]:
        _,meta=plane(p/f'C-part{part}-meta.plane');_,rest=plane(p/f'C-part{part}-rest.plane');_,uv=plane(p/f'C-part{part}-uv.plane');_,rgba=plane(p/f'C-part{part}-rgba.plane');meta,rest,uv,rgba=map(np.flipud,[meta,rest,uv,rgba]);ids=np.argwhere(meta[:,:,0]>0);ids=ids[np.linspace(0,len(ids)-1,min(24,len(ids)),dtype=int)]if len(ids)else ids;world=[];data=[]
        for y,x in ids:
            point,b,ti=rest_world(ctx,part,rest[y,x,:3],int(round(float(uv[y,x,2]))));verts=ctx['triangles'][ti,:3];owner=int(round(float(meta[y,x,2])));xy=b@ctx['maps'][owner][verts];maximum=max(maximum,float(np.linalg.norm(xy-[(x+.5)/8,(y+.5)/8])));depthError=max(depthError,abs(float(b@ctx['depth'][verts])-float(meta[y,x,0])));world.append(point);data.append((int(y),int(x),float(rgba[y,x,3]),float(meta[y,x,0])))
        cast=rays.query(world,[d[3]for d in data])
        for (y,x,a,z),q in zip(data,cast):checks.append({'part':part,'fineYX':[y,x],'CPUFaceIntervalTimesRecordedCandidateAlpha':(np.array(q['faceVisibilityInterval'])*a).tolist(),'GPUVisibilityInterval':v[part-1,y,x,:2].tolist(),'absoluteIntervalDifference':float(np.max(abs(np.array(q['faceVisibilityInterval'])*a-v[part-1,y,x,:2])))})
    return {'directCurrentGeometry':True,'sampledGPUCarrierQueryChecks':len(checks),'maxCPUvsGPUVisibilityIntervalDifference':max((q['absoluteIntervalDifference']for q in checks),default=0),'maxCanonicalProjectionResidualPixels':maximum,'maxDepthResidualMetres':depthError,'checks':checks,'frozenMeshReconstructionUsed':False}

def expose(ctx,alpha,rays,owner,labels,policy='native'):
    p=ctx['path'];hm,hair=plane(p/'S4-meta.plane');hc,colour=plane(p/'S4-rgba.plane');assert hm['sourceId']==hc['sourceId']==ctx['sourceId'];hair,colour=np.flipud(hair),np.flipud(colour);roi=np.array(ctx['manifest']['grid102']['eyeTopLeftROI']);out=[]
    for y,x in np.argwhere(labels>0):
        part=int(labels[y,x]);display=np.floor(np.array([x,y])+ctx['offset']-roi[:2]+.5).astype(int);origin=roi[:2]+display-ctx['offset'];yy,xx=np.mgrid[0:4,0:4];q=np.c_[(xx.ravel()+.5)/4,(yy.ravel()+.5)/4]+origin;carriers=carrier_at(ctx,alpha,owner,part,q,geometryOnly=policy!='native');bank=bank_data()[0]if policy=='feature-canvas'else None
        if bank is not None:
            face=carrier_at(ctx,alpha,owner,0,q,canvasBank=bank)
            for k in range(len(carriers)):
                for c in face[k]:c['carrierBinding']='registered source-bank canvas on actual face triangle'
                carriers[k].extend(face[k])
        flat=[c for group in carriers for c in group];query=rays.query([c['world']for c in flat],canvasOwner=owner if bank is not None else None,canvasBank=bank);at=0;samples=[]
        for k,group in enumerate(carriers):
            for c in group:c['face']=query[at];at+=1
            valid=[c for c in group if c['candidateAlphaBounds'][1]>0]
            if not valid:samples.append({'fine':[int(k//4),int(k%4)],'carrierAbsent':True,'visibleBounds':[0,0]});continue
            z=min(c['depth']for c in valid);front=[c for c in valid if c['depth']<=z+3e-5];lo=min(c['candidateAlphaBounds'][0]*c['face']['faceVisibilityInterval'][0]for c in front);hi=max(c['candidateAlphaBounds'][1]*c['face']['faceVisibilityInterval'][1]for c in front);sampleYX=display[::-1]*4+[k//4,k%4];inside=all(sampleYX>=0)and sampleYX[0]<len(hair)and sampleYX[1]<hair.shape[1]
            entry={'fine':[int(k//4),int(k%4)],'canonicalXY':q[k].tolist(),'displaySampleYX':sampleYX.tolist(),'frontCarriers':front,'sourceFaceAlphaBounds':[lo,hi],'depthSpreadAmongCarriers':max(c['depth']for c in valid)-z}
            if not inside:entry['visibleBounds']=[0,hi];entry['externalHairUnobserved']=True
            else:
                d=hair[tuple(sampleYX)];a=colour[tuple(sampleYX)];cover=float(np.clip(d[3],0,1))if d[0]>0 and a[3]>0 and d[0]<z-3e-5 else 0.;entry['hair']={'depth':float(d[0]),'coverage':cover,'sameSourceId':True,'sameExactRecordedS4Sample':True};entry['visibleBounds']=[lo*(1-cover),hi*(1-cover)]
            samples.append(entry)
        intervals=np.array([v['visibleBounds']for v in samples]);out.append({'cellYX':[int(y),int(x)],'part':part,'displayCellXY':(roi[:2]+display).tolist(),'samples':samples,'visibleCarrierFractionBounds':intervals.sum(0).tolist(),'fractionDenominator':16,'notFinalOpacityOrWholeCellOwner':True})
    return out

def main():
    state,packets=packet_list();bank,groups=bank_data();cache=read(P109/'NATIVE_CACHE109.json');out=[]
    for p in packets:
        ctx=load(p);alpha=NativeAlpha(ctx);rays=FaceRay(ctx,alpha);m,a,v=source_fields(p);lo,hi,*_=joint_arrays(a,v);check=validate(ctx,alpha,rays);eyeRows=[]
        for owner in [1,2]:
            c=next(c for c in cache['curves']if c['owner']==owner);coords=[];world=[];errors=[]
            for point in c['points']:
                if point.get('unresolved'):continue
                tid=ctx['partMap'][3,point['primitive']-1];ids=ctx['triangles'][tid,:3];b=np.array(point['barycentric']);errors.append(float(np.linalg.norm(b@ctx['uv'][ids]-point['sourceUV'])));coords.append(b@ctx['maps'][owner][ids]);world.append(b@ctx['world'][ids])
            assert max(errors)<1e-5,'Native UV curve does not match current topology'
            vis=rays.query(world);coordinates=np.array(coords);visible=np.array([q['faceVisibilityInterval'][0]>0 for q in vis]);columns,info=column_rows(coordinates,visible);bits,active,sourceIDs,unresolved=source_components(ctx,a,lo,owner,bank,groups);hh,ww=lo.shape[1:];h,w=hh//8,ww//8
            def reduce(x):return x.reshape(h,8,w,8).sum((1,3),dtype=float)/64
            lows=[];highs=[]
            for pi in [0,1]:mask=np.rint(a[pi+1,1,:,:,2])==owner;lows.append(reduce(lo[pi]*mask));highs.append(reduce(hi[pi]*mask))
            carrier=np.zeros((h,w),bool)
            for x,y in columns.items():
                if 0<=x<w and 0<=y<h:carrier[y,x]=bool(np.any(visible&(coordinates[:,0]>=x)&(coordinates[:,0]<=x+1)&(coordinates[:,1]>=y)&(coordinates[:,1]<=y+1)))
            variants=[]
            for componentFirst in [False,True]:
                layouts,solver=solve(lows[0],highs[0],lows[1],highs[1],columns,carrier,bits,active,componentFirst);exposures=[expose(ctx,alpha,rays,owner,b)for b in layouts];variants.append({'componentFirst':componentFirst,'solver':solver,'labels':[b.tolist()for b in layouts],'counts':[{'iris':int((b==1).sum()),'white':int((b==2).sum()),'line':int((b==3).sum())}for b in layouts],'exposure':exposures})
            eyeRows.append({'owner':owner,'whiteSourceMass':float(lows[1].sum()),'irisSourceMass':float(lows[0].sum()),'nativeCurveUVRegistrationMaxError':max(errors),'curve':info,'curveColumns':[[x,y]for x,y in columns.items()],'sourceIDs':sourceIDs,'sourceComponentUnresolved':unresolved,'variants':variants})
        # One frame file bounds working memory; all per-sample geometry remains available.
        result={'sourceId':ctx['sourceId'],'frame':ctx['frame'],'stage':m['motion82'],'actualGPUValidation':check,'eyes':eyeRows,'newSourceGeometryReplaces110Reconstruction':True,'runtimeAllocatorApplied':False,'finalRGBProduced':False};(H/f'ANALYSIS111-frame{ctx["frame"]}.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');out.append({'sourceId':ctx['sourceId'],'frame':ctx['frame'],'stage':m['motion82'],'GPUCheck':{k:v for k,v in check.items()if k!='checks'},'eyes':[{'owner':e['owner'],'whiteSourceMass':e['whiteSourceMass'],'irisSourceMass':e['irisSourceMass'],'unresolvedSourceComponents':len(e['sourceComponentUnresolved']),'counts':[(v['componentFirst'],v['counts'])for v in e['variants']]}for e in eyeRows]});print(json.dumps(out[-1]),flush=True)
    (H/'SUMMARY111.json').write_text(json.dumps({'actualGPUFrames':len(out),'PlayEntries':state['PlayEntries'],'frames':out,'stateRestoredExceptUnavailableImporterWrapper':True,'sourceCanonicalAndExposureSeparate':True,'runtimeSourceGeometryAndQueryExecuted':True,'runtime2_2AllocatorExecuted':False},indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
