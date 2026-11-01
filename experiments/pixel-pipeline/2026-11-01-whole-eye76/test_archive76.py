"""Portable CPU replay of actual final GPU packet; no Unity or absolute paths."""
from pathlib import Path
import json,numpy as np
from test76 import supported
R=Path(__file__).resolve().parent
def main():
 z=np.load(R/'fixture76.npz');meta=json.loads((R/'FIXTURE76.json').read_text());bank={tuple(v['xy']):v for v in json.loads((R/'BANK76.json').read_text())['cells']};checks=0
 for info in meta['frames']:
  pre=info['prefix'];b=z[pre+'baseline'];rec=z[pre+'records'];c=z[pre+'counts'];orig=z[pre+'original'];x,y,w,h=info['roi'];rx,ry,rw,rh=info['eyeROI'];pred=np.zeros((rh,rw),bool)
  for yy in range(rh):
   for xx in range(rw):
    sy,sx=yy+ry-y,xx+rx-x;v=b[sy,sx];sm=[z[pre+f'S{i}-meta'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(7)];pt=[z[pre+f'S{i}-point'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(4)];ok,sid,weight=supported(v[0],v[1],v[4],sm,pt,z[pre+'old-eye-owner'][sy,sx]);pred[yy,xx]=ok
    if not ok:continue
    a=rec[yy,xx];assert np.array_equal(a[0],v[0]);assert round(float(a[3,1]))==sid and abs(a[3,2]-weight)<2e-5;checks+=1
    if a[7,3]==1:
     colour=a[0,:3];rgb=np.rint(np.clip(np.where(colour<=.0031308,colour*12.92,1.055*np.maximum(colour,0)**(1/2.4)-.055),0,1)*255).astype(np.uint8);cell=bank[tuple(np.rint(a[7,:2]).astype(int))];assert cell['eye']==sid and cell['role']==round(float(a[7,2]));assert rgb.tolist()==cell['rgba8'][:3]
  assert np.array_equal(pred,rec[...,14,2]>.5);allowed=np.zeros((rh,rw),bool);old=orig[ry-y:ry-y+rh,rx-x:rx-x+rw]
  for eye,sid in enumerate([int(v[3])for v in info['centres']]):
   flags=c[eye,...,10]>.5;assert np.array_equal(flags,pred&(np.rint(rec[...,1,0])==7)&(np.rint(rec[...,3,1])==sid))
   if flags.any():allowed|=(np.rint(old[...,3,1])==sid)&np.isin(np.rint(old[...,3,0]),[5,7])&~pred
  assert np.array_equal(old[...,0,:][~pred&~allowed],rec[...,0,:][~pred&~allowed]);assert not(np.isin(np.rint(rec[...,3,0]),[5,7])&allowed).any()
 assert all((i%4,i//4)==(i&3,i>>2)for i in range(16));print(json.dumps({'actualFrames':len(meta['frames']),'protectedGPUCellChecks':checks,'validSampleIndexPairs':16,'unaffectedRGBError':0,'status':'PASS; no motion/blink/artistic completion claim'}))
if __name__=='__main__':main()
