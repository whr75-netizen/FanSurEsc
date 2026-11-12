"""Current primitive/pixel UV intersection for observed colour-step examples.

This is an unoccluded-carrier upper bound. It does not claim complete pixel
ownership, other primitives' visibility, source gradient semantics or a fix.
"""
from pathlib import Path
from collections import defaultdict
import json,numpy as np
from frame_bytes77 import decode
from selected_light84 import geometry,barycentric_uv
H=Path(__file__).resolve().parent;G=H/'face94/held480'
def clip(p,centre):
 p=np.asarray(p,float)-centre
 for axis,sign in [(0,1),(0,-1),(1,1),(1,-1)]:
  if not len(p):break
  out=[];old=p[-1];a=.5-sign*old[axis]
  for new in p:
   b=.5-sign*new[axis]
   if(a>=0)!=(b>=0):out.append(old+(new-old)*(a/(a-b)))
   if b>=0:out.append(new)
   old=new;a=b
  p=np.asarray(out)
 return p+centre if len(p)else np.empty((0,2))
def area(p):return float(abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))*.5)if len(p)>=3 else 0.
def footprint(f,x,y):
 c=G/'capture';w,h=f['QROI'][2:];a=np.frombuffer(decode((c/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(h,24,w,4).transpose(1,0,2,3);assert a[15,y,x,3]==1;geo=geometry(c/f['light84']['sourceGeometryFile']);pr=int(a[9,y,x,3]);t=geo['v'][geo['tri'][pr-1]].astype(float);screen=t[:,5:7].copy();screen[:,1]=272-screen[:,1];centre=np.array([f['QROI'][0]+x+.5,272-f['QROI'][1]-h+y+.5]);b=barycentric_uv(t[:,3:5],a[10,y,x,:2]);assert b is not None;point=b@screen;poly=clip(screen,centre);assert len(poly)>=3;matrix=np.c_[screen[1]-screen[0],screen[2]-screen[0]];weights=np.linalg.solve(matrix,(poly-screen[0]).T).T;uv=t[0,3:5]+weights[:,0,None]*(t[1,3:5]-t[0,3:5])+weights[:,1,None]*(t[2,3:5]-t[0,3:5]);info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());tw,th=info['textureSize'];ox,oy=info['cropOffset'];tex=uv*[tw,-th]+[-ox,th-oy];labels=np.load(H/'face92/SOURCE_VALUE92.npz')['labels'];lo=np.floor(tex.min(0)).astype(int);hi=np.ceil(tex.max(0)).astype(int);assert np.prod(hi-lo)<=65536;hist=defaultdict(float);total=0.
 for yy in range(max(0,lo[1]),min(labels.shape[0],hi[1])):
  for xx in range(max(0,lo[0]),min(labels.shape[1],hi[0])):
   value=area(clip(tex,np.array([xx+.5,yy+.5])))
   if value>0:hist[int(labels[yy,xx])]+=value;total+=value
 assert total>0;hist={k:v/total for k,v in hist.items()};chosen=int(a[15,y,x,0]-1);return {'frame':f['frame'],'localXY':[x,y],'primitive':pr,'sourcePointOffsetFromPixelCentre':(point-centre).tolist(),'sourcePointInsidePixel':bool((abs(point-centre)<=.5).all()),'unoccludedPrimitiveCellArea':area(poly),'pointSelectedAddress':chosen,'pointAddressFootprintFraction':hist.get(chosen,0.),'dominantAddressUpperBoundOnly':max(hist,key=hist.get),'histogram':hist}
def main():
 r=json.loads((G/'capture/COMPLETE.json').read_text());assert r['packetComplete'];frames={f['frame']:f for f in r['stream77']['frames']};pairs=[]
 for before,after,x,y in [(148,149,6,7),(195,196,6,7)]:
  a=footprint(frames[before],x,y);b=footprint(frames[after],x,y);common=set(a['histogram'])|set(b['histogram']);tv=.5*sum(abs(a['histogram'].get(k,0)-b['histogram'].get(k,0))for k in common);pairs.append({'before':a,'after':b,'normalizedCarrierFootprintTotalVariation':tv,'sameDominantAddressInCarrierUpperBound':a['dominantAddressUpperBoundOnly']==b['dominantAddressUpperBoundOnly']})
 out={'savedActualInputCPUAnalysis':True,'newGPUExecuted':False,'completePixelVisibilityOrSelectionProof':False,'otherPrimitivesHairWorldAndAAVisibilityNotResolved':True,'pairs':pairs};(G/'COLOUR_FOOTPRINT94.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
