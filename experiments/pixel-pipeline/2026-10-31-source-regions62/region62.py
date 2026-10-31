"""Source UV-connected colour regions, independent of frame g, Q and palette.

This is an explicit bounded-colour candidate, not semantic feature detection.
Measured source contrast certificates may introduce scalar cuts/anchor seeds.
No area pruning, RGB blur, k-means, screen-neighbour majority or source overwrite.
"""
from collections import defaultdict
import hashlib,math
import numpy as np

def lab(rgb):
 v=np.asarray(rgb,dtype=np.float64)/255
 v=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
 return np.cbrt(v@np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]]))@np.array([[.2104542553,1.9779984951,.0259040371],[.793617785,-2.428592205,.7827717662],[-.0040720468,.4505937099,-.808675766]])
def from_lch(L,C,h):
 a=C*math.cos(h);b=C*math.sin(h)
 v=np.array([L+.3963377774*a+.2158037573*b,L-.1055613458*a-.0638541728*b,L-.0894841775*a-1.291485548*b])**3
 return v@np.array([[4.0767416621,-1.2684380046,-.0041960863],[-3.3077115913,2.6097574011,-.7034186147],[.2309699292,-.3413193965,1.707614701]])
def rgb8(L,C,h):
 def valid(v):return np.all(v>=-1e-9)and np.all(v<=1+1e-9)
 v=from_lch(L,C,h)
 if not valid(v):
  lo,hi=0.,C
  for _ in range(28):
   mid=(lo+hi)/2
   if valid(from_lch(L,mid,h)):lo=mid
   else:hi=mid
  C=lo;v=from_lch(L,C,h)
 v=np.clip(v,0,1);s=np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055)
 return np.clip(np.floor(s*255+.5),0,255).astype(np.uint8)
def palette(anchor,count,span,interval=1):
 if count<2:raise ValueError('at least two diagnostic palette steps required')
 l,a,b=lab(anchor);c=math.hypot(a,b);h=math.atan2(b,a);out=[]
 for k in range(count):
  L=max(0,l-interval*span*(count-1-k)/(count-1))
  out.append(np.array(anchor,dtype=np.uint8)if k==count-1 or interval==0 else rgb8(L,c,h))
 return np.array(out)

def shade_index(g,thresholds):
 """Only the pure diagnostic classifier. Stored renderer Q is not overwritten."""
 if not math.isfinite(g)or any(not math.isfinite(t)for t in thresholds):raise ValueError('finite shade inputs required')
 if any(a>=b for a,b in zip(thresholds,thresholds[1:])):raise ValueError('strictly ordered thresholds required')
 return int(sum(g>=t for t in thresholds))
def cc4(codes,mask):
 """Two-pass connected components. IDs follow source texel order, not frame order."""
 h,w=mask.shape;labels=np.zeros((h,w),np.int32);parent=[0]
 def find(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 for y in range(h):
  for x in np.flatnonzero(mask[y]):
   c=codes[y,x];left=labels[y,x-1]if x and mask[y,x-1]and codes[y,x-1]==c else 0;up=labels[y-1,x]if y and mask[y-1,x]and codes[y-1,x]==c else 0
   if left and up:
    a,b=find(int(left)),find(int(up));labels[y,x]=min(a,b)
    if a!=b:parent[max(a,b)]=min(a,b)
   elif left or up:labels[y,x]=left or up
   else:labels[y,x]=len(parent);parent.append(len(parent))
 roots=np.array([find(i)for i in range(len(parent))]);canonical=np.zeros(len(parent),np.int32)
 for i,v in enumerate(sorted(set(roots[1:].tolist())),1):canonical[roots==v]=i
 return canonical[labels]
def texel(uv,w,h,unity=False):
 u,v=uv;x=min(w-1,int(math.floor((u%1)*w)))
 y=h-1-min(h-1,int(math.floor((v%1)*h)))if unity else min(h-1,int(math.floor((v%1)*h)))
 return x,y
def build_regions(rgba,mask,band,markers=()):
 assert 0<band<1 and mask.shape==rgba.shape[:2]
 colour=lab(rgba[:,:,:3]);mask=mask&(rgba[:,:,3]>0);h,w=mask.shape
 cuts=[]
 for axis in range(3):
  lo,hi=float(colour[:,:,axis][mask].min()),float(colour[:,:,axis][mask].max())
  cuts.append(list(np.arange(lo+band,hi,band)))
 # A certificate constrains source separation, not screen coordinates or owner.
 # All endpoint seeds are original source texels and remain explicit evidence.
 for a,b in markers:
  ax,ay=a;bx,by=b;va,vb=colour[ay,ax],colour[by,bx];axis=int(np.argmax(np.abs(va-vb)))
  if np.linalg.norm(va-vb)<=1e-7:continue
  if sum(va[axis]>=v for v in cuts[axis])==sum(vb[axis]>=v for v in cuts[axis]):cuts[axis].append(float((va[axis]+vb[axis])/2));cuts[axis].sort()
 bins=[np.searchsorted(cuts[k],colour[:,:,k],side='right')for k in range(3)];codes=bins[0]+(len(cuts[0])+1)*(bins[1]+(len(cuts[1])+1)*bins[2]);labels=cc4(codes,mask)
 # A merged region cannot represent two different certified source witnesses
 # with one anchor. Split that SOURCE region by their measured colour values;
 # no screen-cell override and no deletion of the smaller feature.
 endpoints=list(dict.fromkeys(p for pair in markers for p in pair));fissions=[]
 for _ in range(len(endpoints)):
  groups=defaultdict(list)
  for x,y in endpoints:
   if labels[y,x]>0:groups[int(labels[y,x])].append((x,y))
  conflicts=[points for points in groups.values()if len({tuple(rgba[y,x,:3])for x,y in points})>1]
  if not conflicts:break
  for points in conflicts:
   pairs=[(float(np.linalg.norm(colour[a[1],a[0]]-colour[b[1],b[0]])),a,b)for a in points for b in points];_,a,b=max(pairs)
   va,vb=colour[a[1],a[0]],colour[b[1],b[0]];axis=int(np.argmax(np.abs(va-vb)));cut=float((va[axis]+vb[axis])/2);region=int(labels[a[1],a[0]]);part=labels==region;code=int(codes.max())+1;codes[part]=code;codes[part&(colour[:,:,axis]>=cut)]=code+1;fissions.append({'seedTexels':[a,b],'axisLab':axis,'cut':cut,'reason':'distinct certified native source colours in one connected range region'})
  labels=cc4(codes,mask)
 n=int(labels.max());flat=labels.ravel();valid=mask.ravel();points=colour.reshape(-1,3);count=np.bincount(flat[valid],minlength=n+1)
 sums=np.column_stack([np.bincount(flat[valid],weights=points[valid,k],minlength=n+1)for k in range(3)]);means=sums/np.maximum(count[:,None],1);cost=np.sum((points-means[flat])**2,axis=1);cost[~valid]=np.inf
 best=np.full(n+1,np.inf);np.minimum.at(best,flat[valid],cost[valid]);candidate=valid&(cost<=best[flat]+1e-15);pix=np.arange(h*w);origins=np.full(n+1,h*w);np.minimum.at(origins,flat[candidate],pix[candidate]);anchors=np.zeros((n+1,3),np.uint8)
 for i in range(1,n+1):anchors[i]=rgba.reshape(-1,4)[origins[i],:3]
 # Region identity and palette-reference identity are different. Disconnected
 # regions in the SAME bounded source-colour box can share a native medoid.
 # This avoids introducing a slightly different colour for every tiny UV patch.
 # It never merges region masks, geometry structures or occlusion owners.
 codeFlat=codes.ravel().astype(np.int64);nc=int(codeFlat.max())+1;groupCount=np.bincount(codeFlat[valid],minlength=nc)
 groupSum=np.column_stack([np.bincount(codeFlat[valid],weights=points[valid,k],minlength=nc)for k in range(3)]);groupMean=groupSum/np.maximum(groupCount[:,None],1);groupCost=np.sum((points-groupMean[codeFlat])**2,axis=1);groupCost[~valid]=np.inf
 groupBest=np.full(nc,np.inf);np.minimum.at(groupBest,codeFlat[valid],groupCost[valid]);choose=valid&(groupCost<=groupBest[codeFlat]+1e-15);groupOrigin=np.full(nc,h*w);np.minimum.at(groupOrigin,codeFlat[choose],pix[choose]);regionCode={i:int(codeFlat[origins[i]])for i in range(1,n+1)}
 for i in range(1,n+1):origins[i]=groupOrigin[regionCode[i]];anchors[i]=rgba.reshape(-1,4)[origins[i],:3]
 seeds=defaultdict(set)
 for pair in markers:
  for x,y in pair:
   i=int(labels[y,x])
   if i:seeds[i].add(tuple(rgba[y,x,:3]))
 conflicts=[]
 for i,values in seeds.items():
  if len(values)==1:
   anchors[i]=next(iter(values));origins[i]=min(y*w+x for pair in markers for x,y in pair if labels[y,x]==i)
  else:conflicts.append({'region':i,'seedRGB8':[[int(c)for c in v]for v in sorted(values)],'reason':'multiple certified texel colours in one source region; keep native medoid, mark uncertainty'})
 # This cache key has no g, Q, screen location, camera or palette parameter.
 digest=hashlib.sha256(rgba.tobytes()+mask.tobytes()+repr(cuts).encode()+repr(fissions).encode()).hexdigest()
 residual=points-lab(anchors)[flat];error=np.linalg.norm(residual,axis=1).reshape(h,w)
 rows=[]
 for i in range(1,n+1):
  ix=origins[i];rows.append({'localId':i,'sourceKey':digest+'/'+str(i),'texelCount':int(count[i]),'anchorRGB8':anchors[i].tolist(),'anchorNativeTexel':[int(ix%w),int(ix//w)],'anchorOriginRegion':int(flat[ix]),'paletteReferenceGroup':('certificate-region-'+str(i))if i in seeds else'source-colour-box-'+str(regionCode[i]),'hasCertificateSeed':i in seeds,'anchorConflict':any(c['region']==i for c in conflicts)})
 return {'labels':labels,'anchors':anchors,'mask':mask,'cuts':cuts,'rows':rows,'error':error,'key':digest,'conflicts':conflicts,'certificateFissions':fissions,'regionCount':n,'band':band}
def structure_components(indices,positions,normals=None):
 """Topology identity only. Not a colour/semantic feature or occlusion owner."""
 # Preserve disconnected surfaces even if material/RGB/UV are identical.
 # Duplicate seam vertices weld only on exact Float32 position+normal values.
 pos=np.array(positions,dtype='<f4');norm=np.array(normals,dtype='<f4')if normals is not None else np.zeros_like(pos)
 vert={};keys=[]
 for p,n in zip(pos,norm):
  key=p.tobytes()+n.tobytes();keys.append(vert.setdefault(key,len(vert)))
 parent=list(range(len(indices)));edge={}
 def find(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 for t,tri in enumerate(indices):
  for a,b in zip(tri,np.roll(tri,-1)):
   e=tuple(sorted((keys[int(a)],keys[int(b)])))
   if e in edge:
    x,y=find(t),find(edge[e]);parent[max(x,y)]=min(x,y)
   else:edge[e]=t
 root=[find(i)for i in range(len(indices))];ids={v:i for i,v in enumerate(sorted(set(root)))}
 return np.array([ids[v]for v in root],dtype=np.int32)
def frame_metrics(rows,rgb,key='RGB8'):
 p={(r['x'],r['y']):i for i,r in enumerate(rows)};visited=set();sizes=[];edges=0
 for xy,i in p.items():
  for dx,dy in [(1,0),(0,1)]:
   j=p.get((xy[0]+dx,xy[1]+dy))
   if j is not None and not np.array_equal(rgb[i],rgb[j]):edges+=1
  if i in visited:continue
  stack=[xy];visited.add(i);size=0
  while stack:
   x,y=stack.pop();size+=1
   for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
    j=p.get((x+dx,y+dy))
    if j is not None and j not in visited and np.array_equal(rgb[i],rgb[j]):visited.add(j);stack.append((x+dx,y+dy))
  sizes.append(size)
 L=lab(rgb)[:,0]
 return {'cells':len(rows),'usedRGB8':len(set(map(tuple,rgb.tolist()))),'RGB4Components':len(sizes),'singleCells':sizes.count(1),'visibleRGBCardinalEdges':edges,'Lmin':float(L.min()),'Lmedian':float(np.median(L)),'Lmax':float(L.max())}
