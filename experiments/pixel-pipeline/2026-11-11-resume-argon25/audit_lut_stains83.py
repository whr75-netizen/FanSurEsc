"""Distinguish source colour partition, light-Q edges, and partial-LUT seams.

Immutable actual77 input, CPU candidate82 only. Exact same address is the test;
there is no chosen colour-distance threshold and no proposed Q smoothing.
"""
from pathlib import Path
import json,numpy as np
from frame_bytes77 import decode
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face82'
def main():
 d=np.load(G/'SOURCE_FIELD82.npz');labels=d['labels'];info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=info['cropOffset'];tw,th=info['textureSize'];r=json.loads((H/'face77/loop120/capture/COMPLETE.json').read_text());levels=r['sourcePalette67']['levels'];palette=np.fromfile(G/'PALETTE82.rgb',np.uint8).reshape(-1,levels,3);rows=[]
 for i,f in enumerate(r['stream77']['frames']):
  if i not in [0,20,40,60,80,100,119]:continue
  w,h=f['QROI'][2:];a=np.frombuffer(decode((H/'face77/loop120/capture'/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(h,13,w,4).transpose(1,0,2,3);before,_,_,_,_,cell,owner,uv,source,_,_,domain,_=a;face=(cell[:,:,2]==1)&(owner[:,:,0]==r['sourcePalette67']['zeroWidth69']['role'])&(domain[:,:,0]<.5)&(source[:,:,:3]==owner[:,:,[2,0,1]]).all(2);family=np.full((h,w),-1,int);shade=np.rint(uv[:,:,2]*(levels-1)).astype(int)
  for y,x in np.argwhere(face):
   u,v=uv[y,x,:2];xx=int(np.floor(float(u)*tw))-ox;yy=int(np.floor((1-float(v))*th))-oy
   if 0<=xx<labels.shape[1]and 0<=yy<labels.shape[0]:family[y,x]=labels[yy,xx]
  examples=[];total=0;same=0;changedQ=0;seams=0;oldLUT=a[10,:,:,3]==1
  for y,x in np.argwhere(face&(family>=0)):
   for dy,dx in [(0,1),(1,0)]:
    ny,nx=y+dy,x+dx
    if ny>=h or nx>=w or not face[ny,nx]or family[ny,nx]<0:continue
    total+=1;seams+=int(oldLUT[y,x]!=oldLUT[ny,nx]);same+=int(family[y,x]==family[ny,nx])
    if family[y,x]!=family[ny,nx]or shade[y,x]==shade[ny,nx]:continue
    changedQ+=1;k=family[y,x];out=palette[k,[shade[y,x],shade[ny,nx]]];native=before[[y,ny],[x,nx],:3].astype(float);nyv=native@np.array([.2126,.7152,.0722]);py=luminance(out)
    if len(examples)<6:examples.append({'localXY':[[int(x),int(y)],[int(nx),int(ny)]],'sameSourceColourAddress':int(k),'observedQ':[int(shade[y,x]),int(shade[ny,nx])],'nativeLinearY':nyv.tolist(),'CPUFullLUTRGB8':out.tolist(),'CPUFullLUTY':py.tolist()})
  rows.append({'frame':f['frame'],'faceNeighbourPairs':total,'oldPartialCoverageSeams':seams,'sameSourceAddressPairs':same,'sameSourceAddressDifferentQ':changedQ,'examples':examples})
 result={'actualInputFrames':len(rows),'candidateGPUExecuted':False,'noNewThresholdOrFamilyOrQ':True,'sameAddressDifferentQPairs':sum(x['sameSourceAddressDifferentQ']for x in rows),'oldPartialCoverageSeams':sum(x['oldPartialCoverageSeams']for x in rows),'conclusion':'Uniform LUT coverage removes mixed-path seams, but same-source-family Q boundaries still produce large finite palette jumps. Source-colour segmentation alone cannot guarantee coherent light regions. This does not prove those observed shadows are invalid or authorize erasing them.','rows':rows};(G/'STAIN_CAUSE83.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
