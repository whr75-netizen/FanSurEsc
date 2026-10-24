"""Conservative coverage upper bound: union of possible feature-reference domains
intersected with possible skin/eyeline support and the recorded packet hair test.
Ignoring brow/body and hidden reference surfaces only enlarges this bound.
Cells are disjoint dyadic rectangles. Uncertain rectangles contribute their full area.
This is not a rendering algorithm or a new selection rule.
"""
import sys,json,time
from pathlib import Path
import numpy as np
from geometry_oracle585 import Frame,R
def alpha_range(f,t,c,h):
 if f.global_alpha[t,0]==f.global_alpha[t,1]:return f.global_alpha[t]*f.alpha[t]
 uv=c@f.uv[t,:2]+f.uv[t,2];er=h*np.abs(f.uv[t,:2]).sum(axis=0);return np.array(f.tex_bounds(uv-er,uv+er,f.mi[t]))*f.alpha[t]
def lash_possible(f,ids,c,h):
 u=f.uc[ids,:2]@c+f.uc[ids,2];du=h*np.abs(f.uc[ids,:2]).sum(axis=1);v=f.vc[ids,:2]@c+f.vc[ids,2];dv=h*np.abs(f.vc[ids,:2]).sum(axis=1);ul,uh=u-du,u+du;u2min=np.where((ul<=0)&(uh>=0),0,np.minimum(ul*ul,uh*uh));u2max=np.maximum(ul*ul,uh*uh);a,b=f.cfg['UpperLower348'][:2];gl=v-dv-a-b*u2max;gh=v+dv-a-b*u2min
 return (uh>=-1.08)&(ul<=1.08)&(gh>=-.36)&(gl<=.22)
def known_skin(f,ids,c,h):
 if not len(ids):return None
 B=f.B[ids];bv=B[:,:,:2]@c+B[:,:,2];br=h*np.abs(B[:,:,:2]).sum(axis=2);possible=np.all(bv+br>=-1e-11,axis=1);inside=np.all(bv-br>=1e-11,axis=1);amin=[];amax=[]
 for t in ids:
  a,b=alpha_range(f,t,c,h);amin.append(a);amax.append(b)
 amin=np.array(amin);amax=np.array(amax);possible&=np.where(f.mode[ids]==1,amax>=f.cut[ids]-1/2048,amax>0)
 opaque=(f.mode[ids]==0)|((f.mode[ids]==1)&(amin>=f.cut[ids]+1/2048));covered=np.flatnonzero(inside&opaque)
 if not len(covered):return None
 depths=f.depth[ids,:2]@c+f.depth[ids,2];k=covered[np.argmin(depths[covered])];t=ids[k];diff=f.depth[ids]-f.depth[t];dmin=diff[:,:2]@c+diff[:,2]-h*np.abs(diff[:,:2]).sum(axis=1);possible[k]=False
 # A closer or exactly coplanar competing fragment with different attributes is uncertain.
 identical=(np.abs(f.uc[ids]-f.uc[t]).max(axis=1)<1e-9)&(np.abs(f.vc[ids]-f.vc[t]).max(axis=1)<1e-9)&(np.abs(f.owner[ids]-f.owner[t]).max(axis=1)<1e-9)&(np.abs(f.depth[ids]-f.depth[t]).max(axis=1)<1e-10)&(f.front[ids]==f.front[t])
 if np.any(possible&(dmin<=0)&~identical):return None
 return t
def upper_possible(f,ids,c,h,hair,skin):
 t=known_skin(f,skin,c,h)
 if t is not None:
  own=f.owner[t,:2]@c+f.owner[t,2];od=h*np.abs(f.owner[t,:2]).sum()
  if f.front[t] and own-od>1.5 and own+od<2.5:
   if not lash_possible(f,np.array([t]),c,h)[0]:return 0
   d=f.depth[t,:2]@c+f.depth[t,2];dd=h*np.abs(f.depth[t,:2]).sum()
   hair_cov=hair[0]>0 and hair[1]>.5 and hair[3]>1e-6
   if hair_cov and hair[3]>=1-1e-8 and d-dd>hair[0]+1e-10:return 0
   u=f.uc[t,:2]@c+f.uc[t,2];du=h*np.abs(f.uc[t,:2]).sum();v=f.vc[t,:2]@c+f.vc[t,2];dv=h*np.abs(f.vc[t,:2]).sum();ul,uh=u-du,u+du;a,b=f.cfg['UpperLower348'][:2];mn=0 if ul<=0<=uh else min(ul*ul,uh*uh);mx=max(ul*ul,uh*uh)
   full=ul>=-1.08 and uh<=1.08 and v-dv-a-b*mx>=-.36 and v+dv-a-b*mn<=.22
   # Exact interior of the relaxed upper-bound region. It need not be subdivided.
   if full and (not hair_cov or d+dd<=hair[0]):return 1
   return 2
 if not len(ids):return False
 B=f.B[ids];bv=B[:,:,:2]@c+B[:,:,2];br=h*np.abs(B[:,:,:2]).sum(axis=2);possible=np.all(bv+br>=-1e-11,axis=1)
 own=f.owner[ids,:2]@c+f.owner[ids,2];od=h*np.abs(f.owner[ids,:2]).sum(axis=1);possible&=(own+od>=1.5)&(own-od<=2.5)
 ids=ids[possible]
 if not len(ids):return False
 almax=[]
 for t in ids:
  if f.global_alpha[t,0]==f.global_alpha[t,1]:a=f.global_alpha[t,1]
  else:
   uv=c@f.uv[t,:2]+f.uv[t,2];er=h*np.abs(f.uv[t,:2]).sum(axis=0);_,a=f.tex_bounds(uv-er,uv+er,f.mi[t])
  almax.append(a*f.alpha[t])
 am=np.array(almax);keep=np.where(f.mode[ids]==1,am>=f.cut[ids]-1/2048,np.where(f.mode[ids]==2,am>0,True));ids=ids[keep]
 if not len(ids):return False
 u=f.uc[ids,:2]@c+f.uc[ids,2];du=h*np.abs(f.uc[ids,:2]).sum(axis=1);v=f.vc[ids,:2]@c+f.vc[ids,2];dv=h*np.abs(f.vc[ids,:2]).sum(axis=1);ul,uh=u-du,u+du;u2min=np.where((ul<=0)&(uh>=0),0,np.minimum(ul*ul,uh*uh));u2max=np.maximum(ul*ul,uh*uh);a,b=f.cfg['UpperLower348'][:2];gl=v-dv-a-b*u2max;gh=v+dv-a-b*u2min
 feature=np.isin(f.s[ids],[0,1,2,3])&(uh>=-1.08)&(ul<=1.08)&(gh>=-.36)&(gl<=.22)
 if not np.any(feature):return False
 support=np.isin(f.s[ids],[0,3])
 if hair[0]>0 and hair[1]>.5 and hair[3]>=1-1e-8:
  d=f.depth[ids,:2]@c+f.depth[ids,2];dd=h*np.abs(f.depth[ids,:2]).sum(axis=1);support&=d-dd<=hair[0]+1e-10
 return 2 if np.any(support) else 0
def upper_bounds(f,maxdepth=9):
 states=[]
 for x,y in f.possible_cells():
  box=(f.box[:,0,0]<=x+1)&(f.box[:,1,0]>=x)&(f.box[:,0,1]<=y+1)&(f.box[:,1,1]>=y);ids=np.flatnonzero(np.isin(f.s,[0,1,2,3])&f.rendered&f.front&box);skin=np.flatnonzero((f.s==0)&f.rendered&box);states.append((ids,skin,f.cells[x,y,'HairMETA'],[np.array([x+.5,y+.5])]))
 start=time.perf_counter();out=[];accepted=0
 for level in range(maxdepth+1):
  h=.5/(2**level);count=0;new=[]
  for ids,skin,hair,centres in states:
   kept=[]
   for c in centres:
    result=upper_possible(f,ids,c,h,hair,skin)
    if result==1:accepted+=(2*h)**2
    elif result==2:kept.append(c)
   count+=len(kept);new.append((ids,skin,hair,kept))
  bound=accepted+count*(2*h)**2+f.degenerateArea;out.append({'depth':level,'pitch':2*h,'areaUpper':bound,'acceptedRelaxedArea':accepted,'remainingRectangles':count,'seconds':time.perf_counter()-start});print(json.dumps({'frame':f.i,**out[-1]}),flush=True)
  if level==maxdepth:break
  shift=np.array([[-h/2,-h/2],[h/2,-h/2],[-h/2,h/2],[h/2,h/2]])
  states=[(ids,skin,hair,[c+d for c in kept for d in shift])for ids,skin,hair,kept in new]
 return out
if __name__=='__main__':
 i=int(sys.argv[1])if len(sys.argv)>1 else 1;f=Frame(i);out=upper_bounds(f,int(sys.argv[2])if len(sys.argv)>2 else 10);(R/f'UPPER_CERT5_{i:03}_585.json').write_text(json.dumps(out,indent=2)+'\n')
