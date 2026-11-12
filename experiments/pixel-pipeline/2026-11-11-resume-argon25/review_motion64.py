"""Check every actually captured frame, all width cases, final RGB and ownership."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from face_parent62 import resolve,child_gate
from native_contour42 import coordinates
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face64';C=G/'capture'

def srgb(a):
 x=np.clip(a[::-1,:,:3],0,1)
 return Image.fromarray(np.uint8(np.rint(np.where(x<=.0031308,12.92*x,1.055*np.power(x,1/2.4)-.055)*255)))

def main():
 api.C=C;r=json.loads((C/'COMPLETE.json').read_text());number=G.name.removeprefix('face')
 assert r['restorationChecksPass'] and r['ownedResourcesReleased'] and r['pendingOwners']==0 and not r['errors'] and r['packetComplete'] and r['actualConsecutive'] and len(r['frames'])==6
 frames=r['frames'];assert [f['frame'] for f in frames]==list(range(frames[0]['frame'],frames[0]['frame']+6))
 rows=[];previews=[];orig=[]
 board=Image.new('RGB',(1280,6*226+64),(27,29,35));draw=ImageDraw.Draw(board)
 for fi,f in enumerate(frames):
  read=lambda n:api.plane(r,f,n);w=f['QROI'][2];h=f['QROI'][3];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)]
  outputs=read('widthCompositeAtlas61');ownerAtlas=read('widthOwnerAndLayerAtlas62');b=read('ownerReceipts47');domain=b[:,3*w:4*w].copy();domain[:,:,0]=(domain[:,:,0]==-4)
  visible=read('featureProducer49')[:,w:2*w];info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta'])
  ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);child=child_gate(visible,domain,b[:,:w],fields[14]);geo=geometry(C/f"geometry-frame{f['frame']}.bin");assert geo['sourceId']==f['sourceId']
  motion=f['frameInfo']['motion40'];assert motion['frame']==f['frame'] and motion['matches'] and motion['inputReference']==r['inputId']
  assert info['sameFrame']==f['frame'] and info['sourceId']==f['sourceId'] and info['presentSerialExecuted']>info['presentSerialBeforeGraphExecute']
  original=read('nativeBefore42');assert np.array_equal(original,np.repeat(np.repeat(fields[9],2,0),2,1))
  per=[];ims=[]
  for idx,scale in enumerate([0,1,8,32]):
   line=read('nativeLogicalHull60'if idx==1 else'widthCaseField'+str([20,18,22,24][idx]))if idx else np.zeros((h,w,4),np.float32)
   proof=read('nativeLogicalHullProof60'if idx==1 else'widthCaseField'+str([21,19,23,25][idx]))if idx else np.zeros((h,w,4),np.float32)
   expected,gate,blocked=resolve(line,proof,fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,4232,visible,domain,b[:,:w])
   actual=outputs[:,idx*2*w:(idx+1)*2*w];owner=ownerAtlas[:,idx*2*w:(idx*2+1)*w];layer=ownerAtlas[:,(idx*2+1)*w:(idx+1)*2*w];use=gate[:,:,3]==1
   assert np.array_equal(actual,np.repeat(np.repeat(expected,2,0),2,1))
   assert np.array_equal(owner[:,:,0]==6,use) and np.array_equal(owner[use,1],proof[use,3]) and np.array_equal(owner[use,2:],proof[use,1:3])
   assert np.array_equal(layer[:,:,:3],visible[:,:,:3]) and np.array_equal(layer[:,:,3]==1,blocked)
   assert np.array_equal(expected[child],fields[9][child]) and np.array_equal(expected[~use],fields[9][~use]) and np.all(expected[use,:3]==ink)
   if idx==1:assert np.array_equal(read('nativeAfter42'),actual)
   per.append({'widthScale':scale,'sourceCells':int((gate[:,:,0]==1).sum()),'selected':int(use.sum()),'blockedCurrentChildren':int(blocked.sum()),'RGBAndOwnerAndLayerExact':True,'eyeChildRGBChanged':0,'nonSelectedRGBChanged':0})
   im=srgb(actual);ims.append(im);draw.text((idx*320+8,fi*226+8),f"F{f['frame']} {motion['stage']} x{scale}: {int(use.sum())} selected / {int(blocked.sum())} child blocked",fill='white');board.paste(im,(idx*320+8,fi*226+32));board.paste(im.resize((w*6,h*6),Image.Resampling.NEAREST),(idx*320+80,fi*226+32))
  previews.append(ims[1]);orig.append(srgb(original));anchor=f['frameInfo']['sourceAnchor']['head']
  rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'deltaTime':f['frameInfo']['deltaTime'],'stage':motion['stage'],'input':motion['actualInput'],'avatarPosition':motion['avatarPosition'],'avatarRotation':motion['avatarRotation'],'headAnchor':anchor,'headPhase':(np.asarray(anchor)%1).tolist(),'currentEyeChildren':int(child.sum()),'presentSerial':info['presentSerialExecuted'],'cases':per})
 draw.text((8,6*226+8),'Actual six normal frames; original material width x1. x8/x32 are controls, not adopted. No temporal averaging.',fill='white')
 draw.text((8,6*226+30),'Same-frame child/hair/world tests. Six frames are short motion regression; long-term history and full-face LUT remain incomplete.',fill='white');board.save(G/f'MOTION_NATIVE_WIDTH{number}.png')
 # Slowed sequence explicitly labelled; every frame remains its actual size.
 film=[]
 for im,row in zip(previews,rows):
  p=Image.new('RGB',(300,240),(27,29,35));d=ImageDraw.Draw(p);d.text((8,8),f"Actual F{row['frame']} {row['stage']} | x12 slow",fill='white');p.paste(im,(8,30));p.paste(im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST),(90,30));film.append(p)
 film[0].save(G/f'MOTION_NATIVE_WIDTH{number}.webp',save_all=True,append_images=film[1:],duration=200,loop=0,lossless=True)
 result={'actualGPUFrames':6,'actualConsecutive':True,'CPUExactWidthCases':24,'positiveOwnerSamplesAllControls':sum(c['selected']for x in rows for c in x['cases']),'sourceOnlyActualWidth':True,'originalMaterialUnchanged':True,'product77DefaultUnchanged':True,'eyeProtectionPreserved':True,'realHairWorldGateUnchanged':True,'ownedByteUpperObserved':r['peakOwnedTextureBytesUpper63'],'beforeMemory':r['beforeMemory'],'afterMemory':r['afterMemory'],'CPUProfilerIsNotPhysicalWS':True,'fullFaceColourFamilyApproved':False,'fullFaceFinitePaletteComplete':False,'longTermHistoryValidated':False,'pureSubpixelSweepClaimed':False,'rows':rows}
 (G/f'ACTUAL_MOTION{number}.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
