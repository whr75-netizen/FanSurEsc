"""Actual hull/forced-line/source-width comparison. No new rendering or guessed regions."""
from pathlib import Path
import json,struct,numpy as np
from PIL import Image,ImageDraw
from native_contour42 import coordinates
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face60';C=G/'capture'
def plane(report,frame,name):
 ps=[p for p in report['planes']if p['sourceId']==frame['sourceId']and p['frame']==frame['frame']and p['name']==name];assert ps
 a=np.full((ps[0]['height'],ps[0]['width'],4),np.nan,np.float32);seen=np.zeros(a.shape[:2],bool)
 for p in ps:
  v=np.fromfile(C/p['file'],dtype='<f4');assert v.nbytes==p['bytes']and v.nbytes<=262144;y=p['bottomRow'];n=p['rows'];assert not seen[y:y+n].any();a[y:y+n]=v.reshape(n,p['width'],4);seen[y:y+n]=True
 assert seen.all()and np.isfinite(a).all();return a
def oracle_hull(line,proof,before,meta,world,cell,inside,q,offset,ink,triangles,uv_bounds=True):
 depth=np.float32(proof[:,:,0]+np.float32(offset));finite=np.isfinite(depth)
 for value in[line,proof,meta,world,cell]:finite&=np.isfinite(value).all(2)
 valid=inside&finite&(cell[:,:,:2]==q).all(2)
 uv_valid=((proof[:,:,1:3]>=0).all(2)&(proof[:,:,1:3]<=1).all(2))if uv_bounds else np.ones(inside.shape,bool)
 source=(line[:,:,3]==1)&(line[:,:,:3]==ink).all(2)&(proof[:,:,0]>0)&uv_valid&(proof[:,:,3]>=1)&(proof[:,:,3]==np.rint(proof[:,:,3]))&(proof[:,:,3]<=triangles)
 style=valid&((meta[:,:,0]<=0)|(depth<=np.float32(meta[:,:,0]+np.float32(.0001))));visible=valid&(world[:,:,0]>0)&(depth<=np.float32(world[:,:,0]+np.float32(.0001)));use=source&style&visible;out=before.copy();out[use,:3]=ink;out[use,3]=1
 gate=np.stack([source,style,visible,np.where(valid,use,-1)],2).astype(np.float32);return out,gate
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']and r['pendingOwners']==0 and len(r['frames'])==1
 f=r['frames'][0];x,y,w,h=f['QROI'];read=lambda n:plane(r,f,n);a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];line,proof=read('nativeLogicalHull60'),read('nativeLogicalHullProof60');info=f['frameInfo']['nativeComposite42'];ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);triangles=f['frameInfo']['sourceCarrier48']['triangleCount']
 expected,gate=oracle_hull(line,proof,fields[9],fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,triangles);assert expected.tobytes()==fields[10].tobytes()and gate.tobytes()==fields[11].tobytes();before,after=read('nativeBefore42'),read('nativeAfter42');assert np.array_equal(before,np.repeat(np.repeat(fields[9],2,0),2,1))and np.array_equal(after,np.repeat(np.repeat(expected,2,0),2,1))
 source=gate[:,:,0]==1;use=gate[:,:,3]==1;forced=fields[3][:,:,3]==1
 assert np.all(fields[15][use,0]==6)and np.array_equal(fields[15][use,1],proof[use,3])and np.array_equal(fields[15][use,2:],proof[use,1:3])
 fine=read('nativeOutlineOn58');off=read('nativeOutlineOff58');fineMask=(fine[:,:,3]>0)&(fine[:,:,:3]==ink).all(2);fineOffMask=(off[:,:,3]>0)&(off[:,:,:3]==ink).all(2)
 rx,ry,rw,rh=r['ROI'];assert fine.shape==(rh*8,rw*8,4);counts=fineMask.reshape(rh,8,rw,8).sum((1,3));support=np.zeros((h,w),np.float64);ox=rx-x;oy=(272-ry-rh)-(272-y-h);support[oy:oy+rh,ox:ox+rw]=counts/64
 rawQ,metaQ=read('initialAppliedQ58'),read('initialSurfaceMeta58');face=(metaQ[:,:,1]==4)&(metaQ[:,:,3]==1);steps=f['frameInfo']['faceSteps'];k=np.rint(rawQ[:,:,0]*(steps-1)).astype(int);qExpected=np.float32(k.astype(np.float32)/np.float32(steps-1));qMismatch=face&(rawQ[:,:,0]!=qExpected)
 geo=geometry(C/f"geometry-frame{f['frame']}.bin");assert geo['sourceId']==f['sourceId'];worldPixel=f['frameInfo']['worldPixel'];width=f['frameInfo']['nativeOutlineWidthMetres39'];bound=width/worldPixel
 row={'actualSourceId':f['sourceId'],'frame':f['frame'],'actualGPUCapture':True,'CPUGPUCompositeByteExact':True,'actualNativeBeforeAfterByteExact':True,'forcedMinimumCurveCells':int(forced.sum()),'authoredLogicalHullCells':int(source.sum()),'finalSelectedHullCells':int(use.sum()),'originalSourceFineCoveredSamples8x':int(fineMask.sum()),'originalSourceFineHairOffSamples8x':int(fineOffMask.sum()),'fineCoveredCellCount':int((support>0).sum()),'fineEstimatedAreaInLogicalCells':float(support.sum()),'forcedCurveCellsWithNo8xSample':int((forced&(support==0)).sum()),'eightTimesSamplingIsNotExactFootprintProof':True,'sourceWidthMetres':width,'worldMetresPerLogicalCell':worldPixel,'unitNormalWidthUpperBoundCells':bound,'minimumPixelWidthNoLongerForced':True,'selectedInkComparedPixels':int(use.sum()),'selectedInkMismatch':int((expected[use,:3]!=ink).any(1).sum()),'unselectedNativeRGBChanged':int((expected[~use]!=fields[9][~use]).any(1).sum()),'nativeHullOwnerKind6Declared':True,'nativeHullOwnerPositiveSamples':int(use.sum()),'nativeHullOwnerPositiveValidation':bool(use.any()),'styleRejected':int((source&(gate[:,:,1]==0)).sum()),'worldRejected':int((source&(gate[:,:,2]==0)).sum()),'observedInitialFaceQCells':int(face.sum()),'initialFaceQNotExactKOverN':int(qMismatch.sum()),'facePaletteRegionsConfirmed':0,'appliedQPrimeStageObserved':False,'initialQIsNotFinalQPrime':True,'product77Changed':False,'runtimeHistoryFeedback':False,'temporalStabilityValidated':False,'fullFacePaletteComplete':False}
 (G/'analysis').mkdir(exist_ok=True);(G/'analysis/ACTUAL_HULL60.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
 def image(v):
  z=np.clip(v[::-1,:,:3],0,1);z=np.where(z<=.0031308,12.92*z,1.055*np.power(z,1/2.4)-.055);return Image.fromarray(np.uint8(np.rint(z*255)))
 board=Image.new('RGB',(1080,360),(28,30,35));draw=ImageDraw.Draw(board)
 # Reference remains same-frame: overlay the captured forced minimum on the
 # actual native baseline on CPU. Explicitly label it CPU, never a GPU result.
 reference=fields[9].copy();reference[forced,:3]=ink;reference[forced,3]=1
 for i,(title,z)in enumerate([('Actual Native395',before),('CPU forced-minimum reference',np.repeat(np.repeat(reference,2,0),2,1)),('Actual GPU authored-width candidate',after)]):
  im=image(z);draw.text((i*360+8,10),title,fill='white');board.paste(im,(i*360+8,38));board.paste(im.resize((224,224),Image.Resampling.NEAREST),(i*360+100,38))
 draw.text((8,285),f"Same source frame {f['frame']}; forced curve {forced.sum()} cells -> native logical hull {source.sum()} -> visible {use.sum()}.",fill='white')
 draw.text((8,307),'Width/colour from current original material. No RGB shading multiply, colour average, or forced1px width.',fill='white')
 draw.text((8,330),'Single-frame diagnostic. Full-face palette, temporal/history and art approval remain incomplete.',fill='white');board.save(G/'FACE_AUTHORED_WIDTH60.png');print(json.dumps(row))
if __name__=='__main__':main()
