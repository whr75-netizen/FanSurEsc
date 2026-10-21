"""Exact boundary cycles of already selected A/D faces; offline only."""
from collections import defaultdict
from functools import cmp_to_key
from fractions import Fraction as Q
import math
import face518 as F

def cmp_clockwise(back,a,b):
    def coordinate(v):return(sum(x*y for x,y in zip(back,v)),-F.cross(back,v))
    a,b=coordinate(a),coordinate(b)
    half=lambda p:0 if p[1]>0 or p[1]==0 and p[0]>=0 else 1
    ha,hb=half(a),half(b)
    if ha!=hb:return -1 if ha<hb else 1
    cross=F.cross(a,b)
    if cross:return -1 if cross>0 else 1
    return 0

class LocalChains:
    def __init__(self,incidence):
        self.incidence=incidence;self.overlay=incidence.overlay;self.entries=defaultdict(dict);self.cycles={};self.runs={};self.ambiguous=[]
        o=self.overlay
        def add(root,a,b,role,record):
            item=self.entries[root].setdefault((a,b),{'a':a,'b':b,'roles':set(),'records':[]});item['roles'].add(role);item['records'].append(record)
        for s in o.source:
            for root in{ o.changed.root(fid)for fid in s['changeFaces']}:
                a,b=s['a'],s['b']
                if o.components[root]['tag']=='A':a,b=b,a
                add(root,a,b,'SOURCE',s)
        for s in o.pixel:
            for root in{o.changed.root(fid)for fid in s['changeFaces']}:
                a,b=s['a'],s['b']
                if o.components[root]['tag']=='D':a,b=b,a
                add(root,a,b,'PIXEL',s)
        for root,edges in self.entries.items():
            outgoing=defaultdict(list);incoming=defaultdict(list)
            for key in edges:outgoing[key[0]].append(key);incoming[key[1]].append(key)
            assert set(outgoing)==set(incoming),('OPEN_CHANGED_COMPONENT_BOUNDARY',root)
            assert all(len(outgoing[p])==len(incoming[p])for p in outgoing),('UNBALANCED_COMPONENT_BOUNDARY',root)
            successor={}
            for a,b in edges:
                back=F.sub(a,b);choices=outgoing[b]
                ordered=sorted(choices,key=cmp_to_key(lambda x,y:cmp_clockwise(back,F.sub(x[1],x[0]),F.sub(y[1],y[0]))))
                if len(ordered)>1 and cmp_clockwise(back,F.sub(ordered[0][1],b),F.sub(ordered[1][1],b))==0:self.ambiguous.append({'root':root,'vertex':b,'reason':'COINCIDENT_OUTGOING_RAYS'})
                successor[a,b]=ordered[0]
            assert len(set(successor.values()))==len(edges),('NON_BIJECTIVE_BOUNDARY_SUCCESSOR',root)
            unused=set(edges);cycles=[];runs=[]
            while unused:
                first=min(unused);at=first;cycle=[]
                while at in unused:
                    unused.remove(at);cycle.append(edges[at]);at=successor[at]
                assert at==first,('OPEN_OR_CROSS_LINKED_CYCLE',root)
                cycles.append(cycle);parts=[]
                for e in cycle:
                    role=tuple(sorted(e['roles']))
                    if parts and parts[-1]['roles']==role:parts[-1]['entries'].append(e)
                    else:parts.append({'roles':role,'entries':[e]})
                if len(parts)>1 and parts[0]['roles']==parts[-1]['roles']:parts[-1]['entries']+=parts.pop(0)['entries']
                for part in parts:
                    part['cycle']=len(cycles)-1;part['a']=part['entries'][0]['a'];part['b']=part['entries'][-1]['b'];part['length']=sum(math.hypot(float(e['b'][0]-e['a'][0]),float(e['b'][1]-e['a'][1]))for e in part['entries'])
                runs.append(parts)
            self.cycles[root]=cycles;self.runs[root]=runs

    def describe(self,root):
        return{'root':root,'tag':self.overlay.components[root]['tag'],'atomicBoundaryEdges':len(self.entries[root]),'cycles':[{'edges':len(cycle),'runs':[{'roles':p['roles'],'a':p['a'],'b':p['b'],'entries':len(p['entries']),'length':p['length']}for p in parts]}for cycle,parts in zip(self.cycles[root],self.runs[root])]}

    def summary(self):
        runs=[parts for cycles in self.runs.values()for parts in cycles]
        return{'changedComponents':len(self.entries),'boundaryHalfEdges':sum(len(e)for e in self.entries.values()),'boundaryCycles':len(runs),'roleRuns':sum(len(p)for p in runs),'singleSourcePixelPairCycles':sum(len(p)==2 and{q['roles']for q in p}=={('SOURCE',),('PIXEL',)}for p in runs),'nonAlternatingOrMultiPairCycles':sum(not(len(p)==2 and{q['roles']for q in p}=={('SOURCE',),('PIXEL',)})for p in runs),'ambiguities':self.ambiguous,'newMask':False}
