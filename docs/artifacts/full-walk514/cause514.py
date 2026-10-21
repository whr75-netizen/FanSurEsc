from pathlib import Path
import json,struct,gzip,importlib.util,collections,numpy as np
from fractions import Fraction as Q
from PIL import Image,ImageDraw
W=Path(__file__).parent;R=W/'Loop514';review=json.loads((R/'REVIEW514.json').read_text());spec=importlib.util.spec_from_file_location('compiler511',W/'compile_curve511.py');compiler=importlib.util.module_from_spec(spec);spec.loader.exec_module(compiler)
cache={}
def rd(i,tag):
 key=(i,tag)
 if key not in cache:
  b=gzip.decompress((R/(f'{i:03d}_'+tag+'.bin.gz')).read_bytes());w,h,_,_=struct.unpack_from('<4i',b);cache[key]=np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
 return cache[key]
def clip(poly,axis,value,greater):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ina=a[axis]>=value if greater else a[axis]<=value;inb=b[axis]>=value if greater else b[axis]<=value
  if ina:out.append(a)
  if ina!=inb:
   t=(value-a[axis])/(b[axis]-a[axis]);out.append(tuple(a[j]+t*(b[j]-a[j])for j in range(2)))
 return out
def source_union_area(i,x,y):
 b=(R/f'{i:03d}.hairgeom').read_bytes();nv,ns=struct.unpack_from('<2i',b);v=np.frombuffer(b,'<f4',offset=8,count=nv*3).reshape(nv,3);at=8+nv*12;tri=[]
 for sm in range(ns):
  ni=struct.unpack_from('<i',b,at)[0];at+=4;ids=np.frombuffer(b,'<i4',offset=at,count=ni).reshape(-1,3);at+=ni*4;t=v[ids,:2];ok=(t[:,:,0].max(1)>=x)&(t[:,:,0].min(1)<=x+1)&(t[:,:,1].max(1)>=y)&(t[:,:,1].min(1)<=y+1);tri.extend(t[ok].tolist())
 rings,_=compiler.vector_union(tri);total=Q(0)
 for ring in rings:
  p=ring
  for axis,val,greater in [(0,Q(x),True),(0,Q(x+1),False),(1,Q(y),True),(1,Q(y+1),False)]:
   if p:p=clip(p,axis,val,greater)
  if p:total+=compiler.area(p)
 return {'area':float(total),'triangleCandidates':len(tri),'note':'exact union of bbox-selected projected opaque Hair triangles, then rational cell clipping; local diagnostic only, not repeated curve preparation or a runtime input change'}
events=[]
for e in [e for e in review['events']if e['kind']=='region-ABA']:
 x,y=e['xy'];steps=[]
 for i in [e['target']-1,e['target'],e['target']+1]:
  data=(R/f'{i:03d}_areas.bin').read_bytes();bx,by,bw,bh=struct.unpack_from('<4i',data);a=np.frombuffer(data,'<f4',offset=16).reshape(bh,bw);area=float(a[y-by,x-bx]);m=rd(i,'MASK')[:,:,1]>.5;neighbours=[];delta=float(np.float32(1-np.float32(area)))-area
  for dx,dy,w in [(1,0,.58578644),(-1,0,.58578644),(0,1,.58578644),(0,-1,.58578644),(1,1,.29289322),(-1,1,.29289322),(1,-1,.29289322),(-1,-1,.29289322)]:
   weight=float(np.float32(.14)*np.float32(w));on=int(m[y+dy,x+dx]);contribution=weight*(1-2*on);delta+=contribution;neighbours.append({'xy':[x+dx,y+dy],'selected':on,'edgeWeight':weight,'fillCostMinusEmptyContribution':contribution})
  rings=json.loads((R/f'{i:03d}_curves.json').read_text())['curves'];near=[];centre=np.array([x+.5,y+.5])
  for ri,ring in enumerate(rings):
   p=np.array([[q['x'],q['y']]for q in ring['points']]);
   for si,(aa,bb)in enumerate(zip(p,np.roll(p,-1,axis=0))):
    d=bb-aa;t=np.clip(np.dot(centre-aa,d)/max(np.dot(d,d),1e-30),0,1);distance=np.linalg.norm(aa+t*d-centre)
    if distance<1.6:near.append({'ring':ri,'segment':si,'a':aa.tolist(),'b':bb.tolist(),'distanceToCellCentre':float(distance)})
  steps.append({'target':i,'curveCellArea':area,'selected':bool(m[y,x]),'fixedNeighbourFillMinusEmptyEnergy':delta,'costToToggleWithCurrentNeighbours':float(-delta if m[y,x]else delta),'sourceMeshUnion':source_union_area(i,x,y),'neighbours':neighbours,'nearbyPersistentSegments':near})
 events.append({'headXY':[x,y],'steps':steps,'scope':'local energy conditional on current joint neighbours; no alternative global optimization or new temporal cost was executed'})
def exterior(cov):
 h,w=cov.shape;e=np.zeros_like(cov);q=collections.deque()
 for y,x in [(0,x)for x in range(w)]+[(h-1,x)for x in range(w)]+[(y,0)for y in range(h)]+[(y,w-1)for y in range(h)]:
  if not cov[y,x]and not e[y,x]:e[y,x]=1;q.append((y,x))
 while q:
  y,x=q.popleft()
  for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
   yy,xx=y+dy,x+dx
   if 0<=yy<h and 0<=xx<w and not cov[yy,xx]and not e[yy,xx]:e[yy,xx]=1;q.append((yy,xx))
 return e
lineCache={}
def line(i,tag,x,y):
 p=json.loads((R/f'{i:03d}_pose.json').read_text());ox,oy=p['offset'];mx,my=x+ox,y-oy;key=(i,tag)
 if key not in lineCache:
  c=rd(i,tag+'_FINAL')[:,:,3]>.5;o=rd(i,tag+'_OWNER');lineCache[key]=(c,o,exterior(c))
 c,o,ext=lineCache[key];outer=False;thin=False
 for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
  if ext[my+dy,mx+dx]:outer=True;thin|=not(c[my-dy,mx-dx]and c[my-2*dy,mx-2*dx])
 return {'mainXY':[mx,my],'outer':bool(outer),'thin':bool(thin),'reconstructedHairLineReason':int(outer and not thin),'coverage5x5':c[my-2:my+3,mx-2:mx+3].astype(int).tolist(),'roles3x3':o[my-1:my+2,mx-1:mx+2,0].tolist()}
flashes=[]
originalKeys={(f['target'],tuple(f['xy']))for f in review['flashes']if f['version']=='original'}
for f in [f for f in review['flashes']if f['version']=='candidate']:
 i=f['target'];x,y=f['xy'];steps=[]
 for t in [(i-1)%80,i,(i+1)%80]:
  cfg=json.loads((R/f'{t:03d}_ALT_projection.json').read_text());info=line(t,'ALT',x,y);info.update({'target':t,'light':{k:cfg[k]for k in ['hour','ambientIntensity','directionalIntensity','directionalColour','directionalRotation']}});steps.append(info)
 flashes.append({'observation':f,'alsoScreenedInOriginal':(i,(x,y))in originalKeys,'lineReconstruction':steps,'limit':'Before/Flood/Audit not captured; reconstructed from final coverage/owner. Same primitive is not identical UV; stable directional light does not certify all moving world-shadow inputs.'})
seam=[]
roi=review['headROI'];yy,xx=np.indices((roi[3]-roi[1],roi[2]-roi[0]));yy+=roi[1];xx+=roi[0]
for tag in ['BASE','ALT']:
 entries=[]
 for i in [0,80]:
  pose=json.loads((R/f'{i:03d}_pose.json').read_text());ox,oy=pose['offset'];meta=rd(i,tag+'_META')[yy-oy,xx+ox];colour=rd(i,tag+'_FINAL')[yy-oy,xx+ox];world=rd(i,tag+'_WORLDINFO')[yy-oy,xx+ox];png=np.array(Image.open(R/f'{i:03d}_{tag}.png').convert('RGB'))[2*(yy-oy),2*(xx+ox)];entries.append((meta,colour,world,png))
 a,b=entries;delta=np.max(abs(a[3].astype(int)-b[3].astype(int)),axis=2);covered=(a[0][:,:,0]>0)&(b[0][:,:,0]>0);visible=(a[2][:,:,2]>.5)&(b[2][:,:,2]>.5);ys,xs=np.where(delta==delta.max());spots=[]
 for ry,rx in list(zip(ys,xs))[:10]:spots.append({'headXY':[int(rx+roi[0]),int(ry+roi[1])],'roles':[int(round(float(t[0][ry,rx,1])))for t in entries],'screenRGB':[t[3][ry,rx].tolist()for t in entries],'linearRGB':[t[1][ry,rx].tolist()for t in entries],'worldInfo':[t[2][ry,rx].tolist()for t in entries]})
 seam.append({'version':tag,'screenMaxByte':int(delta.max()),'coveredBothScreenMaxByte':int(delta[covered].max(initial=0)),'coveredVisibleBothScreenMaxByte':int(delta[covered&visible].max(initial=0)),'headPreworldLinearMax':float(np.max(abs(a[1]-b[1]))),'maxLocations':spots,'worldVisibilityChangedCellCount':int(((a[2][:,:,2]>.5)!=(b[2][:,:,2]>.5)).sum())})
out={'regionEpisodes':events,'internalColourScreening':flashes,'seam':seam,'noNewCapture':True,'noProductChanges':True,'classificationLimits':['Source mesh union is geometric evidence, not a requirement to preserve every hair detail.','Current independent area/perimeter optimum is not a perceptual temporal-quality criterion.','Colour screening thresholds are diagnostic selections, not error counts.']}
(R/'CAUSE514.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'regionEpisodes':events,'seam':seam,'flashClassSummary':[{'target':f['observation']['target'],'xy':f['observation']['xy'],'alsoOriginal':f['alsoScreenedInOriginal'],'line':[s['reconstructedHairLineReason']for s in f['lineReconstruction']],'lightEqual':f['lineReconstruction'][0]['light']==f['lineReconstruction'][1]['light']==f['lineReconstruction'][2]['light']}for f in flashes]},ensure_ascii=False))
