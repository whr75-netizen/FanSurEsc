"""Same-frame causal split: source equality mask versus independent Q and RGB.
No segmentation or lighting fit; no Unity calls and no new output colours.
"""
from pathlib import Path
import json,struct,io,hashlib,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face74';C=H/'face73/capture';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 G.mkdir(exist_ok=True);api.C=C;r=json.loads((C/'COMPLETE.json').read_text());spec=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());raw=(R/spec['modelAsset']).read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=raw[28+jl:];mat=spec['sourceFamily']['source']['materialId'];idx=doc['materials'][mat]['pbrMetallicRoughness']['baseColorTexture']['index'];image=doc['images'][doc['textures'][idx]['source']];view=doc['bufferViews'][image['bufferView']];png=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];assert hashlib.sha256(png).hexdigest()==spec['sourceFamily']['source']['imageSHA256'];rgb=np.asarray(Image.open(io.BytesIO(png)).convert('RGBA'))[::-1,:,:3].astype(float)
 def sample(uv):
  p=np.asarray(uv)*[rgb.shape[1],rgb.shape[0]]-.5;lo=np.floor(p).astype(int);frac=p-lo;colour=np.zeros(3)
  for dy in[0,1]:
   for dx in[0,1]:colour+=rgb[(lo[1]+dy)%rgb.shape[0],(lo[0]+dx)%rgb.shape[1]]*(frac[0]if dx else 1-frac[0])*(frac[1]if dy else 1-frac[1])
  return colour
 rows=[]
 for f in r['frames']:
  w=f['QROI'][2];b=api.plane(r,f,'ownerReceipts47');uv=b[:,w:2*w];s=b[:,2*w:3*w];face=b[:,3*w:4*w,0]==4;receipt=api.plane(r,f,'sourcePaletteReceipt67');known=receipt[:,:,3]==1;atlas=api.plane(r,f,'atlas40');before=atlas[:,9*w:10*w];after=api.plane(r,f,'widthCompositeAtlas61')[:,:2*w][::2,::2];edges=[]
  for y,x in np.argwhere(face):
   for dy,dx in[(1,0),(0,1)]:
    yy,xx=y+dy,x+dx
    if yy>=face.shape[0]or xx>=w or not face[yy,xx]or known[y,x]==known[yy,xx]or uv[y,x,2]!=uv[yy,xx,2]:continue
    src0=sample(uv[y,x,:2]);src1=sample(uv[yy,xx,:2]);base0=np.asarray(srgb(before[y:y+1,x:x+1]))[0,0].astype(int);base1=np.asarray(srgb(before[yy:yy+1,xx:xx+1]))[0,0].astype(int);out0=np.asarray(srgb(after[y:y+1,x:x+1]))[0,0].astype(int);out1=np.asarray(srgb(after[yy:yy+1,xx:xx+1]))[0,0].astype(int)
    edges.append({'localXY0':[int(x),int(y)],'localXY1':[int(xx),int(yy)],'sourceUV0':uv[y,x,:2].tolist(),'sourceUV1':uv[yy,xx,:2].tolist(),'sourcePrimitive0':int(s[y,x,3]),'sourcePrimitive1':int(s[yy,xx,3]),'samePrimitive':bool(s[y,x,3]==s[yy,xx,3]),'Q0and1':float(uv[y,x,2]),'LUTAssigned0and1':[bool(known[y,x]),bool(known[yy,xx])],'sourceEncodedBilinearRGB0':src0.tolist(),'sourceEncodedBilinearRGB1':src1.tolist(),'sourceMaxRGB8Delta':float(abs(src0-src1).max()),'nativeRGB0':base0.tolist(),'nativeRGB1':base1.tolist(),'candidateRGB0':out0.tolist(),'candidateRGB1':out1.tolist(),'nativeMaxRGB8Jump':int(abs(base0-base1).max()),'candidateMaxRGB8Jump':int(abs(out0-out1).max())})
  edges.sort(key=lambda v:(not v['samePrimitive'],v['sourceMaxRGB8Delta'],-v['candidateMaxRGB8Jump']));rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'sameQAssignedUnknownFaceEdges':len(edges),'edges':edges})
 witnesses=[dict(e,frame=f['frame'],sourceId=f['sourceId'])for f in rows for e in f['edges']];witnesses.sort(key=lambda v:(not v['samePrimitive'],v['sourceMaxRGB8Delta'],-v['candidateMaxRGB8Jump']));result={'currentInput':'actual same-frame source73 ordinary face/UV/Q/LUT receipt/native RGB/candidate RGB','newUnityGPUCalls':0,'cause':'partial exact-RGB source plateaus are not full source colour regions; same-Q neighbouring face cells enter different RGB contracts','sourceReferenceIsEncodedMathematicalBilinearNotClaimedGPUTextureSample':True,'perFrame':rows,'representative':witnesses[:8],'fullFaceSolution':False};(G/'MOTTLE_CAUSE74.json').write_text(json.dumps(result,indent=2));print(json.dumps({'edges':[f['sameQAssignedUnknownFaceEdges']for f in rows],'first':witnesses[0]if witnesses else None}))
 # srgb() converts bottom-left RT storage to top-left PNG rows. Apply exactly
 # the same flip to a debug label; never change the recorded GPU coordinates.
 f=r['frames'][0];w=f['QROI'][2];a=api.plane(r,f,'atlas40');before=a[:,9*w:10*w];after=api.plane(r,f,'widthCompositeAtlas61')[:,:2*w][::2,::2];receipt=api.plane(r,f,'sourcePaletteReceipt67');overlay=np.asarray(srgb(before)).copy();overlay[(receipt[:,:,3]==1)[::-1]]=[0,220,240];images=[srgb(before),Image.fromarray(overlay),srgb(after)];board=Image.new('RGB',(1000,400),(27,29,35));d=ImageDraw.Draw(board)
 for col,(im,title)in enumerate(zip(images,['Actual native face','Cyan = partial LUT assignment','Actual candidate: partial LUT'])):d.text((col*330+10,10),title,fill='white');board.paste(im,(col*330+10,40));board.paste(im.resize((im.width*6,im.height*6),Image.Resampling.NEAREST),(col*330+10,100))
 d.text((10,370),'Same-frame evidence, not a completed segmentation. No native colours changed by this analysis.',fill='white');board.save(G/'MOTTLE_CAUSE74.png')
if __name__=='__main__':main()
