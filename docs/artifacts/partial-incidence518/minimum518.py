from pathlib import Path
from collections import deque
from fractions import Fraction as Q
import json,hashlib,struct,time
import numpy as np
import active516 as G,face518 as F,select516 as C
W=G.ROOT;R=G.INPUT;D=W/'Region518';D.mkdir(exist_ok=True)
def rect(x,y,xx,yy):return[(x,y),(xx,y),(xx,yy),(x,yy)]
def overlay(rings,mask):return F.Overlay(rings,mask,F.auto_domain(rings,mask),True)
def fingerprint(o):
    value={'summary':o.summary(),'sourceBoundary':sorted((tuple(s['a']),tuple(s['b']))for s in o.source),'pixelBoundary':sorted((s['edge'],tuple(s['a']),tuple(s['b']))for s in o.pixel)}
    return hashlib.sha256(json.dumps(value,sort_keys=True,default=str).encode()).hexdigest()

begin=time.perf_counter();inputFile=W/'Temporal517/SpanArcV2/FIRST_REJECTION517.json';failure=json.loads(inputFile.read_text());case=failure['forcedLocalBarriers'][0];edgeA,edgeB=case['previousPixelEdge'],case['currentPixelEdge'];mask=G.read_mask(0);m=F.mask_from_array(mask);rings=[[(p['x'],p['y'])for p in r['points']]for r in json.loads((R/'000_curves.json').read_text())['curves']]
auto=json.loads((R/'000_auto.json').read_text());assert auto['hiddenCells']==0,'Need original selected labels, not visibility-eroded mask'
def inside_cell(e):
    x,y,u,v=e;dx,dy=u-x,v-y;return(math.floor((x+u-dy)/2),math.floor((y+v+dx)/2))
import math
start,end=inside_cell(edgeA),inside_cell(edgeB);queue=deque([start]);parent={start:None}
while queue and end not in parent:
    x,y=queue.popleft()
    for dx,dy in[(0,-1),(-1,0),(1,0),(0,1)]:
        q=x+dx,y+dy
        if q in m and q not in parent:parent[q]=(x,y);queue.append(q)
assert end in parent;path=[];at=end
while at is not None:path.append(at);at=parent[at]
path=path[::-1];domain=(min(x for x,y in path),min(y for x,y in path),max(x for x,y in path)+1,max(y for x,y in path)+1)
o=F.Overlay(rings,m,domain,False);pa=min(case['previousCandidates'],key=lambda p:p['fit']);pb=min(case['currentCandidates'],key=lambda p:p['fit']);sourceA=[pa['sourceA'],pa['sourceB']];sourceB=[pb['sourceA'],pb['sourceB']]
relation=o.relate(edgeA,edgeB,True,sourceA,sourceB);assert relation['boundaryPathJoin']and relation['candidateSourceAComponents']and relation['candidateSourceBComponents'],relation
bounds,areas=C.areas(0);cert=[];bx,by,ww,hh=bounds
for y in range(domain[1],domain[3]):
    for x in range(domain[0],domain[2]):
        exact=o.cellAreas[x,y];stored=areas[y-by,x-bx];cert.append({'xy':[x,y],'selected':bool(mask[y,x]),'continuousAreaExact':str(exact),'continuousArea':float(exact),'storedSelectorArea':float(stored),'floatAreaDifference':float(exact)-float(stored),'deltaExistingSpatialCostIfToggled':C.delta_spatial(mask,areas,bounds,x,y)})
assert max(abs(c['floatAreaDifference'])for c in cert)<1e-6
packets={(p['x'],p['y']):p for p in json.loads((R/'000_packets.json').read_text())['packets']};refs={(p['x'],p['y']):p for p in json.loads((R/'000_ALT_bodyrefs512.json').read_text())['references']};visibility=[]
for cell in[start,end]:
    p,b=packets[cell],refs[cell];front=b['kind']in[1,2]and b['depth']<p['depth']-.0001
    visibility.append({'cell':cell,'acceptedSourcePacket':p,'bodyReference':b,'knownBodyForeground':front})
    assert not front
variants=[]
for fraction in[Q(1,4),Q(3,4)]:
    changed=[]
    for ring in rings:
        rr=[tuple(Q(float(v))for v in p)for p in ring];s=[]
        for a,b in zip(rr,rr[1:]+rr[:1]):s.extend([a,F.point(a,b,fraction)])
        changed.append(s[len(s)//2:]+s[:len(s)//2])
    variant=F.Overlay(changed,m,domain,False);variants.append({'fraction':str(fraction),'sameIncidenceFingerprint':fingerprint(variant)==fingerprint(o),'relation':variant.relate(edgeA,edgeB,True,sourceA,sourceB)})
assert all(v['sameIncidenceFingerprint']and v['relation']['boundaryPathJoin']for v in variants)

tests=[]
merge=overlay([rect(.1,.1,.9,1.9),rect(2.1,.1,2.9,1.9)],{(x,y):True for x in range(3)for y in range(2)})
merged=[c for c in merge.summary()['components']if c['tag']=='A'and len(c['sourceRegions'])==2 and len(c['selectedRegions'])==1];assert merged
tests.append({'name':'selector-region-merge','passed':True,'components':merged})
split=overlay([rect(.1,.1,2.9,1.9)],{(x,y):True for x in[0,2]for y in range(2)})
splits=[c for c in split.summary()['components']if c['tag']=='D'and len(c['sourceRegions'])==1 and len(c['selectedRegions'])==2];assert splits
tests.append({'name':'selector-region-split-preserves-distinct-output-regions','passed':True,'components':splits})
near=overlay([rect(.1,.1,.9,.9),rect(1.1,1.1,1.9,1.9)],{(0,0):True,(1,1):True});unrelated=near.relate((1,0,1,1),(1,1,2,1),True);assert not unrelated['graphRelation']and not unrelated['boundaryPathJoin']
tests.append({'name':'near-diagonal-point-contact-is-not-region-join','passed':True,'relation':unrelated})
hole=overlay([rect(0,0,3,3),list(reversed(rect(1,1,2,2)))],{(x,y):True for x in range(3)for y in range(3)})
holes=[c for c in hole.summary()['components']if c['tag']=='A'and not c['analysisCutOpen']and c['pixelBoundaryCount']==0 and c['sourceBoundaryCount']>0];assert len(holes)==1 and holes[0]['areaExact']=='1'
tests.append({'name':'selected-hole-omission-no-forced-strand-or-hole-preservation','passed':True,'components':holes})
identity=overlay([rect(0,0,3,3)],{(x,y):True for x in range(3)for y in range(3)});direct=identity.relate((0,0,1,0),(1,0,2,0),True);assert direct['boundaryPathJoin']and direct['directSharedBoundary']
tests.append({'name':'unchanged-region-direct-common-boundary','passed':True,'relation':direct})
front=o.relate(edgeA,edgeB,False,sourceA,sourceB);assert front['graphRelation']and not front['visibleCorrespondenceAccepted']
unknown=o.relate(edgeA,edgeB,None,sourceA,sourceB);assert unknown['graphRelation']and unknown['visibleCorrespondenceAccepted']is None
tests.append({'name':'explicit-front-owner-blocks-region-witness','passed':True,'relation':front});tests.append({'name':'unknown-visibility-not-promoted-by-geometric-donor','passed':True,'relation':unknown})
out={'stage':'MINIMUM_CASE_AND_STRUCTURAL_FIXTURES','minimumPassed':True,'firstTarget':0,'firstPhase':0.,'runtimeChanged':False,'maskChanged':False,'selectorRerun':False,'all81AuditRun':False,'sourceDomain':domain,'localSelectedCellPath':path,'domainIsLocalProofNotWholeHeadBoundary':True,'continuousRegionRule':'positive winding of the existing511 curves','selectorDecisionInput':'existing514 mask.G with hiddenCells0; stored curve-cell areas and unchanged area/perimeter coefficients','overlay':o.summary(),'boundaryRelation':relation,'selectionCertificate':cert,'visibilityScope':'Existing accepted source packets and512 hair/body reference only; no new face/native-world certification.','visibility':visibility,'reparameterization':variants,'fixtures':tests,'syntheticMasksAreStructuralFixturesNotClaimsOfSelectorOptimality':True,'seconds':time.perf_counter()-begin,'inputFiles':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in[inputFile,R/'000_curves.json',R/'000_MASK.bin.gz',R/'000_areas.bin',R/'000_packets.json',R/'000_ALT_bodyrefs512.json']]}
(D/'MINIMUM518.json').write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps({'minimumPassed':True,'relation':relation,'cellSelectionEvidence':cert,'fixtureNames':[t['name']for t in tests],'reparameterizationFingerprint':[v['sameIncidenceFingerprint']for v in variants],'seconds':out['seconds']},default=str,ensure_ascii=False))
