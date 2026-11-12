"""Reuse58 palettes; join86 support and actual85 Q without partial RGB fallback.

Only exactly constant observed source components receive a colour address.
Nonconstant support remains unassigned. This is a failure-preserving input test,
not a new semantic classifier or a whole-face render.
"""
from pathlib import Path
import json,os,struct,subprocess,hashlib,numpy as np
H=Path(__file__).resolve().parent;G=H/'face87';C=H/'face85/capture'

def string(s):
 b=s.encode();n=len(b);out=bytearray()
 while n>=128:out.append((n&127)|128);n>>=7
 out.append(n);return bytes(out)+b

def read_string(f):
 n=0;shift=0
 while True:
  b=f.read(1)[0];n|=(b&127)<<shift
  if b<128:break
  shift+=7
 return f.read(n).decode()

def main():
 from frame_bytes77 import decode
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True);native=np.load(H/'face28/SOURCE_NATIVE28.npz');part=np.load(H/'face86/REGIONS86.npz');rgb=native['rgba'][:,:,:3];mask=part['mask'];regions=part['regions'];fields=json.loads((H/'face86/COLOUR_FIELDS86.json').read_text());info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());spec=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());settings=spec['settingsFromExisting58'];levels=settings['count'];constant=[x for x in fields if x['exactConstantRGB']];refs=sorted({tuple(x['RGBMin'])for x in constant});ref_id={c:i for i,c in enumerate(refs)};by_region=np.full(int(regions.max())+1,-1,np.int32)
 for x in constant:by_region[x['id']]=ref_id[tuple(x['RGBMin'])]
 address=by_region[regions];key=(rgb[:,:,0].astype(np.int32)<<16)|(rgb[:,:,1].astype(np.int32)<<8)|rgb[:,:,2];palette_input=G/'build/palette-input.bin';palette_input.write_bytes(struct.pack('<ii4d',len(refs),levels,*[settings[k]for k in ['darkLRatio','darkCRatio','gamma','intervalScale']])+np.asarray(refs,'<i4').tobytes());csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';palette_exe=G/'build/palette58.exe'
 candidates=[H.parent/'source-palette58/SourcePalette58.cs',H.parent/'2026-10-31-source-palette58/SourcePalette58.cs'];source58=next(p for p in candidates if p.exists());assert hashlib.sha256(source58.read_bytes()).hexdigest()=='c99c191d3d80f7d84c9b33ad0803d9365c6e66fec96db7668ae6f503f1ad1e4c'
 subprocess.run([str(csc),'/nologo','/optimize+','/target:exe','/out:'+str(palette_exe),str(H/'PaletteTable82.cs'),str(source58)],check=True,capture_output=True);subprocess.run([str(palette_exe),str(palette_input),str(G/'build/palette.rgb')],check=True);p=np.fromfile(G/'build/palette.rgb',np.uint8).reshape(len(refs),levels,3).astype(float)/255;p=np.where(p<=.04045,p/12.92,((p+.055)/1.055)**2.4);rgba=np.ones((len(refs),levels,4),'<f4');rgba[:,:,:3]=p
 exe=G/'build/source87.exe';subprocess.run([str(csc),'/nologo','/optimize+','/target:exe','/out:'+str(exe),str(H/'SourceShade87.cs'),str(H/'SourceShadeTests87.cs')],check=True,capture_output=True)
 contract=info['modelSHA256']+'/'+info['sourceImageSHA256']+'/'+spec['meshUVSHA256']+'/observed-support86/existing-palette58';report=json.loads((C/'COMPLETE.json').read_text());frames=report['stream77']['frames'];tw,th=info['textureSize'];ox,oy=info['cropOffset'];rows=[];input_file=G/'build/actual-input.bin';output_file=G/'build/actual-output.bin'
 with input_file.open('wb')as f:
  f.write(struct.pack('<iii',mask.size,len(refs),levels));f.write(string(contract));record=np.empty(mask.shape,np.dtype([('mask','u1'),('support','<i4'),('key','<i4'),('address','<i4')]));record['mask']=mask;record['support']=regions;record['key']=key;record['address']=address;f.write(record.tobytes());f.write(rgba.tobytes());f.write(struct.pack('<i',len(frames)))
  for frame in frames:
   w,h=frame['QROI'][2:];raw=decode((C/frame['compressedFile']).read_bytes(),frame['bytes']);assert hashlib.sha256(raw).hexdigest()==frame['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,17,w,4).transpose(1,0,2,3);visible=a[12,:,:,3]==1;assert not(visible&(a[16,:,:,3]!=1)).any();uv=a[11,:,:,:2].astype(float);xx=np.floor(uv[:,:,0]*tw).astype(int)-ox;yy=np.floor((1-uv[:,:,1])*th).astype(int)-oy;inside=(xx>=0)&(yy>=0)&(xx<mask.shape[1])&(yy<mask.shape[0]);texel=np.where(inside,yy*mask.shape[1]+xx,-1);supported=np.zeros((h,w),bool);assigned=np.zeros((h,w),bool);supported[inside]=mask[yy[inside],xx[inside]];assigned[inside]=address[yy[inside],xx[inside]]>=0;assert not(visible&~supported).any();packet=np.empty((h,w),np.dtype([('visible','u1'),('texel','<i4'),('q','<f4'),('rgba','<f4',(4,))]));packet['visible']=visible;packet['texel']=texel;packet['q']=a[16,:,:,0];packet['rgba']=a[0];f.write(struct.pack('<ii',frame['frame'],w*h));f.write(string(frame['sourceId']));f.write(packet.tobytes());rows.append({'frame':frame['frame'],'sourceId':frame['sourceId'],'actualVisibleFaceCells':int(visible.sum()),'visibleConfirmedConstantSourceCells':int((visible&assigned).sum()),'visibleUnassignedNonconstantSourceCells':int((visible&~assigned).sum()),'visibleSupportMissingCells':int((visible&~supported).sum())})
 run=subprocess.run([str(exe),str(input_file),str(output_file)],capture_output=True,text=True,check=True);assert 'checks=13'in run.stdout
 with output_file.open('rb')as f:
  ready,source,missing,count=struct.unpack('<?iii',f.read(13));assert not ready and source==int(mask.sum())and missing==int((mask&(address<0)).sum())and count==len(rows)
  for row in rows:
   success,has_output=struct.unpack('<??',f.read(2));reason=read_string(f);assert not success and not has_output and reason=='incomplete-source-colour-contract';row.update({'atomicConsumerAccepted':False,'newRGBOutputCreated':False,'reason':reason})
  assert not f.read()
 result={'CPUCompiledCSharp87':True,'reusedPalette58MathWithoutChanges':True,'syntheticContractChecks':13,'actualGPUInputFrames':len(rows),'newGPUExecution':False,'sourceSupportComponents':len(fields),'exactConstantSupportComponents':len(constant),'constantSourceColourReferences':len(refs),'sourceTexels':source,'unassignedSourceTexels':missing,'unassignedBecauseFixtureUsesOnlyWholeConstantComponents':True,'nativeColourOrUVDataMissing':False,'semanticImpossibilityProven':False,'allInputCurrentOwnerAndQMatchCurrentSourceId':True,'partialLUTPlusOriginalMixPrevented':True,'completeFaceColourOrArtClaimed':False,'product77Changed':False,'rows':rows};(G/'SOURCE_SHADE87.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':
 import sys
 if '--output-root'in sys.argv:G=Path(sys.argv[sys.argv.index('--output-root')+1]).resolve()
 main()
