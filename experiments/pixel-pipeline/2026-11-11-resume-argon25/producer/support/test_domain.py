"""Check support coverage against actual allocations and grid-boundary cases."""
from pathlib import Path
import json,math,sys
import numpy as np
H=Path(__file__).resolve().parent;PRE=H.parent;R=PRE.parents[1]
sys.path.insert(0,str(R/'argon23-runtime113'));from inputs113 import buffer

def rect(original,o,size):
 x,y=[math.ceil(v-.5)for v in o];cw,ch=[v//4 for v in size]
 x0=max(0,min(original[0],x));y0=max(0,min(original[1],y))
 x1=min(480,max(original[0]+original[2],x+cw));y1=min(272,max(original[1]+original[3],y+ch))
 if x1<=x0 or y1<=y0 or (x1-x0)*(y1-y0)>512:raise ValueError('budget')
 return [x0,y0,x1-x0,y1-y0]

def main():
 s=json.loads((PRE/'phase-run/STATE113-0008-finished.json').read_text());rows=[];checks=0
 for packet in s['sequencePackets']:
  p=Path(packet['output']);m=json.loads((p/'RAW_MANIFEST.json').read_text());o=np.array(m['forward102']['headHair25']['origin']);size=m['forward102']['canonicalSize'];cw,ch=np.array(size)//4
  ids=buffer(p/'curve-identity.f32').reshape(ch,cw,4);old=m['grid102']['eyeTopLeftROI'];new=rect(old,o,size);missBefore=[]
  for cy,cx in np.argwhere(ids[...,0]>0):
   j=np.ceil(o+np.array([cx,cy])-.5).astype(int)
   assert np.array_equal(np.floor(j+.5-o),[cx,cy]);checks+=1
   assert new[0]<=j[0]<new[0]+new[2] and new[1]<=j[1]<new[1]+new[3]
   if not(old[0]<=j[0]<old[0]+old[2]and old[1]<=j[1]<old[1]+old[3]):missBefore.append([int(cx),int(cy)])
  rows.append({'sourceId':m['sourceId'],'oldROI':old,'newCandidateROI':new,'previouslyClipped':missBefore,'newClipped':0,
   'assignedQueryThreads':new[2]*new[3]*16,'physicalHairFinePixels':new[2]*new[3]*16})
 for phase in [0,.125,.25,.375,.5,.625,.75,.875,1,np.nextafter(.5,0),np.nextafter(.5,1)]:
  o=np.array([211+phase,48+phase]);r=rect([212,48,16,8],o,[72,32])
  for y in range(8):
   for x in range(18):
    j=np.ceil(o+[x,y]-.5).astype(int);assert np.array_equal(np.floor(j+.5-o),[x,y]);checks+=1
    assert r[0]<=j[0]<r[0]+r[2]and r[1]<=j[1]<r[1]+r[3]
 try:rect([0,0,480,272],[0,0],[72,32]);raise AssertionError('oversized domain accepted')
 except ValueError:pass
 out={'actualInputRows':rows,'supportGridInvariants':checks,'newClippedSourceCells':0,'oversizedOutputRejected':True,
  'GPUOrUnityCalls':0,'CSharpCompiledNotExecuted':True,'sourceAllocationChanged':False,'productROIMutated':False}
 (H/'CPU_DOMAIN26.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
if __name__=='__main__':main()
