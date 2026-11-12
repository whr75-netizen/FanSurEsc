from pathlib import Path
import json,numpy as np
from history75 import preference,Scope
from variable_exterior72 import resolve
H=Path(__file__).resolve().parent;G=H/'face75'
def main():
 G.mkdir(exist_ok=True);tests=0;uv=np.array([[[0,0],[1,0],[0,1]]],float);now=np.array([[[5,5],[9,5],[5,9]]],float);at=[.25,.25];key=(4,1,*at);old=now-[.19,.13];cache=np.zeros((15,15,4));cache[6,7]=[104,1,*at]
 assert preference([6,6],[7,6],key,uv,now,old,cache,[0,0],4);tests+=1
 bad=cache.copy();bad[6,7]=[104,1,.9,.01];assert not preference([6,6],[7,6],key,uv,now,old,bad,[0,0],4);tests+=1
 assert not preference([6,6],[7,6],key,uv,now,now-[.5,0],cache,[0,0],4);tests+=1
 assert not preference([6,6],[7,6],(8,1,*at),uv,now,old,cache,[0,0],4);tests+=1
 assert not preference([6,6],[7,6],key,uv,np.zeros_like(now),old,cache,[0,0],4);tests+=1
 for mirrored in[False,True]:
  for k in range(4):
   angle=k*np.pi/2;m=np.rint([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]]);m[:,0]*=-1 if mirrored else 1;centre=np.array([7,7]);transform=lambda a:(np.asarray(a)-centre)@m.T+centre
   q0=transform([6,6]);q1=transform([7,6]);o=np.zeros_like(cache);x,y=transform([7,6]).astype(int);o[y,x]=[104,1,*at]
   assert preference(q0,q1,key,uv,transform(now),transform(old),o,[0,0],4);tests+=1
 s=Scope();assert not s.accept(('model','view',1),100)and s.accept(('model','view',1),101)and not s.accept(('model','view',1),103)and not s.accept(('model','view',2),104)and not s.accept(('model','otherView',2),105);tests+=1
 n=13;a=np.zeros((n,n),bool);a[6,5]=a[6,7]=True;b=np.zeros((n,n,4),np.float32);b[:,:,3]=1;z=np.ones((n,n),np.float32)*3;world=z+4;meta=np.zeros_like(z);keys=np.zeros_like(b);keys[6,5]=[4,1,.1,.1];keys[6,7]=[4,2,.1,.1];inks=np.zeros((n,n,3),np.float32);inks[6,5]=[.1,0,0];inks[6,7]=[0,.1,0];radius=np.ones((n,n),int);callback=lambda yy,xx,y,x,key:xx==7
 unhistoried=resolve(b,a,a,z,world,meta,keys,inks,radius);historied=resolve(b,a,a,z,world,meta,keys,inks,radius,history_preference=callback);assert unhistoried[1][6,6,1]==1 and historied[1][6,6,1]==2;tests+=1
 near=world.copy();near[6,6]=2;assert not resolve(b,a,a,z,near,meta,keys,inks,radius,history_preference=callback)[2][6,6];tests+=1
 hidden=a.copy();hidden[6,7]=False;assert resolve(b,a,hidden,z,world,meta,keys,inks,radius,history_preference=callback)[1][6,6,1]==1;tests+=1
 result={'CPUChecks':tests,'D4OwnerCorrespondenceExact':True,'viewModelGenerationFrameInvalidation':True,'historyOnlyBreaksEqualCurrentGeometryTies':True,'currentOcclusionOverridesHistory':True,'noRGBHistoryInput':True,'wholeShapeOrLongTermStabilityProven':False,'GPUExecuted':False};(G/'CPU_HISTORY75.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
