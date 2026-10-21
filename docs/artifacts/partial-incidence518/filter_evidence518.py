"""Counterexamples separating old filters from exact region incidence.

Diagnostic predicates only. Does not remove filters from the running binder,
reselect masks, modify costs or claim the proposed unrestricted mapping works.
"""
from fractions import Fraction as Q
import json,pickle
import numpy as np
import active516 as G,face518 as F,edge518 as E
D=G.ROOT/'Region518/PartialEdgeV2';FULL=D/'Stored81'
def rect(a,b,c,d):return[(a,b),(c,b),(c,d),(a,d)]
def setup(rings,m):
    o=F.Overlay(rings,m,F.auto_domain(rings,m),True);return o,E.BoundaryIncidence(o)
def old_geometry(edge,source):
    p=np.array(edge[:2],float);end=np.array(edge[2:],float);a,b=np.array(source,float);v=b-a;d=end-p;t=np.clip(((np.array([p,end])-a)*v).sum(1)/(v@v),0,1);dd=((np.array([p,end])-(a+t[:,None]*v))**2).sum(1)
    return{'maxEndpointDistance2':float(dd.max()),'unitDotSource':float(d@v),'oldCorridorPass':bool(dd.max()<=2+1e-9),'oldDirectionPass':bool(d@v>=-1e-9)}
dependency=json.loads((FULL/'CENTRE_FILTER_DEPENDENCY518.json').read_text());nearest=dependency['allSourceSegmentsOwningCentreRegion'][0]
assert nearest['centreRegionEvidence']['accepted']and nearest['rejectedBy']==['EXISTING_UNIT_TANGENT_DIRECTION']

# A single connected added ribbon surrounds the region.  Region membership
# alone admits the opposite boundary, although it is the wrong local arc for
# this top edge.  This demonstrates candidate admission, not a selected result.
ring=rect(2.25,2.25,7.75,5.75);m={(x,y):True for x in range(2,8)for y in range(2,6)};o,e=setup([ring],m);edge=(3,2,4,2);opposite=[ring[2],ring[3]];local=[ring[0],ring[1]]
farSupport=e.candidate_support(edge,opposite);localSupport=e.candidate_support(edge,local)
assert farSupport['accepted']and localSupport['accepted'];farGeometry=old_geometry(edge,opposite);assert not farGeometry['oldDirectionPass']and not farGeometry['oldCorridorPass']

# Distinct regions cannot be linked by dropping the direction/distance tests.
# The exact selected/P overlay still carries separate components.
r1=rect(2.1,2.1,3.9,3.9);r2=rect(5.1,2.1,6.9,3.9);m2={(x,y):True for x in[2,3,5,6]for y in[2,3]};o2,e2=setup([r1,r2],m2);edge2=(4,2,4,3)
foreign=e2.candidate_support(edge2,[r2[0],r2[1]]);assert not foreign['accepted']
out={'passed':True,'actualFalseRejection':{'phase':dependency['phase'],'edge':dependency['edge'],'sourceCandidate':nearest,'interpretation':'The unit tangent is an additional restriction not implied by the valid selected A-face incidence. Its rejection here is geometric and unrelated to physical visibility.'},'sameRibbonOppositeBoundaryCounterexample':{'edge':edge,'localSource':local,'oppositeSource':opposite,'localSupport':localSupport,'oppositeSupport':farSupport,'oldGeometricPredicates':farGeometry,'interpretation':'Removing direction/distance alone admits a nonlocal opposite boundary of the same connected A ribbon. No full-path selection or bad output is asserted.'},'disconnectedForeignRegionCounterexample':{'edge':edge2,'foreignSource':[r2[0],r2[1]],'foreignSupport':foreign,'interpretation':'Exact incidence rejects the foreign region without introducing a proximity radius.'},'conclusion':'The whole-unit predicates conflict with the partial-edge/merged-region representation, but merely deleting them is not a complete correspondence rule. A replacement needs ordered local boundary-chain incidence across the exact partial transitions, preserving selected merge/split decisions and separating unrelated branches.','notImplemented':True,'selectorRuns':0,'newUnityCalls':0,'costOrCoefficientChanged':False}
(D/'FILTER_COUNTEREXAMPLES518.json').write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps({'passed':True,'actualFalseRejection':out['actualFalseRejection'],'oppositeBoundaryAdmittedWithoutFilters':farSupport['accepted'],'disconnectedForeignRegionAccepted':foreign['accepted'],'noPatch':True},default=str),flush=True)
