"""One ordered graph over ALL measured evidence tiers; no smoothing or gap closing.

Confidence changes do not break the identity of an already-connected contour.
Actual degree!=2 vertices remain pins. A source path is not an authored feature,
a visibility owner, a palette family or an independently approved ideal curve.
"""
from collections import defaultdict
import hashlib,json
import numpy as np
def trace_evidence(tiers,sourceKey):
 edges={}
 for tier,axes in tiers.items():
  for axis,bars in axes.items():
   for y,x in np.argwhere(bars):
    key=(axis,int(x),int(y));a,b=((int(x+1),int(y)),(int(x+1),int(y+1))) if axis=='x' else ((int(x),int(y+1)),(int(x+1),int(y+1)))
    if key not in edges:edges[key]={'a':a,'b':b,'tiers':set()}
    edges[key]['tiers'].add(tier)
 adjacency=defaultdict(list)
 for key,e in edges.items():
  adjacency[e['a']].append(key);adjacency[e['b']].append(key)
 for a in adjacency:adjacency[a].sort()
 pins={p for p,inc in adjacency.items() if len(inc)!=2};used=set();paths=[]
 def walk(start,key):
  points=[start];chain=[];at=start
  while key not in used:
   used.add(key);chain.append(key);e=edges[key];at=e['b'] if at==e['a'] else e['a'];points.append(at)
   if at in pins or at==start:break
   options=[k for k in adjacency[at] if k not in used]
   if len(options)!=1:break
   key=options[0]
  status=sorted({t for k in chain for t in edges[k]['tiers']});digest=hashlib.sha256((sourceKey+json.dumps(sorted(chain),separators=(',',':'))).encode()).hexdigest()
  confidence=['uncertain' if 'uncertain' in edges[k]['tiers'] else 'persistent' if 'persistent' in edges[k]['tiers'] else 'fine' for k in chain]
  paths.append({'curveId':digest,'points':points,'edges':chain,'edgeTiers':[sorted(edges[k]['tiers']) for k in chain],'edgeConfidence':confidence,'tiers':status,'closed':points[0]==points[-1],'pinnedStart':points[0] in pins,'pinnedEnd':points[-1] in pins,'edgeCount':len(chain),'uncertain':any(t!='persistent' for t in confidence),'hardFeature':False})
 for p in sorted(pins):
  for key in adjacency[p]:
   if key not in used:walk(p,key)
 for key in sorted(edges):
  if key not in used:walk(min(edges[key]['a'],edges[key]['b']),key)
 assert len(used)==len(edges) and sum(p['edgeCount'] for p in paths)==len(edges)
 return {'sourceKey':sourceKey,'graphCacheKey':hashlib.sha256((sourceKey+'ordered-tier-union70-v1').encode()).hexdigest(),'edges':len(edges),'paths':paths,'pins':[{'point':p,'degree':len(adjacency[p])} for p in sorted(pins)],'gapClosing':False,'newEdges':0,'meaning':'ordered connected source evidence, never automatic semantic regions'}

def continuity_audit(graph):
 paths=graph['paths'];lengths=[p['edgeCount'] for p in paths]
 return {'edges':graph['edges'],'orderedPaths':len(paths),'longestSourceTexelPath':max(lengths,default=0),'medianSourceTexelPath':float(np.median(lengths)) if lengths else 0,'singleEdgePaths':sum(n==1 for n in lengths),'closedPaths':sum(p['closed'] for p in paths),'allPersistentPaths':sum(not p['uncertain'] for p in paths),'uncertainPaths':sum(p['uncertain'] for p in paths),'junctions':sum(p['degree']>=3 for p in graph['pins']),'wholeFeatureBoundaryIdentified':False}
