from pathlib import Path
import json,numpy as np
from alpha_support38 import AlphaSupport
H=Path(__file__).resolve().parent;G=H/'face38';passed=[]
def check(name,test):assert test,name;passed.append(name)
def partition(labels):
 z=labels.reshape(-1);return(z[:,None]==z[None,:])&(z[:,None]>0)&(z[None,:]>0)
def main():
 a=np.array([[0,0,0],[0,254,0],[0,0,0]],np.uint8);s=AlphaSupport(a,False)
 check('partial native pigment is not rejected as nonopaque',s.sample((.5,.5))['supportId']==1 and s.sample((.5,.5))['alpha']==254/255)
 check('positive bilinear AA carries original identity',s.sample((.35,.5))['supportId']==1 and 0<s.sample((.35,.5))['alpha']<254/255)
 check('empty footprint stays absent',s.sample((0,0))['supportId']==0 and s.sample((0,0))['alpha']==0)
 d=np.array([[255,0],[0,255]],np.uint8);r=AlphaSupport(d,False);q=r.sample((.5,.5))
 check('diagonal components do not become one family',len(r.regions)==2 and q['ambiguous']and q['supportId']==0 and q['sourceIds']==[1,2])
 h=np.full((5,5),127,np.uint8);h[2,2]=0;r=AlphaSupport(h,False)
 check('transparent hole survives support extraction',r.labels[2,2]==0 and len(r.regions)==1)
 a=np.zeros((4,5),np.uint8);a[1,0]=1;a[1,-1]=254
 check('repeat is source sampler topology',len(AlphaSupport(a,True).regions)==1 and len(AlphaSupport(a,False).regions)==2)
 a=np.array([[0,255,0,0],[0,0,0,254],[255,0,0,254],[255,255,0,0]],np.uint8);base=AlphaSupport(a,False)
 for flip in [False,True]:
  for k in range(4):
   f=lambda x:np.rot90(np.fliplr(x)if flip else x,k)
   check('D4 source partition '+str((flip,k)),np.array_equal(partition(AlphaSupport(f(a),False).labels),partition(f(base.labels))))
 try:base.sample((float('nan'),0));raise AssertionError('nonfinite accepted')
 except ValueError:passed.append('nonfinite UV rejected')
 check('texel count and alpha retained',sum(x['sourceTexels']for x in base.regions)==np.count_nonzero(a)and np.array_equal(base.alpha,a))
 q=AlphaSupport(d,False).sample((.25,.25));check('footprint ambiguity is not hidden by zero ideal weight',q['supportId']==1 and q['footprintSupportId']==0 and q['footprintSourceIds']==[1,2])
 check('source alpha envelope remains independent of identity',q['alphaEnvelope']==[0.,1.])
 G.mkdir(exist_ok=True);(G/'CPU_ALPHA38.json').write_text(json.dumps({'checks':len(passed),'passed':passed,'UnityGPUCalls':0,'colourFamilyDefined':False,'finalPixelOwnerDefined':False},indent=2),encoding='utf-8',newline='\n');print(json.dumps({'checks':len(passed),'passed':True}))
if __name__=='__main__':main()
