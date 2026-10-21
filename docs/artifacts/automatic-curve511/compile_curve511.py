"""Automatic reference-view vector boundary compilation; no raster source mask.

Fraction arithmetic is preparation only. Runtime consumes persistent anchors.
Semantic part index and source binding are explicit adapter inputs, never inferred.
"""
from pathlib import Path
from fractions import Fraction as Q
from collections import defaultdict
import argparse,struct,json,math,time,hashlib,traceback
import numpy as np

def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def sub(a,b):return a[0]-b[0],a[1]-b[1]
def point(a,b,t):return Q(a[0])+t*(b[0]-a[0]),Q(a[1])+t*(b[1]-a[1])
def area(p):return sum(cross(a,b)for a,b in zip(p,p[1:]+p[:1]))/2
def parameters(a,b,c,d):
 r,s=sub(b,a),sub(d,c);den=cross(r,s);q=sub(c,a)
 if den:
  t,u=Q(cross(q,s),den),Q(cross(q,r),den)
  return [(t,u)]if 0<=t<=1 and 0<=u<=1 else []
 if cross(q,r):return []
 axis=0 if abs(r[0])>=abs(r[1])else 1
 if not r[axis]:return []
 out=[]
 for p in [a,b,c,d]:
  t=Q(p[axis]-a[axis],r[axis]);other=0 if abs(s[0])>=abs(s[1])else 1
  if not s[other]:continue
  u=Q(p[other]-c[other],s[other])
  if 0<=t<=1 and 0<=u<=1:out.append((t,u))
 return out

def vector_union(triangles,progress=lambda **x:None):
 # Exact conversion of binary input coordinates to one integer lattice. This
 # lattice is arithmetic representation, not image/coverage quantization.
 denominator=max(float(x).as_integer_ratio()[1]for t in triangles for p in t for x in p)
 def integer(p):return tuple(n*(denominator//d)for n,d in [float(x).as_integer_ratio()for x in p])
 counts=defaultdict(int)
 for row in triangles:
  t=[integer(p)for p in row];signed=cross(sub(t[1],t[0]),sub(t[2],t[0]))
  if not signed:continue
  if signed<0:t.reverse()
  for a,b in zip(t,t[1:]+t[:1]):
   if a==b:continue
   k=(a,b)if a<b else(b,a);counts[k]+=1 if a<b else-1
 edges=[(a,b,w)if w>0 else(b,a,-w)for(a,b),w in sorted(counts.items())if w]
 ef=np.array([[np.array(a,dtype=float)/denominator,np.array(b,dtype=float)/denominator]for a,b,w in edges]);lo=ef.min(1);hi=ef.max(1)
 splits=[{Q(0),Q(1)}for _ in edges];pairs=hits=0
 for i,(a,b,w)in enumerate(edges):
  js=np.flatnonzero((np.maximum(lo[i],lo[i+1:])<=np.minimum(hi[i],hi[i+1:])).all(1))+i+1
  for j in js:
   pairs+=1
   for t,u in parameters(a,b,edges[j][0],edges[j][1]):splits[i].add(t);splits[j].add(u);hits+=1
  if i%500==0:progress(stage='arrangement',edge=i,edges=len(edges),pairs=pairs)
 fragments=defaultdict(int)
 for(a,b,w),ts in zip(edges,splits):
  ts=sorted(ts)
  for t,u in zip(ts,ts[1:]):
   p,q=point(a,b,t),point(a,b,u)
   if p==q:continue
   key=(p,q)if p<q else(q,p);fragments[key]+=w if p<q else-w
 # Geometry bins only narrow exact winding queries; they are not source alpha.
 bins=[defaultdict(list),defaultdict(list)]
 for i,(a,b,w)in enumerate(edges):
  for axis in [0,1]:
   for k in range(min(a[axis],b[axis])//denominator,max(a[axis],b[axis])//denominator+1):bins[axis][k].append(i)
 def winding(p,rotated=False):
  x,y=(-p[1],p[0])if rotated else p
  d=math.lcm(x.denominator,y.denominator);px=x.numerator*(d//x.denominator);py=y.numerator*(d//y.denominator);value=0
  for i in bins[0 if rotated else 1][py//d//denominator]:
   a,b,w=edges[i];a,b=((-a[1],a[0]),(-b[1],b[0]))if rotated else(a,b)
   orient=(b[0]-a[0])*(py-a[1]*d)-(b[1]-a[1])*(px-a[0]*d)
   if a[1]*d<=py<b[1]*d and orient>0:value+=w
   elif b[1]*d<=py<a[1]*d and orient<0:value-=w
  return value
 boundary=[]
 for i,((a,b),w)in enumerate(fragments.items()):
  if not w:continue
  if w<0:a,b,w=b,a,-w
  delta=sub(b,a);rotated=abs(delta[0])>abs(delta[1]);sign=1 if(delta[0]if rotated else delta[1])>0 else-1
  p=((a[0]+b[0])/2,(a[1]+b[1])/2);right=winding(p,rotated);minus=right+sign*w
  left,right=(minus,right)if sign>0 else(right,minus)
  if min(left,right)<0:raise RuntimeError('Negative triangle-union winding')
  if(left>0)!=(right>0):boundary.append((a,b)if left>0 else(b,a))
  if i%1000==0:progress(stage='classify',fragment=i,fragments=len(fragments),boundary=len(boundary))
 outgoing=defaultdict(set)
 for a,b in boundary:outgoing[a].add(b)
 loops=[];remaining=len(boundary)
 while outgoing:
  start=min(outgoing);at=start;prior=None;ring=[]
  while True:
   if at not in outgoing or not outgoing[at]:raise RuntimeError('Open vector-union boundary')
   ring.append(at);targets=outgoing[at]
   if prior is None:to=min(targets)
   else:
    v=sub(at,prior)
    def turn(q):
     u=sub(q,at);return math.atan2(float(cross(v,u)),float(v[0]*u[0]+v[1]*u[1])),q
    to=max(targets,key=turn)
   targets.remove(to)
   if not targets:del outgoing[at]
   remaining-=1
   if remaining<0:raise RuntimeError('Boundary traversal cycle')
   prior,at=at,to
   if at==start:break
  if len(ring)>=3 and area(ring):loops.append([(x/denominator,y/denominator)for x,y in ring])
 if remaining:raise RuntimeError('Unconsumed boundary')
 return loops,{'weightedEdges':len(edges),'bboxPairs':pairs,'intersectionRecords':hits,'splitFragments':len(fragments),'boundarySegments':len(boundary)}

def inside(p,ring):
 value=0
 for a,b in zip(ring,ring[1:]+ring[:1]):
  c=cross(sub(b,a),sub(p,a))
  if a[1]<=p[1]<b[1]and c>0:value+=1
  elif b[1]<=p[1]<a[1]and c<0:value-=1
 return value!=0

def simplify(ring,error):
 p=np.array(ring,float);n=len(p);split=int(np.argmax(((p-p[0])**2).sum(1)));keep={0,split,n};p=np.concatenate([p,p[:1]])
 def run(a,b):
  if b<=a+1:return
  d=p[b]-p[a];den=float(d@d);v=p[a+1:b]-p[a];t=np.clip(v@d/den,0,1)if den else np.zeros(len(v));e=((v-t[:,None]*d)**2).sum(1);j=int(np.argmax(e))
  if e[j]>error*error:k=a+1+j;keep.add(k);run(a,k);run(k,b)
 run(0,split);run(split,n)
 return [i for i in sorted(keep)if i<n]

def regularize(loops,coefficient,error):
 sizes=[abs(area(r))for r in loops];perimeters=[sum(math.hypot(float(a[0]-b[0]),float(a[1]-b[1]))for a,b in zip(r,r[1:]+r[:1]))for r in loops];parents=[]
 for i,r in enumerate(loops):
  p=((r[0][0]+r[1][0])/2,(r[0][1]+r[1][1])/2);c=[j for j,s in enumerate(loops)if sizes[j]>sizes[i]and inside(p,s)];parents.append(min(c,key=lambda j:sizes[j])if c else-1)
 children=[[]for _ in loops]
 for i,j in enumerate(parents):
  if j>=0:children[j].append(i)
 choices={}
 def cost(i,parent):
  zone=float(sizes[i]-sum(sizes[j]for j in children[i]));source=int(area(loops[i])>0);options=[]
  for label in [0,1]:options.append(zone*(label!=source)+coefficient*perimeters[i]*(label!=parent)+sum(cost(j,label)for j in children[i]))
  label=0 if options[0]<options[1]else 1 if options[1]<options[0]else source;choices[i,parent]=label;return options[label]
 for i,p in enumerate(parents):
  if p<0:cost(i,0)
 records=[];decisions=[]
 def choose(i,parent):
  label=choices[i,parent];active=label!=parent;r=loops[i]
  if active:
   if(area(r)>0)!=(label==1):r=list(reversed(r))
   keep=simplify(r,error);s=[r[k]for k in keep]
   if len(s)>=3 and area(s):records.append({'source':r,'keep':set(keep),'ring':i})
   else:active=False
  decisions.append({'ring':i,'parent':parents[i],'sourceArea':float(area(loops[i])),'perimeter':perimeters[i],'selectedInside':label,'retainedBoundary':active})
  for j in children[i]:choose(j,label)
 for i,p in enumerate(parents):
  if p<0:choose(i,0)
 # A closed-region fit may not cross itself or another retained ring. Restore
 # only source knots on offending chords. This has no pixel/strand/gap rule.
 repairs=[]
 for iteration in range(sum(len(r['source'])for r in records)+1):
  segments=[]
  for ri,record in enumerate(records):
   ids=sorted(record['keep']);segments.extend((ri,a,b,record['source'][a],record['source'][b])for a,b in zip(ids,ids[1:]+ids[:1]))
  failed=None
  for i,s in enumerate(segments):
   a,b=s[-2:]
   for t in segments[i+1:]:
    c,d=t[-2:]
    if a in(c,d)or b in(c,d):continue
    if any(0<x<1 and 0<y<1 for x,y in parameters(a,b,c,d)):failed=(s,t);break
   if failed:break
  if failed is None:
   kept=[[r['source'][i]for i in sorted(r['keep'])]for r in records]
   return kept,decisions,repairs
  changed=False;repair={'iteration':iteration,'chords':[]}
  for ri,a,b,p,q in failed:
   record=records[ri];source=record['source'];n=len(source);between=[];at=(a+1)%n
   while at!=b:between.append(at);at=(at+1)%n
   if not between:continue
   pf,qf=np.array(p,float),np.array(q,float);d=qf-pf;den=float(d@d)
   def distance(i):
    v=np.array(source[i],float)-pf;t=min(1,max(0,float(v@d)/den))if den else 0;return float((v-t*d)@(v-t*d))
   chosen=max(between,key=lambda i:(distance(i),-i));record['keep'].add(chosen);changed=True
   repair['chords'].append({'ring':record['ring'],'sourceFrom':a,'sourceTo':b,'restoredSourceKnot':chosen})
  if not changed:raise RuntimeError('Original closed boundary has a proper crossing')
  repairs.append(repair)
 raise RuntimeError('Closed-region fit refinement did not terminate')

def read_mesh(path,part):
 raw=path.read_bytes();off=84;parts=[]
 for r in range(struct.unpack_from('<i',raw)[0]):
  nv,ns=struct.unpack_from('<2i',raw,off);off+=8;v=np.frombuffer(raw,'<f4',offset=off,count=nv*8).reshape(nv,8).copy();off+=nv*32;indices=[]
  for sm in range(ns):
   n=struct.unpack_from('<i',raw,off)[0];off+=4;indices.append(np.frombuffer(raw,'<i4',offset=off,count=n).reshape(-1,3).copy());off+=n*4
  parts.append((v,indices))
 assert off==len(raw);return parts[part]

def anchor(p,v,indices):
 xy=np.array([float(x)for x in p]);best=None
 for sm,ix in enumerate(indices):
  xytri=v[ix,5:7].astype(float);lo=np.nextafter(xytri.min(1),-np.inf);hi=np.nextafter(xytri.max(1),np.inf)
  for primitive in np.flatnonzero(((xy>=lo)&(xy<=hi)).all(1)):
   ids=ix[primitive];a,b,c=[tuple(Q(float(x))for x in v[n,5:7])for n in ids];den=cross(sub(b,a),sub(c,a))
   if not den:continue
   bv=cross(sub(p,a),sub(c,a))/den;bw=cross(sub(b,a),sub(p,a))/den;weights=[1-bv-bw,bv,bw]
   if min(weights)<0:continue
   depth=sum(float(w)*float(v[n,7])for w,n in zip(weights,ids));key=(depth,sm,int(primitive))
   if best is None or key<best[0]:best=key,sm,int(primitive),ids,[float(w)for w in weights]
 if best is None:raise RuntimeError('Boundary knot has no exact original triangle anchor')
 _,sm,primitive,ids,bary=best;xy2=sum(w*v[n,5:7].astype(float)for w,n in zip(bary,ids));error=float(np.max(abs(xy2-xy)))
 if error>.0005:raise RuntimeError('Anchor projection numeric error')
 return {'submesh':sm,'primitive':primitive,'vertices':list(map(int,ids)),'barycentric':bary,'referenceXY':list(map(float,p)),'referenceDepth':best[0][0],'reprojectionError':error}

def write_asset(report,path):
 binding=report['binding'];controls=report['controls']
 with Path(path).open('xb')as f:
  def write(fmt,*x):f.write(struct.pack('<'+fmt,*x))
  write('4iQ',511,2,binding['vertices'],binding['submeshes'],int(binding['bindSignature'],16))
  write('4id',len(controls),report['sourceRings'],report['sourceBoundaryPoints'],len(report['topologyRepairs']),report['preprocessingSeconds'])
  for ring in controls:
   write('i',len(ring))
   for c in ring:write('5i3d',c['submesh'],c['primitive'],*c['vertices'],*c['barycentric'])

def fixtures():
 def rect(x,y,xx,yy):return [[(x,y),(xx,y),(xx,yy)],[(x,y),(xx,yy),(x,yy)]]
 cases=[('duplicate',rect(0,0,2,2)*2,4),('overlap',rect(0,0,2,2)+rect(1,0,3,2),6),('touch',rect(0,0,2,2)+rect(2,2,4,4),8),('hole',rect(0,0,3,1)+rect(0,2,3,3)+rect(0,1,1,2)+rect(2,1,3,2),8)]
 for name,t,expected in cases:
  loops,_=vector_union(t);actual=sum(area(p)for p in loops)
  if actual!=expected:raise RuntimeError('Union fixture '+name+' '+str(actual))

def main():
 a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--binding',type=Path,required=True);a.add_argument('--part',type=int,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
 if args.output.exists():raise RuntimeError('Preserve existing compilation')
 args.output.mkdir(parents=True);start=time.perf_counter()
 def progress(**d):d['elapsedSeconds']=time.perf_counter()-start;(args.output/'progress.json').write_text(json.dumps(d))
 try:
  fixtures();progress(stage='fixtures passed')
  binding=json.loads(args.binding.read_text());v,ix=read_mesh(args.input,args.part);assert len(v)==binding['vertices']and len(ix)==binding['submeshes']
  triangles=[v[row,5:7].astype(float).tolist()for ids in ix for row in ids];raw,counts=vector_union(triangles,progress);extracted=time.perf_counter();progress(stage='closed vector regions',rings=len(raw),**counts)
  (args.output/'RAW_VECTOR_BOUNDARY511.json').write_text(json.dumps({'rings':[[[str(x),str(y)]for x,y in r]for r in raw],'counts':counts,'extractionSeconds':extracted-start}))
  curves,decisions,repairs=regularize(raw,.14,.1875);designed=time.perf_counter();controls=[]
  for i,r in enumerate(curves):controls.append([anchor(p,v,ix)for p in r]);progress(stage='persistent anchors',ring=i+1,rings=len(curves))
  report={'status':'COMPILED_NOT_RENDER_VALIDATED','input':str(args.input.resolve()),'inputSHA256':hashlib.sha256(args.input.read_bytes()).hexdigest(),'binding':binding,'part':args.part,'curveRepresentation':'closed piecewise-linear, source triangle/barycentric persistent anchors','sourceRings':len(raw),'sourceBoundaryPoints':sum(map(len,raw)),'curveRings':len(curves),'controlPoints':sum(map(len,curves)),'counts':counts,'regionDecisions':decisions,'topologyRepairs':repairs,'controls':controls,'preprocessingSeconds':time.perf_counter()-start,'preprocessingStagesSeconds':{'vectorExtraction':extracted-start,'regionDesign':designed-extracted,'anchorBinding':time.perf_counter()-designed},'profile':{'curveErrorLogicalCells':.1875,'areaPerimeterCost':.14},'semanticIntentInferred':False,'newPackages':False}
  (args.output/'CURVES511.json').write_text(json.dumps(report,indent=2)+'\n')
  write_asset(report,args.output/'HeadCurve511.bytes')
  progress(stage='COMPLETED',**{k:report[k]for k in ['sourceRings','curveRings','controlPoints','preprocessingSeconds']});print(json.dumps({k:report[k]for k in ['status','sourceRings','sourceBoundaryPoints','curveRings','controlPoints','preprocessingSeconds']}))
 except Exception:
  progress(stage='FAILED',error=traceback.format_exc());raise
if __name__=='__main__':main()
