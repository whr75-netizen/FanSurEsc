"""Explicit, conservative source-affiliation cache; NOT an eyelid mask.

VRM blink semantics identify deformation membership. Native material6 pigment
and the closed native aperture ring have separate identities. Unknown skin
occlusion ownership never becomes transparency or feature-owned canvas.
"""
from collections import defaultdict
import hashlib,json
import numpy as np
from source112 import Source,HERE,P111,load,packet_list,read,MODEL_HASH
from geometry111 import P109
from analyse111 import bank_data

def connected(triangles,selected):
    """Edge adjacency, no nearest-distance or vertex weld."""
    edge=defaultdict(list)
    for t in np.flatnonzero(selected):
        v=triangles[t]
        for a,b in zip(v,np.roll(v,-1)):edge[tuple(sorted((int(a),int(b))))].append(int(t))
    near=defaultdict(set)
    for ts in edge.values():
        for t in ts:near[t].update(ts)
    left=set(np.flatnonzero(selected).tolist());out=[]
    while left:
        todo=[min(left)];left.remove(todo[0]);group=[]
        while todo:
            t=todo.pop();group.append(t)
            for n in sorted(near[t]):
                if n in left:left.remove(n);todo.append(n)
        out.append(sorted(group))
    return sorted(out,key=lambda g:(-len(g),g[0]))

class Support:
    def __init__(self,source,ctx):
        self.s=source;self.m=source.map_to_capture(ctx);self.ctx=ctx;mesh=self.m['meshData'];self.tri=source.accessor(mesh['primitives'][3]['indices']).reshape(-1,3).astype(int)
        self.fields={};self.bindings={};self.deltas={};presets=source.g['extensions']['VRMC_vrm']['expressions']['preset']
        for name in ['blinkLeft','blinkRight']:
            bs=presets[name]['morphTargetBinds'];assert len(bs)==1 and bs[0]['node']==self.m['binding']['node']
            b=bs[0];d=source.accessor(mesh['primitives'][0]['targets'][b['index']]['POSITION']);moving=np.any(d!=0,axis=1)
            matches=[owner for owner,ring in self.m['rings'].items()if moving[ring].all()]
            assert len(matches)==1,'Unilateral source expression does not identify one registered ring'
            owner=matches[0];assert all(not moving[ring].any()for o,ring in self.m['rings'].items()if o!=owner)
            self.fields[owner]=moving;self.deltas[owner]=d;self.bindings[owner]={'expression':name,'node':b['node'],'morphTarget':b['index'],'weight':b['weight']}
        assert len(self.fields)==len(self.m['rings'])
        # Do not mistake the missing joint skin ownership for absent native
        # iris/white bindings:89 already registered every template cell centre.
        nativeRegistration=read(P109/'inputs/REGISTRATION89.json');self.attachedCells=[]
        for cell in nativeRegistration['cells']:
            b=cell['nativeBinding'];ids=np.array(b['triangleVertexIds']);weights=np.array(b['barycentric']);sm=int(cell['role']);ti=int(ctx['partMap'][1 if sm==1 else 2,int(b['primitive'])-1]);assert sm in[1,4]
            assert np.array_equal(ctx['triangles'][ti,:3]-self.m['faceVertexOffset'],ids)
            rest=weights@ctx['rest'][ids+self.m['faceVertexOffset']];uv=weights@ctx['uv'][ids+self.m['faceVertexOffset']]
            err=float(np.linalg.norm(rest-np.array(b['point'])));uvErr=float(np.linalg.norm(uv-np.array(b['uv'])));assert err<1e-7 and uvErr<1e-7
            self.attachedCells.append({'cellId':cell['cellId'],'eye':cell['eye'],'part':sm,'sourceXY':cell['sourceXY'],'sourcePrimitive':b['primitive'],'sourceVertices':b['triangleVertexIds'],'barycentric':b['barycentric'],'restPointErrorMetres':err,'UVError':uvErr,'pointAttachmentIsNotWholeCellOcclusionOwnership':True})
        assert len(self.attachedCells)==20 and not nativeRegistration['unboundCells']
        signature=hashlib.sha256()
        for array in [self.m['positions'],self.m['uv'],self.m['delta'],self.tri]+[self.deltas[k]for k in sorted(self.fields)]:signature.update(np.ascontiguousarray(array).tobytes())
        registration=read(ctx['path'].parent/'REGISTRATION_CURRENT102.json');bank,_=bank_data()
        pointBindings=[{k:v for k,v in c.items()if k not in ['restPointErrorMetres','UVError']}for c in self.attachedCells]
        self.key=hashlib.sha256(json.dumps({'model':MODEL_HASH,'sourceData':signature.hexdigest(),'binding':self.bindings,'rings':{str(k):r.tolist()for k,r in self.m['rings'].items()},'registration':{'topology':registration['sourceTopology'],'projection':registration['projection']},'nativePointBindings':pointBindings,'bankShape':sorted(bank),'policy':'deformation-affiliation-is-not-occlusion-ownership/v1'},sort_keys=True).encode()).hexdigest()

    def evidence(self,global_triangle):
        c=self.ctx;src=c['sources'][global_triangle];assert list(src[:2])==[1,3]
        original=int(src[2])-1;v=self.tri[original]
        assert set((c['triangles'][global_triangle,:3]-self.m['faceVertexOffset']).tolist())==set(v.tolist())
        out={'globalTriangle':int(global_triangle),'sourcePrimitive':int(src[2]),'sourceMesh':self.m['mesh'],'sourceSubmesh':3,'sourceVertices':v.tolist(),'legacyNearestEyeVertexTags':c['triOwners'][global_triangle,:3].tolist(),'registeredRingContact':{str(k):len(set(v)&set(r))for k,r in self.m['rings'].items()},'unilateralBlinkVertexInfluence':{str(k):self.fields[k][v].astype(int).tolist()for k in self.fields}}
        out['occlusionOwnership']='UNRESOLVED_SKIN_NOT_A_SEMANTIC_EYELID_LABEL'
        out['safeAction']='retain recorded depth and original alpha; no occluder removed'
        return out

    def cache(self):
        s=self.s;m=self.m;mesh=m['meshData'];delta=m['delta'];moving=np.any(delta!=0,axis=1);groups=connected(self.tri,moving[self.tri].all(1));rows=[]
        for sm,p in enumerate(mesh['primitives']):
            ids=np.unique(s.accessor(p['indices']));rows.append({'sourceSubmesh':sm,'vertices':len(ids),'blinkMovingVertices':int(moving[ids].sum()),'unilateralMovingVertices':{str(k):int(v[ids].sum())for k,v in self.fields.items()},'roleSource':'existing59/111 renderer binding; not inferred from material name'})
        skinVertices=np.unique(self.tri);shared=skinVertices[self.fields[1][skinVertices]&self.fields[2][skinVertices]]
        return {'schema':'native-eye-affiliation112/v1','cacheKey':self.key,'modelSHA256':MODEL_HASH,'sourceNode':m['binding']['node'],'sourceMesh':m['mesh'],'captureSourceRendererOrdinal':1,'captureFaceVertexOffset':m['faceVertexOffset'],'glTFToCaptureIndexPermutation':m['permutation'],'UVTransform':'vUnity=1-vGltf; max error 0 in recorded source','rings':{str(k):{'sourceVertices':r.tolist(),'blinkSource':self.bindings[k]}for k,r in m['rings'].items()},'existingNativeTemplatePointBindings':self.attachedCells,'existingDestinationFootprints':'111 carrier_at already enumerates actual destination I/W triangles/UV/depth/alpha per sample. These data are NOT missing.','parts':rows,'unilateralSharedSkinVertices':shared.tolist(),'combinedBlinkAllMovingSkinEdgeComponents':[{'triangles':len(g),'ringContacts':{str(k):len(set(self.tri[g].ravel())&set(r))for k,r in m['rings'].items()}}for g in groups],'separatePigmentCache':'../2026-11-01-pigment-carrier109/NATIVE_CACHE109.json (upper colour ribbon, not skin ownership)','semanticSkinLidMask':None,'jointCorrectedEyeCanvasSkinOwnership':None,'internalVsExternalSkinOcclusionPolicy':None,'unknownIsTransparent':False,'unilateralBlinkIsEyelidMask':False,'nearestEyeOwnerIsEyelidMask':False,'runtimeReady':False,'invalidation':['source model/topology/UV/bindings/morph data','registered native rings and source feature/bank content','ownership policy generation if one is supplied'],'scope':'immutable source cache may be shared; current vertices/view/sourceID/alpha and layout history remain per renderer/view/generation','cost':{'sourceVertices':len(delta),'skinTriangles':len(self.tri),'runtimeGPUToCPUReadbackRequired':False,'runtimeAllocationsImplemented':False},'missingDefinition':'The missing element is not the20 native I/W point attachments or111 destination geometry. It is the closed source-local support and skin-ownership/deformation transfer of the jointly corrected eye/canvas: which physical skin is internal lid versus external occluder after stylized reallocation. Neither expression influence nor a2D upper boundary specifies that rule.'}

def main():
    s=Source();_,paths=packet_list();ctx=load(paths[3]);sup=Support(s,ctx);s.freeze();cache=sup.cache();(HERE/'AFFILIATION_CACHE112.json').write_text(json.dumps(cache,indent=2)+'\n',encoding='utf8');print(json.dumps({'rings':{str(k):v['blinkSource']for k,v in cache['rings'].items()},'skinComponents':cache['combinedBlinkAllMovingSkinEdgeComponents'],'runtimeReady':cache['runtimeReady']}))

if __name__=='__main__':main()
