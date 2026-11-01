"""Feature-local source identities after current carrier/visibility gating.

New rule, not recovered artist intent: transport a source identity by nearest
rest-head projected bank centre (I/W), or nearest source-UV ribbon section (L).
All exact ties stay ambiguous. This addresses provenance, not independent
nearest-cell shape allocation: the JOINT resolver alone decides cell labels.
Immutable form and optional previous SOURCE-ID histograms only Pareto-filter
geometrically equivalent solutions; neither can revive an ineligible part.
"""
from fractions import Fraction
from collections import defaultdict
import numpy as np
from fields110 import R,read
from stored110 import P109,source_packet
from io109 import buffer,joint_arrays
from history109 import source_histograms

def conditional_l1(target,current,available,part):
    a={k:v for k,v in target.items()if k[1]==part and k in available};b={k:v for k,v in current.items()if k[1]==part and k in available};sa=sum(a.values());sb=sum(b.values())
    if not sa or not sb:return None
    return sum(abs(a.get(k,0)/sa-b.get(k,0)/sb)for k in a.keys()|b.keys())

def nondominated(vectors):
    dimensions=[k for k in vectors[0]if all(v[k]is not None for v in vectors)]if vectors else[]
    return [i for i,a in enumerate(vectors)if not any(all(b[k]<=a[k]for k in dimensions)and any(b[k]<a[k]for k in dimensions)for b in vectors)]

def transport(row,owner,ctx,records,reference,domain,cache,external_hair_in_shape=False):
    source=read(P109/'inputs/SOURCE_FIXTURE88.json');reg=read(P109/'inputs/REGISTRATION89.json');projection={e['eye']:np.asarray(e['nativeToAuthoredProjection'],np.float32)for e in reg['eyes']};bank={(x['owner'],x['part'],x['x'],x['y']):source['paletteRGB8'][x['palette']]for x in source['source']};_,avail,check=source_histograms(row,bank,projection,source_packet(row))
    available={k:Fraction(1)for k in avail if k[0]==owner};canonical={k:Fraction(1)for k in bank if k[0]==owner and k in available};curve=next(c for c in cache['curves']if c['owner']==owner);valid=[v for v in curve['points']if not v.get('unresolved')];uv=np.array([v['sourceUV']for v in valid]);visible=[i for i,v in enumerate(reference['nativeCurveVisibility'])if v['visibleBounds'][0]>0]
    for i in visible:available[(owner,6,i,0)]=Fraction(1);canonical[(owner,6,i,0)]=Fraction(1)
    out={};ties=0;unresolved=0
    for record in records:
        part=record['sourcePart'];cell=tuple(record['cellYX']);hist=defaultdict(Fraction)
        choices=[k for k in available if k[1]==part]
        if not choices:continue
        for s in record['samples']:
            bounds=s['visibleBounds']if external_hair_in_shape else s['faceVisibleBounds']
            if bounds[0]<=0:continue
            if part==6:
                d=((uv[visible]-s['UV'])**2).sum(1);ix=np.where(d==d.min())[0];keys=[(owner,6,visible[i],0)for i in ix]
            else:
                ids=ctx['indices'][part][s['primitive']-1];rest=np.r_[np.array(s['barycentric'])@domain['rest'][ids],1];q=rest@projection[owner];centres=np.array([[k[2]+.5,k[3]+.5]for k in choices]);d=((centres-q)**2).sum(1);ix=np.where(d==d.min())[0];keys=[choices[i]for i in ix]
            if len(keys)!=1:ties+=1;continue
            key=keys[0];hist[key]+=Fraction(1);s['transportedSourceKey']=list(key)
        if not hist:unresolved+=1
        out[(cell[0],cell[1],record['part'])]=dict(hist)
    return out,available,canonical,{'bankSourceCheck':check,'exactTransportTiesUnresolved':ties,'carrierCellsWithoutUniqueSourceID':unresolved,'transportRule':'rest-head-bank-centre / native-UV-section; not RGB nearest'}

def histogram(cells,labels,transported):
    hist=defaultdict(Fraction)
    for (y,x),p in zip(cells,labels):
        if p:
            for k,v in transported.get((y,x,p),{}).items():hist[k]+=v
    return dict(hist)

def rank(solutions,cells,transported,available,canonical,prior):
    h=[histogram(cells,v,transported)for v in solutions];vectors=[{p:conditional_l1(canonical,v,available,p)for p in [1,4,6]}for v in h];intrinsic=nondominated(vectors);winners=set(intrinsic);history=[]
    if prior:
        winners=set()
        for previous in prior:
            a=[{p:conditional_l1(previous,h[i],available,p)for p in [1,4,6]}for i in intrinsic];ix=nondominated(a);winners.update(intrinsic[i]for i in ix);history.append([{str(p):str(v)if v is not None else None for p,v in q.items()}for q in a])
    return sorted(winners),[h[i]for i in sorted(winners)],{'intrinsicNondominated':intrinsic,'immutableFormPartVectors':[{str(p):str(v)if v is not None else None for p,v in q.items()}for q in vectors],
      'historyAvailable':bool(prior),'historyPartVectors':history,'historyAfterCurrentEligibilityAndGeometry':True,'noRGBScore':True}

def encode(hist):return [{'key':list(k),'weight':str(v)}for k,v in sorted(hist.items())]

def observed_key_centres(row,owner):
    """Current deformed source-ID geometry, independently from its palette.
    Legitimate deformation changes this reference. A previous output is never
    promoted to canonical geometry. Exact binary inputs -> rational centroids.
    """
    p=source_packet(row);m=read(p/'RAW_MANIFEST.json');w,h=m['forward102']['canonicalSize'];a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);v=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4);lo,*_=joint_arrays(a,v);reg=read(P109/'inputs/REGISTRATION89.json');projection=np.asarray(next(e for e in reg['eyes']if e['eye']==owner)['nativeToAuthoredProjection'],np.float32);sums={}
    for part,i in [(1,1),(4,2)]:
        for y,x in np.argwhere((lo[i-1]>0)&(np.rint(a[i,1,:,:,2])==owner)):
            q=np.r_[a[i,2,y,x,:3],np.float32(1)].astype(np.float32)@projection;k=tuple([owner,part,*np.floor(q).astype(int)]);weight=Fraction(float(lo[i-1,y,x]));record=sums.setdefault(k,[Fraction(0),Fraction(0),Fraction(0)]);record[0]+=weight;record[1]+=weight*Fraction(2*int(x)+1,8);record[2]+=weight*Fraction(2*int(y)+1,8)
    return {k:(x/w,y/w)for k,(w,x,y)in sums.items()}

def relative_form(cells,labels,transported,expected,available):
    sums={}
    for(y,x),p in zip(cells,labels):
        if p not in [1,2]:continue
        for key,weight in transported.get((y,x,p),{}).items():
            if key not in expected or key not in available:continue
            q=sums.setdefault(key,[Fraction(0),Fraction(0),Fraction(0)]);q[0]+=weight;q[1]+=weight*Fraction(2*x+1,2);q[2]+=weight*Fraction(2*y+1,2)
    centres={k:(x/w,y/w)for k,(w,x,y)in sums.items()};out={}
    for p in [1,4]:
        keys=[k for k in expected if k[1]==p and k in available];pairs=[(a,b)for i,a in enumerate(keys)for b in keys[i+1:]];lost=0;error=Fraction(0)
        for a,b in pairs:
            if a not in centres or b not in centres:lost+=1;continue
            error+=sum(((centres[a][j]-centres[b][j])-(expected[a][j]-expected[b][j]))**2 for j in [0,1])
        out[f'{p}:missingSourcePairs']=Fraction(lost,max(1,len(pairs)));out[f'{p}:relativeGeometry']=error/max(1,len(pairs))
    return out

def rank_with_relative(solutions,cells,transported,available,canonical,prior,expected):
    """Histogram identity is insufficient for shape; add actual source-key
    relative geometry as SEPARATE Pareto dimensions, never a fitted weight.
    Missing pairs and displacement stay distinct. Unobserved native interval
    transport is not silently certified by the iris/white pair criterion.
    """
    h=[histogram(cells,v,transported)for v in solutions];vectors=[]
    for labels,v in zip(solutions,h):
        q={str(p):conditional_l1(canonical,v,available,p)for p in [1,4,6]};q.update(relative_form(cells,labels,transported,expected,available));vectors.append(q)
    intrinsic=nondominated(vectors);winners=set(intrinsic);history=[]
    if prior:
        winners=set();groups={}
        for i in intrinsic:groups.setdefault(tuple(vectors[i].values()),[]).append(i)
        # History breaks genuinely equal current-form scores only. It cannot
        # turn a tradeoff between source shape and identity into a fake tie.
        for equal in groups.values():
            if len(equal)==1:winners.add(equal[0]);continue
            for previous in prior:
                a=[{p:conditional_l1(previous,h[i],available,p)for p in [1,4,6]}for i in equal];ix=nondominated(a);winners.update(equal[i]for i in ix);history.append({'equalCurrentFormIndices':equal,'partVectors':[{str(p):str(v)if v is not None else None for p,v in q.items()}for q in a]})
    return sorted(winners),[h[i]for i in sorted(winners)],{'intrinsicNondominated':intrinsic,'sourceFormDimensions':[{str(p):str(v)if v is not None else None for p,v in q.items()}for q in vectors],
      'historyAvailable':bool(prior),'historyPartVectors':history,'historyAfterCurrentEligibilityAndGeometry':True,'noRGBScore':True,'nativeIntervalRelativeGeometryNotCertified':True}
