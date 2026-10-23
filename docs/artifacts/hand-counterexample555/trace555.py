from pathlib import Path
import struct,json,csv
import numpy as np
O=Path(__file__).resolve().parent
def read_curves(path):
 b=path.read_bytes();pos=0;out=[]
 for k in range(2):
  n=struct.unpack_from('<i',b,pos)[0];pos+=4;r=[]
  for j in range(n):
   m=struct.unpack_from('<i',b,pos)[0];pos+=4;r.append(np.frombuffer(b,'<f4',count=2*m,offset=pos).reshape(m,2).copy());pos+=8*m
  out.append(r)
 return out
def extrema(rings):
 for ring,rr in enumerate(rings):
  r=rr.astype(float)
  if np.sum(r[:,0]*np.roll(r[:,1],-1)-r[:,1]*np.roll(r[:,0],-1))/2<=0:continue
  for i,p in enumerate(r):
   a,b=r[(i-1)%len(r)],r[(i+1)%len(r)];v=p-a;w=b-p
   if v[0]*w[1]-v[1]*w[0]<=0:continue
   for axis in range(2):
    for sign in [-1,1]:
     q,u,w=p[axis]*sign,a[axis]*sign,b[axis]*sign
     if q<=u and q<=w and(q<u or q<w):yield {'ring':ring,'index':i,'point':p.tolist(),'axis':axis,'sign':sign}
def mapped(e):
 p=e['point'];axis=e['axis'];normal=int(np.floor(p[axis]+.5))-(e['sign']<0);tangent=int(np.floor(p[1-axis]))
 for t in [tangent-1,tangent]if p[1-axis]==tangent else[tangent]:yield(normal,t)if axis==0 else(t,normal)
def key(e):return(tuple(e['point']),e['axis'],e['sign'])
rows=[]
for frame,path,target in [(33,'Actual553/033_ON_CURVES.bin',(229,90)),(49,'Cases553/049_ON_CURVES.bin',(232,88))]:
 source,fit=read_curves(O/path);a=list(extrema(source));b=list(extrema(fit));reference={key(e)for e in a}
 origin=[e for e in a if target in mapped(e)];current=[dict(e,referenceRetained=key(e)in reference)for e in b if target in mapped(e)]
 row={'frame':frame,'target':target,'sourceExtremaMappingToTarget':origin,'fitExtremaMappingToTarget':current,'sourceNearbyMappedExtrema':[dict(e,mapped=list(mapped(e)))for e in a if any(abs(x-target[0])<=1 and abs(y-target[1])<=1 for x,y in mapped(e))],'existing554TargetAccepted':any(line.startswith(f'{target[0]},{target[1]},')for line in (O/f'hand{frame}_END_CERT554.txt').read_text().splitlines())}
 rows.append(row)
summary=[]
with(O/'Minimal555/COMPARISON555.csv').open()as f:
 for r in csv.DictReader(f):summary.append(r)
receipt={'kind':'same input cause isolation; no product edits, no Unity render, no554 selection rerun','comparison':summary,'trace554CandidateConstruction':rows,'interpretation':['Both target cells belong to zero543groups; removing groups leaves both absent.','Using unsimplified source areas also leaves both absent.','Forced true is feasible, changes only target, and has positive original objective gap: no hard prohibition.','554 only constructs anchors at quantized convex axis extrema:33 has retained mapped anchors;49 has zero source anchors and one generated fit anchor without an identical source point/axis/sign. Restoring original point coordinates alone cannot establish a source extremum at this cell.','Original distal-weight detector is a surface-sample audit, not proof that an entire anatomical fingertip disappeared. Preserve that distinction.']}
(O/'Minimal555/CAUSE555.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps([{'frame':r['frame'],'sourceAnchors':len(r['sourceExtremaMappingToTarget']),'fitAnchors':len(r['fitExtremaMappingToTarget']),'accepted554':r['existing554TargetAccepted']}for r in rows]))
