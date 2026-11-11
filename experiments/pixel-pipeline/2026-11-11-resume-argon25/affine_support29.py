"""Interval-feasible source-background hypothesis, never a semantic decoder.

Six flank samples constrain an affine RGB field under native half-code bounds.
At a centre, only a colour outside ALL feasible fields is a residual witness.
Original RGB is not filtered. Infeasible models and AA ambiguity stay unknown.
"""
from pathlib import Path
import itertools,json
import numpy as np
H=Path(__file__).resolve().parent;G=H/'face29'
XY=np.array([(x,y)for x in [-1,1]for y in [-1,0,1]],float)
P=np.column_stack([XY,np.ones(6)]);A=np.concatenate([P,-P])
COMB=np.array([c for c in itertools.combinations(range(12),3)if abs(np.linalg.det(A[list(c)]))>1e-9])
INV=np.linalg.inv(A[COMB])
def intervals(samples):
 # channels are independent interval constraints; the six sample coordinates
 # are fixed geometry. Enumerate vertices of a bounded3-variable polytope.
 y=samples.transpose(0,2,1);b=np.concatenate([y+.5,-y+.5],axis=2)
 rhs=b[:,:,COMB];beta=np.einsum('kij,nckj->ncki',INV,rhs)
 feasible=np.ones(beta.shape[:3],bool)
 for row in range(12):feasible &= np.einsum('ncki,i->nck',beta,A[row])<=b[:,:,row,None]+1e-8
 low=np.min(np.where(feasible,beta[...,2],np.inf),axis=2);high=np.max(np.where(feasible,beta[...,2],-np.inf),axis=2)
 return low,high,np.all(np.any(feasible,axis=2),axis=1)
def probe(rgb,mask,positions,radius=1,direction=(1,0),batch=128):
 n=len(positions);out=np.full((n,7),np.nan);d=np.array(direction);t=np.array([-d[1],d[0]])
 offsets=(XY[:,0,None]*d+XY[:,1,None]*t).astype(int)*radius;hh,ww=mask.shape
 for start in range(0,n,batch):
  at=np.asarray(positions[start:start+batch],int);samples=at[:,None,:]+offsets[None,:,:]
  good=(samples[...,0]>=0)&(samples[...,1]>=0)&(samples[...,0]<ww)&(samples[...,1]<hh)
  sx=np.clip(samples[...,0],0,ww-1);sy=np.clip(samples[...,1],0,hh-1)
  valid=np.all(good&mask[sy,sx],axis=1)&mask[at[:,1],at[:,0]]
  low,high,feasible=intervals(rgb[sy,sx].astype(float));valid &=feasible
  centre=rgb[at[:,1],at[:,0]].astype(float);dark=np.max(low-centre-.5,axis=1);bright=np.max(centre-.5-high,axis=1)
  out[start:start+len(at),0]=valid;out[start:start+len(at),1]=np.where(valid,np.maximum(dark,bright),np.nan)
  out[start:start+len(at),2:5]=np.where(valid[:,None],low,np.nan);out[start:start+len(at),5]=np.where(valid,dark,np.nan);out[start:start+len(at),6]=np.where(valid,bright,np.nan)
 return out
def component(mask,seed):
 x,y=seed;out=np.zeros_like(mask,bool)
 if not mask[y,x]:return out,False
 queue=[(x,y)];out[y,x]=True;h,w=mask.shape
 for x,y in queue:
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   a,b=x+dx,y+dy
   if 0<=a<w and 0<=b<h and mask[b,a]and not out[b,a]:out[b,a]=True;queue.append((a,b))
 return out,not(out[0].any()or out[-1].any()or out[:,0].any()or out[:,-1].any())
def trace_native(rgb,mask,seed,radius,budget=65536):
 cache={};pending={tuple(seed)};support=set();frontier={tuple(seed)};boundary=False;limited=False
 def evaluate(points):
  missing=[p for p in points if p not in cache]
  if len(cache)+len(missing)>budget:return False
  if missing:
   a=np.asarray(missing);valid=np.zeros(len(a),bool);positive=np.zeros(len(a),bool)
   for d in [(1,0),(0,1),(1,1),(1,-1)]:
    out=probe(rgb,mask,a,radius,d);valid |=out[:,0]>0;positive |=out[:,1]>1e-7
   cache.update((p,(bool(v),bool(z)))for p,v,z in zip(missing,valid,positive))
  return True
 while frontier:
  if not evaluate(sorted(frontier)):limited=True;break
  accepted={p for p in frontier if cache[p][1]};support |=accepted;frontier=set()
  for x,y in accepted:
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    p=(x+dx,y+dy)
    if not(0<=p[0]<mask.shape[1]and 0<=p[1]<mask.shape[0])or not mask[p[1],p[0]]:boundary=True
    elif p not in cache:frontier.add(p)
 boundary_nodes=set()
 for x,y in support:
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
   p=(x+dx,y+dy)
   if p not in support and p in cache:boundary_nodes.add(p)
 unknown=sum(not cache[p][0]for p in boundary_nodes)
 return {'seed':seed,'radius':radius,'componentCells':len(support),'nodesEvaluated':len(cache),'budgetExceeded':limited,'touchesActualUVDomainBoundary':boundary,'boundaryNeighbours':len(boundary_nodes),'boundaryWithNoFeasibleBackgroundModel':unknown,'wholePigmentOrAARegionConfirmed':False,'supportXY':sorted(support),'unknownBoundaryXY':sorted(p for p in boundary_nodes if not cache[p][0])}
def main():
 data=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=data['rgba'][...,:3];mask=data['mask']&(data['rgba'][...,3]==255)
 # Source diagnostic bounds from the existing weak-stroke counterexample.
 box=(310,620,425,710);x0,y0,x1,y1=box;yy,xx=np.mgrid[y0:y1,x0:x1];pos=np.column_stack([xx.ravel(),yy.ravel()]);rows=[];fields={}
 for radius in [1,2,4]:
  merged=np.full(len(pos),-np.inf);valid=np.zeros(len(pos),bool)
  for direction in [(1,0),(0,1),(1,1),(1,-1)]:
   z=probe(rgb,mask,pos,radius,direction);ok=z[:,0]>0;valid |=ok;merged[ok]=np.maximum(merged[ok],z[ok,1]);print(json.dumps({'radius':radius,'axis':direction,'valid':int(ok.sum()),'residual':int(np.count_nonzero(z[:,1]>1e-7))}),flush=True)
  residual=(merged>1e-7).reshape(y1-y0,x1-x0);island,closed=component(residual,(382-x0,704-y0));fields['residual'+str(radius)]=residual;fields['feasible'+str(radius)]=valid.reshape(residual.shape)
  rows.append({'radius':radius,'positiveCells':int(residual.sum()),'seedComponentCells':int(island.sum()),'closedInsideDiagnosticBox':closed,'seedPositive':bool(residual[704-y0,382-x0])})
 np.savez_compressed(G/'AFFINE_SUPPORT29.npz',**fields)
 native=[trace_native(rgb,mask,(382,704),r)for r in [2,4]]
 (G/'AFFINE_NATIVE_COMPONENT29.json').write_text(json.dumps(native,indent=2),encoding='utf-8',newline='\n')
 report={'sourceBox':box,'testsAtNativeRadii':rows,'rule':'No fixed colour threshold or palette bins; reject affine background only when no interval-feasible field fits centre. Positive residual is NOT proof of pigment vs smooth curvature.','classification':'hypothesis/diagnostic only; no source regions approved or filled','GPUCalls':0,'curvePriorStillNeeded':'A smooth nonlinear source colour gradient can reject an affine model. Residual closure alone is insufficient for source-feature semantics; keep original28 evidence and source RGB.'}
 (G/'AFFINE_SUPPORT29.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n')
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()
