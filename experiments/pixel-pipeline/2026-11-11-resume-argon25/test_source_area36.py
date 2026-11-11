from pathlib import Path
import json
import numpy as np
H=Path(__file__).resolve().parent
def resolve(old,labels,own=None,steps=3):
 q=np.asarray(labels,float);own=np.ones((8,8),bool)if own is None else own;n=int(own.sum())
 if n!=64:return old,0,n/64,1
 v,c=np.unique(q,return_counts=True);best=int(c.max());w=v[c==best]
 if len(w)!=1:return old,0,best/64,2
 ring=np.r_[q[0,:],q[1:,-1],q[-1,-2::-1],q[-2:0:-1,0]];trans=sum(abs(ring-np.roll(ring,-1))>.01)
 ix=np.rint(q*(steps-1));valid=np.max(abs(q-ix/(steps-1)))<.001 and ix.min()>=0 and ix.max()<steps
 if not valid or not np.any(abs(q-old)<.01)or ix.max()-ix.min()>1 or trans>2:return old,0,best/64,3
 proposed=float(w[0]);change=abs(proposed-old)>=.01;return proposed,int(change),best/64,5 if change else 4
def main():
 checks=[]
 def check(ok,name):assert ok,name;checks.append(name)
 q=np.zeros((8,8));q[2,0]=.5;q[3,:4]=.5;q[4:7,:5]=.5;q[7,:7]=.5
 check(resolve(.5,q)==(0,1,37/64,5),'actual-style37/27 continuous source boundary chooses area')
 check(resolve(0,np.zeros((8,8)))==(0,0,1,4),'uniform field fixed point')
 check(resolve(.5,np.zeros((8,8)))[3]==3,'unseen original label is not silently discarded')
 partial=np.ones((8,8),bool);partial[0,0]=False
 check(resolve(.5,q,partial)==(.5,0,63/64,1),'one external/unknown sub-sample protects whole pixel')
 tie=np.zeros((8,8));tie[:4]=.5;check(resolve(.5,tie)==(.5,0,.5,2),'exact tie keeps original and reports tie')
 stripe=np.zeros((8,8));stripe[:,2:4]=.5;check(resolve(.5,stripe)[3]==3,'two separate border arcs are not merged by area')
 jump=q.copy();jump[jump==.5]=1;check(resolve(1,jump)[3]==3,'non-adjacent shade levels protected')
 invalid=q.copy();invalid[0,0]=.1;check(resolve(.5,invalid)[3]==3,'no invented quantizer levels')
 for flip in [False,True]:
  for k in range(4):
   a=np.rot90(q,k);a=a[:,::-1]if flip else a;check(resolve(.5,a)==resolve(.5,q),'D4 area/arc invariance '+str((flip,k)))
 out=H/'face36';out.mkdir(exist_ok=True);r={'checks':len(checks),'passed':checks,'GPUCalls':0};(out/'CPU_AREA36.json').write_text(json.dumps(r,indent=2),encoding='utf-8',newline='\n');print(json.dumps(r))
if __name__=='__main__':main()
