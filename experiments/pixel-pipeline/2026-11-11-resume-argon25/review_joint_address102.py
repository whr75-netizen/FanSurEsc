"""CPU counterfactual on exact actual960 UV/Q/owner inputs, not a GPU render."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from compare_range99 import stats
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face102'

def main():
 root=H/'face99/long960';r=json.loads((root/'capture/COMPLETE.json').read_text());candidate=np.load(G/'JOINT_ADDRESS102.npz');labels=candidate['sourceLabels'];base=np.load(H/'face92/SOURCE_VALUE92.npz');region=np.load(H/'face86/REGIONS86.npz')['regions'];info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=info['cropOffset'];tw,th=info['textureSize'];original=np.fromfile(H/'face99/original99/details/ORIGINAL99.rgba',np.uint8).reshape(th,tw,4);palette=np.fromfile(root/'capture/RUNTIME_PALETTE89.rgb',np.uint8).reshape(-1,3,3);previous=None;pairs=[];boundaries=np.zeros((2,2),np.int64);samples=changes=0;pictures=[]
 for f in r['stream77']['frames']:
  a,_,_=packet(root,f);uv=a[1,:,:,:2];sx=np.floor(uv[:,:,0]*np.float32(tw)).astype(int)%tw;sy=np.floor(uv[:,:,1]*np.float32(th)).astype(int)%th;tx=sx-ox;ty=th-1-sy-oy;valid=(a[4,:,:,3]==1)&(a[4,:,:,0]>0);assert ((tx[valid]>=0)&(ty[valid]>=0)&(tx[valid]<labels.shape[1])&(ty[valid]<labels.shape[0])).all();newfam=np.zeros(valid.shape,int);newfam[valid]=labels[ty[valid],tx[valid]];oldfam=a[4,:,:,0].astype(int)-1;q=a[4,:,:,2].astype(int);old=np.flipud(np.asarray(srgb(a[5])))[:,:,:3].astype(int);assert np.array_equal(old[valid],palette[oldfam[valid],q[valid]]);new=old.copy();new[valid]=palette[newfam[valid],q[valid]];source=original[sy,sx,:3].astype(int);reg=np.zeros(valid.shape,int);reg[valid]=region[ty[valid],tx[valid]];samples+=int(valid.sum());changes+=int((valid&(new!=old).any(2)).sum());boundaries[0]+=stats(old,valid);boundaries[1]+=stats(new,valid)
  if previous is not None:
   before,oldSource,oldRGB,newRGB,wasValid,oldReg=previous;mask=valid&wasValid&(reg==oldReg)&(reg>0)&(a[0,:,:,1]==before[0,:,:,1])&(a[0,:,:,3]==before[0,:,:,3])&(a[4,:,:,2]==before[4,:,:,2])
   for y,x in np.argwhere(mask):pairs.append({'frame':f['frame'],'xy':[int(x),int(y)],'sourceStep':(source[y,x]-oldSource[y,x]).tolist(),'baselineStep':(old[y,x]-oldRGB[y,x]).tolist(),'candidateStep':(new[y,x]-newRGB[y,x]).tolist()})
  previous=a,source,old,new,valid,reg
  if f['frame']in[102,149,585]:
   board=Image.new('RGB',(780,286),'#20252c');d=ImageDraw.Draw(board);d.text((8,6),f"Frame {f['frame']} actual UV/Q; right panel CPU102 prediction, NOT GPU render",fill='white');view=np.flipud(np.asarray(srgb(a[7])))[:,:,:3];target=view.copy();direct=valid&(a[7]==a[5]).all(2);target[direct]=new[direct]
   for i,(im,title)in enumerate([(srgb(a[11]),'Actual native'),(srgb(a[7]),'Actual98B + CPU99C'),(Image.fromarray(np.flipud(target)),'CPU102 prediction')]):
    board.paste(im,(8+258*i,30));board.paste(im.resize((208,208),Image.Resampling.NEAREST),(8+258*i,64));d.text((42+258*i,34),title,fill='white')
   pictures.append(board)
 sourceNorm=np.array([np.linalg.norm(p['sourceStep'])for p in pairs]);oldNorm=np.array([np.linalg.norm(p['baselineStep'])for p in pairs]);newNorm=np.array([np.linalg.norm(p['candidateStep'])for p in pairs]);oldGain=np.divide(oldNorm,sourceNorm,out=np.zeros_like(oldNorm),where=sourceNorm>0);newGain=np.divide(newNorm,sourceNorm,out=np.zeros_like(newNorm),where=sourceNorm>0);examples=[dict(p,baselineGain=float(a),candidateGain=float(b))for p,a,b in zip(pairs,oldGain,newGain)];examples.sort(key=lambda p:-p['baselineGain']);out={'CPUCounterfactualNotGPURender':True,'actualSourceFrames':len(r['stream77']['frames']),'sameActualUVAndSelectedQ':True,'colourSamples':samples,'changedColourSamples':changes,'comparedAdjacentSamePrimitiveRegionQPairs':len(pairs),'RGBChangingPairsBeforeAfter':[int((oldNorm>0).sum()),int((newNorm>0).sum())],'maximumPointStepGainBeforeAfter':[float(oldGain.max()),float(newGain.max())],'improvedStepPairs':int((newNorm<oldNorm).sum()),'worsenedStepPairs':int((newNorm>oldNorm).sum()),'equalRGBBoundaryEdgesBeforeAfter':boundaries[:,0].tolist(),'singletonPixelsBeforeAfter':boundaries[:,1].tolist(),'largestOldStepExamples':examples[:12],'sameSurfaceFootprintNotProvenByAdjacentCell':True,'GPUOrArtAdopted':False};(G/'ACTUAL_INPUT_COUNTERFACTUAL102.json').write_text(json.dumps(out,indent=2));sheet=Image.new('RGB',(780,286*len(pictures)),'#20252c')
 for i,p in enumerate(pictures):sheet.paste(p,(0,286*i))
 sheet.save(G/'COUNTERFACTUAL102.png');native=np.load(H/'face28/SOURCE_NATIVE28.npz')['rgba'][:,:,:3];mask=base['mask'];oldSource=native.copy();newSource=native.copy();oldSource[mask]=base['colours'][base['referenceIndices'][base['labels'][mask]]];newSource[mask]=base['colours'][base['referenceIndices'][labels[mask]]];board=Image.new('RGB',(1260,420),'#20252c');d=ImageDraw.Draw(board)
 for i,(im,title)in enumerate([(native,'Original RGB'),(oldSource,'Original226 source references'),(newSource,'CPU102 same226 source references')]):board.paste(Image.fromarray(im[620:740,300:440]).resize((420,360),Image.Resampling.NEAREST),(i*420,32));d.text((i*420+5,8),title,fill='white')
 d.text((8,394),'Source reference view, NOT shaded GPU output. Mask/RGBA and detected component IDs unchanged.',fill='white');board.save(G/'SOURCE_WEAK102.png');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
