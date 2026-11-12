"""Recorded actual evaluated normals and camera, CPU MToon extrusion only."""
from pathlib import Path
import json,hashlib,io,struct,numpy as np
from PIL import Image,ImageDraw
from native_width86 import normals,green_repeat_bilinear,extrude
from selected_light84 import geometry
H=Path(__file__).resolve().parent;G=H/'face86';C=H/'face85/pulse120/capture';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')

def source_texture(policy):
 model=R/policy['modelAsset'];assert hashlib.sha256(model.read_bytes()).hexdigest()==policy['modelSHA256']
 src=json.loads((H/'face67/SOURCE_FLAT67.json').read_text())
 with model.open('rb')as f:
  assert struct.unpack('<I',f.read(4))[0]==0x46546c67;f.read(8);size,kind=struct.unpack('<II',f.read(8));assert kind==0x4e4f534a and size<2097152;doc=json.loads(f.read(size));bs,bt=struct.unpack('<II',f.read(8));assert bt==0x004e4942;start=f.tell();m=doc['materials'][src['sourceFamily']['source']['materialId']];tex=m['extensions']['VRMC_materials_mtoon']['outlineWidthMultiplyTexture'];im=doc['images'][doc['textures'][tex['index']]['source']];v=doc['bufferViews'][im['bufferView']];assert v.get('buffer',0)==0 and v['byteLength']<=1048576;f.seek(start+v.get('byteOffset',0));png=f.read(v['byteLength'])
 assert hashlib.sha256(png).hexdigest()==policy['sourcePNG_SHA256'];a=np.asarray(Image.open(io.BytesIO(png)).convert('RGBA'));assert np.array_equal(a,np.asarray(Image.open(H/'face40/analysis-directed/SOURCE_WIDTH_MASK40.png').convert('RGBA')));return a

def main():
 receipt=json.loads((C/'COMPLETE.json').read_text());assert receipt['restorationChecksPass']and receipt['ownedResourcesReleased'];policy=json.loads((H/'face69/ZERO_POLICY69.json').read_text());rgba=source_texture(policy);rows=[];examples=[]
 for f in receipt['stream77']['frames']:
  info=f['light84'];name=info['nativeNormals86File']
  if name=='not-sampled':continue
  geo=geometry(C/info['sourceGeometryFile']);n=normals(C/name);settings=info['originalWidth86'];assert n['sourceId']==geo['sourceId']==f['sourceId']and n['frame']==geo['frame']==f['frame'];assert settings['mode']==1 and settings['filter']=='Bilinear'and settings['wrapU']==settings['wrapV']=='Repeat'and settings['textureImageHash']==policy['liveTextureImageHash'];assert len(n['normal'])==len(geo['v'])
  uv=geo['v'][:,3:5];assert hashlib.sha256(uv.astype('<f4').tobytes()).hexdigest()==policy['uvSHA256'];assert hashlib.sha256(geo['tri'].astype('<i4').tobytes()).hexdigest()==policy['indexSHA256'];green=green_repeat_bilinear(rgba,uv,settings['textureSRGB'])if settings['parameterMapEnabled']else np.ones(len(uv));projection=np.array(info['projection85']).reshape(4,4,order='F');a=extrude(geo['v'][:,:3],n['normal'],n['valid'],settings['widthMetres'],green,geo['view'],projection,[480,272]);err=float(np.max(abs(a['start']-geo['v'][:,5:])));assert err<2e-5
  lengths=a['length'];positive=lengths[lengths>0];row={'frame':f['frame'],'sourceId':f['sourceId'],'vertices':len(uv),'projectionHeadMaxErrorCells':err,'widthMetres':settings['widthMetres'],'worldPixel':info['worldPixel85'],'nominalWidthBeforeGreenAndProjectionCells':settings['widthMetres']/info['worldPixel85'],'positiveVertexExtrusionCount':len(positive),'zeroVertexExtrusionCount':int((lengths==0).sum()),'projectedVertexExtrusionCellsPercentile0_50_95_100':np.percentile(lengths,[0,50,95,100]).tolist(),'greenMinMax':[float(green.min()),float(green.max())],'samplerOracle':'mathematical bilinear LOD0, not GPU fixed-point exact','newGPUWidthRaster':False};rows.append(row);examples.append((f,a,green))
 assert len(rows)==8;out={'actualRecordedFrames':len(rows),'currentNormalsSourceAndCameraIdentityMatch':True,'sourceTextureFromOriginalVRMBytes':True,'sourceShaderRule':'native MToon worldPosition + original deformed worldNormal * widthMetres * greenLOD0','sourceInkOrDepthAltered':False,'newGPUWidthRaster':False,'oneOpaquePixelIsSourceFaithfulClaimed':False,'fullInvertedHullVisibilityOrIntegerWidthPolicyProven':False,'rows':rows};(G/'NATIVE_WIDTH86.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k!='rows'}));print('max displacement cells',max(x['projectedVertexExtrusionCellsPercentile0_50_95_100'][-1]for x in rows))
 # Scientific diagnostic of actual recorded geometry with CPU projected arrows.
 # 40x arrows are explicitly marked; this is not a final GPU line rendering.
 board=Image.new('RGB',(1000,490),(27,29,35));draw=ImageDraw.Draw(board)
 for col,i in enumerate([0,7]):
  f,a,green=examples[i];p=a['start'];lo=p.min(0)-1;scale=15;offset=np.array([col*500+15,45]);screen=(p-lo)*scale+offset
  for j in range(len(p)):
   if green[j]<=0:continue
   pt=tuple(screen[j]);end=tuple(screen[j]+a['delta'][j]*scale*40);draw.line([pt,end],fill=(60,160,205),width=1)
  draw.text((col*500+8,8),f"F{f['frame']} actual normals/camera; CPU displacement arrows x40",fill='white')
 draw.text((8,449),'No integer raster or visibility claim. Native projected displacement is much smaller than one opaque pixel.',fill='white');draw.text((8,470),'Actual source green and deformed vertex normals; no geometry-normal/normal-map substitution.',fill='white');board.save(G/'NATIVE_WIDTH86.png')
if __name__=='__main__':main()
