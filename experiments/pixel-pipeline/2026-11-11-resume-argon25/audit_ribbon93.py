"""Eight saved actual86-normal packets; independent geometric width oracle."""
from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image
from native_width86 import normals,green_repeat_bilinear,extrude
from selected_light84 import geometry
from projected_ribbon93 import raster
from audit_native_width86 import source_texture
H=Path(__file__).resolve().parent;G=H/'face93';C=H/'face85/pulse120/capture'
def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def edges(geo,weld):
 tri=geo['tri'];p=geo['v'][:,5:7].astype(float);t=p[tri];det=cross2(t[:,1]-t[:,0],t[:,2]-t[:,0]);sign=np.sign(det);source={}
 for i,row in enumerate(tri):
  for a,b in zip(row,np.roll(row,-1)):
   key=tuple(sorted((int(weld[a]),int(weld[b]))))
   if key[0]==key[1]:continue
   if key not in source:source[key]=[int(a),int(b),[]]
   source[key][2].append(i)
 return np.asarray([[a,b]for key,(a,b,faces)in sorted(source.items())if len(faces)==2 and sign[faces[0]]!=sign[faces[1]]],int)
def main():
 r=json.loads((C/'COMPLETE.json').read_text());policy=json.loads((H/'face69/ZERO_POLICY69.json').read_text());rgba=source_texture(policy);weld=np.asarray(json.loads((H/'face40/WELD40.json').read_text())['weld']);rows=[]
 for f in r['stream77']['frames']:
  info=f['light84']
  if info['nativeNormals86File']=='not-sampled':continue
  geo=geometry(C/info['sourceGeometryFile']);normal=normals(C/info['nativeNormals86File']);assert normal['sourceId']==geo['sourceId']==f['sourceId'];setting=info['originalWidth86'];green=green_repeat_bilinear(rgba,geo['v'][:,3:5],setting['textureSRGB'])if setting['parameterMapEnabled']else np.ones(len(geo['v']));p=extrude(geo['v'][:,:3],normal['normal'],normal['valid'],setting['widthMetres'],green,geo['view'],np.array(info['projection85']).reshape(4,4,order='F'),[480,272]);ix=edges(geo,weld);a=p['start']-.5;b=p['expanded']-.5;out,budget=raster(a,b,ix);area=0
  for ia,ib in ix:
   area+=abs(cross2(a[ib]-a[ia],b[ib]-a[ia]))*.5+abs(cross2(b[ib]-a[ia],b[ia]-a[ia]))*.5
  rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'segments':len(ix),'bboxPixelUpperMeasured':budget,'nativeWidthMetres':setting['widthMetres'],'maximumProjectedNativeDisplacementCells':float(p['length'].max()),'positiveAreaRibbonCellsBeforeVisibility':len(out),'sumProjectedTriangleAreasNotUnionArea':float(area),'oneOpaqueCellEqualsNativeAreaClaimed':False})
 assert len(rows)==8;result={'savedActualSourcePackets':8,'newGPUExecuted':False,'allSourceIdentityNormalsUVProjectionMatched':True,'allBBoxWithinDeclared8192Budget':all(x['bboxPixelUpperMeasured']<=8192 for x in rows),'currentAlphaOrWorldOcclusionProven':False,'rows':rows};(G/'SAVED_GEOMETRY93.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
