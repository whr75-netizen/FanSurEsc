import pickle,json,math
import numpy as np
import active516 as G,arc517 as A
D=G.ROOT/'Region518'
with(D/'FIRST_FULL518.pickle').open('rb')as f:cache=pickle.load(f)
region,arcs=cache['graph'],cache['arcs'];loop=A.pixel_loops(G.read_mask(0))[0];edges=loop['edges']
def candidates(edge):
    p=np.array([(edge[0]+edge[2])*.5,(edge[1]+edge[3])*.5]);direction=np.array([edge[2]-edge[0],edge[3]-edge[1]]);out=[]
    for ai,arc in enumerate(arcs):
        a,d,ll=arc['p'],arc['d'],arc['length']**2;ends=np.array([p-direction*.5,p+direction*.5]);t=np.clip(((ends[:,None]-a)*d).sum(2)/ll,0,1);q=a+t[:,:,None]*d;dd=((ends[:,None]-q)**2).sum(2);valid=(dd.max(0)<=2+A.EPS)&((direction*d).sum(1)>=-A.EPS);tm=np.clip(((p-a)*d).sum(1)/ll,0,1)
        for si in np.where(valid)[0]:out.append({'arc':ai,'segment':int(si),'t':float(tm[si]),'edge':tuple(edge),'sourceA':a[si].tolist(),'sourceB':arc['b'][si].tolist(),'fit':float(dd[:,si].mean())})
    return out
def direct(a,b,vertex):
    if a['arc']!=b['arc']:return False
    arc=arcs[a['arc']];sa,sb=a['segment'],b['segment']
    if sa==sb and b['t']>=a['t']-1e-10:return True
    return sb==(sa+1)%len(arc['p'])and np.max(abs(arc['b'][sa]-vertex))<=1+A.EPS
states=[candidates(e)for e in edges];barriers=[]
for i in range(len(edges)):
    vertex=edges[i][:2];possibilities=[]
    for a in states[i-1]:
        for b in states[i]:
            if direct(a,b,vertex):possibilities.append({'direct':True});continue
            r=region.relate(a['edge'],b['edge'],None,[a['sourceA'],a['sourceB']],[b['sourceA'],b['sourceB']]);possibilities.append({'direct':False,'relation':r,'a':a,'b':b})
    if not any(v.get('direct')or v['relation']['boundaryPathJoin']for v in possibilities):
        unrestricted=region.relate(edges[i-1],edges[i],None);barriers.append({'index':i,'vertex':vertex,'withoutCandidateRestriction':unrestricted,'candidatePairs':possibilities})
out={'barriers':barriers,'count':len(barriers),'noNewGraphOrSelectionOrCapture':True}
(D/'FIRST_FULL_PROBE518.json').write_text(json.dumps(out,indent=2,default=str)+'\n');print(json.dumps({'count':len(barriers),'first':barriers[0]if barriers else None},ensure_ascii=False,default=str))
