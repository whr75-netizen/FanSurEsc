"""CPU application to immutable actual77 inputs, explicitly NOT GPU output."""
from pathlib import Path
import json,struct,subprocess,os,sys,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from review_motion64 import srgb
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face82'

def main():
 (G/'build').mkdir(exist_ok=True);refs=np.array(json.loads((G/'HIERARCHY82.json').read_text())['references'],np.uint8);spec=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());settings=spec['settingsFromExisting58'];levels=settings['count'];csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';exe=G/'build/palette82.exe';subprocess.run([str(csc),'/nologo','/optimize+','/target:exe','/out:'+str(exe),str(H/'PaletteTable82.cs'),str(H.parent/'source-palette58/SourcePalette58.cs')],check=True,capture_output=True)
 inp=G/'build/INPUT.bin';out=G/'PALETTE82.rgb';inp.write_bytes(struct.pack('<ii4d',len(refs),levels,*[settings[k]for k in['darkLRatio','darkCRatio','gamma','intervalScale']])+refs.astype('<i4').tobytes());subprocess.run([str(exe),str(inp),str(out)],check=True);palette=np.frombuffer(out.read_bytes(),np.uint8).reshape(len(refs),levels,3);linear=palette.astype(float)/255;linear=np.where(linear<=.04045,linear/12.92,((linear+.055)/1.055)**2.4).astype(np.float32)
 data=np.load(G/'SOURCE_FIELD82.npz');labels=data['labels'];info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=info['cropOffset'];tw,th=info['textureSize'];report=json.loads((H/'face77/loop120/capture/COMPLETE.json').read_text());rows=[];panels=[];q=report['sourcePalette67']['zeroWidth69']['role']
 for ordinal,f in enumerate(report['stream77']['frames']):
  if ordinal not in[0,20,40,60,80,100,119]:continue
  w,h=f['QROI'][2:];raw=decode((H/'face77/loop120/capture'/f['compressedFile']).read_bytes(),f['bytes']);a=np.frombuffer(raw,'<f4').reshape(h,w*13,4);parts=[a[:,i*w:(i+1)*w]for i in range(13)];before=parts[0];cell,owner,uv,source=parts[5:9];domain=parts[11];face=(cell[:,:,2]==1)&(owner[:,:,0]==q)&(domain[:,:,0]<.5)&(source[:,:,0]==owner[:,:,2])&(source[:,:,1]==owner[:,:,0])&(source[:,:,2]==owner[:,:,1]);candidate=before.copy();known=np.zeros((h,w),bool);family=np.full((h,w),-1,int)
  for y,x in np.argwhere(face):
   u,v=uv[y,x,:2];xx=int(np.floor(float(u)*tw))-ox;yy=int(np.floor((1-float(v))*th))-oy
   if not(0<=xx<labels.shape[1]and 0<=yy<labels.shape[0])or labels[yy,xx]<0:continue
   k=round(float(uv[y,x,2])*(levels-1));assert 0<=k<levels;family[y,x]=int(labels[yy,xx]);candidate[y,x,:3]=linear[family[y,x],k];known[y,x]=True
  oldface=parts[10][:,:,3]==1;rows.append({'frame':f['frame'],'ordinaryFaceCells':int(face.sum()),'candidateKnownCells':int(known.sum()),'unknownCells':int((face&~known).sum()),'oldPartialLUTCells':int(oldface.sum()),'nativeFaceUniqueRGB8':len(np.unique(np.array(srgb(before))[np.flipud(face)],axis=0))if face.any()else 0,'candidateFaceUniqueRGB8':len(np.unique(np.array(srgb(candidate))[np.flipud(known)],axis=0))if known.any()else 0,'sourceAddressesUsed':len(np.unique(family[known])),'allChangedFaceUsesFiniteLUT':True});panels.append((f,srgb(before),srgb(parts[1]),srgb(candidate)))
 inp=np.load(G/'ORDER_INPUT82.npz');address=data['colourAddress'];paletteY=luminance(palette);violations=[]
 for k in range(levels):violations.append(int(sum(paletteY[address[int(a)],k]>=paletteY[address[int(b)],k]for a,b in inp['orders'])))
 result={'CPUReusedOriginalCSharp58':True,'actualGPUInputFrames':len(rows),'candidateGPUExecuted':False,'settingsUnchangedFrom67':settings,'sourceColourAddresses':len(refs),'strictSourceOrderViolationsAfterFiniteLUTByShade':violations,'unknownOrdinaryFaceCells':sum(r['unknownCells']for r in rows),'perTexelFamilyClaimed':False,'fullFaceArtAdopted':False,'rows':rows};(G/'DISPLAY82.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));board=Image.new('RGB',(1050,205*len(panels)+30),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(f,*images)in enumerate(panels):
  for j,(im,title)in enumerate(zip(images,['Actual native77','Actual partial LUT77','CPU whole-source82, NOT GPU'])):draw.text((350*j+4,i*205+3),f"F{f['frame']} {title}",fill='white');board.paste(im,(350*j+4,i*205+24));board.paste(im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST),(350*j+48,i*205+24))
 board.save(G/'CPU_DISPLAY82.png')
if __name__=='__main__':main()
