"""517 binding with selector-derived PARTIAL edge incidence.

The only replacement is a selector-derived added/removed-face incidence
witness. No new selection, output mask, edit weight or temporal state rule.
"""
import math
import numpy as np
import arc517 as A
from edge518 import source_segment
EPS=A.EPS

def bind(mask,arcs,region):
    assigned={};unsupported=[];joinCache={}
    def candidates(edge):
        return region.candidates(edge)
    def link(a,b,vertex):
        if a['arc']==b['arc']:
            arc=arcs[a['arc']];sa,sb=a['segment'],b['segment']
            if sa==sb and b['t']>=a['t']-1e-10:return ('CONTINUOUS_ARC',[])
            if sb==(sa+1)%len(arc['p']):
                node=arc['b'][sa]
                if abs(node[0]-vertex[0])<=1+EPS and abs(node[1]-vertex[1])<=1+EPS:return ('CONTINUOUS_ARC_CORNER',[])
        key=(a['edge'],b['edge'],a['arc'],a['segment'],b['arc'],b['segment'])
        if key not in joinCache:
            aa,bb=arcs[a['arc']],arcs[b['arc']];sa,sb=a['segment'],b['segment']
            relation=region.relate(a['edge'],b['edge'],None,source_segment(aa,sa),source_segment(bb,sb))
            joinCache[key]=('SELECTOR_REGION_FACE_JOIN',relation['witness'])if relation['boundaryPathJoin']else None
        return joinCache[key]
    def better(score,aliases,best):return best is None or score<best[0]-1e-10 or abs(score-best[0])<=1e-10 and aliases<best[1]
    for li,loop in enumerate(A.pixel_loops(mask)):
        edges=loop['edges'];states=[candidates(e)for e in edges]
        if any(not s for s in states):unsupported.append({'reason':'NO_GEOMETRIC_UNIT_EDGE_CANDIDATE','pixelLoop':li});continue
        links={}
        def connection(i,a,b):
            key=(i,a,b)
            if key not in links:links[key]=link(states[i-1][a],states[i][b],tuple(edges[i][:2]))
            return links[key]
        best=None
        for first in range(len(states[0])):
            costs={first:(states[0][first]['fit'],0)};backs=[]
            for i in range(1,len(states)):
                current={};back={}
                for b,s in enumerate(states[i]):
                    value=None;winner=None
                    for a,(cost,count)in costs.items():
                        con=connection(i,a,b)
                        if con is None:continue
                        score=cost+s['fit'];aliases=count+(con[0]=='SELECTOR_REGION_FACE_JOIN')
                        if better(score,aliases,value):value=(score,aliases);winner=a
                    if value is not None:current[b]=value;back[b]=winner
                costs=current;backs.append(back)
                if not costs:break
            if len(backs)!=len(states)-1 or not costs:continue
            for last,(cost,count)in costs.items():
                close=link(states[-1][last],states[0][first],tuple(edges[0][:2]))
                if close is None:continue
                count+=close[0]=='SELECTOR_REGION_FACE_JOIN'
                if better(cost,count,None if best is None else best[:2]):
                    path=[last];at=last
                    for i in range(len(backs)-1,-1,-1):at=backs[i][at];path.append(at)
                    best=(cost,count,path[::-1])
        if best is None:unsupported.append({'reason':'NO_CONNECTED_REGION_OWNED_SPAN_PATH','pixelLoop':li});continue
        chosen=[states[i][k]for i,k in enumerate(best[2])];runs=[];run=[];joins=[]
        for i,s in enumerate(chosen):
            con=link(chosen[i-1],s,tuple(edges[i][:2]));assert con is not None;s={**s,'pixelLoop':li,'connectionFromPrevious':con[0],'partialIncidence':region.record(s['edge'])}
            if con[0]=='SELECTOR_REGION_FACE_JOIN':joins.append({'atPixelVertex':edges[i][:2],'fromArc':chosen[i-1]['arc'],'toArc':s['arc'],'regionWitness':con[1]})
            if run and(s['arc']!=run[-1]['arc']or s['direction']!=run[-1]['direction']or con[0]=='SELECTOR_REGION_FACE_JOIN'):runs.append(run);run=[]
            run.append(s)
        if run:runs.append(run)
        if len(runs)>1 and runs[0][0]['arc']==runs[-1][0]['arc']and runs[0][0]['direction']==runs[-1][0]['direction']and runs[0][0]['connectionFromPrevious']!='SELECTOR_REGION_FACE_JOIN':runs[-1]+=runs.pop(0)
        for run in runs:
            ai=run[0]['arc'];value=assigned.setdefault(ai,{'spans':[],'samples':[],'fit':0.,'maxFit':0.,'monotone':True,'regionJoins':[]})
            value['spans'].append({'samples':run,'length':len(run)});value['samples']+=run;value['fit']+=sum(s['fit']for s in run);value['maxFit']=max(value['maxFit'],max(math.sqrt(s['fit'])for s in run))
        for ai in {s['arc']for s in chosen}:assigned[ai]['regionJoins']+=joins
    for value in assigned.values():value['spans'].sort(key=lambda s:(s['samples'][0]['u'],s['samples'][0]['edge']))
    return assigned,unsupported
