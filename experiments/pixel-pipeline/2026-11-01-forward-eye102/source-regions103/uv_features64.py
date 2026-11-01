"""Source-native jump/gradient evidence, not Lab-bin segmentation or art truth.

Fit independent one-dimensional affine profiles on each side of a source edge.
Extrapolate to the edge; a linear ramp has zero jump at every scale. Intersect
RGB8-uncertainty jump intervals across scales. Keep fine/ambiguous evidence too.
No RGB filtering, palette, minimum-area deletion or screen-coordinate cache.
"""
from collections import defaultdict
import hashlib,json
import numpy as np
RULE_VERSION='uv-affine-jump64.2'

def source_key(rgb,mask,scales):
 policy={'rule':RULE_VERSION,'scales':list(scales),'space':'sRGB8-to-OKLab','interval':'decode-positive-LMS-cuberoot-mixed-Lab','borders':'no-wrap-explicit-unknown','ridge':'opposed-local-curvature-lobes'}
 return hashlib.sha256(rgb.tobytes()+mask.tobytes()+json.dumps(policy,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def lab(rgb):
 v=np.asarray(rgb,dtype=np.float64)/255.;v=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
 return np.cbrt(v@np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]]))@np.array([[.2104542553,1.9779984951,.0259040371],[.793617785,-2.428592205,.7827717662],[-.0040720468,.4505937099,-.808675766]])

def colour_intervals(rgb):
 """RGB8 +/-half-code interval propagated through decode/LMS/cuberoot/Lab.

Positive LMS coefficients and monotone decode/cuberoot permit interval bounds;
mixed-sign Lab coefficients use lower/upper separately. No corner-only extrema
assumption. Floating bounds are widened outward; this is not a formal proof of
every platform's floating implementation or a perceptual contrast threshold.
 """
 codes=rgb[:,:,0].astype(np.uint32)*65536+rgb[:,:,1].astype(np.uint32)*256+rgb[:,:,2]
 unique,inverse=np.unique(codes,return_inverse=True);values=np.column_stack([unique//65536,unique//256%256,unique%256]);centre=lab(values)
 def decode(v):
  v=np.clip(v,0,255)/255.;return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
 m1=np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]])
 m2=np.array([[.2104542553,1.9779984951,.0259040371],[.793617785,-2.428592205,.7827717662],[-.0040720468,.4505937099,-.808675766]])
 lower=np.nextafter(np.cbrt(np.nextafter(decode(values-.5)@m1,-np.inf)),-np.inf);upper=np.nextafter(np.cbrt(np.nextafter(decode(values+.5)@m1,np.inf)),np.inf)
 lo=lower@np.maximum(m2,0)+upper@np.minimum(m2,0);hi=upper@np.maximum(m2,0)+lower@np.minimum(m2,0)
 shape=(*rgb.shape[:2],3)
 return centre[inverse].reshape(shape),np.nextafter(lo[inverse].reshape(shape),-np.inf),np.nextafter(hi[inverse].reshape(shape),np.inf)

def intercept_weights(radius,side):
 if radius<2:raise ValueError('two samples per side are needed for a slope')
 x=np.arange(radius,dtype=float)+.5
 if side<0:x=-x[::-1]
 return (np.sum(x*x)-np.sum(x)*x)/(radius*np.sum(x*x)-np.sum(x)**2)

def shifted(a,offset,axis):
 return np.take(a,np.clip(np.arange(a.shape[axis])+offset,0,a.shape[axis]-1),axis=axis)

def jump_interval(lo,hi,mask,radius,axis):
 """edge index i is the boundary between source samples i and i+1."""
 lower=np.zeros_like(lo);upper=np.zeros_like(hi);valid=mask.copy();wl=intercept_weights(radius,-1);wr=intercept_weights(radius,1)
 offsets=list(range(-radius+1,1))+list(range(1,radius+1));weights=list(-wl)+list(wr)
 for offset,w in zip(offsets,weights):
  a=shifted(lo,offset,axis);b=shifted(hi,offset,axis);lower+=w*(a if w>=0 else b);upper+=w*(b if w>=0 else a);valid &= shifted(mask,offset,axis)
 positions=np.arange(mask.shape[axis]);interior=(positions>=radius-1)&(positions<mask.shape[axis]-radius);valid &= interior[None,:]if axis==1 else interior[:,None]
 return np.nextafter(lower,-np.inf),np.nextafter(upper,np.inf),valid

def axis_evidence(lo,hi,mask,scales,axis):
 commonLo=np.full_like(lo,-np.inf);commonHi=np.full_like(hi,np.inf);allValid=mask.copy();allAffine=mask.copy();allResolved=mask.copy();fine=None;scaleCounts=[];prefix=[];anyResolved=np.zeros(mask.shape,bool)
 curvatureLo=lo-(shifted(hi,-1,axis)+shifted(hi,1,axis))/2
 curvatureHi=hi-(shifted(lo,-1,axis)+shifted(lo,1,axis))/2
 affinePossible=np.all((curvatureLo<=0)&(curvatureHi>=0),axis=2)
 # Side fits can produce extrapolation lobes adjacent to a true step. Do not
 # turn a boundary between identical source samples into a fine edge.
 directLo=shifted(lo,1,axis)-hi;directHi=shifted(hi,1,axis)-lo
 directResolved=np.any((directLo>0)|(directHi<0),axis=2)
 for r in scales:
  a,b,valid=jump_interval(lo,hi,mask,r,axis);resolved=valid&directResolved&np.any((a>0)|(b<0),axis=2);anyResolved |= resolved
  sideAffine=mask.copy()
  for offset in list(range(-r+2,0))+list(range(2,r)):
   sideAffine &= shifted(affinePossible,offset,axis)
  if fine is None:fine=resolved.copy()
  commonLo=np.maximum(commonLo,a);commonHi=np.minimum(commonHi,b);allValid &=valid;allAffine &=sideAffine;allResolved &=resolved
  prefix.append(allValid&allAffine&allResolved&np.all(commonLo<=commonHi,axis=2)&np.any((commonLo>0)|(commonHi<0),axis=2))
  scaleCounts.append({'radius':r,'validEdges':int(valid.sum()),'resolvedJumpEdges':int(resolved.sum()),'withAffineCompatibleSides':int((resolved&sideAffine).sum())})
 consistent=np.all(commonLo<=commonHi,axis=2);combined=allValid&allAffine&directResolved&consistent&np.any((commonLo>0)|(commonHi<0),axis=2)
 persistent=combined&allResolved
 # Fine evidence is never erased because a broader window mixes both edges of
 # a thin painted strip. It is an unresolved child, not a forced coarse split.
 fineOnly=fine&~persistent
 for row,p in zip(scaleCounts,prefix):row['prefixPersistentEdgesOnLargestSupport']=int((p&allValid).sum())
 assert np.all(~persistent|fine)
 assert all(a['prefixPersistentEdgesOnLargestSupport']>=b['prefixPersistentEdgesOnLargestSupport']for a,b in zip(scaleCounts,scaleCounts[1:]))
 return {'persistent':persistent,'fine':fine,'fineOnly':fineOnly,'scaleEmergentUncertain':combined&~allResolved,'inconsistentScales':allValid&(~consistent|~allAffine)&anyResolved,'validAllScales':allValid,'counts':scaleCounts}

def thin_ridges(lo,hi,mask,axis):
 """Native three-sample lobe with opposite flanking curvature signs.

Retain as a thin/ridge *candidate*. A tiny painted mark and a sampled narrow
smooth highlight may be identical data; the code does not infer their meaning.
"""
 cmLo=lo-(shifted(hi,-1,axis)+shifted(hi,1,axis))/2
 cmHi=hi-(shifted(lo,-1,axis)+shifted(lo,1,axis))/2
 positive=cmLo>0;negative=cmHi<0
 paired=np.any((positive&shifted(negative,-1,axis)&shifted(negative,1,axis))|(negative&shifted(positive,-1,axis)&shifted(positive,1,axis)),axis=2)
 valid=mask&shifted(mask,-2,axis)&shifted(mask,2,axis)
 pos=np.arange(mask.shape[axis]);inside=(pos>=2)&(pos<mask.shape[axis]-2);valid &=inside[None,:]if axis==1 else inside[:,None]
 return paired&valid

def barrier_components(mask,xbar,ybar):
 """Pixel adjacency cut only by measured SOURCE-edge evidence, never colour bins."""
 h,w=mask.shape;labels=np.full(mask.shape,-1,np.int32);parent=[]
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for y,x in np.argwhere(mask):
  candidates=[]
  if x and mask[y,x-1]and not xbar[y,x-1]:candidates.append(int(labels[y,x-1]))
  if y and mask[y-1,x]and not ybar[y-1,x]:candidates.append(int(labels[y-1,x]))
  if not candidates:i=len(parent);parent.append(i)
  else:
   roots=[find(i)for i in candidates];i=min(roots)
   for j in roots:parent[max(i,j)]=min(i,j)
  labels[y,x]=i
 roots=np.array([find(i)for i in range(len(parent))],np.int32);ids={v:i for i,v in enumerate(sorted(set(roots.tolist())))}
 lookup=np.array([ids[int(v)]for v in roots],np.int32);labels[mask]=lookup[labels[mask]]
 return labels,len(ids)

def edge_components(xbar,ybar):
 """Keep open source contours, which cannot define a closed fill region.

No gap closing or minimum length. Component/junction status is evidence only.
"""
 edges=[];adjacency=defaultdict(list)
 for axis,bars in [('x',xbar),('y',ybar)]:
  for y,x in np.argwhere(bars):
   a,b=((int(x+1),int(y)),(int(x+1),int(y+1)))if axis=='x'else((int(x),int(y+1)),(int(x+1),int(y+1)))
   i=len(edges);edges.append((axis,int(x),int(y),a,b));adjacency[a].append(i);adjacency[b].append(i)
 visited=set();groups=[];membership={}
 for start in range(len(edges)):
  if start in visited:continue
  stack=[start];visited.add(start);found=[];vertices=set()
  while stack:
   i=stack.pop();found.append(i);e=edges[i];vertices.update(e[3:])
   for p in e[3:]:
    for j in adjacency[p]:
     if j not in visited:visited.add(j);stack.append(j)
  group=len(groups)
  for i in found:membership[edges[i][:3]]=group
  groups.append({'id':group,'edges':len(found),'endpoints':sum(len(adjacency[p])==1 for p in vertices),'junctions':sum(len(adjacency[p])>2 for p in vertices),'closedNonBranching':all(len(adjacency[p])==2 for p in vertices),'bounds':[min(p[0]for p in vertices),min(p[1]for p in vertices),max(p[0]for p in vertices),max(p[1]for p in vertices)],'sourceContourNotSemanticStrand':True})
 return groups,membership

def extract(rgb,mask,scales=(2,4,8)):
 if tuple(sorted(set(scales)))!=tuple(scales):raise ValueError('strictly increasing scales required')
 colour,lo,hi=colour_intervals(rgb);x=axis_evidence(lo,hi,mask,scales,1);y=axis_evidence(lo,hi,mask,scales,0);ridgeX=thin_ridges(lo,hi,mask,1);ridgeY=thin_ridges(lo,hi,mask,0)
 coarse,nc=barrier_components(mask,x['persistent'],y['persistent']);fine,nf=barrier_components(mask,x['fine']|x['persistent'],y['fine']|y['persistent'])
 # Fine partition must refine, never merge, coarse source regions.
 relations=defaultdict(set)
 for f,c in zip(fine[mask],coarse[mask]):relations[int(f)].add(int(c))
 assert all(len(v)==1 for v in relations.values())
 cg,cm=edge_components(x['persistent'],y['persistent']);fg,fm=edge_components(x['fine']|x['persistent'],y['fine']|y['persistent']);ancestry=defaultdict(set)
 for edge,parent in cm.items():ancestry[fm[edge]].add(parent)
 key=source_key(rgb,mask,scales)
 return {'x':x,'y':y,'thinRidgeX':ridgeX,'thinRidgeY':ridgeY,'coarse':coarse,'fine':fine,'parents':{k:next(iter(v))for k,v in relations.items()},'contourHierarchy':{'persistent':cg,'fine':fg,'fineToPersistent':{k:sorted(v)for k,v in ancestry.items()},'meaning':'open contour hierarchy/DAG, no inferred gap closing'},'cacheKey':key,'scales':list(scales),'coarseRegions':nc,'fineRegions':nf,'sourceColourSpace':'OKLab from sRGB8','sourceUnchanged':True,'semanticMeaning':'persistent affine-jump / fine edge / thin ridge evidence only; not authored strand identity','colour':colour}

def palette_invariant(rows,sourceRGB,outputRGB):
 """Report equal-source/Q output contradictions without changing an anchor.

Material ID and topology ID are provenance; neither is silently a colour-policy
key. This checker does not create one palette family for every RGB colour.
"""
 groups=defaultdict(list)
 for i,(r,rgb)in enumerate(zip(rows,sourceRGB)):groups[tuple(rgb)+(int(r['Q']),)].append(i)
 contradictions=[]
 for key,indices in groups.items():
  colours={tuple(outputRGB[i])for i in indices}
  if len(colours)>1:contradictions.append({'sourceRGB8':list(key[:3]),'Q':key[3],'cells':[{'x':rows[i]['x'],'y':rows[i]['y'],'materialId':rows[i]['materialId'],'sourceRegionId':rows[i]['sourceRegionId'],'RGB8':outputRGB[i]}for i in indices],'status':'different palette choices require explicit colour-region policy; material ID alone is not evidence'})
 return contradictions
