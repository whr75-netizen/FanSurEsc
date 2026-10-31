"""Match actual configured renderer mesh/material slots to original GLB primitives.

No selected material IDs or names. Exact full UV + triangle index correspondence;
actual readable material texture point checks are a separate validation stage.
"""
from pathlib import Path
import hashlib,json,struct
import numpy as np
R=Path(__file__).resolve().parent
d=json.loads((R/'CONFIGURED_RENDERER59.json').read_text());P=Path(d['before']['project']).parent
assert d['liveNativeCount']==0 and d['configuredNativeCount']==1 and not d['stateChanges']
native=d['nativeRenderers'][0];containers={m['mainTexture']['assetPath']for s in native['sourceRenderers']for m in s['materials']}
assert len(containers)==1
container=next(iter(containers));b=(P/container).read_bytes();modelSHA=hashlib.sha256(b).hexdigest();size=struct.unpack_from('<I',b,12)[0];doc=json.loads(b[20:20+size]);binary=b[size+28:]
def accessor(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];dim={'VEC2':2,'SCALAR':1}[a['type']];step=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],dim),dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',step*dim),step)).copy()
permutations={'same':[0,1,2],'reverse12':[0,2,1],'reverse01':[1,0,2],'reverse02':[2,1,0],'cycle012':[1,2,0],'cycle021':[2,0,1]}
bindings=[]
for s in native['sourceRenderers']:
    uv=np.fromfile(R/s['uvFile'],dtype='<f4').reshape(-1,2)
    for row in s['indexFiles']:
        sub=row['subMesh'];indices=np.fromfile(R/row['file'],dtype='<u4').reshape(-1,3);matches=[]
        for mi,mesh in enumerate(doc['meshes']):
            for pi,primitive in enumerate(mesh['primitives']):
                sourceUV=accessor(primitive['attributes']['TEXCOORD_0']);sourceIndices=accessor(primitive['indices']).reshape(-1,3).astype('<u4')
                if sourceUV.shape!=uv.shape or sourceIndices.shape!=indices.shape:continue
                for convention in ['same','unity-flip-v']:
                    expected=sourceUV.copy()
                    if convention=='unity-flip-v':expected[:,1]=np.float32(1)-expected[:,1]
                    if not np.array_equal(expected,uv):continue
                    for winding,order in permutations.items():
                        if np.array_equal(sourceIndices[:,order],indices):matches.append((mi,pi,primitive,convention,winding))
        material=s['materials'][sub]
        entry={'bindingOrdinal':len(bindings),'rendererOrdinal':s['ordinal'],'subMesh':sub,'rendererEntityId':s['entityId'],
            'meshAssetGUID':s['mesh']['guid'],'meshUVSHA256':s['uvSHA256'],'indexSHA256':row['sha256'],'triangleCount':len(indices),
            'materialAssetPath':material['assetPath'],'materialEntityId':material['entityId'],'textureEntityId':material['mainTexture']['entityId'],
            'textureContainerAsset':container,'textureContainerGUID':material['mainTexture']['guid'],'candidateMatches':len(matches),'status':'unresolved'}
        if len(matches)==1:
            mi,pi,primitive,convention,winding=matches[0];mat=primitive['material'];pbr=doc['materials'][mat]['pbrMetallicRoughness'];tex=pbr['baseColorTexture']['index'];imageId=doc['textures'][tex]['source'];view=doc['bufferViews'][doc['images'][imageId]['bufferView']];png=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
            factor=pbr.get('baseColorFactor',[1,1,1,1]);factorMatch=material.get('color')==factor
            entry.update(gltfMesh=mi,gltfPrimitive=pi,materialId=mat,textureIndex=tex,imageIndex=imageId,imageSHA256=hashlib.sha256(png).hexdigest(),
                factorLinear=factor,materialFactorExact=factorMatch,uvConvention=convention,indexPermutation=winding,
                sourceFamilyId=f'{modelSHA}/mesh{mi}/primitive{pi}/material{mat}',status='geometry-factor-exact-pending-actual-texture-check'if factorMatch else'material-factor-mismatch')
        bindings.append(entry)
report={'modelAsset':container,'modelSHA256':modelSHA,'source':'Actual GameMap1 bootstrap shellPrefab renderer graph; not live visible frame',
    'bindings':bindings,'sourceSlots':len(bindings),'geometryFactorExact':sum(x['status']=='geometry-factor-exact-pending-actual-texture-check'for x in bindings),
    'unresolvedSlots':sum(x['status']=='unresolved'for x in bindings),'visibleCellCount':None,'fullCharacterRendered':False,'manualPrimitiveSelection':False,
    'liveNativeCount':0,'configuredNativeCount':1,'playStartScene':d['playStartScene'],'enterPlayModeOptionsEnabled':d['enterPlayModeOptionsEnabled'],'enterPlayModeOptions':d['enterPlayModeOptions']}
(R/'SOURCE_REGISTRY59.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items()if k!='bindings'},ensure_ascii=False))
