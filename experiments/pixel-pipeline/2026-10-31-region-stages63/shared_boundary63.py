"""Shared categorical boundary graph and source-reference metrics, not smoothing.

Adapted to arbitrary labels from44's edge_graph/span_tangent_error. Each dual edge
has exactly one two-sided record. Source colour bins never become feature locks.
"""
from collections import defaultdict
import math
import numpy as np

def trace(labels,mask):
 h,w=mask.shape;edges=[];incident=defaultdict(set)
 for y,x in np.argwhere(mask):
  for dx,dy in [(1,0),(0,1)]:
   xx,yy=int(x+dx),int(y+dy)
   if xx>=w or yy>=h or not mask[yy,xx]or labels[y,x]==labels[yy,xx]:continue
   left,right=int(labels[y,x]),int(labels[yy,xx]);pair=tuple(sorted([left,right]))
   a,b=((int(x+1),int(y)),(int(x+1),int(y+1)))if dx else((int(x),int(y+1)),(int(x+1),int(y+1)))
   if (dx and left!=pair[0])or(dy and right!=pair[0]):a,b=b,a
   for p in [a,b]:incident[p].update(pair)
   edges.append({'a':a,'b':b,'pair':pair,'cells':[(int(x),int(y)),(xx,yy)]})
 paths=[];used=set()
 for pair in sorted({e['pair']for e in edges}):
  group=[i for i,e in enumerate(edges)if e['pair']==pair];outgoing=defaultdict(list);incoming=defaultdict(list)
  for i in group:outgoing[edges[i]['a']].append(i);incoming[edges[i]['b']].append(i)
  pins={p for p in set(outgoing)|set(incoming)if len(outgoing[p])!=1 or len(incoming[p])!=1 or len(incident[p])>=3}
  for start in sorted(group,key=lambda i:(edges[i]['a']not in pins,edges[i]['a'],edges[i]['b'])):
   if start in used:continue
   chain=[];i=start
   while i not in used:
    used.add(i);chain.append(i);p=edges[i]['b']
    if p==edges[start]['a']or p in pins:break
    options=[j for j in outgoing[p]if j not in used]
    if len(options)!=1:break
    i=options[0]
   points=[edges[chain[0]]['a']]+[edges[i]['b']for i in chain]
   paths.append({'pair':list(pair),'points':[list(p)for p in points],'edgeIndices':chain,'closed':points[0]==points[-1],'junctionStart':len(incident[points[0]])>=3,'junctionEnd':len(incident[points[-1]])>=3,'metrics':path_metrics(points)})
 assert len(used)==len(edges)and sum(len(p['edgeIndices'])for p in paths)==len(edges)
 return edges,paths

def path_metrics(points):
 p=np.array(points,float);d=np.diff(p,axis=0);d=d[np.linalg.norm(d,axis=1)>1e-12]
 lengths=np.linalg.norm(d,axis=1)
 if not len(d):return {'length':0.,'turnAbsRadians':0.,'turns':0,'reverseTurns':0,'runs':[]}
 unit=d/lengths[:,None];angles=np.arctan2(unit[:-1,0]*unit[1:,1]-unit[:-1,1]*unit[1:,0],(unit[:-1]*unit[1:]).sum(axis=1));runs=[]
 for v,L in zip(unit,lengths):
  direction=tuple(v.tolist())
  if runs and direction==tuple(runs[-1]['direction']):runs[-1]['length']+=float(L)
  else:runs.append({'direction':list(direction),'length':float(L)})
 chord=float(np.linalg.norm(p[-1]-p[0]))
 return {'length':float(lengths.sum()),'chord':chord,'lengthOverChord':float(lengths.sum()/chord)if chord>1e-12 else None,'turnAbsRadians':float(abs(angles).sum()),'turns':int((abs(angles)>1e-12).sum()),'reverseTurns':int((abs(angles)>math.pi/2+1e-12).sum()),'runs':runs,'qualityWithoutSourceReference':'unknown'}

def nearest(poly,points):
 p=np.asarray(poly,float);a=p[:-1];d=p[1:]-a;valid=np.isfinite(a).all(axis=1)&np.isfinite(d).all(axis=1)&((d*d).sum(axis=1)>1e-24);a=a[valid];d=d[valid];ds=(d*d).sum(axis=1)
 q=np.asarray(points,float);t=np.clip(((q[:,None]-a)*d).sum(axis=2)/ds,0,1);delta=q[:,None]-(a+t[:,:,None]*d);sq=(delta*delta).sum(axis=2);i=sq.argmin(axis=1)
 return np.sqrt(sq[np.arange(len(q)),i]),d[i]/np.sqrt(ds[i,None])

def reference_metrics(path,reference):
 """44 metric on fixed reference arclength; no output-edge denominator gaming."""
 p=np.array(path,float);r=np.array(reference,float);runs=[]
 for a,b in zip(p[:-1],p[1:]):
  d=b-a
  if np.linalg.norm(d)<1e-12:continue
  direction=tuple(np.sign(d).astype(int))
  if runs and runs[-1][0]==direction:runs[-1][2]=b
  else:runs.append([direction,a.copy(),b.copy()])
 spans=[(a[1],b[2])for a,b in zip(runs[:-1],runs[1:])]
 if not spans:spans=[(a[1],a[2])for a in runs]
 poly=np.concatenate([np.vstack([a,b,[np.nan,np.nan]])for a,b in spans]);delta=np.diff(r,axis=0);L=np.linalg.norm(delta,axis=1);good=L>1e-12;t=delta[good]/L[good,None];mid=(r[:-1]+r[1:])[good]/2;_,rt=nearest(poly,mid)
 # The squared tangent cost cannot detect an exactly reversed parallel run.
 # Measure traversal separately on the SAME reference, not sorted run lengths.
 a=r[:-1][good];segments=delta[good];lengths=L[good];cum=np.r_[0.,np.cumsum(lengths)]
 along=np.clip(((p[:,None]-a)*segments).sum(axis=2)/(lengths**2),0,1);distance=((p[:,None]-(a+along[:,:,None]*segments))**2).sum(axis=2);at=distance.argmin(axis=1);s=cum[at]+along[np.arange(len(p)),at]*lengths[at]
 orientation=1 if s[-1]>=s[0]else-1;progress=np.diff(s)*orientation;back=np.maximum(-progress,0)
 return {'fixedReferenceArclengthTangent':float(np.sum(L[good]*(1-(t*rt).sum(axis=1)**2))/L[good].sum()),'hausdorffSampled':float(max(nearest(p,r)[0].max(),nearest(r,p)[0].max())),'sourceArclengthBacktracking':float(back.sum()),'sourceArclengthReversalSteps':int((back>1e-12).sum()),'referenceLength':float(L.sum()),'sampling':'saved fitted guide points; nearest-reference projection may be ambiguous at self-intersections, not an analytic curvature guarantee'}

def separate_layers(source_id,rows,range_ids,feature_edges=()):
 """Smallest premise correction: range IDs are soft colour faces, not features.

No palette pooling, region merge, geometry inference or RGB output is performed.
Only supplied source-feature edge witnesses can create feature locks.
"""
 feature_edges=set(tuple(sorted(e))for e in feature_edges)
 return {'sourceId':source_id,'cells':[{'x':r['x'],'y':r['y'],'featureDomain':'caller-supplied visible hair domain','childFeatureId':None,'colourRangeRegionId':rid,'surfaceStructureId':[r['materialId'],r['sourceStructureId']],'occlusionOwner':r['occlusionOwnerBufferUnchanged'],'shadeQ':r['Q'],'sourceUVNativeTexel':r['nativeTexel'],'nativeColourRangeIsHardFeature':False}for r,rid in zip(rows,range_ids)],'sourceFeatureEdgeWitnesses':[list(e)for e in sorted(feature_edges)],'unresolved':'child feature masks/curves are not present in frozen frame60. Sparse contrast witnesses do not define their full footprints.','colourCurveCorrectionApplied':False,'shadeCurveCorrectionApplied':False,'paletteSharingCountsAsSpatialCorrection':False}
