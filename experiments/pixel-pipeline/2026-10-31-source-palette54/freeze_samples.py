"""Freeze original material/mesh-UV texels, without screenshots or Unity.

Point native texels are authoring inputs, not a replay of GPU bilinear/mip
sampling. Primitive-centroid samples and surface weights are explicit fixtures,
not a claimed semantic segmentation or full-texture optimal representative.
"""
from pathlib import Path
import hashlib,json,struct
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent
O=Path('C:/Users/15352/Documents/Codex/2026-10-30/task/model-source')
model=Path('C:/Users/15352/Desktop/작업폴더/AvatarSample_A.vrm')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
blob=model.read_bytes();model_sha=sha(model)
assert model_sha=='0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3'
size=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+size]);binary=blob[28+size:]
audit=json.loads((O/'SOURCE_AUDIT.json').read_text())
def acc(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
    dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];step=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],dim),dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',step*dim),step)).copy()
families=[]
for material_id in[12,10]:
    mesh_id,prim_id,primitive=next((mi,pi,p)for mi,m in enumerate(doc['meshes'])for pi,p in enumerate(m['primitives'])if p['material']==material_id)
    material=next(m for m in audit['materials']if m['materialId']==material_id)
    path=Path(material['image']['file']);assert sha(path)==material['image']['SHA256']
    pbr=doc['materials'][material_id]['pbrMetallicRoughness'];texture=doc['textures'][pbr['baseColorTexture']['index']]
    source_image=doc['images'][texture['source']];image_view=doc['bufferViews'][source_image['bufferView']]
    embedded=binary[image_view.get('byteOffset',0):image_view.get('byteOffset',0)+image_view['byteLength']]
    assert hashlib.sha256(embedded).hexdigest()==material['image']['SHA256']
    assert pbr.get('baseColorFactor',[1,1,1,1])==material['baseColorFactorLinear']
    rgba=np.array(Image.open(path).convert('RGBA'));height,width=rgba.shape[:2]
    xyz=acc(primitive['attributes']['POSITION']);uv=acc(primitive['attributes']['TEXCOORD_0']);tri=acc(primitive['indices']).reshape(-1,3)
    samples=[]
    for triangle in np.linspace(0,len(tri)-1,32,dtype=int):
        ids=tri[triangle];p=xyz[ids].astype(float);area=float(np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))/2)
        if area<=0:continue
        requested=uv[ids].mean(axis=0);x,y=np.floor((requested%1)*[width,height]).astype(int)
        pixel=rgba[y,x].tolist()
        if pixel[3]==0:continue
        samples.append(dict(id=f'mesh{mesh_id}/primitive{prim_id}/triangle{int(triangle)}',materialId=material_id,
            imageSHA256=material['image']['SHA256'],primitiveId=prim_id,triangle=int(triangle),vertexIndices=ids.tolist(),
            barycentric=[1/3]*3,uv=requested.tolist(),texel=[int(x),int(y)],
            texelCentreUV=[(int(x)+.5)/width,(int(y)+.5)/height],rgba8=pixel,weight=area))
    assert samples
    families.append(dict(id=f'material-{material_id}-primitive-{prim_id}',domainId=f'mesh{mesh_id}/primitive{prim_id}',
        source=dict(modelSHA256=model_sha,materialId=material_id,imageSHA256=material['image']['SHA256'],
            imageFile=path.name,textureSize=[width,height],factorLinear=material['baseColorFactorLinear'],
            encoding='srgb8',uvOrigin='top-left',sampleRule='native PNG texel containing original mesh UV centroid; point authoring fixture, not GPU bilinear/mip replay'),samples=samples))
# An explicitly synthetic second model/ID namespace checks that the same core
# does not assume Avatar roles or a brown default colour.
synthetic=[([10,150,180,255],2),([20,120,180,255],3),([100,210,220,255],1)]
sid=hashlib.sha256(json.dumps(synthetic).encode()).hexdigest()
families.append(dict(id='synthetic-ocean/material-87',domainId='test-domain-not-a-real-avatar',
    source=dict(modelSHA256=hashlib.sha256(b'synthetic-model54').hexdigest(),materialId=87,imageSHA256=sid,
        imageFile='synthetic-source',textureSize=[3,1],factorLinear=[.8,1,.9,1],encoding='srgb8',uvOrigin='top-left',sampleRule='explicit synthetic3texel fixture'),
    samples=[dict(id=f'synthetic-texel-{i}',materialId=87,imageSHA256=sid,primitiveId=0,triangle=0,
        uv=[(i+.5)/3,.5],texel=[i,0],rgba8=rgb,weight=w)for i,(rgb,w)in enumerate(synthetic)]))
out=dict(kind='original-material-uv-samples/v1',families=families,
    sourceAuditSHA256=sha(O/'SOURCE_AUDIT.json'),gFixture='diagnostic shade scalar supplied independently, NOT a new Unity light capture',
    limitations=['Two real materials from one model, plus one synthetic model fixture; not proof of100% model generality',
        'Material domains provided by mesh primitive; fine painted-feature segmentation not implemented',
        'Representative of this finite UV sample set; not an automatic optimal palette for every source pattern'])
(R/'fixtures.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'families':[(f['id'],len(f['samples']))for f in families],'newUnityCalls':0},ensure_ascii=False))
