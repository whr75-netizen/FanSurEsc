"""Frozen-source reference. Compare feature union against canvas FIRST.

The old Select kernel compares each small eye PART with the canvas as if they
were unrelated features. No target pixel count, RGB distance or light value is
used here. Source depth resolves equal part coverage only when unique.
"""
import numpy as np
def choose(L,U,zweight,zsum):
 L=np.asarray(L,dtype=np.float32);U=np.asarray(U,dtype=np.float32)
 eyeL=np.float32(16-U[3]);eyeU=np.float32(16-L[3])
 exact=bool(np.array_equal(L,U))
 if L[3]>eyeU:return {'winner':3,'reason':'canvas union coverage'}
 if not(eyeL>U[3]or(exact and eyeL==U[3]and eyeL>0)):
  return {'winner':-1,'reason':'uncertain feature/canvas coverage'}
 winners=[p for p in range(3)if all(L[p]>U[q]for q in range(3)if q!=p)]
 if len(winners)==1:return {'winner':winners[0],'reason':'whole-feature first, unique part coverage'}
 if not exact:return {'winner':-1,'reason':'uncertain part coverage'}
 maxL=max(L[:3]);candidates=[p for p in range(3)if L[p]==maxL and L[p]>0]
 means={p:float(zsum[p]/zweight[p])for p in candidates if zweight[p]>0}
 if not means:return {'winner':-1,'reason':'no positive source support'}
 nearest=min(means.values());front=[p for p,z in means.items()if z==nearest]
 return {'winner':front[0]if len(front)==1 else-1,'reason':'source depth part tie'if len(front)==1 else'exact coverage and source-depth tie','means':means}

def cell(layers,vis,x,y):
 # Source layout [part,field,y,x,rgba]; no image reconstruction or data mixing.
 L=np.zeros(4,np.float32);U=L.copy();zw=np.zeros(3,np.float32);zs=zw.copy()
 for yy in range(y*4,y*4+4):
  for xx in range(x*4,x*4+4):
   v=vis[1:4,yy,xx];valid=layers[1:4,1,yy,xx,0]>0;z=np.where(valid,v[:,2],np.finfo(np.float32).max);order=np.argsort(z,kind='stable');tl=np.float32(1);th=np.float32(1)
   for p in order:
    lo,hi=v[p,:2];w=np.float32(tl*lo);L[p]+=w;U[p]+=np.float32(th*hi)
    if w>0:zw[p]+=w;zs[p]+=np.float32(w*z[p])
    tl=np.float32(tl*(1-hi));th=np.float32(th*(1-lo))
   L[3]+=tl;U[3]+=th
 legacy=[p for p in range(4)if all(L[p]>U[q]+1e-7 for q in range(4)if q!=p)]
 out=choose(L,U,zw,zs);out.update({'L':L.tolist(),'U':U.tolist(),'legacyUnique':legacy,'featureUnion':[float(16-U[3]),float(16-L[3])]});return out

def tests():
 assert choose([7,2,0,7],[7,2,0,7],[7,2,0],[7,3,0])['winner']==0
 assert choose([0,0,0,16],[0,0,0,16],[0]*3,[0]*3)['winner']==3
 assert choose([0,0,1,15],[0,0,1,15],[0,0,1],[0,0,1])['winner']==3
 assert choose([5,4,0,7],[5,4,0,7],[5,4,0],[5,8,0])['winner']==0
 assert choose([8,8,0,0],[8,8,0,0],[8,8,0],[8,9,0])['winner']==0
 assert choose([8,8,0,0],[8,8,0,0],[8,8,0],[8,8,0])['winner']==-1
 assert choose([5,3,0,6],[6,4,0,8],[5,3,0],[5,3,0])['winner']==-1
 # Identity is invariant to permutation when source depths are unique.
 for perm in [(0,1,2),(2,0,1),(1,2,0)]:
  L=np.array([8,8,0]);z=np.array([8,9,0]);w=choose(list(L[list(perm)])+[0],list(L[list(perm)])+[0],L[list(perm)],z[list(perm)])['winner'];assert perm[w]==0
 return 10
if __name__=='__main__':print('synthetic selection cases',tests())
