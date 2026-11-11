from pathlib import Path
import json,struct,io,hashlib,numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 reg=json.loads((H.parent/'renderer-family59/SOURCE_REGISTRY59.json').read_text());raw=(R/reg['modelAsset']).read_bytes();assert hashlib.sha256(raw).hexdigest()==reg['modelSHA256'];chunks={};at=12
 while at<len(raw):n,t=struct.unpack_from('<II',raw,at);at+=8;chunks[t]=raw[at:at+n];at+=n
 doc=json.loads(chunks[0x4e4f534a]);blob=chunks[0x004e4942];rows=[]
 for sm in [0,3,6]:
  b=next(b for b in reg['bindings']if b['rendererOrdinal']==1 and b['subMesh']==sm);v=doc['bufferViews'][doc['images'][b['imageIndex']]['bufferView']];data=blob[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];assert hashlib.sha256(data).hexdigest()==b['imageSHA256'];image=Image.open(io.BytesIO(data)).convert('RGBA');a=np.asarray(image);colors,count=np.unique(a.reshape(-1,4),axis=0,return_counts=True);ix=np.argsort(-count)[:12];rows.append({'subMesh':sm,'material':doc['materials'][b['materialId']].get('name'),'size':image.size,'uniqueRGBA':len(colors),'top':[{'rgba':colors[i].tolist(),'n':int(count[i])}for i in ix]});image.thumbnail((512,512));image.save(H/'face45'/f'source-submesh{sm}.png')
 (H/'face45/SOURCE_TEXTURE_AUDIT45.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))
if __name__=='__main__':main()
