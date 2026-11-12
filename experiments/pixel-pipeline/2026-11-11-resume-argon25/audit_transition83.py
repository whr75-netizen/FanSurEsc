"""Attribute final curve transitions to observed source, target or depth gates."""
from pathlib import Path
import json,numpy as np
from frame_bytes77 import decode
H=Path(__file__).resolve().parent;G=H/'face83/fix1';C=G/'capture'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());frames=r['stream77']['frames'];previous=None;rows=[]
 for f in frames:
  w,h=f['QROI'][2:];a=np.frombuffer(decode((C/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(h,23,w,4).transpose(1,0,2,3);before,meta,world,cell,owner=a[:5];colour,proof,projection=a[8:11];receipt=a[14];current={}
  for y,x in np.argwhere((colour[:,:,3]==1)|(receipt[:,:,3]==1)):
   q=(int(x+f['QROI'][0]+f['join'][0]),int(y+272-f['QROI'][1]-h+f['join'][1]));current[q]={'sourceVisible':bool(colour[y,x,3]==1),'sourceEdge':float(proof[y,x,1]),'sourceT':float(proof[y,x,2]),'sourceDepth':float(proof[y,x,0]),'destinationDepthWithOffset':float(np.float32(proof[y,x,0]+f['depthOffset'])),'depthAllowed':bool(receipt[y,x,1]==1),'targetEmpty':bool(receipt[y,x,2]==1),'finalUsed':bool(receipt[y,x,3]==1),'actorCell':cell[y,x].tolist(),'actorOwner':owner[y,x].tolist(),'worldDepth':float(world[y,x,0]),'styleDepth':float(meta[y,x,0])}
  if previous is not None:
   old,oldf=previous;trans=[]
   for q in sorted(set(old)|set(current)):
    p=old.get(q);n=current.get(q)
    if bool(p and p['finalUsed'])==bool(n and n['finalUsed']):continue
    trans.append({'destinationGlobalXY':q,'before':p,'after':n,'sourceCoverageChanged':bool(p and p['sourceVisible'])!=bool(n and n['sourceVisible']),'sameVisibleSourceEdge':bool(p and n and p['sourceEdge']==n['sourceEdge']),'targetOccupancyChanged':bool(p and p['targetEmpty'])!=bool(n and n['targetEmpty']),'depthGateChanged':bool(p and p['depthAllowed'])!=bool(n and n['depthAllowed'])})
   rows.append({'fromFrame':oldf['frame'],'toFrame':f['frame'],'sameSnappedAnchor':oldf['curve81']['snappedHeadAnchor']==f['curve81']['snappedHeadAnchor'],'bothWalk':oldf['motion']['stage']==f['motion']['stage']=='walk','transitions':trans})
  previous=(current,f)
 result={'actualConsecutiveFrames':len(frames),'CPUOnlyAttributionOfActualGPU':True,'historyCanOverrideCurrentOcclusion':False,'rows':rows};(G/'TRANSITIONS83.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
