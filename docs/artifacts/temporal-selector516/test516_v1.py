from pathlib import Path
import json,math
import numpy as np
import active516 as G,span516 as S

OUT=G.OUTPUT;OUT.mkdir(exist_ok=True)
def rectangle(x,y,xx,yy):return[(x,y),(xx,y),(xx,yy),(x,yy)]
def make(rings,mask):
    active,stats=G.fragments(rings)
    packets={(int(x),int(y)):{'submesh':0,'primitive':0,'world':[0,0,0],'depth':1.,'bodyForeground':False}for y,x in zip(*np.where(mask))}
    ds=[G.descriptor(e,active,rings,packets)for e in G.boundary(mask)];ss,bad=G.spans(ds)
    assert not bad,(bad,stats)
    return active,ss
def cost(a,b,rings,aa,bb):
    keys=sorted({(s['ring'],s['segment'])for s in a+b})
    vals=[S.channel_cost([s for s in a if(s['ring'],s['segment'])==key],[s for s in b if(s['ring'],s['segment'])==key],rings,aa,bb,key,True)for key in keys]
    return sum(v['raw']for v in vals),vals
m=np.zeros((10,10),bool);m[2:5,2:5]=True;r=[rectangle(2,2,5,5)];aa,a=make(r,m)
identity,details=cost(a,a,r,aa,aa);assert identity==0
mt=np.zeros_like(m);mt[2:5,3:6]=True;rt=[rectangle(3,2,6,5)];bb,b=make(rt,mt);translation,_=cost(a,b,rt,aa,bb);assert translation<1e-12
# Rotate the same source parameterization and mask around the centre.
rr=[[(7-y,x)for x,y in r[0]]];mr=np.zeros_like(m)
for y,x in zip(*np.where(m)):mr[x,6-y]=True
cc,c=make(rr,mr);rotation,_=cost(a,c,rr,aa,cc);assert rotation<1e-12
# Geometry no longer carries this active boundary: cancellation by a reversed
# coincident region must terminate its correspondence instead of keeping it.
dead,st=G.fragments([r[0],list(reversed(r[0]))]);assert len(dead)==0
ended=[S.channel_cost([s for s in a if s['segment']==i],[],[r[0],list(reversed(r[0]))],aa,dead,(0,i),True)for i in range(4)]
assert sum(v['raw']for v in ended)==0 and sum(v['resetOldSpans']for v in ended)==len(a)
# Collinear overlap and T junctions are split before union; multiplicity
# remains explicit and cannot acquire a singular ID by array order.
merged,ms=G.fragments([rectangle(1,1,4,4),rectangle(3,1,6,4)])
assert ms['unbalancedNodes']==0 and any(len(e['lineages'])>1 for e in merged)
# A known foreground packet invalidates history regardless of old identity.
pk={(2,2):{'submesh':0,'primitive':0,'world':[0,0,0],'depth':1.,'bodyForeground':True}}
front=G.descriptor({'a':(2,2),'b':(3,2),'inside':[2,2]},aa,r,pk)
assert not front['valid']and front['reason']=='CURRENT_FOREGROUND_RESET'
# Nonidentity costs are finite and never exceed delete-all + add-all.
shifted=dict(a[0]);shifted['samples']=[dict(v,q=[v['q'][0]+.2,v['q'][1]])for v in a[0]['samples']]
e=S.edit([a[0]],[shifted],r,True);assert 0<e['raw']<=e['deleteAddUpperBound']
out={'identityCost':identity,'integerTranslationCost':translation,'rigidRotation90Cost':rotation,'activeBoundaryEndedHistoryCost':sum(v['raw']for v in ended),'endedSpans':sum(v['resetOldSpans']for v in ended),'collinearOverlapIncidence':ms,'foregroundReset':front['reason'],'nonidentityExample':e,'passed':True,'scope':'Synthetic geometry/DP/reset checks only; no actual hand-crossing Walk/native-world or visual pass.'}
(OUT/'FIXTURES516.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
