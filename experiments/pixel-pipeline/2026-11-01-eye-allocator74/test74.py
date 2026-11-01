from pathlib import Path
import json,numpy as np
from allocator74 import legacy,connected,components
R=Path(__file__).resolve().parent
C={'connectivity':4,'provenance':'synthetic explicit connected source feature'}
def packet(points):
 a=np.zeros((4,5,12),np.float32)
 for (x,y),value in points.items():a[y,x,2]=value;a[y,x,8]=x;a[y,x,9]=y
 return a
def main():
 cases=[]
 def test(name,fn):fn();cases.append(name)
 def ok(x):assert x
 a=packet({(0,0):15,(1,0):5,(1,1):13});b=connected(a,C)
 test('same budget removes unsupported diagonal split inside connected support',lambda:ok(legacy(a)['budget']==b['budget']==2 and len(components(legacy(a)['selected']))==2 and len(components(b['selected']))==1))
 test('no implicit source-design topology declaration',lambda:ok(connected(a)['status']=='missing-source-style-connectivity-contract'))
 test('declared diagonal design uses8-neighbour contract unchanged',lambda:ok(not connected(a,dict(C,connectivity=8))['changed']))
 test('no mandatory eye-size minimum',lambda:ok(connected(packet({(0,0):1}),C)['selected']==[]))
 test('one-cell budget remains one cell',lambda:ok(connected(packet({(0,0):16}),C)['budget']==1))
 test('disconnected support never invents bridge or hides occlusion',lambda:ok(connected(packet({(0,0):16,(2,0):16}),C)['status']=='disconnected-visible-support-unresolved-no-bridge'))
 test('connected legacy result is preserved exactly',lambda:ok(not connected(packet({(0,0):16,(1,0):16}),C)['changed']))
 test('candidate search has an explicit CPU budget',lambda:ok(connected(a,C,max_combinations=1)['status']=='offline-enumeration-budget-exceeded'))
 sym=connected(packet({(0,0):14,(1,0):5,(1,1):14}),C)
 test('equal objective alternatives reported instead of unique art claim',lambda:ok(sym['ambiguousOptimalSets']==2))
 # No palette input exists; unrelated family values outside the used histogram
 # cannot move the result. No forced equality with another eye.
 n=a.copy();n[...,10:12]=123
 test('unused channels do not influence colour-independent allocation',lambda:ok(connected(n,C)['selected']==b['selected']))
 test('two different budgets are not forced equal',lambda:ok(connected(packet({(0,0):16}),C)['budget']!=b['budget']))
 shifted=np.zeros_like(a);shifted[1:,1:]=a[:-1,:-1]
 test('integer translation preserves local allocation',lambda:ok(set(connected(shifted,C)['selected'])=={(x+1,y+1)for x,y in b['selected']}))
 for turn in [1,2,3]:
  z=np.rot90(a,turn);out=set(connected(z,C)['selected']);mask=np.zeros(a.shape[:2],bool)
  for x,y in b['selected']:mask[y,x]=True
  expected={(int(x),int(y))for y,x in np.argwhere(np.rot90(mask,turn))}
  test('unique optimum follows source rotation'+str(turn),lambda out=out,expected=expected:ok(out==expected))
 left=connected(packet({(0,0):12.0001,(1,0):8,(2,0):11.9999}),C);right=connected(packet({(0,0):11.9999,(1,0):8,(2,0):12.0001}),C)
 test('known limitation: tiny score change can still move connected cluster',lambda:ok(set(left['selected'])!=set(right['selected']) and left['budget']==right['budget']==2))
 result={'passed':len(cases),'cases':cases,'UnityCalls':0,'productChanges':0,'limits':'Conditional connected-subset selection only; no temporal/cache/whole-eye/colour composition solution'}
 with (R/'TEST74.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
if __name__=='__main__':main()
