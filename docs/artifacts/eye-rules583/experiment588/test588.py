from pathlib import Path
from fractions import Fraction as Q
from dataclasses import replace
import json,sys,tracemalloc
import numpy as np
from coverage588 import Plane,Patch,Band,Kernel,fit,point,solve
from decompose588 import fixture
R=Path(__file__).parent
F=lambda x:Q(float(np.float32(x)))
BAND=Band(F(-.82),F(.35),-F(.36),F(.22),-F(1.08),F(1.08))
TOL=Q(1,10000)  # one tenth of the0.001 threshold margin, fixed before tests

def make(target,transform=None):
    f=fixture(target);p=[point(f['x0'],f['y0']),point(f['x0'],f['y1']),point(f['x1'],f['y1']),point(f['x1'],f['y0'])]
    if transform:p=[transform(x,y)for x,y in p]
    u=[BAND.umin,BAND.umin,BAND.umax,BAND.umax];v=[Q(-3,2),Q(1,2),Q(1,2),Q(-3,2)]
    patches=[]
    for draw,ids in enumerate([(0,1,2),(0,2,3)]):
        tri=tuple(p[i]for i in ids);patches.append(Patch('skin'+str(draw),tri,Plane(c=Q(6)),fit(tri,[u[i]for i in ids]),fit(tri,[v[i]for i in ids]),draw=draw))
    exact=(Q(f['x1'])-Q(f['x0']))*((Q(f['y1'])-Q(f['y0']))/2)*(BAND.up-BAND.down)
    return patches,exact,tuple(p)

def occ(id,p,z,kind='body',layer='body6',draw=0,alpha=Q(1)):
    return Patch(id,p,z,Plane(),Plane(),layer,kind,0,True,draw,True,alpha,alpha)
def trim(patches,h):
    k=Kernel();result=[]
    for p in patches:
        poly=k.clip(p.polygon,h)
        if poly:result.append(replace(p,polygon=poly))
    return result
def serial(value):
    if isinstance(value,Q):return str(value.numerator)+'/'+str(value.denominator)
    if isinstance(value,dict):return {k:serial(v)for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [serial(v)for v in value]
    return value

def main():
    cases=[]
    for target in [.499,.501,.65,.55,.45,.35]:
        p,a,_=make(target);cases.append(('area_'+str(target),p,a,'CERTIFIED',int(a+Q(1,2))))
    p,a,quad=make(.501);u=p[0].u
    cases.append(('full_front_body',p+[occ('front',quad,Plane(c=Q(5)))],Q(0),'CERTIFIED',0))
    cases.append(('body_behind',p+[occ('behind',quad,Plane(c=Q(7)))],a,'CERTIFIED',1))
    cases.append(('depth_cross_same_ray',p+[occ('cross',quad,Plane(u.x,u.y,u.c+6))],a/2,'CERTIFIED',0))
    left=Kernel().clip(quad,u.scale(-1))
    foreground=replace(p[0],id='otherOwner',polygon=left,z=Plane(c=Q(5)),owner=9,draw=10)
    cases.append(('front_other_owner_before_eligibility',p+[foreground],a/2,'CERTIFIED',0))
    other_feature=replace(foreground,id='otherFeature',owner=2,v=p[0].v.offset(10))
    cases.append(('front_same_owner_other_feature',p+[other_feature],a/2,'CERTIFIED',0))
    duplicates=[replace(t,id='duplicate'+t.id,draw=t.draw+10)for t in p]
    cases.append(('overlap_triangles_not_double_counted',p+duplicates,a,'CERTIFIED',1))
    brow1=occ('brow1',quad,Plane(c=Q(5)),'brow','brow5',0,Q(1,2));brow2=replace(brow1,id='brow2',draw=1,z=Plane(c=Q(9,2)))
    cases.append(('same_layer_alpha_nearest_once',p+[brow1,brow2],a/2,'CERTIFIED',0))
    hair=occ('hair',quad,Plane(c=Q(4)),'hair','hair4',0,Q(1,2))
    cases.append(('separate_layers_transmittance',p+[brow1,hair],a/4,'CERTIFIED',0))
    cases.append(('proven_alpha_pass_domain_half',trim(p,u.scale(-1)),a/2,'CERTIFIED',0))
    uncertain=replace(brow1,id='boundedBrow',alpha_lo=Q(2,5),alpha_hi=Q(3,5))
    cases.append(('opacity_interval_not_falsely_precise',p+[uncertain],a/2,'UNRESOLVED_OPACITY',None))
    cases.append(('unproven_alpha_domain_refused',[replace(p[0],passed=None),p[1]],None,'UNRESOLVED_INPUT',None))
    cases.append(('unexpressed_support_fallback_refused',p+[replace(p[0],id='source3',layer='source3',draw=0)],None,'UNRESOLVED_INPUT',None))
    rotate=lambda x,y:(Q(3,5)*(x-Q(3,2))-Q(4,5)*(y-Q(3,2))+Q(3,2),Q(4,5)*(x-Q(3,2))+Q(3,5)*(y-Q(3,2))+Q(3,2))
    transformed,ta,_=make(.501,rotate);cases.append(('rational_rotation_same_area',transformed,ta,'CERTIFIED',1))
    shifted,sa,_=make(.499,lambda x,y:(x+Q(1,1009),y+Q(1,997)))
    cases.append(('subgrid_translation_not_lattice_aligned',shifted,sa,'CERTIFIED',0))
    constant_u=Patch('constantU',((0.,0.),(1.,0.),(1.,1.),(0.,1.)),Plane(c=6),Plane(),Plane(y=1,c=-1.5))
    cases.append(('constant_u_nonzero_screen_area',[constant_u],BAND.up-BAND.down,'CERTIFIED',1))
    # Same method/tolerance, deliberately unresolved when the certified interval
    # still straddles the rounding boundary. It must never turn unknown into0.
    boundary,ba,_=make(.5);cases.append(('near_exact_threshold_not_forced',boundary,ba,'UNRESOLVED_THRESHOLD',None))
    results=[]
    for name,patches,expected,status,budget in cases:
        tracemalloc.start();result=solve(patches,BAND,tolerance=TOL,max_leaves=2048);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        enclosed=expected is None or result.get('lower') is not None and result['lower']<=expected<=result['upper']
        passed=result['status']==status and result['budget']==budget and enclosed
        row=dict(name=name,expected=expected,expectedStatus=status,expectedBudget=budget,contained=enclosed,passed=passed,
            sourcePatches=len(patches),inputVertices=sum(len(p.polygon)for p in patches),pythonTracedPeakBytes=peak,result=result)
        results.append(row)
        (R/'RESULT588.json').write_text(json.dumps(serial(dict(complete=False,results=results)),indent=2)+'\n')
        print(json.dumps(dict(case=name,status=result['status'],budget=result['budget'],contained=enclosed,passed=passed,
            width=float(result['upper']-result['lower'])if result.get('lower')is not None else None,
            seconds=result['seconds'],peakBytes=peak,leaves=result.get('leaves'))),flush=True)
        if not passed:break
    summary=dict(complete=len(results)==len(cases),allExpectedOutcomes=all(r['passed']for r in results),
        certifiedCases=sum(r['result']['status']=='CERTIFIED'for r in results),
        unresolvedCases=sum(r['result']['status']!='CERTIFIED'for r in results),
        requiredTolerance=TOL,method='Exact half-plane ownership clipping plus parabola chord/tangent inner/outer polygons; no centre sampling',
        gpuTextures=0,productConnected=False,results=results)
    (R/'RESULT588.json').write_text(json.dumps(serial(summary),indent=2)+'\n')
    print(json.dumps({k:serial(v)for k,v in summary.items()if k!='results'}),flush=True)
if __name__=='__main__':main()
