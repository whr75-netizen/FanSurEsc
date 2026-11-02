"""Trace only completed113 inputs. No Unity/Play, no inferred missing samples."""
from pathlib import Path
import sys,json,hashlib,collections,zipfile
import numpy as np
from paths114 import H,R,folder
P=folder('113')
sys.path.insert(0,str(P))
from inputs113 import load_packets,plane,buffer,Reader

def read(p):
    if isinstance(p,Path)and not p.exists()and p.parent==H and(H/'DATA114.zip').exists():
        with zipfile.ZipFile(H/'DATA114.zip')as z:return json.loads(z.read(p.name))
    return json.loads(p.read_text(encoding='utf8'))
def matrix(a):return np.asarray(a).reshape(4,4,order='F')
def geometry(path,m):
    t=read(path/'SOURCE_TRANSFORMS111.json');r=Reader(path/'SOURCE_GEOMETRY111.bin');assert r.s()=='feature-source-geometry111/v1';sid=r.s();frame=r.i();serial=r.i();scope=r.s();assert sid==m['sourceId']==t['sourceId']and frame==m['frameIndex']==t['frame']and serial==m['mainSerial']==t['serial']
    n=r.i();world=r.a(n*4).reshape(n,4);rest=r.a(n*4).reshape(n,4);uv=r.a(n*2).reshape(n,2);nt=r.i();raw=r.take(nt*48);tr=np.frombuffer(raw,dtype=np.dtype([('ints','<i4',8),('owners','<f4',4)]));ix=tr['ints'][:,:4].copy();src=tr['ints'][:,4:].copy();owners=tr['owners'].copy();nm=r.i();materials=r.a(nm*12).reshape(nm,3,4);stride=r.i();count=r.i();partmap=r.a(count,'<i4').reshape(4,stride);r.end()
    view=matrix(t['currentPhysicalView']);projection=matrix(t['currentPhysicalProjection']);vv=world@view.T;clip=vv@projection.T
    return {'world4':world,'rest4':rest,'uv':uv,'triangles':ix,'sources':src,'owners':owners,'materials':materials,'partMap':partmap,'view':view,'projection':projection,'physicalXY':np.c_[(clip[:,0]/clip[:,3]*.5+.5)*480,(.5-clip[:,1]/clip[:,3]*.5)*272],'depth':-vv[:,2],'physicalW':clip[:,3],'transforms':t}
def transferred_sample(ctx,part,rest,primitive):
    ti=int(ctx['partMap'][part,primitive-1]);assert ti>=0
    ids=ctx['triangles'][ti,:3];v=ctx['rest4'][ids,:3].astype(float);q=np.linalg.lstsq(np.stack([v[1]-v[0],v[2]-v[0]],axis=1),rest-v[0],rcond=None)[0];b=np.r_[1-q.sum(),q]
    world=b@ctx['world4'][ids];view=ctx['view']@world;clip=ctx['projection']@view
    return {'triangle':ti,'sourcePrimitive':primitive,'barycentric':b.tolist(),'world':world[:3].tolist(),'nativePhysicalXY':[(clip[0]/clip[3]*.5+.5)*480,(.5-clip[1]/clip[3]*.5)*272],'nativeDepth':float(-view[2]),'sourceUV':(b@ctx['uv'][ids]).tolist()}
def arrays(path,prefix):
    return {n:np.flipud(plane(path/(prefix+n+'.plane'))[1])for n in['rgba','meta','rest','uv']}
def main():
    _,packets=load_packets(P);rows=[];all_samples=[]
    for entry,path in packets:
        m=read(path/'RAW_MANIFEST.json');ctx=geometry(path,m);cw,ch=np.array(m['forward102']['canonicalSize'])//4;sw,sh=m['forward102']['denseSize'];sourceOrigin=np.array(m['forward102']['nativeRegistration']['anchor'])+np.array(m['forward102']['nativeRegistration']['bounds'][:2]);carrierOrigin=np.array(ctx['transforms']['carrier']['anchor'])+np.array(ctx['transforms']['carrier']['bounds'][:2]);roi=np.array(m['grid102']['eyeTopLeftROI']);fw,fh=map(int,roi[2:]);uniformROIY=272-roi[1]-roi[3];ids=buffer(path/'curve-identity.f32').reshape(ch,cw,4);audit=buffer(path/'curve-audit.f32').reshape(ch,cw,4);decision=buffer(path/'curve-decision.f32').reshape(ch,cw,4);cells=buffer(path/'REGION113-cells.f32').reshape(512,7,4);ex=buffer(path/'REGION113-exposure.f32').reshape(512,2,4)[:fw*fh].reshape(fh,fw,2,4);C={p:arrays(path,f'C-part{p}-')for p in[1,2,3]};D={p:arrays(path,'D-lid-'if p==3 else f'D-part{p}-')for p in[1,2,3]};vis=buffer(path/'carrier-three-part-visibility.f32').reshape(3,sh,sw,4);dvis=buffer(path/'dense-three-part-visibility.f32').reshape(3,sh,sw,4);hairmeta=plane(path/'S4-meta.plane')[1];hairrgba=plane(path/'S4-rgba.plane')[1];issues=[]
        selected=ex[:,:,1,3]<0
        if '--all-selected'in sys.argv:
            selected=np.zeros((fh,fw),bool)
            for py in range(fh):
                for px in range(fw):
                    absolute=np.array([roi[0]+px+.5,272-(uniformROIY+py+.5)]);cx,cy=np.floor(absolute-sourceOrigin).astype(int)
                    if 0<=cx<cw and 0<=cy<ch:selected[py,px]=ids[cy,cx,0]>0
        for py,px in np.argwhere(selected):
            absolute=np.array([roi[0]+px+.5,272-(uniformROIY+py+.5)]);cx,cy=np.floor(absolute-sourceOrigin).astype(int);id=ids[cy,cx]if 0<=cx<cw and 0<=cy<ch else np.zeros(4);part={1:1,4:2,6:3}.get(int(id[0]),0);owner=int(id[1]);assert part>0
            fine=[]
            for yy in range(4):
                for xx in range(4):
                    desired=np.array([roi[0]+px+(xx+.5)/4,272-(uniformROIY+py+(yy+.5)/4)]);qx,qy=np.floor((desired-carrierOrigin)*8).astype(int);assert 0<=qx<sw and 0<=qy<sh;meta=C[part]['meta'][qy,qx];vv=vis[part-1,qy,qx];known=meta[0]>0 and round(float(meta[2]))==owner;hit=hairmeta[py*4+yy,px*4+xx];hc=hairrgba[py*4+yy,px*4+xx];record={'fineXY':[xx,yy],'desiredPhysicalXY':desired.tolist(),'carrierFineXY':[int(qx),int(qy)],'queryPhysicalXY':(carrierOrigin+(np.array([qx,qy])+.5)/8).tolist(),'coordinateDelta':(carrierOrigin+(np.array([qx,qy])+.5)/8-desired).tolist(),'validNativeCarrier':bool(known),'rawCarrierOwner':int(round(float(meta[2]))),'rawCarrierDepth':float(meta[0])if meta[0]>0 else None,'faceInterval':vv[:2].tolist()if known else None,'queryDepth':float(vv[2])if known else None,'queryOverflow':int(vv[3])if known else None,'hairDepth':float(hit[0])if hit[0]>0 and hc[3]>0 else None,'hairAlphaCoverage':float(hit[3])if hit[0]>0 and hc[3]>0 else 0}
                    if known:
                        primitive=int(round(float(C[part]['uv'][qy,qx,2])));record['source']=transferred_sample(ctx,part,C[part]['rest'][qy,qx,:3],primitive);record['nativePhysicalVsQueryDelta']=(np.array(record['source']['nativePhysicalXY'])-record['queryPhysicalXY']).tolist();record['depthError']=record['source']['nativeDepth']-record['rawCarrierDepth'];all_samples.append(record)
                    fine.append(record)
            cellLow=np.array([roi[0]+px,roi[1]+fh-py-1]);start=np.rint((cellLow-carrierOrigin)*8).astype(int);sx,sy=start;patch=vis[part-1,sy:sy+8,sx:sx+8];metaPatch=C[part]['meta'][sy:sy+8,sx:sx+8];valid=(metaPatch[...,0]>0)&(np.rint(metaPatch[...,2])==owner);mass64=(patch[...,:2]*valid[...,None]).sum((0,1));current=ex[py,px];faceKnown=sum(q['validNativeCarrier']for q in fine);faceSum=np.sum([q['faceInterval']for q in fine if q['faceInterval']is not None],axis=0)if faceKnown else np.zeros(2);assert np.array_equal(faceSum,current[0,:2]);assert faceKnown==int(current[1,2])
            issues.append({'tileXYBottomLeft':[int(px),int(py)],'mainXYBottomLeft':[int(roi[0]+px+round(m['grid102']['headToMainOffset'][0])),int(uniformROIY+py+round(m['grid102']['headToMainOffset'][1]))],'canonicalXY':[int(cx),int(cy)],'owner':owner,'part':int(id[0]),'finalStatus':int(current[1,3]),'face16Interval':current[0,:2].tolist(),'hair16Interval':current[0,2:].tolist(),'knownCarrier16':faceKnown,'validCarrier64':int(valid.sum()),'face64Interval':mass64.tolist(),'unknownHairOnlyMissingCarrier':bool(current[1,3]==-113 and any(not q['validNativeCarrier']and q['hairAlphaCoverage']>0 for q in fine)),'singleOwnerDepthUsed':False,'fine':fine})
        unsupported=[]
        for cy,cx in np.argwhere(audit[:,:,0]==-1):
            cell=cells[cy*cw+cx];owner=int(cell[3,0]);meta=D[3]['meta'][cy*8:cy*8+8,cx*8:cx*8+8];rgba=D[3]['rgba'][cy*8:cy*8+8,cx*8:cx*8+8];vv=dvis[2,cy*8:cy*8+8,cx*8:cx*8+8];unsupported.append({'canonicalXY':[int(cx),int(cy)],'owner':owner,'depthSampleRecorded':None,'matchedOwnerSourceMeta64':int(((meta[...,0]>0)&(np.rint(meta[...,2])==owner)).sum()),'positiveSourceRGBAAlpha64':int((rgba[...,3]>0).sum()),'positiveCertainVisibility64':int((vv[...,0]>0).sum()),'uncertainVisibility64':int((vv[...,0]!=vv[...,1]).sum()),'overflow64':int((vv[...,3]>0).sum()),'alphaMax64':float(rgba[...,3].max()),'unmeasuredDepthError':None})
        rows.append({'sourceId':entry['sourceId'],'frame':entry['frame'],'close':m['motion82']['requestedClose'],'sourceOrigin':sourceOrigin.tolist(),'carrierOrigin':carrierOrigin.tolist(),'physicalProjectionEqualsEffective':m['displayPhysicalProjectionEqual113'],'issues':issues,'unsupportedSourceLid':unsupported})
    result={'frames':rows,'issuesCount':sum(len(r['issues'])for r in rows),'matchedCarrierSamples':len(all_samples),'matchedDepthMaxError':max(abs(q['depthError'])for q in all_samples)if all_samples else None,'sampleCoordinateDeltaValues':sorted({tuple(q['coordinateDelta'])for r in rows for c in r['issues']for q in c['fine']}),'unmeasuredNotScoredAsZero':True,'runtimeExecuted':False}
    out='TRACE_ALL114.json'if'--all-selected'in sys.argv else'TRACE114.json';result['allSelectedCellsNotOnlyFailures']='--all-selected'in sys.argv
    (H/out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'file':out,'cases':result['issuesCount'],'matchedSamples':result['matchedCarrierSamples'],'maxDepthError':result['matchedDepthMaxError'],'coordinateDeltas':result['sampleCoordinateDeltaValues']},ensure_ascii=False))
if __name__=='__main__':main()
