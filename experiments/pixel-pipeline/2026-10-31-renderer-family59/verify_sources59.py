from pathlib import Path
import hashlib,io,json,struct
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent;registry=json.loads((R/'SOURCE_REGISTRY59.json').read_text());data=json.loads((R/'ACTUAL_SOURCE_POINTS59.json').read_text())
assert not data.get('error') and not data['stateChanges'] and data['invalidDrawRejected']
P=Path(data['before']['project']).parent;model=(P/registry['modelAsset']).read_bytes();assert hashlib.sha256(model).hexdigest()==registry['modelSHA256']
n=struct.unpack_from('<I',model,12)[0];doc=json.loads(model[20:20+n]);binary=model[n+28:]
images={};mismatches=[];known=0
for point in data['points']:
    binding=registry['bindings'][point['draw']];imageId=binding['imageIndex']
    if imageId not in images:
        view=doc['bufferViews'][doc['images'][imageId]['bufferView']];png=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
        assert hashlib.sha256(png).hexdigest()==binding['imageSHA256'];images[imageId]=Image.open(io.BytesIO(png)).convert('RGBA')
    if not point['known']:continue
    im=images[imageId];x,y=point['unityTexel'];expected=list(im.getpixel((x,im.height-1-y)));known+=1
    if expected!=point['rgba8']:mismatches.append({'draw':point['draw'],'triangle':point['triangle'],'expected':expected,'actual':point['rgba8']})
words=np.fromfile(R/'DRAW_DESCRIPTORS59.uint4',dtype='<u4').reshape(-1,4)
expectedWords=np.array([[b['bindingOrdinal']+1,b['rendererOrdinal'],b['subMesh'],b['triangleCount']]for b in registry['bindings']],dtype='<u4');assert np.array_equal(words,expectedWords)
summary={'configuredDraws':data['draws'],'geometryFactorExact':registry['geometryFactorExact'],'actualTexturePointSamples':len(data['points']),'readablePoints':known,
    'nativePNGExact':known-len(mismatches),'mismatches':mismatches,'drawDescriptorBytes':(R/'DRAW_DESCRIPTORS59.uint4').stat().st_size,
    'manualPrimitiveOrMaterialNameSelection':False,'sourceSamplesAreNotVisibleFrameCells':True,'currentLiveRendererCount':0,'fullCharacterABRendered':False,
    'visibleCellUnknownCounts':None,'postLineTonePaletteOutsideCounts':None,'newGPUExecution':False,'stateChanges':data['stateChanges'],
    'dirtyCount':len(data['after']['dirty']),'sceneClean':not data['after']['scenes'][0]['dirty'],
    'memoryDelta':{k:data['memoryAfter'][k]-data['memoryBefore'][k]for k in data['memoryBefore']if k!='utc'},
    'requiredNextStep':'Normal GameMap1 Play creates the configured shell/presentation. Current enterPlayModeOptionsEnabled=false implies domain+scene reload; domain-reload-free temporary option change is required before Play under current task constraints.'}
(R/'VERIFIED_SOURCE59.json').write_text(json.dumps(summary,indent=2),encoding='utf8');print(json.dumps(summary))
