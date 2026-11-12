from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from selected_light84 import known,geometry,barycentric_uv
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face84';C=G/'capture'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];rows=[];panels=[];points=[]
 for f in r['stream77']['frames']:
  w,h=f['QROI'][2:];raw=decode((C/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,16,w,4).transpose(1,0,2,3);before,meta,world,cell,owner,uv,src,domain,cls,sm,norm,suv,addr,hu,hm,mask=a;yy,xx=np.indices((h,w));q=np.stack([xx+f['QROI'][0]+f['join'][0],yy+272-f['QROI'][1]-h+f['join'][1]],2);face=(cell[:,:,2]==1)&(owner[:,:,0]==4)&(domain[:,:,0]<.5)&(src[:,:,:3]==owner[:,:,[2,0,1]]).all(2);valid=known(cell,owner,src,domain,sm,suv,hu,uv,cls)&(cell[:,:,:2]==q).all(2);assert np.array_equal(addr[:,:,3]==1,valid)
  why={'role':sm[:,:,1]==4,'rawToHeadUV':(suv[:,:,:2]==hu[:,:,:2]).all(2),'headToMainUV':(hu[:,:,:2]==uv[:,:,:2]).all(2),'classToHeadQ':hu[:,:,2]==cls[:,:,0],'sourceMetaIdentity':(src[:,:,1:]==sm[:,:,1:]).all(2)};geo=geometry(C/f"geometry-frame{f['frame']}.bin");assert geo['sourceId']==f['sourceId']and geo['frame']==f['frame']and geo['model']==f['model'];v=geo['v'];grows=[]
  for y,x in np.argwhere(face):
   p=int(src[y,x,3])-1
   if not 0<=p<len(geo['tri']):continue
   t=v[geo['tri'][p]].astype(float);b=barycentric_uv(t[:,3:5],uv[y,x,:2]);record={'frame':f['frame'],'localXY':[int(x),int(y)],'globalXY':q[y,x].tolist(),'known':bool(valid[y,x]),'role':int(owner[y,x,0]),'primitive':p+1,'UV':uv[y,x,:2].tolist(),'qSelected':float(uv[y,x,2]),'sourceClass':cls[y,x].tolist(),'sourceMask':mask[y,x].tolist(),'address':addr[y,x].tolist(),'normal':norm[y,x].tolist(),'headMeta':hm[y,x].tolist(),'rawMeta':sm[y,x].tolist()}
   if b is not None:
    cross=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n=np.linalg.norm(cross);en=np.linalg.norm(norm[y,x,:3]);z=-float((geo['view']@np.r_[b@t[:,:3],1])[2]);record.update(barycentric=b.tolist(),geometryDepth=z,geometryVsClassDepth=z-float(cls[y,x,2]))
    if n>0 and en>0:record['absGeometryEffectiveDot']=float(abs((cross/n)@(norm[y,x,:3]/en)))
   points.append(record);grows.append(record)
  good=cls[:,:,1][valid];rows.append({'frame':f['frame'],'motion':f['motion']['stage'],'faceCells':int(face.sum()),'knownSelectedG':int(valid.sum()),'unknownFace':int((face&~valid).sum()),'failedConditions':{k:int((face&~v).sum())for k,v in why.items()},'gRange': [float(good.min()),float(good.max())]if len(good)else None,'selectedQHistogram':{str(float(qv)):int(((uv[:,:,2]==qv)&valid).sum())for qv in np.unique(uv[:,:,2][valid])},'minAbsGeometryEffectiveDot':min([x['absGeometryEffectiveDot']for x in grows if x.get('known')and'absGeometryEffectiveDot'in x],default=None),'maxGeometryVsClassDepth':max([abs(x['geometryVsClassDepth'])for x in grows if x.get('known')and'geometryVsClassDepth'in x],default=None)})
  normal=np.zeros_like(before);normal[:,:,:3]=(norm[:,:,:3]+1)*.5;normal[:,:,3]=1;gg=np.zeros_like(before);gg[:,:,:3]=np.clip(cls[:,:,1,None],0,1);gg[:,:,3]=1;qq=np.zeros_like(before);qq[:,:,:3]=uv[:,:,2,None];qq[:,:,3]=1;panels.append((f,srgb(before),srgb(gg),srgb(qq),srgb(normal)))
 board=Image.new('RGB',(1120,len(panels)*190+30),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(f,*images)in enumerate(panels):
  for j,(im,title)in enumerate(zip(images,['Actual native','Existing selected g','Actual selected Q','Existing effective normal'])):draw.text((j*280+3,i*190+3),f"F{f['frame']} {title}",fill='white');board.paste(im,(j*280+3,i*190+25));board.paste(im.resize((w*5,h*5),Image.Resampling.NEAREST),(j*280+40,i*190+25))
 draw.text((4,len(panels)*190+7),'Read-only existing producer. Unknown address/UV cases are not lighting evidence.',fill='white');board.save(G/'SELECTED_LIGHT84.png');result={'actualFrames':len(rows),'existingLightReevaluated':False,'GPUComputeDispatchesAdded':0,'knownSelectedG':sum(x['knownSelectedG']for x in rows),'unknownFaceCells':sum(x['unknownFace']for x in rows),'newQOrPaletteOrArtAdopted':False,'rows':rows,'points':points};(G/'SELECTED_LIGHT84.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='points'}))
if __name__=='__main__':main()
