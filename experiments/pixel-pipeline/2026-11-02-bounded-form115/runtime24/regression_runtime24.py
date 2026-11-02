"""Saved-source CPU mirrors of runtime geometry. No GPU-result fabrication."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
H=Path(__file__).resolve().parent;B=H.parent;sys.path.insert(0,str(B))
from direct_support24 import P,F,sibling
from geometry24 import affiliation,ring_limits,transport_assigned_depth,column_curve
T=sibling('eye-failures114');sys.path.insert(0,str(T));sys.path.insert(0,str(P))
from inputs113 import load_packets,buffer,plane
from trace114 import geometry,read
from geometry114 import mapped,Face114
from pairing114 import compose
from pigment114 import clip_column

def check_prepared():
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    prepared=read(H/'PREPARED_RUNTIME24.json')
    for name,digest in prepared['files'].items():assert sha(H/name)==digest,name
    hlsl=read(H/'HLSL_RUNTIME24.json');assert not hlsl['GPUDeviceCreated'] and not hlsl['GPUDriverModules'] and hlsl['GPUOrUnityCalls']==0 and len(hlsl['kernels'])==15
    for k in hlsl['kernels']:
        assert k['sourceSHA256']==sha(H/'ForwardEye113_Geometry24.compute')
        if k['entry']not in ['Select','GatherEye113']:assert not any(w in k['diagnostics']for w in ['X4714','X3550','X3556','forcing loop'])
        arrays=k['audit']['privateArrayDeclarations']
        if k['entry']not in ['Select','GatherEye113']:assert len(arrays)==(1 if k['entry']in ['Query','ColumnVisibility24','AssignedVisibility24']else 0)
        for b in k['bindings']:
            if b['Name']=='_Columns24':assert b['NumSamples']==48
            if b['Name']=='_CurveProof24':assert b['NumSamples']==32
            if b['Name']in ['_AssignedDepth24','_AssignedVisibility24']:assert b['NumSamples']==16
    cs=read(H/'CS_RUNTIME24.json');assert cs['success']and not cs['compiledOutputExecuted']and cs['GPUOrUnityCalls']==0
    for name,digest in cs['candidateSourceSHA256'].items():assert sha(H/name)==digest
    forward=(H/'Forward113_Geometry24.cs').read_text();driver=(H/'RegionDriver113_Geometry24.cs').read_text();source=(H/'SourcePigment113_Geometry24.cs').read_text()
    draw=forward[forward.index(' void Draw('):forward.index(' public void AssertRendered')]
    assert draw.index('RefitOnly24(')<draw.index('Region.Draw(')<draw.index('Region.PrepareCarrier(')<draw.index('ComposeRegion113(cmd)')
    assert 'Vector2 carrierOrigin,Vector2 sourceAnchor' in driver and 'new Vector4(sourceAnchor.x,sourceAnchor.y,0,0)'in driver
    assert 'new Vector4(carrierOrigin.x,carrierOrigin.y,0,0)'in driver
    assert 'Proof?.Dispose();Proof=null;proofRows24=null;uv24.Clear();'in source and 'ValidateUV24();mesh.GetVertices(vertices);'in source
    for name in prepared['files']:
        if Path(name).suffix not in ['.cs','.compute']:continue
        s=(H/name).read_text()
        for banned in ['EvaluateForm115','BoundRun115','Forward115','GetData(','WaitForCompletion','SetGlobalBuffer','InputSystem.settings=','SaveAssets','ClearDirty','GC.Collect']:
            assert banned not in s,(name,banned)
    from host_audit24 import functions
    before=functions((B/'ForwardEye113_Direct24.compute').read_text());after=functions((H/'ForwardEye113_Geometry24.compute').read_text())
    for name in ['BuildSubsets113','Enumerate113','Reduce113','Write113','PackPart','Refit','Select','GatherEye113']:assert before[name]['source']==after[name]['source']
    return {'hlslKernels':15,'CSharpLinkedBundle':True,'fourAllocatorBodiesPreserved':True,'CPUHelpersAreNotUploadedAsGPUResults':True,'newOwnedGPUBytesPerView':1024*48+2*512*16*16+846*32,'shaderSHA256':sha(H/'ForwardEye113_Geometry24.compute'),'binaryBindingsSHA256':sha(H/'GEOMETRY_BINDINGS24.bin')}

def midpoint(segments,owner,x):
    pieces=[]
    for i,(a,b)in enumerate(segments):
        if round(float(a[3]))!=owner:continue
        v=clip_column(a[:3].astype(float),b[:3].astype(float),x)
        if v is None:continue
        aa,bb=v;arc=np.linalg.norm(bb[:2]-aa[:2])
        if arc>0:pieces.append((i,aa,bb,arc))
    total=sum(p[3]for p in pieces)
    if total<=0:return None
    meanY=sum((p[1][1]+p[2][1])*.5*p[3]for p in pieces)/total;row=int(np.floor(meanY));clipped=[]
    for i,a,b,arc in pieces:
        d=b-a;lo=0.;hi=1.
        if abs(d[1])<1e-12:
            if a[1]<row or a[1]>row+1:continue
        else:
            t,u=(row-a[1])/d[1],(row+1-a[1])/d[1];lo=max(lo,min(t,u));hi=min(hi,max(t,u))
            if hi<=lo:continue
        aa=a+d*lo;bb=a+d*hi;length=float(np.linalg.norm(bb[:2]-aa[:2]))
        if length>0:clipped.append((i,aa,bb,length))
    cellArc=sum(p[3]for p in clipped);cursor=0
    for i,a,b,arc in clipped:
        if cursor+arc<cellArc*.5:cursor+=arc;continue
        point=a+(b-a)*np.clip((cellArc*.5-cursor)/arc,0,1)
        original_a,original_b=segments[i];d=original_b[:2]-original_a[:2]
        u=float(np.dot(point[:2]-original_a[:2],d)/np.dot(d,d))
        assert row<=point[1]<=row+1
        return {'segment':i,'point':point,'u':u,'arc':float(total),'cellArc':cellArc,'meanY':float(meanY)}
    return None
def transport(z,source,limits):
    z=np.asarray(z,np.float32).copy();known=z>0;count=int(known.sum());total=np.float32(0)
    for value in z[known]:total=np.float32(total+value)
    fill=np.float32(total/np.float32(count))if count else np.float32(source if limits[0]<=source<=limits[1]else 0)
    z[~known]=fill;return z,count
def destination(main):
    x,y=main;return np.array([[np.float32(x+(i%4+.5)/4),np.float32(272-(y+(i//4+.5)/4))]for i in range(16)],np.float32)
def layer_depth(meta,point,origin,owner):
    q=np.floor((point-np.asarray(origin,np.float32))*8).astype(int)
    if (q<0).any()or q[0]>=meta.shape[1]or q[1]>=meta.shape[0]:return 0.
    m=meta[q[1],q[0]];return float(m[0])if m[0]>0 and round(float(m[2]))==owner else 0.
def check_weights(vis):
    # Same multiplication order as the original q=0,1,2 loop. Explicit scalar
    # roles avoid the original dynamic float3 l-value/forced-unroll warning.
    z=vis[:,:,2];a=vis[:,:,:2].copy();old=a.copy();new=a.copy()
    for p in range(3):
        for q in range(3):
            if p==q:continue
            active=(z[:,q]>0)&(a[:,q,1]>0);front=active&(z[:,q]<z[:,p]-3e-5);same=active&(abs(z[:,q]-z[:,p])<=3e-5)&~front
            old[front,p,0]*=1-a[front,q,1];old[front,p,1]*=1-a[front,q,0];old[same,p,0]*=1-a[same,q,1]
    for p,others in enumerate([(1,2),(0,2),(0,1)]):
        for q in others:
            active=(z[:,q]>0)&(a[:,q,1]>0);front=active&(z[:,q]<z[:,p]-3e-5);same=active&(abs(z[:,q]-z[:,p])<=3e-5)&~front
            new[front,p,:]*=1-a[front,q,::-1];new[same,p,0]*=1-a[same,q,1]
    assert np.array_equal(old.view(np.uint32),new.view(np.uint32))
    return len(vis)

def main():
    compiled=check_prepared()
    cache=affiliation();native=read(B.parent/'pigment-carrier109/NATIVE_CACHE109.json');proof=[(a,b)for c in native['curves']for a,b in zip(c['points'],c['points'][1:])]
    source=read(P/'SOURCE113.json');reg=read(T/'REGISTRATION_CURRENT102.json');traces=read(T/'TRACE_ALL114.json');changes=read(F/'DELTA_CLASSIFICATION115.json')
    wanted={(r['frame'],tuple(r['mainXYBottomLeft'])):r for r in changes['rows']};_,packets=load_packets(P)
    rows=[];curves=[];ghost=[];bridge=[];scale=0;weights=0;sourceUVError=0.;directRetained=0;coordinateChecks=0;columnChecks=0;proofBindings=0
    for entry,packet in packets:
        frame=entry['frame'];manifest=read(packet/'RAW_MANIFEST.json');raw=geometry(packet,manifest);trace=next(r for r in traces['frames']if r['frame']==frame)
        ctx=mapped(raw,reg,np.array(trace['carrierOrigin']));face=Face114(ctx,source['ownSkinMask']);limits=ring_limits(ctx,cache)
        Cmeta={part:plane(packet/f'C-part{part}-meta.plane')[1][::-1]for part in [1,2,3]}
        Cvis=buffer(packet/'carrier-three-part-visibility.f32').reshape(3,-1,4)
        for part in [1,2,3]:
            C=Cmeta[part].reshape(-1,4);V=Cvis[part-1];valid=V[:,2]>0
            assert np.array_equal(C[valid,0],V[valid,2]),'Declared RT/PackPart flip must match saved visibility depth'
        weights+=check_weights(buffer(packet/'dense-three-part-visibility.f32').reshape(3,-1,4).transpose(1,0,2))
        for owner,lim in limits.items():
            for multiplier in [.5,1,2]:
                assert np.isclose(lim['diameterWorld']*multiplier,np.linalg.norm(ctx['world4'][np.asarray(cache['rings'][str(owner)]['sourceVertices'])+cache['captureFaceVertexOffset'],None,:3]*multiplier-ctx['world4'][None,np.asarray(cache['rings'][str(owner)]['sourceVertices'])+cache['captureFaceVertexOffset'],:3]*multiplier,axis=2).max(),rtol=2e-6)
                scale+=1
        selected=buffer(packet/'curve-colour.f32');identity=buffer(packet/'curve-identity.f32');width=manifest['forward102']['canonicalSize'][0]//4
        canvas=plane(packet/'L0-RGBA.plane')[1];canvasmeta=plane(packet/'L0-META.plane')[1];hairmeta=plane(packet/'S4-meta.plane')[1];hairrgba=plane(packet/'S4-rgba.plane')[1]
        if frame in [103,111]:
            allocation=next(r for r in read(B/'DIRECT_SUPPORT24.json')['rows']if r['frame']==frame and r['owner']==2)
            target=next(v for v in allocation['selectedCellsYX'][0]if v['part']==1 and v['YX']==[5,6]);assert allocation['sourceId']==entry['sourceId']and allocation['withExisting113KeyFallback']==[1]
            cy,cx=target['YX'];cellData=buffer(packet/'REGION113-cells.f32').reshape(512,7,4)[cy*width+cx];roi=manifest['grid102']['eyeTopLeftROI'];rh,rw=canvas.shape[0]//4,canvas.shape[1]//4
            found=[]
            for py in range(rh):
                for px in range(rw):
                    base=[roi[0]+px,272-roi[1]-roi[3]+py];centre=np.array([base[0]+.5,272-(base[1]+.5)])
                    if not np.array_equal(np.floor(centre-np.asarray(trace['sourceOrigin'])).astype(int),[cx,cy]):continue
                    points=destination(base);depths=np.asarray([layer_depth(Cmeta[2],q,trace['carrierOrigin'],2)for q in points],np.float32);z,known=transport(depths,cellData[3,2],limits[2]['depthRange']);assert(z>0).all()
                    interval=np.asarray([q['faceInterval']for q in face.query(points,z,2,limit=limits[2]['diameterWorld'])]);fake={'fine':[{'fineXY':[i%4,i//4]}for i in range(16)]}
                    result=compose(fake,interval,z,canvas[py*4+1,px*4+1],canvasmeta[py*4+1,px*4+1],cellData[2],4,2,hairmeta[py*4:py*4+4,px*4:px*4+4],hairrgba[py*4:py*4+4,px*4:px*4+4]);found.append({'physicalXYBottomLeft':base,'knownRaster16':known,'faceInterval':interval.sum(0).tolist(),'result':result})
            assert found
            bridge.append({'frame':frame,'sourceId':entry['sourceId'],'selectedCanonicalXY':[cx,cy],'selectionSource':'CPU Direct24 oracle only; no GPU output claimed or uploaded','allocatedRole':4,'partSourceDepth':float(cellData[3,2]),'destinations':found})
        for case in trace['issues']:
            key=(frame,tuple(case['mainXYBottomLeft']))
            if key not in wanted:continue
            owner=case['owner'];role=case['part'];part={1:1,4:2,6:3}[role];px,py=case['tileXYBottomLeft'];roi=manifest['grid102']['eyeTopLeftROI'];surfaceXY=[roi[0]+px,272-roi[1]-roi[3]+py]
            # mainXYBottomLeft includes headToMainOffset and is a display label,
            # not the source-view query coordinate. Never feed it into a ray.
            points=destination(surfaceXY);assert np.array_equal(points,np.asarray([f['desiredPhysicalXY']for f in case['fine']],np.float32));coordinateChecks+=16
            depths=np.asarray([layer_depth(Cmeta[part],p,trace['carrierOrigin'],owner)for p in points],np.float32)
            at=case['canonicalXY'][1]*width+case['canonicalXY'][0];z,count=transport(depths,identity[at,2],limits[owner]['depthRange']);assert np.array_equal(z[depths>0],depths[depths>0]);directRetained+=count
            assert (z>0).all();query=face.query(points,z,owner,limit=limits[owner]['diameterWorld']);interval=np.array([q['faceInterval']for q in query]);px,py=case['tileXYBottomLeft']
            result=compose(case,interval,z,canvas[py*4+1,px*4+1],canvasmeta[py*4+1,px*4+1],selected[at],role,owner,hairmeta[py*4:py*4+4,px*4:px*4+4],hairrgba[py*4:py*4+4,px*4:px*4+4])
            rows.append({'frame':frame,'sourceId':entry['sourceId'],'mainXY':case['mainXYBottomLeft'],'surfaceXYBottomLeft':surfaceXY,'part':role,'owner':owner,'category':wanted[key]['category'],'directRasterDepthCount':count,'queryPhysicalXY16':points.tolist(),'transportedDepth16':z.tolist(),'faceInterval16':interval.sum(0).tolist(),'result':result,'actualExternalHairRetained':wanted[key]['category']!='definite_hair_at_matched_destination'or result['hairInterval'][0]>=8})
        rawSeg=(packet/'curve-segments106.f32').read_bytes();count,stride=struct.unpack_from('<ii',rawSeg);assert stride==32 and count==len(proof);segments=np.frombuffer(rawSeg,offset=8,dtype='<f4').reshape(count,2,4)
        for cu in native['curves']:
            for point in cu['points']:
                uv=np.asarray(point['barycentric'])@ctx['uv'][np.asarray(point['vertices'])+cache['captureFaceVertexOffset']];sourceUVError=max(sourceUVError,float(abs(uv-point['sourceUV']).max()))
                ti=int(ctx['partMap'][0,point['primitive']-1]);assert ti>=0 and np.array_equal(ctx['sources'][ti,:3],[1,3,point['primitive']]);proofBindings+=1
        for owner in [1,2]:
            for x in range(width):
                reference=column_curve(segments,owner,x);candidate=midpoint(segments,owner,x)
                if reference is None:assert candidate is None;continue
                if candidate is not None:assert np.floor(reference['midXYZ'][1])==np.floor(candidate['meanY'])and int(np.floor(candidate['point'][1]))==int(np.floor(candidate['meanY']))
                columnChecks+=1
        if frame==107:
            roles=identity[:,0];ghost.append({'frame':frame,'sourceId':entry['sourceId'],'savedAssignedIrisWhite':int(np.isin(roles,[1,4]).sum()),'note':'Input-no-ghost invariant only; final new GPU composition not captured.'});assert not np.isin(roles,[1,4]).any()
            for missing in trace['unsupportedSourceLid']:
                owner=missing['owner'];x,y=missing['canonicalXY'];mid=midpoint(segments,owner,x);assert mid is not None
                a,b=proof[mid['segment']];uv=np.asarray(a['sourceUV'])*(1-mid['u'])+np.asarray(b['sourceUV'])*mid['u'];ti=[int(ctx['partMap'][0,a['primitive']-1])];assert ti[0]>=0 and np.array_equal(ctx['sources'][ti[0],:3],[1,3,a['primitive']])
                alpha=face.alpha.bounds(int(ctx['triangles'][ti[0],3]),[uv])[0];point=np.asarray(trace['sourceOrigin'])+mid['point'][:2];visible=face.query([point],[mid['point'][2]],owner,limit=limits[owner]['diameterWorld'])[0]
                curves.append({'frame':frame,'sourceId':entry['sourceId'],'canonicalXY':[x,y],'owner':owner,'arcLengthPixels':mid['arc'],'midpointXYZ':mid['point'].tolist(),'sourceUV':uv.tolist(),'nativePrimitive':a['primitive'],'sourceAlphaBounds':alpha.tolist(),'externalFaceInterval':visible['faceInterval'],'fallbackEligible':bool(alpha[0]>0 and visible['faceInterval'][0]>0 and visible['faceInterval'][0]==visible['faceInterval'][1])})
    assert len(rows)==22 and all(r['actualExternalHairRetained']for r in rows)
    assert curves and all(c['fallbackEligible']for c in curves)
    # Boundary conditions are separate from measured cases: missing all source
    # depths cannot synthesize geometry or resurrect a rejected/closed identity.
    a,n=transport(np.zeros(16),2.,[1.,1.5]);assert n==0 and not a.any()
    a,n=transport(np.zeros(16),1.2,[1.,1.5]);assert n==0 and (a==np.float32(1.2)).all()
    synthetic=np.full(16,1.2,np.float32);synthetic[3]=0;z,n=transport(synthetic,9,[1,2]);assert n==15 and(z>0).all()
    status={str(k):sum(r['result']['status']==k for r in rows)for k in sorted({r['result']['status']for r in rows})}
    result={'GPUOrUnityCalls':0,'runtimeGPUVerified':False,'scope':'Runtime CPU mirrors on same-source saved113 data; no current GPU outputs uploaded or fabricated.','sourceFrames':len(packets),'changedCoordinateCases':len(rows),'destinationCoordinatesChecked':coordinateChecks,'measuredRasterDepthsUnchanged':directRetained,'statusCounts':status,'weightVectorScalarBitwiseChecks':weights,'ringDiameterScaleChecks':scale,'sourceUVMaxError':sourceUVError,'nativeSkinSlot0BindingsChecked':proofBindings,'unchangedBoundaryColumnRowsChecked':columnChecks,'close100InputGhostChecks':ghost,'curveEndRecovery':curves,'rows':rows,'limitations':['Native direct depths remain raster samples at their recorded8x cells; exact destination visibility uses16 distinct coordinates. Missing values are explicit assigned-cell transport, not newly measured geometry.','Scale checks cover evaluated ring geometry and socket policy; absolute3e-5 depth epsilon is not claimed scale invariant.','Close100/reopen/motion and final RGB/owner remain GPU-unverified.','Pure CPU texture/geometry query cannot attest driver compilation/scheduling or device safety.']}
    result['preparedSourceChecks']=compiled
    result['allocatorToTransportBridgeCPUOnly']=bridge
    (H/'REGRESSION_RUNTIME24.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='rows'},indent=2))
if __name__=='__main__':main()
