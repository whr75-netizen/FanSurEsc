from pathlib import Path
import io,json,struct,hashlib
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw
from alpha_support38 import AlphaSupport
H=Path(__file__).resolve().parent;G=H/'face38';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 reg=json.loads((H.parent/'renderer-family59/SOURCE_REGISTRY59.json').read_text());binding=[b for b in reg['bindings']if b['rendererOrdinal']==1 and b['subMesh']==6];assert len(binding)==1;b=binding[0];data=(R/reg['modelAsset']).read_bytes();assert hashlib.sha256(data).hexdigest()==reg['modelSHA256'];chunks={};at=12
 while at<len(data):n,t=struct.unpack_from('<II',data,at);at+=8;chunks[t]=data[at:at+n];at+=n
 doc=json.loads(chunks[0x4e4f534a]);blob=chunks[0x004e4942];im=doc['images'][b['imageIndex']];view=doc['bufferViews'][im['bufferView']];encoded=blob[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];assert hashlib.sha256(encoded).hexdigest()==b['imageSHA256'];rgba=np.asarray(Image.open(io.BytesIO(encoded)).convert('RGBA'));a=rgba[:,:,3];mat=doc['materials'][b['materialId']];tex=doc['textures'][b['textureIndex']];sampler=doc['samplers'][tex['sampler']]
 assert sampler=={'magFilter':9729,'minFilter':9729,'wrapS':10497,'wrapT':10497},sampler
 assert mat['pbrMetallicRoughness'].get('baseColorFactor',[1,1,1,1])==[1,1,1,1]and b['uvConvention']=='unity-flip-v'
 support=AlphaSupport(a,True);capture=H/'face33/capture';r=json.loads((capture/'COMPLETE.json').read_text())
 def field(name):
  ps=sorted([p for p in r['planes']if p['name']==name],key=lambda x:x['bottomRow']);assert ps and sum(p['rows']for p in ps)==ps[0]['height'];return np.concatenate([np.fromfile(capture/p['file'],dtype='<f4').reshape(p['rows'],p['width'],4)for p in ps])
 colour,meta=field('source2'),field('source3');valid=(meta[:,:,0]>0)&(colour[:,:,3]>0);records=[];ids=np.zeros(valid.shape,np.uint32)
 for y,x in np.argwhere(valid):
  # Registry declares Unity V-flip; encoded PNG rows are top-to-bottom.
  q=support.sample((meta[y,x,1],1-meta[y,x,2]));ids[y,x]=q['supportId'];records.append({'fineXY':[int(x),int(y)],'sourceUV':meta[y,x,1:3].tolist(),'predictedAlpha':q['alpha'],'GPUAlpha':float(colour[y,x,3]),'supportId':q['supportId'],'ambiguous':q['ambiguous'],'sourceIds':q['sourceIds'],'footprintSupportId':q['footprintSupportId'],'alphaEnvelope':q['alphaEnvelope'],'insideSourceAlphaEnvelope':q['alphaEnvelope'][0]<=float(colour[y,x,3])<=q['alphaEnvelope'][1]})
 errors=np.array([abs(x['predictedAlpha']-x['GPUAlpha'])for x in records]);stats={'modelSHA256':reg['modelSHA256'],'binding':{k:b[k]for k in ['rendererOrdinal','subMesh','materialId','imageIndex','imageSHA256','uvConvention']},'sourceImageSize':list(a.shape[::-1]),'sourceAlphaMax':int(a.max()),'sourceAlphaPositiveTexels':int((a>0).sum()),'sourceOpaqueTexels':int((a==255).sum()),'sourceSupportComponents':len(support.regions),'sourceComponents':support.regions,'actualSourceId':r['frameKey'],'actualFrame':r['capturedFrame'],'actualVisibleFineSamples':len(records),'observedSupportIds':dict(Counter(int(x['supportId'])for x in records)),'ambiguousFineSamples':sum(x['ambiguous']for x in records),'fourTexelFootprintUniqueIdentity':sum(x['footprintSupportId']>0 for x in records),'outsideSourceAlphaEnvelope':sum(not x['insideSourceAlphaEnvelope']for x in records),'alphaAbsError':{'mean':float(errors.mean()),'max':float(errors.max())},'alphaSamplingEqualityProven':False,'colourFamilyDefined':False,'finalPixelOwnerDefined':False,'GPUExecutedByThisScript':False,'records':records}
 G.mkdir(exist_ok=True);(G/'NATIVE_SUPPORT38.json').write_text(json.dumps(stats,indent=2),encoding='utf-8',newline='\n');palette=np.array([[0,0,0]]+[[int(40+(i*53)%216),int(40+(i*97)%216),int(40+(i*173)%216)]for i in range(1,len(support.regions)+1)],np.uint8);left=Image.fromarray(a).convert('RGB').resize((384,384));right=Image.fromarray(palette[support.labels]).resize((384,384),Image.Resampling.NEAREST);board=Image.new('RGB',(768,424),(35,37,43));board.paste(left,(0,40));board.paste(right,(384,40));d=ImageDraw.Draw(board);d.text((8,8),'original native alpha support (not final colour)',fill='white');d.text((392,8),'source support IDs (not colour families)',fill='white');board.save(G/'SOURCE_SUPPORT38.png');print(json.dumps({k:v for k,v in stats.items()if k not in ['records','sourceComponents']},indent=2))
if __name__=='__main__':main()
