"""One stored actual input tile -> existing588; no Unity/runtime product change.

Alpha endpoint certificates only. Ambiguous cutout and reference/support domains
stay unknown; they never become zero coverage. Same reference/support priority as
Sample583, using existing exact half-plane partition instead of another renderer.
"""
from pathlib import Path
from fractions import Fraction as Q
from dataclasses import replace
import sys,json,time,hashlib,csv
import numpy as np
R=Path(__file__).parent
sys.path.insert(0,str(R.with_name('EyeCoverage588')))
sys.path.insert(0,str(R.with_name('EyeArea585')))
from geometry_oracle585 import Frame,TEXTURES
from coverage588 import Kernel,Patch,Plane,Band,point,fit,area,solve

def serial(v):
    if isinstance(v,Q):return str(v.numerator)+'/'+str(v.denominator)
    if isinstance(v,dict):return {k:serial(x)for k,x in v.items()}
    if isinstance(v,(tuple,list)):return [serial(x)for x in v]
    return v

def main():
    start=time.perf_counter()
    f=Frame(0,R.with_name('EyeFollow584')/'Runtime584/OneCase2',R.with_name('EyeArea585')/'Runtime585/Geometry2')
    inventory=json.loads((R.with_name('EyeCoverage588')/'INPUT_INVENTORY589.json').read_text())
    weighted=[]
    for row in inventory['rows']:
        x,y=row['cell'];pts=np.array([(x+(k%4+.5)/4,y+(k//4+.5)/4)for k in range(16)])
        weighted.append((float(f.weights(pts).sum()/16),row))
    weight,row=max(weighted,key=lambda v:v[0]);assert weight>0
    x,y=row['cell'];cell=(point(x,y),point(x+1,y),point(x+1,y+1),point(x,y+1))
    k=Kernel();raw=[];owner={};records=[]
    for q in row['triangles']:
        t=q['triangle'];tri=tuple(point(*p)for p in f.xy[t]);poly=k.overlap(tri,cell)
        assert area(poly)>0
        material=f.mats[f.tr[t]['material']]
        assert material['textureST']=='1,1,0,0'
        assert all(float(material[n])==0 for n in ['_UvAnimScrollXSpeed','_UvAnimScrollYSpeed','_UvAnimRotationSpeed'])
        layer=int(f.s[t]);kind='source'if layer<4 else 'brow'if layer==5 else 'body'
        uv_u=fit(tri,f.v[t,:,7]);uv_v=fit(tri,f.v[t,:,8]);tex=TEXTURES[int(f.mi[t])]['alpha']
        alpha=q['alphaMin']*q['colorAlpha']
        # Only exact endpoints are used for a positive BLEND certificate.
        # Every actual material in this selected tile is MASK or OPAQUE.
        if q['mode']==2 and q['passed']is True:assert q['alphaMin']==q['alphaMax']
        opacity=Q(1)if q['mode']in [0,1]else Q(alpha)
        p=Patch(str(t),poly,Plane(*map(Q,f.depth[t])),Plane(*map(Q,f.uc[t])),Plane(*map(Q,f.vc[t])),
            layer=str(layer),kind=kind,owner=2,front=q['front'],draw=t,passed=q['passed'],alpha_lo=opacity,alpha_hi=opacity)
        owner[p.id]=Plane(*map(Q,f.owner[t]));raw.append(p)
        records.append(dict(id=p.id,layer=layer,primitive=q['primitive'],material=q['material'],domain=poly,z=p.z.__dict__,u=p.u.__dict__,v=p.v.__dict__,owner=owner[p.id].__dict__,alphaCertificate=q))
    print(json.dumps(dict(selectedActualTile=[x,y],oldGridArea=weight,triangles=len(raw))),flush=True)
    # Per-layer depth first, then front/eye eligibility. Unknown alpha may hide
    # a known fragment, so any possibly closer unknown is removed from certainty.
    known=k.nearest([p for p in raw if p.passed is True])
    uncertain=[p for p in raw if p.passed is None]
    certain=[]
    def remove(polys,mask):return [p for a in polys for p in k.subtract(a,mask)]
    for p in known:
        pieces=[p.polygon]
        for u in uncertain:
            if u.layer!=p.layer:continue
            mask=k.overlap(p.polygon,u.polygon)
            if not area(mask):continue
            if p.z==u.z:
                if u.draw<p.draw:continue
            else:mask=k.clip(mask,p.z-u.z)
            pieces=remove(pieces,mask)
        certain.extend(replace(p,polygon=z)for z in pieces)
    def eligible(p):
        if not p.front:return ()
        poly=k.clip(p.polygon,owner[p.id].offset(-Q(3,2)))
        return k.clip(poly,owner[p.id].scale(-1).offset(Q(5,2)))
    possible={str(s):[]for s in [0,1,2,3]}
    for p in raw:
        if p.kind=='source'and p.passed is not False:
            poly=eligible(p)
            if area(poly):possible[p.layer].append(replace(p,polygon=poly))
    def priority(order):
        result=[];higher=[]
        for layer in map(str,order):
            for p in certain:
                if p.layer!=layer:continue
                poly=eligible(p)
                if not area(poly):continue
                pieces=[poly]
                for h in higher:pieces=remove(pieces,h.polygon)
                result.extend(replace(p,polygon=z)for z in pieces)
            higher.extend(possible[layer])
        return result
    refs=priority([0,1,2,3]);supports=priority([0,3]);canonical=[];mapping=[]
    for ref in refs:
        for sup in supports:
            poly=k.overlap(ref.polygon,sup.polygon)
            if not area(poly):continue
            id='ref'+ref.id+'/support'+sup.id+'/'+str(len(canonical))
            # Reference rest coordinates and support depth remain independent.
            canonical.append(Patch(id,poly,sup.z,ref.u,ref.v,layer='canonical',owner=2))
            mapping.append(dict(id=id,reference=ref.id,referenceLayer=ref.layer,support=sup.id,supportLayer=sup.layer,area=area(poly)))
    # Any uncertain front occluder is excluded from a certified subdomain.
    # Its possible contribution is restored to the final upper bound below.
    safe=[]
    for p in canonical:
        pieces=[p.polygon]
        for u in uncertain:
            if u.kind=='source':continue
            mask=k.overlap(p.polygon,u.polygon)
            if not area(mask)or p.z==u.z:continue
            mask=k.clip(mask,p.z-u.z);pieces=remove(pieces,mask)
        safe.extend(replace(p,id=p.id+'/'+str(i),polygon=z)for i,z in enumerate(pieces))
    occluders=[p for p in certain if p.kind!='source']
    hm=row['hairMETA']
    if hm[0]>0 and hm[1]>.5 and hm[3]>1e-6:
        occluders.append(Patch('packetHair',cell,Plane(c=Q(hm[0])),Plane(),Plane(),layer='hair',kind='hair',owner=0,alpha_lo=Q(hm[3]),alpha_hi=Q(hm[3])))
    a,b=map(Q,f.cfg['UpperLower348'][:2]);band=Band(a,b,-Q(float(np.float32(.36))),Q(float(np.float32(.22))),-Q(float(np.float32(1.08))),Q(float(np.float32(1.08))))
    result=solve(safe+occluders,band,tolerance=Q(1,10000))
    # Conservative upper area for domains that have no certain ref/support
    # pair. It uses the actual possible support and reference geometry, never
    # borrowed owner/depth. Overlapping upper pieces may overcount, capped by
    # the tile complement's area; this can only widen uncertainty.
    unsafe=[]
    for layer in possible.values():
        for p in layer:
            pieces=[p.polygon]
            for q in safe:pieces=remove(pieces,q.polygon)
            for poly in pieces:
                for s in possible['0']+possible['3']:
                    overlap=k.overlap(poly,s.polygon)
                    if not area(overlap):continue
                    w=replace(p,polygon=overlap);uv=[p.u.at(z)for z in overlap]
                    l=max(band.umin,min(uv));r=min(band.umax,max(uv))
                    if l>r:continue
                    from coverage588 import Weighted
                    _,hi,_=k.enclosure(Weighted(overlap,w,Q(0),Q(1)),band,l,r)
                    if hi:unsafe.append(hi)
    safe_domain=sum((area(p.polygon)for p in safe),Q(0))
    unknown_upper=min(sum(unsafe,Q(0)),max(Q(0),Q(1)-safe_domain))
    assert result.get('lower')is not None
    lower=result['lower'];upper=min(Q(1),result['upper']+unknown_upper)
    # Independent old-grid label/depth check for the certified paired domains.
    checks=[]
    for index in range(16):
        p=point(x+Q(2*(index%4)+1,8),y+Q(2*(index//4)+1,8))
        found=[q for q in safe if all(h.at(p)>=0 for h in k.edges(q.polygon))]
        if not found:continue
        q=found[0];entry=next(z for z in mapping if q.id.startswith(z['id']+'/'))
        ref=int(entry['reference']);sup=int(entry['support']);pt=np.array([[float(p[0]),float(p[1])]])
        actual_ref=next((int(v[0][0])for layer in [0,1,2,3]if (v:=f.point_layer(pt,layer))[0][0]>=0 and f.front[v[0][0]]and round(float(np.r_[pt[0],1]@f.owner[v[0][0]]))==2),-1)
        actual_sup=next((int(v[0][0])for layer in [0,3]if (v:=f.point_layer(pt,layer))[0][0]>=0 and f.front[v[0][0]]and round(float(np.r_[pt[0],1]@f.owner[v[0][0]]))==2),-1)
        assert ref==actual_ref and sup==actual_sup
        checks.append(dict(sample=index,referenceLayer=entry['referenceLayer'],supportLayer=entry['supportLayer'],referencePrimitive=int(f.prim[ref]),supportPrimitive=int(f.prim[sup]),referenceSupportMatch=True))
    out=dict(status='LIMITED_REAL_INPUT_CONNECTED_PRODUCT_NOT_CONNECTED',sourcePose=inventory['pose'],selectedTile=[x,y],selection='Largest old-grid positive tile in this stored pose; observation only, no algorithm coordinate/pose exception',
        rows=records,referenceSupportMapping=mapping,canonicalPieces=len(canonical),certifiedPieces=len(safe),safeDomainArea=safe_domain,
        alphaUnknownPatches=len(uncertain),core=result,unknownAreaUpper=unknown_upper,totalLower=lower,totalUpper=upper,
        areaAccuracyCertified=upper-lower<=Q(1,10000),localOldGridArea=weight,oldGridChecks=checks,
        secondsIncludingInputLoad=time.perf_counter()-start,providerClipCalls=k.clips,providerDepthPairs=k.pairs,
        productSourceChanged=False,actualGPUReRender=False,
        guarantee='Conditional on stored projected geometry and conservative alpha endpoint bounds. Not a full hardware alpha-boundary/projection error certificate. Missing input is explicit, never0.',
        remaining='Subpixel alpha-cutout and GPU projection/interpolation rounding bounds; nonconstant translucent alpha; full feature ROI and GPU execution/cost.')
    (R/'REAL_INPUT589.json').write_text(json.dumps(serial(out),indent=2)+'\n')
    print(json.dumps(dict(status=out['status'],tile=[x,y],canonical=len(canonical),safe=len(safe),lower=float(lower),upper=float(upper),unknownUpper=float(unknown_upper),accuracyCertified=out['areaAccuracyCertified'],oldGridChecks=len(checks),seconds=out['secondsIncludingInputLoad'])),flush=True)
if __name__=='__main__':main()
