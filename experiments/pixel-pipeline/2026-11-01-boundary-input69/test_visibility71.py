import json
import numpy as np
from pathlib import Path
from opaque_visibility71 import OpaqueScene
def main():
 cases=[]
 base=np.array([[-2,-2],[3,-2],[.5,3]],float)
 def scene(tri,z):return OpaqueScene([base,tri],[[10]*3,z],[[0,0,0],[1,0,0]])
 a=scene([[.25,-1],[.75,-1],[.5,1]],[9]*3);r=a.line([[0,0],[1,0]],[0,0,0]);assert np.allclose(r['blockedIntervals'],[[.375,.625]]);cases.append('triangle entry/exit partitions whole line')
 a=scene(base,[9,11,10]);r=a.line([[0,0],[1,0]],[0,0,0]);assert abs(r['blockedFraction']-.5)<1e-5;cases.append('affine depth crossing splits one segment')
 a=scene(base,[11]*3);assert a.line([[0,0],[1,0]],[0,0,0])['blockedFraction']==0;cases.append('behind triangle does not occlude')
 a=scene(base,[10]*3);assert a.line([[0,0],[1,0]],[0,0,0])['blockedFraction']==0;cases.append('coplanar tie does not create strict occlusion')
 a=scene([[.5001,-1],[.5003,-1],[.5002,1]],[9]*3);r=a.line([[0,0],[1,0]],[0,0,0]);assert 0<r['blockedFraction']<.001;cases.append('narrow subpixel blocker not missed by midpoint sampling')
 a=scene(base,[9]*3);r=a.line([[0,0],[1,0]],[0,0,0]);assert r['blockedFraction']==1;cases.append('complete opaque occlusion')
 a=OpaqueScene([base,base,base],[[10]*3,[9]*3,[8]*3],[[0,0,0],[1,0,0],[2,0,0]]);assert a.line([[0,0],[1,0]],[0,0,0])['blockedFraction']==1;cases.append('overlapping blocker union not double-counted')
 a=scene(base,[9]*3);x=a.line([[0,0],[1,0]],[0,0,0]);y=a.line([[1,0],[0,0]],[0,0,0]);assert x['blockedFraction']==y['blockedFraction'];cases.append('endpoint reversal invariant')
 ids,d=a.point([.5,0]);assert len(ids)==2 and d.min()==9;cases.append('point depth agrees with analytic line')
 b=OpaqueScene([base,[[0,0],[0,0],[0,0]]],[[10]*3,[9]*3],[[0,0,0],[1,0,0]]);assert b.line([[0,0],[1,0]],[0,0,0])['blockedFraction']==0;cases.append('degenerate triangle excluded explicitly')
 result={'passed':len(cases),'cases':cases,'UnityCalls':0,'limits':'Opaque geometry solver only; no shader alpha or artistic reference proof'}
 (Path(__file__).parent/'VISIBILITY_TEST71.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
