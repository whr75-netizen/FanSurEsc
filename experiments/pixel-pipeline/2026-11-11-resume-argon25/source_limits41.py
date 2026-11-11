"""Read original source fields and actual evaluated projection; never assign a guessed family."""
from pathlib import Path
import io,json,struct,hashlib,numpy as np
from PIL import Image
from alpha_support38 import AlphaSupport
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face41';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 reg=json.loads((H.parent/'renderer-family59/SOURCE_REGISTRY59.json').read_text());raw=(R/reg['modelAsset']).read_bytes();assert hashlib.sha256(raw).hexdigest()==reg['modelSHA256'];chunks={};at=12
 while at<len(raw):n,t=struct.unpack_from('<II',raw,at);at+=8;chunks[t]=raw[at:at+n];at+=n
 doc=json.loads(chunks[0x4e4f534a]);blob=chunks[0x004e4942];b=next(b for b in reg['bindings']if b['rendererOrdinal']==1 and b['subMesh']==6);im=doc['images'][b['imageIndex']];v=doc['bufferViews'][im['bufferView']];encoded=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];assert hashlib.sha256(encoded).hexdigest()==b['imageSHA256'];rgba=np.asarray(Image.open(io.BytesIO(encoded)).convert('RGBA'));support=AlphaSupport(rgba[:,:,3],True)
 rows=[]
 for i in range(1,len(support.regions)+1):
  mask=support.labels==i;rows.append({'sourceSupportId':i,'positiveAlphaTexels':int(mask.sum()),'originalRGBCount':len(np.unique(rgba[mask,:3],axis=0))})
 capture=json.loads((G/'capture/COMPLETE.json').read_text());width=[]
 for f in capture['frames']:
  g=geometry(G/'capture'/('geometry-frame'+str(f['frame'])+'.bin'));assert g['sourceId']==f['sourceId'];w,h=f['QROI'][2:];assert np.array_equal(g['vp'][3],[0,0,0,1]);projected=g['vp'][:2,:3]*np.array([[w/2],[h/2]]);metres=f['frameInfo']['nativeOutlineWidthMetres39'];bound=float(np.linalg.svd(projected,compute_uv=False).max()*metres);width.append({'frame':f['frame'],'sourceId':f['sourceId'],'sourceWorldOutlineWidth':metres,'maxProjectedSourceDisplacementCellsForAnyUnitNormalAndWidthGreen01':bound})
 result={'modelSHA256':reg['modelSHA256'],'nativePigmentImageSHA256':b['imageSHA256'],'nativePigmentPositiveRGBCount':len(np.unique(rgba[rgba[:,:,3]>0,:3],axis=0)),'sourceSupportComponents':rows,'proof':'Alpha connectivity supplies source identity, not a uniform-colour family. Large supports each retain thousands of source RGB values. No mean/threshold or family was assigned.','actualProjectedOutlineBounds':width,'variableThicknessStatus':'All current native widths project below one cell. Actual input cannot validate >1-cell variable thickness. Minimum-representation/thickness policy is not silently inferred from source width.','fullBaseFacePaletteApplied':False,'GPUOrUnityCalls':0};(G/'SOURCE_LIMITS41.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'pigmentRGBCount':result['nativePigmentPositiveRGBCount'],'largeSourceSupports':rows[1:3],'projectedWidthMax':[r['maxProjectedSourceDisplacementCellsForAnyUnitNormalAndWidthGreen01']for r in width]}))
if __name__=='__main__':main()
