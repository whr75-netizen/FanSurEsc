"""Independent original GLB PNG/UV validation; no Unity calls."""
from pathlib import Path
import hashlib,io,json,struct
from PIL import Image
R=Path(__file__).resolve().parent;config=json.loads((R/'CONFIG58.json').read_text());data=json.loads((R/'SOURCE58.json').read_text())
model=Path(config['modelPath']).read_bytes();assert hashlib.sha256(model).hexdigest()==config['modelSHA256']==data['modelSHA256']
n=struct.unpack_from('<I',model,12)[0];doc=json.loads(model[20:20+n]);binary=model[n+28:]
count=0
for record,selection in zip(data['records'],config['domains']):
    f=record['family'];primitive=doc['meshes'][selection['meshIndex']]['primitives'][selection['primitiveIndex']];material=primitive['material'];pbr=doc['materials'][material]['pbrMetallicRoughness']
    imageId=doc['textures'][pbr['baseColorTexture']['index']]['source'];view=doc['bufferViews'][doc['images'][imageId]['bufferView']]
    png=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];im=Image.open(io.BytesIO(png)).convert('RGBA')
    assert f['source']['materialId']==material and f['source']['imageSHA256']==hashlib.sha256(png).hexdigest()
    assert f['source']['factorLinear']==pbr.get('baseColorFactor',[1,1,1,1])
    for sample in f['samples']:
        assert list(im.getpixel(tuple(sample['texel'])))==sample['rgba8'],sample['id']
        count+=1
assert not data['stateChanges'] and data['ownedTextureIdentitiesRestored']
report={'originalPNGPointSamplesExact':count,'modelSHA256':data['modelSHA256'],'nativeChannelAndVerticalOriginValidated':True,
    'oldEqualsCorrectedCases':sum(s['k']==s['kPrime'] for s in data['cases'] if s['bound']),
    'changedIndexCases':sum(s['k']!=s['kPrime'] for s in data['cases'] if s['bound']),
    'dirtyBefore':len(data['before']['dirty']),'dirtyAfter':len(data['after']['dirty']),
    'sourceMemoryDelta':{k:data['memoryAfter'][k]-data['memoryBefore'][k] for k in data['memoryBefore'] if k!='utc'},
    'peakOwnedDecodedImageBytes':data['peakOwnedDecodedTextureBytes'],'stateChanges':data['stateChanges']}
(R/'NATIVE_VERIFICATION58.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
