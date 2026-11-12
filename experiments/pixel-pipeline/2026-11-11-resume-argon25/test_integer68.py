from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from integer_exterior68 import resolve,current_history
from native_contour42 import coordinates
from review_motion64 import srgb
import review_hull60 as api
H=Path(__file__).resolve().parent;G=H/'face68'

def transform(a,k,mirror):return np.rot90(a[:,::-1]if mirror else a,k)

def main():
 G.mkdir(exist_ok=True);tests=0
 n=13;b=np.zeros((n,n,4),np.float32);b[:,:,3]=1;actor=np.zeros((n,n),bool);actor[4:9,4:9]=True;source=actor.copy();z=np.ones((n,n),np.float32)*3;world=np.ones_like(z)*8;meta=np.zeros_like(z);keys=np.zeros((n,n,4),np.float32)
 yy,xx=np.indices((n,n));keys[:,:,0]=1;keys[:,:,1]=1+yy*n+xx;keys[:,:,2]=xx/16;keys[:,:,3]=yy/16;ink=np.array([.1,.02,.03],np.float32)
 out,owner,selected,r=resolve(b,actor,source,z,world,meta,keys,ink,1);assert selected.sum()==24 and not(selected&actor).any();tests+=1
 for mirror in [False,True]:
  for k in range(4):
   a=[transform(v,k,mirror)for v in[b,actor,source,z,world,meta,keys]];o,p,m,_=resolve(*a,ink,1)
   assert np.array_equal(o,transform(out,k,mirror))and np.array_equal(p,transform(owner,k,mirror))and np.array_equal(m,transform(selected,k,mirror));tests+=1
 # Existing history is a source-key tie preference, not an eligibility override.
 history=current_history(owner,selected);zero=np.zeros_like(source);o,p,m,r=resolve(b,actor,zero,z,world,meta,keys,ink,1,history);assert not m.any()and np.array_equal(o,b);tests+=1
 near=np.ones_like(world);o,p,m,r=resolve(b,actor,source,z,near,meta,keys,ink,1,history);assert not m.any()and np.array_equal(o,b);tests+=1
 o,p,m,r=resolve(b,actor,source,z,world,meta,keys,ink,0,history);assert not m.any();tests+=1
 # An occluded nearest neighbour cannot prevent a farther CURRENT admissible
 # source from supplying its own depth. Filter visibility before choosing ties.
 two=np.zeros_like(source);two[6,6]=two[5,6]=True;dz=z.copy();dz[6,6]=5;dw=world.copy();dw[6,7]=3.5
 o,p,m,_=resolve(b,np.zeros_like(actor)|two,two,dz,dw,meta,keys,ink,1);assert m[6,7]and np.array_equal(p[6,7],keys[5,6]);tests+=1
 # Compensated integer source translation preserves the complete band and key.
 a=[np.roll(v,1,axis=1)for v in[b,actor,source,z,world,meta,keys]];o,p,m,_=resolve(*a,ink,1,history);assert np.array_equal(m,np.roll(selected,1,axis=1))and np.array_equal(p,np.roll(owner,1,axis=1));tests+=1
 # A centre-sampled subpixel native line can genuinely supply no current source.
 # No source-key history can recover its geometry. Do not count the integer-band
 # construction above as reproducing that thin native hull or feature motion.
 counts=[int(abs(.5-(phase+.5)%1)<.068/2)for phase in np.arange(8)/8];assert min(counts)==0 and max(counts)==1;tests+=1
 root=H/'face67/motion/capture';api.C=root;r=json.loads((root/'COMPLETE.json').read_text());rows=[];board=Image.new('RGB',(1050,len(r['frames'])*230+70),(27,29,35));draw=ImageDraw.Draw(board)
 for i,f in enumerate(r['frames']):
  read=lambda name:api.plane(r,f,name);w=f['QROI'][2];a=read('atlas40');fields=[a[:,j*w:(j+1)*w]for j in range(16)];proof=read('ownerReceipts47');native_owner=proof[:,:w];source=proof[:,3*w:4*w,0]==4;actor=fields[14][:,:,2]==1;depth=native_owner[:,:,2];keys=np.stack([proof[:,2*w:3*w,1],proof[:,2*w:3*w,3],proof[:,w:2*w,0],proof[:,w:2*w,1]],2);q,_,inside=coordinates(f['QROI'],f['frameInfo']['nativeComposite42']['joinOffset'],f['frameInfo']['nativeComposite42']['nativeOrigin'],f['frameInfo']['nativeComposite42']['deliveredDelta']);source&=inside
  ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);ims=[srgb(np.repeat(np.repeat(fields[9],2,0),2,1))];counts=[]
  for width in [1,2]:
   o,p,m,state=resolve(fields[9],actor,source,depth,fields[13][:,:,0],fields[12][:,:,0],keys,ink,width)
   assert not(m&actor).any()and np.array_equal(o[~m],fields[9][~m])
   counts.append(int(m.sum()));ims.append(srgb(np.repeat(np.repeat(o,2,0),2,1)))
  for col,(im,title)in enumerate(zip(ims,['Actual native baseline','CPU exterior width1','CPU exterior width2'])):
   draw.text((col*350+8,i*230+8),f"F{f['frame']} {title}",fill='white');board.paste(im,(col*350+8,i*230+35));board.paste(im.resize((w*6,im.height*3),Image.Resampling.NEAREST),(col*350+100,i*230+35))
  rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'currentlyVisibleRegisteredFaceSources':int(source.sum()),'integerBandCellsWidth1And2':counts,'actorOverwrite':0,'unknownPacketBorderSkipped':True,'CPUOnly':True})
 draw.text((8,len(rows)*230+8),'CPU diagnostic only. Explicit width1/2 is NOT equality to original subpixel hull or adopted art.',fill='white');draw.text((8,len(rows)*230+30),'Current visible registered face sources only; no whole-character material registration or real GPU history.',fill='white');board.save(G/'CPU_INTEGER_EXTERIOR68.png')
 result={'CPUChecks':tests,'realStoredFrames':rows,'GPUExecuted':False,'adopted':False,'historyOnlyBreaksCurrentGeometryTies':True,'wholeCharacterSourceMapping':False,'subpixelHullEqualityClaimed':False,'pureFractionalFeatureMotionValidated':False,'centreSampledNativeThinStrokePresence8Phases':[int(abs(.5-(p+.5)%1)<.068/2)for p in np.arange(8)/8]};(G/'CPU_INTEGER68.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':main()
