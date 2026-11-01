"""Fixed source-reference arclength metrics; never use fewer output edges as truth."""
import numpy as np
from shared_boundary63 import trace,nearest
def iso_segments(triangles,threshold=.5):
 result=[]
 for t in triangles:
  hits=[]
  for a,b in zip(t,np.roll(t,-1,axis=0)):
   if (a[2]>=threshold)!=(b[2]>=threshold):hits.append(a[:2]+(b[:2]-a[:2])*((threshold-a[2])/(b[2]-a[2])))
  if len(hits)==2 and np.linalg.norm(hits[1]-hits[0])>1e-12:result.append(hits)
 return np.asarray(result,float).reshape((-1,2,2))
def fixed_reference(q,mask,reference):
 edges,paths=trace(q,mask);raw=np.array([[e['a'],e['b']] for e in edges],float);spans=[]
 for p in paths:
  points=np.array(p['points'],float);runs=[]
  for a,b in zip(points[:-1],points[1:]):
   d=b-a;d/=np.linalg.norm(d)
   if runs and np.all(d==runs[-1][0]):runs[-1][2]=b
   else:runs.append([d,a,b])
  spans.extend([[a[1],b[2]] for a,b in zip(runs[:-1],runs[1:])]);spans.extend([[r[1],r[2]] for r in runs] if len(runs)==1 else [])
 def poly(segments):return np.concatenate([np.vstack([a,b,[np.nan,np.nan]]) for a,b in segments])
 mid=reference.mean(1);d=reference[:,1]-reference[:,0];L=np.linalg.norm(d,axis=1);unit=d/L[:,None];distance,_=nearest(poly(raw),mid);_,direction=nearest(poly(spans),mid)
 return {'referenceLength':float(L.sum()),'referenceSegments':len(L),'positionRMSE':float(np.sqrt(np.sum(L*distance**2)/L.sum())),'positionMaxAtReferenceMidpoints':float(distance.max()),'spanTangentCost':float(np.sum(L*(1-(unit*direction).sum(1)**2))/L.sum()),'gridTurnAbsRadians':float(sum(p['metrics']['turnAbsRadians'] for p in paths)),'meaning':'same reference arclength/midpoints for both masks, with adjacent-run spans for tangent; not analytic curvature or a full-domain error guarantee'}

def reference_gate(metrics):
 reasons=[]
 for row in metrics:
  for key in ['positionRMSE','positionMaxAtReferenceMidpoints','spanTangentCost']:
   if row['candidate'][key]>row['before'][key]+1e-12:reasons.append({'diagonal':row['diagonal'],'metric':key,'before':row['before'][key],'candidate':row['candidate'][key]})
 return {'passesNonRegression':not reasons,'rejections':reasons,'limits':'A metric pass would still not establish complete feature/art/temporal acceptance'}
