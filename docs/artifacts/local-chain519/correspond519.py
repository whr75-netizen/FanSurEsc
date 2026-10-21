"""Crossing-anchored local ribbon chains replace whole-unit predicates.

Only correspondence is changed. No mask, coefficients or temporal recurrence.
Existing accepted518 candidates are retained. Only a missing candidate can be
replaced by an exact endpoint-paired chain. Unresolved branches remain explicit.
"""
from collections import defaultdict
from fractions import Fraction as Q
import math
import numpy as np
import arc517 as A,edge518 as E,face518 as F,chain519 as C

def reverse(entries):return[{**e,'a':e['b'],'b':e['a']}for e in entries[::-1]]

class Correspondence:
    def __init__(self,incidence,arcs):
        self.incidence=incidence;self.arcs=arcs;self.chains=None;self.pairs=[];self.pixelIndex=defaultdict(list);self.unanchored=set();self.unresolved=set();self.sourceLookup={};self.stats=defaultdict(int)

    def _ensure_chains(self):
        if self.chains is not None:return
        # Accepted518 candidates do not depend on this new representation.
        # Construct it only after an actual per-edge candidate rejection.
        self.chains=C.LocalChains(self.incidence);o=self.incidence.overlay
        for root,cycles in self.chains.runs.items():
            for ci,parts in enumerate(cycles):
                pixelParts=[p for p in parts if p['roles']==('PIXEL',)];sourceParts=[p for p in parts if p['roles']==('SOURCE',)]
                pixelEdges={s['edge']for p in pixelParts for e in p['entries']for s in e['records']if'edge'in s}
                if len(parts)==2 and len(pixelParts)==len(sourceParts)==1:
                    pixel=pixelParts[0]['entries'];source=sourceParts[0]['entries'];tag=o.components[root]['tag']
                    if tag=='A':source=reverse(source)
                    else:pixel=reverse(pixel)
                    assert pixel[0]['a']==source[0]['a']and pixel[-1]['b']==source[-1]['b'],('CHAIN_ENDPOINTS_NOT_SHARED',root)
                    pc=[Q(0)];sc=[0.]
                    for e in pixel:pc.append(pc[-1]+abs(e['b'][0]-e['a'][0])+abs(e['b'][1]-e['a'][1]))
                    for e in source:sc.append(sc[-1]+math.hypot(float(e['b'][0]-e['a'][0]),float(e['b'][1]-e['a'][1])))
                    pair={'id':len(self.pairs),'root':root,'cycle':ci,'tag':tag,'pixel':pixel,'source':source,'pixelCum':pc,'sourceCum':sc,'pixelLength':pc[-1],'sourceLength':sc[-1]}
                    self.pairs.append(pair)
                    for k,e in enumerate(pixel):
                        for s in e['records']:
                            if'edge'in s:self.pixelIndex[s['edge']].append((pair,k,e))
                elif len(parts)==1 and(pixelParts or sourceParts):self.unanchored|=pixelEdges
                else:self.unresolved|=pixelEdges

    def source_owner(self,entry):
        key=(entry['a'],entry['b'])
        if key not in self.sourceLookup:
            found=[]
            for ai,arc in enumerate(self.arcs):
                for si,(a,b)in enumerate(zip(arc['exactP'],arc['exactB'])):
                    if E.contains(entry['a'],a,b)and E.contains(entry['b'],a,b)and sum(x*y for x,y in zip(F.sub(b,a),F.sub(entry['b'],entry['a'])))>0:found.append((ai,si))
            assert len(found)==1,('CHAIN_SOURCE_NOT_UNIQUELY_ON_ACTIVE_ARC',key,found)
            self.sourceLookup[key]=found[0]
        return self.sourceLookup[key]

    def local(self,edge,point=None):
        self._ensure_chains()
        e=tuple(edge);p=tuple(Q(v,2)for v in(e[0]+e[2],e[1]+e[3]))if point is None else point;out=[]
        for pair,k,part in self.pixelIndex[e]:
            if not E.contains(p,part['a'],part['b']):continue
            along=pair['pixelCum'][k]+abs(p[0]-part['a'][0])+abs(p[1]-part['a'][1]);fraction=along/pair['pixelLength'];target=float(fraction)*pair['sourceLength'];si=min(len(pair['source'])-1,int(np.searchsorted(pair['sourceCum'],target,side='right')-1));si=max(0,si)
            source=pair['source'][si];lo,hi=pair['sourceCum'][si:si+2];t=np.clip((target-lo)/(hi-lo),0.,1.);q=np.array(source['a'],float)+float(t)*np.array(F.sub(source['b'],source['a']),float);ai,index=self.source_owner(source);arc=self.arcs[ai];a,d=arc['p'][index],arc['d'][index];tt=float(np.clip(np.dot(q-a,d)/np.dot(d,d),0.,1.));reference=a+tt*d
            direction=np.array([e[2]-e[0],e[3]-e[1]],float);ends=np.array([e[:2],e[2:]],float);et=np.clip(((ends-a)*d).sum(1)/np.dot(d,d),0,1);dist=((ends-(a+et[:,None]*d))**2).sum(1)
            assert self.incidence.candidate_support(e,E.source_segment(arc,index))['accepted']
            out.append({'arc':ai,'segment':index,'q':[float(v)for v in p],'direction':direction.tolist(),'edge':e,'reference':reference.tolist(),'tangent':(d/arc['length'][index]).tolist(),'u':float(((arc['cum'][index]+tt*arc['length'][index])/arc['total'])%1.),'t':tt,'fit':float(dist.mean()),'bindingRule':'EXACT_ENDPOINT_PAIRED_LOCAL_CHAIN','chain':{'pair':pair['id'],'root':pair['root'],'tag':pair['tag'],'cycle':pair['cycle'],'pixelStart':pair['pixel'][0]['a'],'pixelEnd':pair['pixel'][-1]['b'],'sourceStart':pair['source'][0]['a'],'sourceEnd':pair['source'][-1]['b'],'pixelProgressExact':str(fraction),'pixelLengthExact':str(pair['pixelLength']),'sourceLength':pair['sourceLength'],'sourcePieceIndex':si,'sourcePieceCount':len(pair['source'])}})
        # A centre exactly at a sweep subdivision can occur in two atomic
        # entries of one pair.  It is the same correspondence, not two votes.
        unique={}
        for s in out:unique.setdefault((s['chain']['pair'],s['arc'],s['segment'],tuple(s['reference'])),s)
        return list(unique.values())

    def candidates(self,edge):
        e=tuple(edge);existing=self.existing_candidates(e)
        if existing:
            self.stats['existingAcceptedUnitEdges']+=1
            return existing
        local=self.local(e)
        if local:self.stats['localUnitEdges']+=1;self.stats['localCandidateStates']+=len(local);return local
        if e in self.unresolved:self.stats['unresolvedMultiRunEdges']+=1;return[]
        self.stats['unrepresentedCentreEdges']+=1;return[]

    def existing_candidates(self,edge):
        # Exactly the518 per-unit admission predicates.  This is an accepted
        # correspondence, not a fallback mask/output for a failed new rule.
        # Its use remains labelled; no claim is made that all multi-run or
        # unanchored ribbon correspondence has been replaced by local chains.
        e=tuple(edge)
        p=np.array([(e[0]+e[2])*.5,(e[1]+e[3])*.5]);direction=np.array([e[2]-e[0],e[3]-e[1]]);out=[]
        for ai,arc in enumerate(self.arcs):
            if not arc.get('visible',True):continue
            a,d,ll=arc['p'],arc['d'],arc['length']**2;ends=np.array([p-direction*.5,p+direction*.5]);t=np.clip(((ends[:,None]-a)*d).sum(2)/ll,0,1);q=a+t[:,:,None]*d;dist=((ends[:,None]-q)**2).sum(2);ok=(dist.max(0)<=2+A.EPS)&((direction*d).sum(1)>=-A.EPS);tm=np.clip(((p-a)*d).sum(1)/ll,0,1)
            for si in np.where(ok)[0]:
                if not self.incidence.candidate_support(e,E.source_segment(arc,int(si)))['accepted']:continue
                ref=a[si]+tm[si]*d[si];u=(arc['cum'][si]+tm[si]*arc['length'][si])/arc['total'];out.append({'arc':ai,'segment':int(si),'q':p.tolist(),'direction':direction.tolist(),'edge':e,'reference':ref.tolist(),'tangent':(d[si]/arc['length'][si]).tolist(),'u':float(u%1.),'t':float(tm[si]),'fit':float(dist[:,si].mean()),'bindingRule':'EXISTING518_ACCEPTED_GEOMETRIC_CANDIDATE'})
        return out

    def relate(self,*args,**kwargs):return self.incidence.relate(*args,**kwargs)
    def record(self,edge):return self.incidence.record(edge)
    def summary(self):return{**(self.chains.summary()if self.chains is not None else{'newMask':False}),'chainConstructed':self.chains is not None,'anchoredPairs':len(self.pairs)if self.chains is not None else None,'indexedPixelEdges':len(self.pixelIndex)if self.chains is not None else None,'unanchoredPixelEdges':len(self.unanchored)if self.chains is not None else None,'unresolvedPixelEdges':len(self.unresolved)if self.chains is not None else None,'sourcePiecesResolved':len(self.sourceLookup),'candidateCounts':dict(self.stats),'uniformProgressIsLocalGeometricCorrespondenceNotTemporalHistory':True}
