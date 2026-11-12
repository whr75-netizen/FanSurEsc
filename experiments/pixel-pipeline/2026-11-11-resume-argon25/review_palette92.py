"""CPU palette and actual-input preview, not a new GPU result.

Use the exact observed89 floor and the same standalone C#89 builder. A positive
source RGB contrast alone is insufficient: test every palette level as well.
No new semantic labels, per-model colours, threshold search or RGB averaging.
"""
from pathlib import Path
import json,subprocess,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from review_motion64 import srgb
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face92'

def main():
 d=np.load(G/'SOURCE_VALUE92.npz');base=np.load(H/'face88/SOURCE_VALUE88.npz');colours=d['colours'];address=d['colourAddress'];refs=colours[d['referenceIndices']];pairs=d['profilePairs'];nativeDelta=colours[pairs[:,0]].astype(float)-colours[pairs[:,1]];edges=np.array(sorted(set((int(address[a]),int(address[b]))for a,b in base['orders'])),'<i4');assert(edges[:,0]!=edges[:,1]).all();refs.tofile(G/'REFERENCES92.rgb');edges.tofile(G/'ORDERS92.i32');live=json.loads((H/'face89/fix2/capture/RUNTIME_PALETTE89.json').read_text());exe=H/'face88/build/runtime89-core.exe';run=subprocess.run([str(exe),str(G/'REFERENCES92.rgb'),str(G/'ORDERS92.i32'),str(live['liveLinearFloor']),str(G/'PALETTE92.rgb')],check=True,capture_output=True,text=True);pal=np.fromfile(G/'PALETTE92.rgb',np.uint8).reshape(-1,3,3);metrics=[]
 for k in range(3):
  delta=pal[address[pairs[:,0]],k].astype(float)-pal[address[pairs[:,1]],k];dot=(nativeDelta*delta).sum(1);ratio=np.linalg.norm(delta,axis=1)/np.linalg.norm(nativeDelta,axis=1);bad=np.flatnonzero(dot<=0);metrics.append({'shade':k,'nativeRGBVectorNonpositive':len(bad),'sourceYOrderViolations':int(sum(luminance(pal[a,k])>=luminance(pal[b,k])for a,b in edges)),'contrastLengthRatioMinMedianMax':np.percentile(ratio,[0,50,100]).tolist(),'badPairRGBExamples':[[colours[pairs[i,0]].tolist(),colours[pairs[i,1]].tolist(),delta[i].tolist()]for i in bad[:5]]})
 v=pal.astype(float)/255;v=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).astype(np.float32);capture=H/'face89/fix2/capture';r=json.loads((capture/'COMPLETE.json').read_text());info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=info['cropOffset'];tw,th=info['textureSize'];labels=d['labels'];rows=[];board=Image.new('RGB',(1050,len(r['stream77']['frames'])*190+35),(27,29,35));draw=ImageDraw.Draw(board)
 for i,f in enumerate(r['stream77']['frames']):
  w,h=f['QROI'][2:];a=np.frombuffer(decode((capture/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(h,22,w,4).transpose(1,0,2,3);visible=a[20,:,:,3]==1;uv=a[11,:,:,:2].astype(float);x=np.floor(uv[:,:,0]*tw).astype(int)-ox;y=np.floor((1-uv[:,:,1])*th).astype(int)-oy;new=a[0].copy();k=np.rint(a[16,:,:,0][visible]*2).astype(int);new[visible,:3]=v[labels[y[visible],x[visible]],k];ims=[srgb(a[0]),srgb(a[19]),srgb(new)];row={'frame':f['frame'],'sourceId':f['sourceId'],'actualNativeUniqueFaceRGB8':len(np.unique(np.array(ims[0])[np.flipud(visible)],axis=0)),'actual89UniqueFaceRGB8':len(np.unique(np.array(ims[1])[np.flipud(visible)],axis=0)),'CPU92UniqueFaceRGB8':len(np.unique(np.array(ims[2])[np.flipud(visible)],axis=0)),'nonfaceAndAlphaChanges':int(np.count_nonzero((new[~visible]!=a[0][~visible]).any(1)))+int(np.count_nonzero(new[:,:,3]!=a[0,:,:,3]))};rows.append(row)
  for j,(im,title)in enumerate(zip(ims,['Actual native RGB','Actual GPU89,740 addresses','CPU92,226 addresses; NOT GPU'])):
   draw.text((j*350+3,i*190+4),f"F{f['frame']} {title}",fill='white');board.paste(im,(j*350+3,i*190+27));board.paste(im.resize((w*5,h*5),Image.Resampling.NEAREST),(j*350+45,i*190+27))
 draw.text((4,len(rows)*190+8),'Same observed source/Q/floor. CPU92 is not a new runtime or an artistic adoption.',fill='white');board.save(G/'CPU_PALETTE92.png');result={'CPUOnly':True,'newGPUExecution':False,'liveFloorFromActual89':live['liveLinearFloor'],'actualCSharp89Builder':True,'builderOutput':run.stdout.strip(),'sourceAddresses':len(refs),'paletteLevels':3,'rows':rows,'paletteContrast':metrics,'sourceContrastDoesNotGuaranteePaletteContrast':any(x['nativeRGBVectorNonpositive']for x in metrics)>0,'artAdopted':False};(G/'CPU_PALETTE92.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
