"""Read exact source material/texture/geometry clues; no segmentation tuning."""
from pathlib import Path
import json,struct,hashlib,sys,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')

def main():
    reg=json.loads((R/'renderer-family59/SOURCE_REGISTRY59.json').read_text(encoding='utf-8-sig'))
    path=P/reg['modelAsset'];b=path.read_bytes();assert hashlib.sha256(b).hexdigest()==reg['modelSHA256']
    size,kind=struct.unpack_from('<II',b,12);g=json.loads(b[20:20+size]);at=20+size;n,t=struct.unpack_from('<II',b,at);binary=b[at+8:at+8+n]
    def texture(index):
        tx=g['textures'][index];image=g['images'][tx['source']];view=g['bufferViews'][image['bufferView']];raw=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
        im=Image.open(io.BytesIO(raw));chunks=[];pos=8
        if raw.startswith(b'\x89PNG\r\n\x1a\n'):
            while pos<len(raw):
                length=struct.unpack_from('>I',raw,pos)[0];chunks.append(raw[pos+4:pos+8].decode('ascii'));pos+=length+12
        return {'textureId':index,'imageId':tx['source'],'imageSHA256':hashlib.sha256(raw).hexdigest(),'size':list(im.size),'mode':im.mode,'PNGChunkTypes':sorted(set(chunks)),'sampler':g.get('samplers',[])[tx.get('sampler',0)]}
    materials=[]
    for sm in (3,6):
        binding=next(x for x in reg['bindings']if x['rendererOrdinal']==1 and x['subMesh']==sm);mi=binding['materialId'];mat=g['materials'][mi];mtoon=mat.get('extensions',{}).get('VRMC_materials_mtoon',{});pbr=mat.get('pbrMetallicRoughness',{})
        rows={}
        for field,value in [('baseColorTexture',pbr.get('baseColorTexture')),('normalTexture',mat.get('normalTexture')),('emissiveTexture',mat.get('emissiveTexture'))]+[(k,v)for k,v in mtoon.items()if isinstance(v,dict)and 'index'in v]:
            if value is not None:rows[field]=texture(value['index'])
        materials.append({'sourceRendererOrdinal':1,'sourceSubmesh':sm,'materialId':mi,'materialName':mat.get('name'),
            'baseColorFactor':pbr.get('baseColorFactor',[1]*4),'alphaMode':mat.get('alphaMode','OPAQUE'),'alphaCutoff':mat.get('alphaCutoff',.5),
            'mtoonScalarAndFactorFields':{k:v for k,v in mtoon.items()if not isinstance(v,dict)},'textures':rows,
            'materialExtrasKeys':list(mat.get('extras',{})),'sourcePrimitiveExtrasKeys':list(g['meshes'][0]['primitives'][sm].get('extras',{}))})
    expressions=g.get('extensions',{}).get('VRMC_vrm',{}).get('expressions',{}).get('preset',{})
    blink={k:{f:v for f,v in d.items()if f in ('morphTargetBinds','materialColorBinds','textureTransformBinds','isBinary')}for k,d in expressions.items()if 'blink'in k.lower()}
    authorSuffix={'.psd','.psb','.ora','.kra','.aseprite','.ase','.blend','.clip','.sai','.svg'}
    files=[p.name for p in path.parent.iterdir()if p.is_file()and p.suffix.lower()in authorSuffix]
    bank=np.load(R/'hair-isolation100/TEMPLATE_REFERENCE100.npz');roles,counts=np.unique(bank['TemplateRole'][...,0],return_counts=True)
    result={'sourceModelAsset':reg['modelAsset'],'sourceModelSHA256':reg['modelSHA256'],'materials':materials,'blinkSourceBindings':blink,
        'authorLayerSourceFilesInExactModelInputFolder':files,'searchScope':'exact source model Input folder only, not entire user drive',
        'existingBankRoleCounts':dict(zip(map(str,roles.tolist()),counts.tolist())),
        'implementedBankConsumer':'NativeSurface89 only uses bank for native role1/4; parent/iris registration does not provide source face blush/shading-layer labels',
        'separatedClues':['native primitive/material/UV support and source-alpha domains','native eyelid vs skin geometry','existing native upper/lower lid component IDs','registered eye parent/iris and original source atlas colours','VRM blink morph bindings'],
        'notEquivalent':['material ID is not a painted colour-region ID','a source shadow-like gradient is not the current scene lighting g','normal/outline/alpha maps are not automatically blush/skin/paint layer labels','generic source RGB quantisation noise bounds do not authorise deleting coherent low-contrast paint'],
        'minimumAutomaticContract':{'required':['source hash/material/texture/sampler/UV/mesh-domain provenance','unchanged unlit source RGBA field','hierarchical colour/shape evidence with coherent weak-child support and explicit uncertainty','separate source tone/colour identity from dynamic g/Q','declared colour-loss and feature-importance policy before flattening a source field to finite P'],
            'optionalAuthorEvidence':['paint layer/region masks or registered feature constraints when available'],
            'fallback':'retain unresolved source field/feature evidence; do not silently average or discard it as lighting'},
        'reviewQuestions':['What objective can preserve weak coherent strokes while assigning finite-width AA transition to shared regions without treating every gradient band as a feature?',
            'Should a colour region carry a continuous source field and source-tone label separately from LightQ, rather than a single flat representative colour?',
            'How should registered skin-ring curve support and source lid-pigment support jointly allocate cells where102 iris/white protection prevents a connected line?']}
    (H/'UV_INPUT_CONTRACT106.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'materials':materials,'blinkSourceBindings':blink,'authorLayerFilesInExactModelInputFolder':files},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
