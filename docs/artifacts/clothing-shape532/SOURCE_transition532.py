"""Inspect the first new transition using the same stored math outputs."""
from pathlib import Path
import sys,json,math,struct
import numpy as np
O=Path(__file__).resolve().parent
# Load definitions only; do not rerun probe or previous analysis.
namespace={'__file__':str(O/'analyze532.py')};exec((O/'analyze532.py').read_text().split('actual=[]')[0],namespace)
probe=namespace['probe'];cells=namespace['cells'];REF=namespace['REF']
def read_rings(f):
 b=(REF/f'{f:03d}_ALT_GEOMETRY.bin').read_bytes();at=0;groups=[]
 for _ in range(2):
  n=struct.unpack_from('<i',b,at)[0];at+=4;rs=[]
  for k in range(n):
   m=struct.unpack_from('<i',b,at)[0];at+=4;rs.append(np.frombuffer(b,'<f4',m*2,at).reshape(-1,2).copy());at+=m*8
  groups.append(rs)
 return groups
def crossing(rings,y):
 out=[]
 for ring in rings:
  for a,b in zip(ring,np.roll(ring,-1,axis=0)):
   if min(a[1],b[1])<=y<max(a[1],b[1]):
    t=(y-float(a[1]))/(float(b[1])-float(a[1]));x=float(a[0])+t*(float(b[0])-float(a[0]))
    if 198<=x<=203:out.append({'x':x,'a':a.tolist(),'b':b.tolist()})
 return out
def delta(box,a,m,p):
 bx,by,w,h=box;x,y=p;on=lambda x,y:bool(m[y-by,x-bx])if bx<=x<bx+w and by<=y<by+h else False
 old=on(x,y);aa=float(a[y-by,x-bx]);unary=(aa-(1-aa))if old else((1-aa)-aa);boundary=0
 for dx in[-1,0,1]:
  for dy in[-1,0,1]:
   if dx or dy:
    q=on(x+dx,y+dy);boundary+=.14*(.29289322 if dx and dy else .58578644)*(int((not old)!=q)-int(old!=q))
 return {'selected':old,'area':aa,'flipUnaryDelta':unary,'flipBoundaryDelta':boundary,'flipTotalDelta':unary+boundary}
rows=[]
for f in[42,43,44]:
 source,old=read_rings(f);curve,box,a,m=probe(f'actual{f}_area')
 rows.append({'frame':f,'newCell':[200,96],'sourceCrossing':crossing(source,96.5),'oldCurveCrossing':crossing(old,96.5),'candidateCurveCrossing':crossing(curve,96.5),'selection':delta(box,a,m,(200,96))})
# Exact ordered arc metrics: both progression and local absolute area matter.
old=json.loads((O.parent/'Cloth527/Order529/MINIMAL_GATE529.json').read_text())
def metric(p):
 p=np.array(p,float);d=p[-1]-p[0];length=float(np.linalg.norm(d));v=p-p[0];s=v@d/length;h=(d[0]*v[:,1]-d[1]*v[:,0])/length
 area=0
 for a,b,sa,sb in zip(h,h[1:],s,s[1:]):
  u,w=abs(a),abs(b);area+=(sb-sa)*((u*u+w*w)/(2*(u+w))if a*b<0 else(u+w)*.5)
 return {'arcLength':float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum()),'chordLength':length,'maxWidthFromChord':float(abs(h).max()),'projectionOrdered':bool(np.all(np.diff(s)>=0)),'absoluteAreaFromChord':float(area)}
metrics={'actual43':metric(old['actual43'][1]['target43Spans'][0]['arc']),'normalSingleEnd':metric(old['pairedThinEnds']['candidateSpans'][0]['arc']),'normalShortcutThatDistanceRDPIncorrectlyAccepted':metric([(0,7),(0,4),(-.75,4),(-.75,1)])}
j={'status':'FIRST_NEW_TRANSITION_NOT_RUNTIME_VALIDATED','rows':rows,'shapeMetrics':metrics,'originalTargetRemoved':True,'normal8MaskPreserved':True,'productApplied':False}
(O/'FIRST_NEW_TRANSITION532.json').write_bytes(json.dumps(j,indent=2).encode());print(json.dumps(j))
