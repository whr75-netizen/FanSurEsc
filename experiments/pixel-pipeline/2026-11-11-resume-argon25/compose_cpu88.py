"""Complete source-value88 table through actual C#87, frozen actual85 inputs.

Output is explicitly CPU, before any new GPU render. Current source ownership
and alpha are preserved; all eligible face cells use one finite LUT path.
"""
from pathlib import Path
import json,os,struct,subprocess,hashlib,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from audit_source_shade87 import string,read_string
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face88';C=H/'face85/capture'

def main():
 d=np.load(G/'SOURCE_VALUE88.npz');part=np.load(H/'face86/REGIONS86.npz');native=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=native['rgba'][:,:,:3];mask=d['mask'];address=d['labels'];key=(rgb[:,:,0].astype(np.int32)<<16)|(rgb[:,:,1].astype(np.int32)<<8)|rgb[:,:,2];info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());levels=3;p=np.fromfile(G/'PALETTE88.rgb',np.uint8).reshape(-1,levels,3);v=p.astype(float)/255;v=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).astype('<f4');palette=np.ones((len(p),levels,4),'<f4');palette[:,:,:3]=v;assert not(mask&(address<0)).any();root=G/'build';root.mkdir(exist_ok=True);csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';exe=root/'source88.exe';subprocess.run([str(csc),'/nologo','/optimize+','/target:exe','/out:'+str(exe),str(H/'SourceShade87.cs'),str(H/'SourceShadeTests87.cs')],check=True,capture_output=True);r=json.loads((C/'COMPLETE.json').read_text());frames=r['stream77']['frames'];cases=[];contract=info['modelSHA256']+'/'+info['sourceImageSHA256']+'/source-value88/existing58/ordered-RGB8';tw,th=info['textureSize'];ox,oy=info['cropOffset']
 with(root/'complete-input.bin').open('wb')as f:
  f.write(struct.pack('<iii',mask.size,len(p),levels));f.write(string(contract));table=np.empty(mask.shape,np.dtype([('mask','u1'),('support','<i4'),('key','<i4'),('address','<i4')]));table['mask']=mask;table['support']=part['regions'];table['key']=key;table['address']=address;f.write(table.tobytes());f.write(palette.tobytes());f.write(struct.pack('<i',len(frames)*2))
  for frame in frames:
   w,h=frame['QROI'][2:];raw=decode((C/frame['compressedFile']).read_bytes(),frame['bytes']);assert hashlib.sha256(raw).hexdigest()==frame['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,17,w,4).transpose(1,0,2,3);visible=a[12,:,:,3]==1;uv=a[11,:,:,:2].astype(float);x=np.floor(uv[:,:,0]*tw).astype(int)-ox;y=np.floor((1-uv[:,:,1])*th).astype(int)-oy;inside=(x>=0)&(y>=0)&(x<mask.shape[1])&(y<mask.shape[0]);texel=np.where(inside,y*mask.shape[1]+x,-1);known=np.zeros_like(visible);known[inside]=mask[y[inside],x[inside]];assert not(visible&~known).any()
   for case in [0,1]:
    q=a[8,:,:,0]if case==0 else a[16,:,:,0];packet=np.empty((h,w),np.dtype([('visible','u1'),('texel','<i4'),('q','<f4'),('rgba','<f4',(4,))]));packet['visible']=visible;packet['texel']=texel;packet['q']=q;packet['rgba']=a[0];f.write(struct.pack('<ii',frame['frame'],w*h));f.write(string(frame['sourceId']));f.write(packet.tobytes());expected=a[0].copy();k=np.rint(q[visible]*(levels-1)).astype(int);expected[visible,:3]=v[address[y[visible],x[visible]],k];cases.append((frame,case,a,visible,expected))
 run=subprocess.run([str(exe),str(root/'complete-input.bin'),str(root/'complete-output.bin'),'--rgb'],check=True,capture_output=True,text=True);assert 'checks=13'in run.stdout;out=[]
 with(root/'complete-output.bin').open('rb')as f:
  ready,source,missing,count=struct.unpack('<?iii',f.read(13));assert ready and source==int(mask.sum())and missing==0 and count==len(cases)
  for frame,case,a,visible,expected in cases:
   success,has=struct.unpack('<??',f.read(2));reason=read_string(f);assert success and has and reason=='';n=struct.unpack('<i',f.read(4))[0];actual=np.frombuffer(f.read(n*4),'<f4').reshape(expected.shape);assert np.array_equal(actual,expected);assert np.array_equal(actual[~visible],a[0][~visible]);assert np.array_equal(actual[:,:,3],a[0,:,:,3]);out.append(actual.copy())
  assert not f.read()
 board=Image.new('RGB',(1050,len(frames)*200+40),(27,29,35));draw=ImageDraw.Draw(board);rows=[]
 for i,frame in enumerate(frames):
  _,_,a,visible,_=cases[2*i];current,history=out[2*i:2*i+2];ims=[srgb(a[0]),srgb(current),srgb(history)];changes=int(np.count_nonzero((current!=history).any(2)));rows.append({'frame':frame['frame'],'sourceId':frame['sourceId'],'eligibleFaceCells':int(visible.sum()),'allEligibleUseFiniteLUT':True,'sourceAddressUnknown':0,'CSharpAndCPUReferenceExact':True,'outsideCurrentFaceOrAlphaChanges':0,'historyChangesRGBFromSameInput':changes,'nativeFaceUniqueRGB8':len(np.unique(np.array(ims[0])[np.flipud(visible)],axis=0)),'candidateFaceUniqueRGB8':len(np.unique(np.array(ims[2])[np.flipud(visible)],axis=0))})
  for j,(im,title)in enumerate(zip(ims,['Actual native RGB control','CPU88 full LUT/current Q','CPU88 full LUT/actual GPU85 Q history'])):
   draw.text((j*350+3,i*200+3),f"F{frame['frame']} {title}",fill='white');board.paste(im,(j*350+3,i*200+27));board.paste(im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST),(j*350+45,i*200+27))
 draw.text((4,len(frames)*200+8),'CPU preview only. New full-colour GPU not yet executed. Existing58 palette interval unchanged; art not adopted.',fill='white');board.save(G/'CPU_FULL_COLOUR88.png');result={'CSharpCompiled':True,'CPUActualInputFrames':len(frames),'casesPerFrame':2,'currentOwnerAndAlphaPreserved':True,'sourceValueAddressCount':len(p),'unassignedSourceTexels':0,'partialLUTMixedFallback':False,'newGPUColourExecuted':False,'artAdopted':False,'rows':rows};(G/'CPU_FULL_COLOUR88.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
