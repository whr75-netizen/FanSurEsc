"""Read only native source metadata and existing region decisions; no inference."""
from pathlib import Path
import hashlib,io,json,struct
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];G=H/'surface27'
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 registry=read(R/'renderer-family59/SOURCE_REGISTRY59.json');binding=next(b for b in registry['bindings']if b['rendererOrdinal']==1 and b['subMesh']==3)
 p=REPO/registry['modelAsset'];raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==registry['modelSHA256'];n,t=struct.unpack_from('<II',raw,12);assert t==0x4e4f534a;g=json.loads(raw[20:20+n]);material=g['materials'][binding['materialId']];mesh=g['meshes'][binding['gltfMesh']];primitive=mesh['primitives'][binding['gltfPrimitive']]
 mtoon=material.get('extensions',{}).get('VRMC_materials_mtoon',{});textures={};pixels={}
 for name,value in [('baseColor',material.get('pbrMetallicRoughness',{}).get('baseColorTexture')),('shadeMultiply',mtoon.get('shadeMultiplyTexture')),('shadingShift',mtoon.get('shadingShiftTexture')),('normal',material.get('normalTexture'))]:
  if value is None:continue
  i=value['index'];texture=g['textures'][i];image=g['images'][texture['source']];view=g['bufferViews'][image['bufferView']];at=20+n+8+view.get('byteOffset',0);payload=raw[at:at+view['byteLength']]
  textures[name]={'textureIndex':i,'imageIndex':texture['source'],'imageSHA256':hashlib.sha256(payload).hexdigest(),'sampler':g['samplers'][texture['sampler']]if 'sampler'in texture else None,'transform':value.get('extensions',{}).get('KHR_texture_transform')}
  if name in ['baseColor','normal']:
   with Image.open(io.BytesIO(payload))as im:
    assert im.size==(1024,1024);im=im.convert('RGBA');pixels[name]=[list(im.getpixel((x+4,704+7)))for x in [382,380,384]]
 assert textures['baseColor']['imageSHA256']==binding['imageSHA256']
 decision=read(R/'source-regions104/DECISION104.json');review=read(R/'source-regions104/REVIEW104.json');bridge=read(REPO/'experiments/pixel-pipeline/2026-11-02-face-region-lut/CONTRACT.json')
 result={'nativeBinding':{k:binding[k]for k in ['rendererOrdinal','subMesh','materialId','gltfMesh','gltfPrimitive','imageSHA256']},'modelSHA256':registry['modelSHA256'],
  'sourceFields':{'textures':textures,'baseColorFactor':material.get('pbrMetallicRoughness',{}).get('baseColorFactor'),'mtoonScalarAndColourFields':{k:v for k,v in mtoon.items()if not isinstance(v,dict)},'vertexAttributes':list(primitive['attributes']),'materialExtraKeys':list(material.get('extras',{})),'primitiveExtraKeys':list(primitive.get('extras',{}))},
  'existingLayer202':'Eye202Layers.Selected(0,role) and Selected(5,role) both select role3. FaceSkin and LidSkinCarrier are separate render products of the same source role; neither is a scalp/cheek/AA source-colour partition.',
  'existing104':{'hypothesis1':decision['hypothesis1']['status'],'hypothesis2':decision['hypothesis2']['status'],'weakCheek':review[0]['thinCheekStrokeProbe']},
  'sameUVWeakCheekProbes':{'sourceCropXY':[[382,704],[380,704],[384,704]],'fullTextureOffset':[4,7],'baseColorRGBA8':pixels['baseColor'],'normalRGBA8':pixels['normal']},
  'finiteOutlineColourInput':{'materialId':binding['materialId'],'source':'original VRMC_materials_mtoon.outlineColorFactor','linearRGB':mtoon.get('outlineColorFactor'),'lightingMix':mtoon.get('outlineLightingMixFactor'),'widthMode':mtoon.get('outlineWidthMode'),'widthMetres':mtoon.get('outlineWidthFactor'),'renderApplied':False,'missing':'Verified per-stage silhouette/interior-region/partial-alpha outline classification and priority. Known colour alone does not identify outline pixels.'},
  'confirmedFaceBindingsAdded':0,'newRegionDecisionMade':False,'paletteBridgeMissingInputs':bridge['missingCurrentFaceInputs'],
  'preciseLimit':'Original face colour/UV and shading metadata exist. Existing records do not contain an accepted hierarchy/decision for weak cheek paint vs continuous gradient/AA simplification. This is missing validated region assignment/objective, not missing raw texture or a proof that automatic segmentation is impossible.',
  'requiredTests':['Keep cheek source probes(382,704)/(380,704)/(384,704) distinct from discarded AA only when evidence/policy justifies it.','Same original RGB/Q must not change because material anchor changes.','Per-stage confirmed region/Q binding and explicit outline/partial-alpha handling are required before whole-face finite-palette claims.'],
  'GPUUnityOrAssetWrites':0,'product77Changed':False}
 (G/'FACE_INPUT27.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'sameUVProbes':result['sameUVWeakCheekProbes'],'outlineSource':result['finiteOutlineColourInput'],'faceBindingsAdded':0,'unconfirmedRegionsNotApplied':True}))
if __name__=='__main__':main()
