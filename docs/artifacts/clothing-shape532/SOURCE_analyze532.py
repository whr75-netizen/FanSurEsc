from pathlib import Path
import struct,json,math,sys
import numpy as np
O=Path(__file__).resolve().parent;REF=O.parent/'Cloth527/FullLoopB'
variant=sys.argv[1]if len(sys.argv)>1 else'halfcell'
class Reader:
 def __init__(self,b):self.b=b;self.at=0
 def i(self):q=struct.unpack_from('<i',self.b,self.at)[0];self.at+=4;return q
 def a(self,d,n):q=np.frombuffer(self.b,d,n,self.at).copy();self.at+=q.nbytes;return q
def probe(name):
 r=Reader((O/(name+'.bin')).read_bytes());rings=[r.a('<f4',r.i()*2).reshape(-1,2)for _ in range(r.i())];box=tuple(r.i()for _ in range(4));x,y,w,h=box;a=r.a('<f4',w*h).reshape(h,w);m=r.a('?',w*h).reshape(h,w);assert r.at==len(r.b)
 return rings,box,a,m
def old(f):
 r=Reader((REF/f'{f:03d}_ALT_REGION.bin').read_bytes());box=tuple(r.i()for _ in range(4));x,y,w,h=box;a=r.a('<f4',w*h).reshape(h,w);m=r.a('?',w*h).reshape(h,w);return box,a,m
def cells(box,m):
 x,y,w,h=box;return{(int(xx)+x,int(yy)+y)for yy,xx in np.argwhere(m)}
def first(rows,y,x0=196,x1=207):return min((x for x in range(x0,x1)if(x,y)in rows),default=None)
actual=[]
for f in [42,43,44,45]:
 bs,b,a,m=probe(f'actual{f}_baseline');cs,c,aa,mm=probe(f'actual{f}_{variant}');ob,oa,om=old(f)
 oldcells=cells(ob,om);base=cells(b,m);cand=cells(c,mm)
 row={'frame':f,'baselineMaskDifferenceVs527':len(base^oldcells),'baseCurvePoints':[len(r)for r in bs],'halfcellCurvePoints':[len(r)for r in cs],'totalSelectedChanged':len(base^cand),'target43SelectedBase':[[x,y]for x,y in [(200,98),(200,99)]if(x,y)in base],'target43SelectedCandidate':[[x,y]for x,y in [(200,98),(200,99)]if(x,y)in cand],'leftBoundaryBase':{str(y):first(base,y)for y in range(95,104)},'leftBoundaryCandidate':{str(y):first(cand,y)for y in range(95,104)},'case44SelectedBase':(231,78)in base,'case44SelectedCandidate':(231,78)in cand,'roi43Candidate':[''.join('#'if(x,y)in cand else'.'for x in range(198,205))for y in range(95,104)]}
 actual.append(row)
normal=[]
for rot in range(4):
 for sub in range(2):
  bs,b,a,m=probe(f'thin{rot}_{sub}_baseline');cs,c,aa,mm=probe(f'thin{rot}_{sub}_{variant}')
  bc,cc=cells(b,m),cells(c,mm)
  normal.append({'rotation':rot,'subdivision':bool(sub),'baselineCurvePoints':[len(r)for r in bs],'candidateCurvePoints':[len(r)for r in cs],'selectedMaskDifference':len(bc^cc),'removed':sorted(bc-cc),'added':sorted(cc-bc),'baseSelected':len(bc),'candidateSelected':len(cc),'candidateRings':[r.tolist()for r in cs]})
result={'trial':variant+' closed curve approximation; original area and spatial cut unchanged, no529 excursion exceptions','actual':actual,'normal':normal,'baselineVerified':all(x['baselineMaskDifferenceVs527']==0 for x in actual),'normalMasksPreserved':all(x['selectedMaskDifference']==0 for x in normal),'notRuntimeOrArtPass':True,'productCodeChanged':False}
(O/('RESULT_AREA532.json'if variant=='area'else'RESULT532.json')).write_bytes(json.dumps(result,indent=2).encode())
print(json.dumps({'baselineVerified':result['baselineVerified'],'normalMasksPreserved':result['normalMasksPreserved'],'actual':actual,'normal':[{'rot':x['rotation'],'sub':x['subdivision'],'changed':x['selectedMaskDifference'],'points':x['candidateCurvePoints']}for x in normal]}))
