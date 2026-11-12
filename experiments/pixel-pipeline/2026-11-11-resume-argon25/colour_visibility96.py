"""Visible source UV area; no new palette, semantic label or GPU result.

Retain per-source-family/paint-component masses separately. In particular this
does not let a background majority erase a small foreground paint component.
"""
from pathlib import Path
from collections import defaultdict
import json,numpy as np,time
from actor_visibility96 import ActorQuery,packet
from visible_ribbon96 import area,half,visible,area_roundoff
H=Path(__file__).resolve().parent

def square(p,lo,hi):
 for n,c in[(np.array([1.,0]),-hi[0]),(np.array([-1.,0]),lo[0]),(np.array([0.,1]),-hi[1]),(np.array([0.,-1.]),lo[1])]:p=half(p,n,c)
 return p

def histogram(polygons,xy,uv,labels,foreground,regions,info):
 tw,th=info['textureSize'];ox,oy=info['cropOffset'];hist=defaultdict(float);fg=defaultdict(float);reg=defaultdict(float);total=0.;det=abs(np.linalg.det(xy[1:]-xy[0]));uvdet=abs(np.linalg.det((uv[1:]-uv[0])*[tw,-th]));ratio=det/uvdet if uvdet else None
 if ratio is None:return None
 for p in polygons:
  if area(p)<=area_roundoff(p):continue
  weights=np.linalg.solve((xy[1:]-xy[0]).T,(p-xy[0]).T).T;u=uv[0]+weights[:,0,None]*(uv[1]-uv[0])+weights[:,1,None]*(uv[2]-uv[0]);tex=u*[tw,-th]+[-ox,th-oy];lo=np.floor(tex.min(0)).astype(int);hi=np.ceil(tex.max(0)).astype(int)
  if np.prod(hi-lo)>65536:raise ValueError('source texel intersection budget')
  if (lo<0).any()or hi[0]>labels.shape[1]or hi[1]>labels.shape[0]:raise ValueError('source crop lacks footprint; no inferred fill')
  for yy in range(lo[1],hi[1]):
   for xx in range(lo[0],hi[0]):
    value=area(square(tex,np.array([xx,yy]),np.array([xx+1,yy+1])))*ratio
    if value:
     hist[int(labels[yy,xx])]+=value;fg[int(foreground[yy,xx])]+=value;reg[int(regions[yy,xx])]+=value;total+=value
 return {'cellArea':total,'familyMass':dict(hist),'existingForegroundMass':dict(fg),'existingRegionMass':dict(reg)}

def main():
 root=Path(__import__('sys').argv[1]);report=json.loads((root/'capture/COMPLETE.json').read_text());assert report['packetComplete']and report['restorationChecksPass'];labels=np.load(H/'face92/SOURCE_VALUE92.npz')['labels'];regions=np.load(H/'face86/REGIONS86.npz');info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());rows=[]
 for f in report['stream77']['frames']:
  if 'actorSource96'not in f or f['ordinal']not in[46,47]:continue
  start=time.perf_counter();query=ActorQuery(root,f);a,world,worlddepth=packet(root,f);w=f['QROI'][2];lo=np.array([f['QROI'][0]+6,272-f['QROI'][1]-w+7]);hi=lo+1;pieces=[];selected=a[4,7,6].tolist();primitive=int(a[0,7,6,3]);worldFront=False
  for row in query.rows:
   if query.table[row['renderer'],row['submesh']]['role']!=4:continue
   material=query.materials[row['renderer'],row['submesh']];valid=(row['det']!=0)&(row['hi']>lo).all(1)&(row['lo']<hi).all(1)
   if material['cull']==2:valid&=row['det']>0
   elif material['cull']==1:valid&=row['det']<0
   for index in np.flatnonzero(valid):
    xy=row['xy'][index];p=square(xy,lo,hi)
    if not len(p):continue
    result=visible(query,p,xy,row['z'][index],exclude=(row['renderer'],row['submesh'],int(index)))
    # Native world tiles are actual raster samples, not continuous world
    # geometry. Flag any closer tile rather than assert world visibility.
    minimum=float(row['z'][index].min());worldFront|=bool((worlddepth[:,:,0]<minimum).any())
    pieces.append({'renderer':row['renderer'],'submesh':row['submesh'],'primitive':int(index)+1,'projectedArea':area(p),'lower':histogram(result['lower'],xy,row['uv'][index],labels,regions['foreground'],regions['regions'],info),'upper':histogram(result['upper'],xy,row['uv'][index],labels,regions['foreground'],regions['regions'],info)})
  sums={}
  for side in['lower','upper']:
   dest=defaultdict(float);areaTotal=0
   for piece in pieces:
    value=piece[side]
    if value is None:raise ValueError('degenerate UV mapping; footprint remains unknown')
    areaTotal+=value['cellArea']
    for k,v in value['familyMass'].items():dest[int(k)]+=v
   sums[side]={'cellArea':areaTotal,'familyMass':dict(dest)}
  rows.append({'sourceId':f['sourceId'],'frame':f['frame'],'localXY':[6,7],'selectedFamilyQ':selected,'selectedPrimitive':primitive,'anyCloserWorldHaloSample':worldFront,'pieces':pieces,'aggregate':sums});print(json.dumps({'frame':f['frame'],'pieces':len(pieces),'CPUSeconds':time.perf_counter()-start,'lowerFaceArea':sums['lower']['cellArea'],'upperFaceArea':sums['upper']['cellArea'],'paletteCandidateCreated':False}),flush=True)
 assert len(rows)==2
 out={'actualGeometryAlphaSource':True,'CPUOnly':True,'paletteCandidateCreated':False,'wholeCellSelectionOrSemanticContractSolved':False,'worldContinuousGeometryKnown':False,'rows':rows};(root/'COLOUR_VISIBLE96.json').write_text(json.dumps(out,indent=2))
if __name__=='__main__':main()
