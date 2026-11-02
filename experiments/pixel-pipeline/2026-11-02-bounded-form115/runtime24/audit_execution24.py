"""Source/frozen-input budget audit. No Unity, device, shader execution or timing claim."""
from pathlib import Path
import hashlib,json,math,struct,sys
import numpy as np
H=Path(__file__).resolve().parent;B=H.parent
sys.path.insert(0,str(B));from direct_support24 import P,sibling
from host_audit24 import functions
sys.path.insert(0,str(P));from inputs113 import load_packets,buffer
sys.path.insert(0,str(sibling('eye-failures114')));from trace114 import geometry,read
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def levels(n):
    out=[]
    def add(n,d):
        if len(out)<=d:out.append(0)
        out[d]+=1
        if n>1:add(n//2,d+1);add(n-n//2,d+1)
    add(n,0);return out
def ceil(n,d):return(n+d-1)//d
def threads(w,h,scale=8):return ceil(w,scale)*ceil(h,scale)*scale*scale
def plan(cellsW,cellsH,roiW,roiH,triangles,curves,old=False):
    cw,ch=cellsW,cellsH;n=cw*ch;sw,sh=cw*8,ch*8;tw,th=cw*4,ch*4
    L=levels(triangles);nodes=sum(L);rays=4*tw*th+4*sw*sh+(4*sw*sh if old else 2*cw+roiW*roiH*16)
    rows=[]
    def row(name,dispatch,nominal,active,largest,bound):rows.append({'kernel':name,'dispatchCalls':dispatch,'nominalThreads':nominal,'inBoundsThreads':active,'largestDispatchThreads':largest,'perThreadBound':bound})
    row('PackPart',12,4*(threads(tw,th)+2*threads(sw,sh)),4*(tw*th+2*sw*sh),max(threads(tw,th),threads(sw,sh)),'5 fixed texture loads/stores; no data-dependent loop')
    refitNom=sum(ceil(v,64)*64 for v in L)
    row('Refit',3*len(L),3*refitNom,3*nodes,max(ceil(v,64)*64 for v in L),'One owned node; leaf3 projected vertices or internal2 child boxes. Levels submitted bottom-up.')
    q=4*tw*th+(2 if old else 1)*4*sw*sh
    row('Query',3 if old else 2,q,q,4*sw*sh,f'At most {nodes} box reads/valid ray, {nodes+1} loop attempts with new guard; stack32, existing push guard. Leaf cap{triangles}; native face alpha hits at most4232 in this fixture.')
    selNom=threads(cw,ch)+(2 if old else 0)*threads(sw//4,sh//4)
    if not old:selNom=0
    selActive=n+(2 if old else 0)*sw*sh//16
    if not old:selActive=0
    row('Select',3 if old else 0,selNom,selActive,threads(sw//4,sh//4)if old else 0,'Historical code:16 samples x3 parts,3 sorting comparisons/sample; optional3x16 tie-depth scan,16 winner scan. Inactive importer entry and no dispatch in guarded candidate.')
    if old:
        row('ApplyCurve106',1,threads(cw,ch),n,threads(cw,ch),'Control-only legacy curve processing, removed from runtime24.')
        row('ComposeForward102',2,2*threads(roiW,roiH),2*roiW*roiH,threads(roiW,roiH),'2 controls; fixed16 hair samples. Removed from runtime24.')
        row('CarrierQueries113',1,4*sw*sh,4*sw*sh,4*sw*sh,'One old8x coordinate/metadata record.')
    else:
        for k in ['CurveColumns24','ColumnVisibility24']:
            row(k,1,ceil(2*cw,64)*64,2*cw,ceil(2*cw,64)*64,('3 curve scans x'+str(curves)+' segment tags; at most4 alpha texel loads; no BVH'if k=='CurveColumns24'else f'1 external ray, at most{nodes} box reads; bounded BVH stack32'))
    row('PrepareCells113',1,threads(cw,ch),n,threads(cw,ch),('64 samples x2 keys scans(max32 keys); up to3x'+str(curves)+' curve scans/cell and64x'+str(curves)+' curve distances/boundary cell'if old else '64 samples x2 key scans(max32 keys),2 column records, at most64 native lid candidates; no curve loop/BVH'))
    row('GatherEye113',1,2,2,2,f'Each eye:32 header clears +{n} cell scan +24x24 adjacency +16 scopes. RawConnected scope seed scan{n}, coded512 passes x{n}; valid flood-fill needs <= {n} passes. Arrays seen16 (512bits).')
    row('BuildSubsets113',1,16384,16384,16384,'Each valid state:np<=24 point scan +8 scopes x Connected<=24 passes x24 points; max4632 loop predicates.4x4096 slots; ni,nw<=12, ni+nw<=21, bad header skips.')
    row('Enumerate113',1,4194304,4194304,4194304,'2x32768 groups x64 lanes. One state/lane; invalid states still participate in6 reduction rounds +initial barrier.7 barriers/group, no unbounded loop.')
    row('Reduce113',1,128,128,128,'512 group merges/lane +6 shared reduction rounds (7 barriers/group).32768 group records/eye.')
    row('Write113',1,threads(cw,ch),n,threads(cw,ch),'At most24 point lookups/cell; no BVH.8UAVs still present.')
    if not old:
        row('CarrierQueries113',1,ceil(roiW*roiH*16,64)*64,roiW*roiH*16,ceil(roiW*roiH*16,64)*64,'16 native depth samples +1 own sample per thread, no BVH; assigned16 arrays.')
        row('AssignedVisibility24',1,ceil(roiW*roiH*16,64)*64,roiW*roiH*16,ceil(roiW*roiH*16,64)*64,f'1 external ray/thread, at most{nodes} box reads; same coordinate/depth record used in composition.')
    row('ComposeRegion113',1,threads(roiW,roiH),roiW*roiH,threads(roiW,roiH),'16 face/depth samples +16 hair samples; no BVH.')
    return {'scope':'one Forward.Draw invocation; excludes native raster/URP/product77/capture presentation and other views','grid':[cw,ch],'physicalROI':[roiW,roiH],'bvhLevelCounts':L,'nodes':nodes,'maxDepth':len(L)-1,'maxValidDFSStack':len(L),'rows':rows,'totalDispatches':sum(r['dispatchCalls']for r in rows),'totalNominalThreads':sum(r['nominalThreads']for r in rows),'raySlots':rays,'validTreeWorstNodeReads':rays*nodes,'invalidTreeGuardLoopAttemptsUpper':rays*(nodes+1),'isGPUTimeEstimate':False}
def walk(nodes,guard):
    stack=[0];visited=0;reads=0;peak=1;leaf=[]
    while stack:
        node=stack.pop();visited+=1
        if guard and(node<0 or node>=len(nodes)or visited>len(nodes)):return False,visited,reads,peak,leaf
        if visited>len(nodes)*3+8:return None,visited,reads,peak,leaf
        a,b,t=nodes[node];reads+=1
        if t>=0:leaf.append(t);continue
        if len(stack)>29:return False,visited,reads,peak,leaf
        stack.extend([a,b]);peak=max(peak,len(stack))
    return True,visited,reads,peak,leaf
def tree(n):
    nodes=[]
    def add(start,n):
        at=len(nodes);nodes.append(None)
        if n==1:nodes[at]=(-1,-1,start)
        else:
            a=add(start,n//2);b=add(start+n//2,n-n//2);nodes[at]=(a,b,-1)
        return at
    add(0,n);return nodes
def main():
    _,packets=load_packets(P);frames=[];topology=None;fixture=bytearray(struct.pack('<i',len(packets)));oldSha=sha(P/'ForwardEye113.compute')
    for entry,packet in packets:
        m=read(packet/'RAW_MANIFEST.json');c=geometry(packet,m);assert m['computeSHA113']==oldSha
        frame=buffer(packet/'REGION113-frame.f32').view(np.uint32).reshape(64,4);heads=frame[[0,32]]
        for a in ['world4','rest4','uv','materials','view','projection','physicalXY','depth']:assert np.isfinite(c[a]).all(),(entry['frame'],a)
        assert np.linalg.det(c['view'])!=0 and np.linalg.det(c['projection'])!=0 and(c['physicalW']!=0).all()
        assert c['triangles'][:,:3].min()>=0 and c['triangles'][:,:3].max()<len(c['world4']) and c['triangles'][:,3].min()>=0 and c['triangles'][:,3].max()<len(c['materials'])
        topobytes=c['triangles'].astype('<i4').tobytes()+c['partMap'].astype('<i4').tobytes()
        if topology is None:topology=topobytes;first=c
        else:assert topology==topobytes
        tw,th=m['forward102']['canonicalSize'];sw,sh=m['forward102']['denseSize'];rw,rh=m['grid102']['eyeTopLeftROI'][2:];keys=len(read(P/'SOURCE113.json')['keys']);curves=m['forward102']['curves106']['segments']
        fixture+=struct.pack('<11i',tw,th,sw,sh,sw,sh,rw,rh,keys,curves,entry['frame'])
        frames.append({'frame':entry['frame'],'sourceId':entry['sourceId'],'heads':heads.tolist(),'subsetStateRanges':sum((1<<int(h[1]))+(1<<int(h[2]))for h in heads),'enumerationStateRange':sum(1<<int(h[1]+h[2])for h in heads),'keyCount':keys,'curves':curves,'grid':[tw//4,th//4],'ROI':[rw,rh]})
    fixture+=struct.pack('<5i',len(first['world4']),len(first['triangles']),len(first['materials']),first['partMap'].shape[1],first['partMap'].size)+first['triangles'].astype('<i4').tobytes()+first['partMap'].astype('<i4').tobytes()
    (H/'BOUNDS_INPUT24.bin').write_bytes(fixture)
    validTree=tree(len(first['triangles']));a=walk(validTree,False);b=walk(validTree,True);assert a==b and b[0]and b[1]==59083 and b[3]==16
    cycle=[(0,1,-1),(-1,-1,0)];badIndex=[(1,99,-1),(-1,-1,0)];assert walk(cycle,False)[0]is None and walk(cycle,True)[0]is False and walk(badIndex,True)[0]is False
    old=plan(18,8,16,8,29542,846,True);candidate=plan(18,8,16,8,29542,846);cap=plan(512,1,512,1,262144,1024)
    cache=read(B/'CACHE_PREFIX24.json');compiled=read(H/'HLSL_RUNTIME24.json');comparisons=[]
    for row in compiled['kernels']:
        prior=[r for r in cache['rows']if row['entry']in r['kernelCandidatesByResourceSignature']]
        comparisons.append({'kernel':row['entry'],'candidateActive':row['activeEntrypoint'],'candidateInstructions':row['audit']['instructions'],'candidatePrivateArrays':len(row['audit']['privateArrayDeclarations']),'candidateLoops':row['audit']['loops'],'candidateUAVs':sum(b['Type']==6 for b in row['bindings']),'oldResourceSignatureMatches':[{'file':r['file'],'sha':r['SHA256'],'instructions':r['instructionCount'],'privateArrays':r['privateArrayDeclarations'],'loops':r['loopInstructions']}for r in prior],'exactOldDriverBinaryAttestation':False})
    full=(H/'ForwardEye113_Geometry24.compute').read_text();forward=(H/'Forward113_Geometry24.cs').read_text();engine=(H/'WholeEye107_Geometry24.cs').read_text()
    assert '#pragma kernel Select'not in full and 'false,0,false);'in forward and 'if(!selectOutput)'in engine
    assert full.count('visits>(uint)_NodeCount96')==2 and 'cmd.SetComputeIntParam(cs,"_NodeCount96",nodeCount)'in engine
    assert forward.index('DispatchBounds24.Grid(')<forward.index('var cmd=CommandBufferHelpers')
    for text in [full,forward,engine,(H/'RegionDriver113_Geometry24.cs').read_text()]:
        assert all(t not in text for t in ['EvaluateForm115','BoundRun115','Forward115','Pareto115'])
    result={'GPUOrUnityCalls':0,'oldCapturedShaderSHA256':oldSha,'candidateSourceSHA256':sha(H/'ForwardEye113_Geometry24.compute'),'capturedFrames':frames,'old113':old,'candidate':candidate,'independentAcceptedInputEnvelope':cap,'bytecodeComparison':comparisons,
      'treeChecks':{'balancedValidTreeNodes':b[1],'peakStack':b[3],'sameGuardedTraversalAsOriginal':True,'cyclicGraphStopsUnknown':True,'badChildRejectedBeforeRead':True,'notCapturedGPUNodeTopology':True},
      'limits':['Counts are per one callback/view and are not GPU milliseconds. Other scene/URP/driver work is excluded.','Cache resource-signature matches are not a proof of which old native-driver binary executed.','Loop visit cap prevents unbounded/cyclic traversal but still permits billions of node reads across a full callback.','CPU input guards cannot attest actual GPU constants/resources, device health, driver JIT or synchronization.'],
      'minimumNextExecution':{'runNow':False,'scope':'existing prefix24 STAGE1 only; Edit compute; no Play/BVH/Select/full runtime24','sourceFrame':103,'owner':2,'header':[9,5,6,0],'dispatch':[1,2,1],'threads':128,'validSubsets':96,'structuredAllocationBytes':591616,'readbackBytes':4096,'closureLoopBound':'Per valid subset9 point scans + at most8 scopes x24x24 connectivity predicates; finite frozen point/mask bounds.','success':'One submitted dispatch; all real readbacks done/error0; byte-for-byte CPU oracle+input hashes; state equal; own resources released; COMPLETE marker last.','stop':'Any error/pending/unknown/outcome or state mismatch: no next stage/retry/forced cleanup. Host device creation can still trigger unknown driver failure.','remainingRisk':'Four prefix kernels may be loaded/created even when only BuildSubsets dispatches; Write still8 UAV. Known115 evaluator is absent but original device-reset cause is unresolved.'}}
    (H/'EXECUTION_BUDGET24.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'oldDispatches':old['totalDispatches'],'candidateDispatches':candidate['totalDispatches'],'candidateThreads':candidate['totalNominalThreads'],'candidateRaySlots':candidate['raySlots'],'validTreeWorstNodeReads':candidate['validTreeWorstNodeReads'],'treePeakStack':b[3],'maxSubsetRanges':max(r['subsetStateRanges']for r in frames),'maxEnumerationRange':max(r['enumerationStateRange']for r in frames),'selectDispatches':0,'GPUOrUnityCalls':0},indent=2))
if __name__=='__main__':main()
