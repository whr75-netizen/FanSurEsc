"""Bounded, portable verification of the one-cell saved-input GPU replay."""
from pathlib import Path
import json, struct, numpy as np
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent

def string(f):
 n=shift=0
 while True:
  b=f.read(1)[0];n|=(b&127)<<shift
  if b<128:break
  shift+=7
  assert shift<35
 return f.read(n).decode('utf-8')

def gpu(path):
 with path.open('rb')as f:
  assert string(f)=='final-palette89-GPU/v1'
  header={'sourceId':string(f),'variant':string(f)}
  frame,serial,w,h=struct.unpack('<4i',f.read(16));header.update(frame=frame,serial=serial,size=[w,h])
  a=np.frombuffer(f.read(),'<f4').reshape(h,w,4).copy()
  assert np.isfinite(a).all()
 return header,a

def rgb8(a):
 a=np.clip(a[...,:3],0,1)
 return np.rint(np.where(a<=.0031308,12.92*a,1.055*np.power(a,1/2.4)-.055)*255).astype(np.uint8)

def main(write=True):
 report=json.loads((HERE/'FOCUS_GPU90.json').read_text());assert report['dispatchComplete'] and report['ownedResourcesReleased']
 assert all(report['unchanged'].values());assert report['before']['RTcount']==report['after']['RTcount']==30
 output=HERE/Path(report['output']).name
 if not output.exists():output=Path(report['output'])
 assert(output/'DISPATCH_COMPLETE90.marker').exists()
 expected=np.load(HERE/'FOCUS_EXPECTED90.npz');headers=[];arrays=[]
 for channel in range(3):
  h,a=gpu(output/f'0140-focused90-{channel}.bin');headers.append(h);arrays.append(a)
 assert all(h==headers[0]for h in headers)
 c,owner,valid=arrays;target=expected['target'];assert target.sum()==4
 assert np.array_equal(c,expected['colour']) and np.array_equal(owner,expected['owner'])
 validExpected=np.zeros_like(valid);validExpected[...,0]=1
 invalid=(owner[...,0]>0)&(owner[...,3]<0);validExpected[invalid]=[0,2,0,0]
 assert np.array_equal(valid,validExpected)
 assert np.array_equal(c[~target],expected['oldColour'][~target])
 assert np.array_equal(c[target],expected['baseline'][target]);assert(rgb8(c[target])==[183,127,113]).all()
 assert np.array_equal(c[...,3],expected['oldColour'][...,3])
 # Every retained candidate remains literal finite LUT; pass-through is the
 # original native image, not an invented palette entry or owner0 assignment.
 selected=owner[...,0]>0
 assert np.array_equal(c[selected],expected['palette'][owner[...,0][selected].astype(int)-1])
 ys,xs=np.where(target);x0,x1=max(0,xs.min()-5),min(c.shape[1],xs.max()+6);y0,y1=max(0,ys.min()-5),min(c.shape[0],ys.max()+6)
 pictures=[('Product77 original source',expected['baseline']),('89 ray-visible (unadopted)',expected['oldColour']),('90 one-cell query fix',c)]
 board=Image.new('RGB',(3*300,370),'#141923');draw=ImageDraw.Draw(board)
 for col,(title,a)in enumerate(pictures):
  im=Image.fromarray(np.flipud(rgb8(a)))
  crop=Image.fromarray(np.flipud(rgb8(a[y0:y1,x0:x1])))
  if write:im.save(HERE/f'focus-{col}-native1x.png');crop.save(HERE/f'focus-{col}-crop1x.png')
  enlarged=crop.resize((crop.width*20,crop.height*20),Image.Resampling.NEAREST);board.paste(enlarged,(col*300+10,65))
  draw.text((col*300+10,10),title,fill='white');board.paste(crop,(col*300+10,35))
  tx0=col*300+10+(xs.min()-x0)*20;ty0=65+(y1-1-ys.max())*20
  draw.rectangle((tx0,ty0,tx0+40-1,ty0+40-1),outline='#00ffff',width=1)
  draw.text((col*300+10,310),'head (226,53); source frame140',fill='white')
  draw.text((col*300+10,330),'#B77F71'if col!=1 else'#FFFFFF',fill='white')
 draw.text((10,354),'One false-white overlay removed. Other89 unresolved cells are unchanged. Product77 stays active.',fill='white')
 if write:board.save(HERE/'FOCUS_COMPARISON90.png')
 metrics={'status':'FOCUSED_GPU_REPLAY_MATCHED_NOT_PRODUCT_INTEGRATED','header':headers[0],'changedNativePixels':int(np.any(c!=expected['oldColour'],axis=-1).sum()),'outsideTargetChanged':int(np.any(c[~target]!=expected['oldColour'][~target],axis=-1).sum()),'oldRGB8':[255,255,255],'newRGB8':[183,127,113],'maxGPUExpectedError':float(abs(c-expected['colour']).max()),'selectedPaletteLookupViolations':0,'originalAlphaChanged':False,'targetOriginalOwnerDepthPassthrough':True,'otherUnresolved89Selections':int(invalid.sum()),'PlayEntries':0,'newCapture':False,'productIntegration':False,'RTbeforeAfter':[report['before']['RTcount'],report['after']['RTcount']],'internalAllocatedBytesDelta':report['after']['allocated']-report['before']['allocated'],'stateUnchanged':report['unchanged']}
 if write:(HERE/'GPU_VALIDATION90.json').write_text(json.dumps(metrics,indent=2)+'\n')
 return metrics
if __name__=='__main__':print(json.dumps(main(),indent=2))
