"""CPU counterfactual only: same captured current inputs, history disabled.

Actual GPU results stay immutable. This is not a second GPU A/B capture, nor a
whole-feature silhouette cache. Count owner ties separately from visible RGB.
"""
from pathlib import Path
import json,numpy as np
from frame_bytes77 import decode
from variable_exterior72 import resolve
H=Path(__file__).resolve().parent;G=H/'face77/long';C=G/'capture'

def main():
 report=json.loads((C/'COMPLETE.json').read_text());frames=report['stream77']['frames'];table=json.loads((C/'SOURCE_TABLE77.json').read_text());enabled=np.zeros(16,bool);maximum=np.zeros(16,int);inks=np.zeros((16,3),np.float32)
 for r in table:enabled[r['role']]=r['sourceEnabled'];maximum[r['role']]=r['triangles'];inks[r['role']]=r['sourceInkLinear']
 z=report['sourcePalette67']['zeroWidth69'];zero=np.fromfile(H/'face69/ZERO_TRIANGLES69.r8',np.uint8);rows=[]
 for f in frames:
  w,h=f['QROI'][2:];data=np.frombuffer(decode((C/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(h,w*13,4);p=[data[:,i*w:(i+1)*w]for i in range(13)];before,after,key,meta,world,cell,owner,uv,source,trace,receipt,domain,scalar=p
  actor=cell[:,:,2]==1
  if not actor.any():continue
  yy,xx=np.indices((h,w));origin=np.array([f['QROI'][0]+f['join'][0],272-f['QROI'][1]-h+f['join'][1]]);valid=(cell[:,:,:2]==np.stack([xx+origin[0],yy+origin[1]],2)).all(2);roles=np.rint(owner[:,:,0]).astype(int);ix=np.clip(roles,0,15)
  eligible=valid&actor&(domain[:,:,0]<.5)&(roles>0)&(roles<16)&(owner[:,:,0]==roles)&(source[:,:,0]==owner[:,:,2])&(source[:,:,1]==owner[:,:,0])&(source[:,:,2]==owner[:,:,1])&(source[:,:,3]>=1)&(source[:,:,3]==np.rint(source[:,:,3]))&(source[:,:,3]<=maximum[ix])&enabled[ix]&(scalar[:,:,2]==1)
  tri=np.clip(np.rint(source[:,:,3]).astype(int)-1,0,z['triangles']-1);eligible&=~((roles==z['role'])&(zero[tri]>0));keys=np.stack([owner[:,:,0],source[:,:,3],uv[:,:,0],uv[:,:,1]],2);radius=np.rint(scalar[:,:,1]).astype(int)
  rgb,own,mask,rad=resolve(before,actor,eligible,owner[:,:,2],np.where(valid,world[:,:,0],0),meta[:,:,0],keys,inks[ix],radius)
  core=np.zeros((h,w),bool);core[2:-2,2:-2]=True;actual=key[:,:,0]>=100;assert np.array_equal(actual[core],mask[core]);candidate=own.copy();candidate[mask,0]+=100
  changed=core&mask&(candidate!=key).any(2);rgb_changed=core&mask&(rgb!=after).any(2);assert not np.any(rgb_changed&~changed)
  rows.append({'frame':f['frame'],'actualGPUHistoryMatched':int((trace[:,:,3]==1).sum()),'sameInputCPUWithoutHistoryDifferentOwner':int(changed.sum()),'sameInputCPUWithoutHistoryDifferentRGB':int(rgb_changed.sum()),'coreCoordinatesXY':np.argwhere(changed)[:,::-1].tolist()})
  if len(rows)%20==0:print(json.dumps({'counterfactualFrames':len(rows)}),flush=True)
 result={'actualSourceFrames':len(rows),'GPUCounterfactualExecuted':False,'comparison':'immutable actual GPU history output versus CPU no-history selection from identical captured current buffers','ownerDifferences':sum(r['sameInputCPUWithoutHistoryDifferentOwner']for r in rows),'RGBDifferences':sum(r['sameInputCPUWithoutHistoryDifferentRGB']for r in rows),'shapeStabilityOrArtImprovementProven':False,'rows':rows};(G/'HISTORY_COUNTERFACTUAL77.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
