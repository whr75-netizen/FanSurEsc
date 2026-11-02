"""Static operation/range audit using frozen113 inputs. Never calls Unity/GPU."""
from pathlib import Path
import hashlib,json,math,sys,collections
import numpy as np
H=Path(__file__).resolve().parent
def sibling(local,repo):
    a=H.parent/local
    return a if a.exists()else H.parent/repo
P=sibling('argon23-runtime113','2026-11-02-argon23-runtime113')
F=sibling('gpu-form115','2026-11-02-gpu-form115')
T=sibling('eye-failures114','2026-11-02-eye-failures114')
sys.path[:0]=[str(P),str(T)]
from inputs113 import load_packets,buffer
from trace114 import geometry
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw_connected(cells,tags,owner,part,bit,n,w):
    selected=[i for i in range(n)if round(float(cells[i,3,0]))==owner and int(tags[i,part])&bit]
    visits=n
    if len(selected)<2:return True,0,visits
    seen={selected[-1]};passes=0
    for _ in range(512):
        passes+=1;visits+=n;changed=False
        for i in range(n):
            if i in seen or round(float(cells[i,3,0]))!=owner or not int(tags[i,part])&bit:continue
            near=(i%w>0 and i-1 in seen)or(i%w+1<w and i+1 in seen)or(i>=w and i-w in seen)or(i+w<n and i+w in seen)
            if near:seen.add(i);changed=True
        if not changed:break
    return len(seen)==len(selected),passes,visits
def main():
    source=json.loads((P/'SOURCE113.json').read_text());reference=json.loads((F/'REFERENCE115.json').read_text());_,packets=load_packets(P)
    k=len(source['keys']);own=len(source['ownSkinMask']);cases=[];scope_checks=0;finite_geometry_cases=0
    for item,path in packets:
        meta=json.loads((path/'RAW_MANIFEST.json').read_text());frame=buffer(path/'REGION113-frame.f32').view(np.uint32).reshape(64,4);cells=buffer(path/'REGION113-cells.f32').reshape(512,7,4);tags=buffer(path/'REGION113-tags.f32').view(np.uint32).reshape(512,4);w,h=(int(x)//4 for x in meta['forward102']['canonicalSize']);n=w*h
        assert n<=512 and list(meta['forward102']['denseSize'])==[w*8,h*8]
        geom=geometry(path,meta)
        assert all(np.isfinite(geom[name]).all()for name in ['world4','rest4','view','projection']);finite_geometry_cases+=1
        row={'sourceId':item['sourceId'],'frame':item['frame'],'cellsWH':[w,h],'cells':n,'curveSegments':meta['forward102']['curves106']['segments'],'boundaryCells':int(sum(cells[:n,5,0]==2)),'eyes':[]}
        ref=next(r for r in reference['rows']if r['frame']==item['frame'])
        for eye in range(2):
            np_,ni,nw,bad=map(int,frame[eye*32]);assert np_<=24 and ni<=12 and nw<=12 and ni+nw<=21 and bad==0
            owner=eye+1;pts=[i for i in range(n)if round(float(cells[i,3,0]))==owner and cells[i,5,0]==1 and cells[i,0,0]+cells[i,0,2]>0];assert len(pts)==np_
            passes=[];visits=0
            for part in range(2):
                active=int(frame[eye*32+2,part])
                for bit in range(8):
                    if not active&(1<<bit):continue
                    connected,iteration,scans=raw_connected(cells,tags,owner,part,1<<bit,n,w);passes.append(iteration);visits+=scans
                    scope=sum(1<<p for p,c in enumerate(pts)if int(tags[c,part])&(1<<bit))if connected else 0
                    assert scope==int(frame[eye*32+4+part*8+bit,0]);scope_checks+=1
            r=ref['eyes'][eye]
            row['eyes'].append({'owner':owner,'points':np_,'irisBits':ni,'whiteBits':nw,'stateBits':ni+nw,'eligibleJointStates':1<<(ni+nw),'eligiblePartSubsets':(1<<ni)+(1<<nw),'sourceFormInputCandidates':r['primaryFourMetricOptima'],'sourceFormSurvivorsCPU':r['sourceFormSurvivors'],'rawConnectivityMaxPassesObserved':max(passes,default=0),'rawConnectivityCellScansCPUReplay':visits})
        row['eligibleJointStatesBothEyes']=sum(e['eligibleJointStates']for e in row['eyes']);cases.append(row)
    first=packets[0][1];g=geometry(first,json.loads((first/'RAW_MANIFEST.json').read_text()));v=len(g['world4']);t=len(g['triangles']);m=len(g['materials']);stride=g['partMap'].shape[1];nodes=2*t-1
    assert v<=131072 and t<=262144 and np.all(g['triangles'][:,:3]>=0)and np.all(g['triangles'][:,:3]<v)and np.all(g['triangles'][:,3]>=0)and np.all(g['triangles'][:,3]<m)
    mapped=g['partMap'];assert np.all((mapped==-1)|((mapped>=0)&(mapped<t)))
    for part,submesh in enumerate([3,1,4,6]):
        for primitive,index in enumerate(mapped[part],1):
            if index<0:continue
            assert list(g['sources'][index,:3])==[1,submesh,primitive]
    topology_bytes=t*48+v*(16+8+16)+4*stride*4+nodes*(16+32+4)+m*48+8*4
    n=cases[0]['cells'];pixel_bytes=lambda scale:n*scale*scale*580
    region113=k*48+own*4+512*7*16+512*16+64*16+48*16+65536*48+2*48+16384*32+1024*16
    extras=512*k*32+k*32+2*16+256*16+256*80+256*4+2*48
    header_cases=[(a,b)for a in range(13)for b in range(13)if a+b<=21];assert len(header_cases)==163 and max(1<<(a+b)for a,b in header_cases)==2097152
    valid_subsets_both=2*max((1<<a)+(1<<b)for a,b in header_cases);assert valid_subsets_both==9216
    shape_bounds={'cellMomentMaxIndex':512*k-1,'cellMomentElements':512*k,'pointsMaxIndex':47,'pointsElements':48,'frameScopeMaxIndex':51,'frameElements':64,'subsetMaxIndex':16383,'subsetElements':16384,'groupMaxIndex':65535,'groupElements':65536,'candidateMetricMaxIndex':255,'candidateMetricElements':256}
    assert all(shape_bounds[a]<shape_bounds[b]for a,b in [('cellMomentMaxIndex','cellMomentElements'),('pointsMaxIndex','pointsElements'),('frameScopeMaxIndex','frameElements'),('subsetMaxIndex','subsetElements'),('groupMaxIndex','groupElements'),('candidateMetricMaxIndex','candidateMetricElements')])
    sizes={'Key113':48,'Group113':48,'Subset113':32,'Stat115':32,'Metric115':80,'Triangle107':48,'MaterialData107':48};assert region113==3771712
    report={'schema':'gpu-static-audit115/v1','UnityCalls':0,'GPUDispatches':0,'current115GPUHeadersAvailable':False,'source113HeadersAreNotFailed115Frame':True,'inputSHA256':{'ForwardEye115.compute':sha(F/'ForwardEye115.compute'),'RegionDriver115.cs':sha(F/'RegionDriver115.cs')},'stored113Cases':cases,'scopeReplayChecksPassed':scope_checks,'finiteHeaderBoundaryCases':len(header_cases),'nominalLargeDispatch':{'groupsXY':[32768,2],'threadsPerGroup':64,'workItemsPerDispatch':4194304,'original113Enumerations':1,'combined115EnumerationsAndCollection':3,'combinedNominalWorkItems':12582912},'maximumBounds':{'cells':512,'keys':32,'curveSegments':1024,'points':24,'partBits':12,'jointBits':21,'jointStatesPerEye':2097152,'formPoolPerEye':128,'formPairComparisonsPerEye':128*127,'formDimensionTestsPerEye':128*127*6,'rawConnectivityCellScansBothEyes':2*16*(512+512*512),'subsetConnectivityPointIterationsAllDispatchedRows':16384*8*24*24,'curveDistanceTestsAllCells':512*64*1024,'prepareSourceKeyComparisons':512*64*2*32,'queryPixelsPerEngine':32768,'queryRaysPerEngine':32768*4,'triangles':262144,'bvhNodes':524287,'bvhTraversalVisitUpperBoundForValidTree':524287,'bvhKernelHasExplicitVisitBudget':False,'privateMetricArrayFloatsPerInvocation':5*32*2,'privateMetricArrayBytesPerInvocation':5*32*2*4},'currentSourceDimensions':{'vertices':v,'triangles':t,'materials':m,'partPrimitiveStride':stride,'bvhNodes':nodes,'balancedTreeMaxDepth':math.ceil(math.log2(t)),'keys':k,'keyDistribution':{f'{owner}/{part}':count for(owner,part),count in collections.Counter((x['owner'],x['part'])for x in source['keys']).items()},'gridCells':n,'original113QueryRays':n*(16+64+64)*4,'combined115QueryRays':n*(16+64+64+16)*4},'structuredBuffers':{'sizes':sizes,'rangeProofs':shape_bounds,'sourceTopologyIndexChecksPassed':True,'region113Bytes':region113,'region115ExtraBytes':extras,'region115TotalBytes':region113+extras,'combinedRegionsBytes':2*region113+extras,'wholeEyeTopologyBytesPerEngine':topology_bytes,'source4xPixelBufferBytes':pixel_bytes(4),'source8xPixelBufferBytes':pixel_bytes(8),'original113WholeEyeOwners':3,'combined115WholeEyeOwners':4,'original113StructuredBytes':region113+3*topology_bytes+pixel_bytes(4)+2*pixel_bytes(8)+4*n*16+846*32,'combined115StructuredBytes':2*region113+extras+4*topology_bytes+2*pixel_bytes(4)+2*pixel_bytes(8)+8*n*16+846*32,'excludesRTDriverShaderTextureAllocations':True},'synchronizationReview':{'eachWholeEyeOwnsDistinctComputeShaderClone':True,'allGraphBuffersDeclared':True,'regionCommandsUseSameOrderedCommandBuffer':True,'enumerationGroupBarriersOutsideDivergentBranches':True,'newEvaluateRWUAVResources':8,'newParetoRWUAVResources':7,'newThreadGroupBarrierAddedBySourceForm':False,'cleanupHadNotStartedAtInitialFailure':True,'CPUWaitForCompletionCanBlockEditorTimeoutAndExit':True},'causeConclusion':'Device reset confirmed in old log; no per-kernel completion trace/timing. Static finite bounds do not establish safe GPU duration. No unique root kernel proved.','safetyDecision':'Do not repeat unchanged full115 or a large offscreen dispatch. Tiny bounded source-form-only diagnostic must omit BVH and exhaustive search; larger stages need work partitions/continuations and completion-driven scheduling, not a longer timeout.'}
    rest_den=[]
    for part in range(4):
        ix=mapped[part];ix=ix[ix>=0];a=g['rest4'][g['triangles'][ix,:3],:3];u=a[:,1]-a[:,0];z=a[:,2]-a[:,0];den=(u*u).sum(1)*(z*z).sum(1)-(u*z).sum(1)**2
        assert np.all(den>0)
        rest_den.append({'part':part,'mappedTriangles':len(ix),'minimumFloat32RestDeterminant':float(den.min()),'nonpositiveCount':int(sum(den<=0))})
    report['frozenGeometryFiniteCases']=finite_geometry_cases
    report['frozenRestTriangleDeterminants']=rest_den
    report['maximumBounds']['validPartSubsetsBothEyes']=valid_subsets_both
    report['maximumBounds']['validSubsetConnectivityPointIterationsUpperBound']=valid_subsets_both*8*21*24
    report['maximumBounds']['metricKeyPairTermsAcrossEyesForShared32Keys']=128*(32*31//2)
    (H/'STATIC_AUDIT115.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k]for k in ['scopeReplayChecksPassed','finiteHeaderBoundaryCases','nominalLargeDispatch','currentSourceDimensions','structuredBuffers','causeConclusion','safetyDecision']},ensure_ascii=False))
if __name__=='__main__':main()
