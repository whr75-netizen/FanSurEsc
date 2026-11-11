from surface_paths34 import UVSurface
import numpy as np,json
from pathlib import Path
def main():
 checks=[]
 def check(ok,name):assert ok,name;checks.append(name)
 uv=np.array([[0,0],[1,0],[0,1],[1,1]],float);indices=[[0,1,2],[1,3,2]]
 s=UVSurface(uv,indices);check(s.path([.2,.2],[.8,.8],0,1)['known'],'shared edge source path')
 check(s.path([.2,.2],[.3,.3],0,0)['known'],'convex same triangle')
 check(not s.path([2,2],[.8,.8],0,1)['known'],'primitive and UV must correspond')
 check(not s.path([.2,.2],[.8,.8],-1,1)['known'],'invalid primitive fails closed')
 seam=UVSurface(np.array([[0,0],[1,0],[0,1],[1,0],[1,1],[0,1]]),[[0,1,2],[3,4,5]])
 check(not seam.path([.2,.2],[.8,.8],0,1)['known'],'touching UV islands with distinct source indices are not joined')
 overlap=UVSurface(np.r_[uv[:3],uv[:3]],[[0,1,2],[3,4,5]])
 check(not overlap.path([.2,.2],[.3,.3],0,1)['known'],'overlapping UV islands are not a shared surface')
 nonmanifold=UVSurface(np.r_[uv,[[.5,-1]]],[[0,1,2],[1,3,2],[1,4,2]])
 check(len(nonmanifold.nonmanifold)==1 and not nonmanifold.path([.2,.2],[.8,.8],0,1)['known'],'nonmanifold edge is not traversed')
 singular=UVSurface([[0,0],[1,0],[2,0]],[[0,1,2]])
 check(not singular.path([.2,0],[.8,0],0,0)['known'],'degenerate source UV stays unknown')
 for swap in [False,True]:
  for sx,sy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
   f=lambda a:np.asarray(a)[...,::-1]*[sx,sy] if swap else np.asarray(a)*[sx,sy]
   t=UVSurface(f(uv),indices);check(t.path(f([.2,.2]),f([.8,.8]),0,1)['known'],'D4 source path '+str((swap,sx,sy)))
 result={'checks':len(checks),'passed':checks,'GPUCalls':0,'doesNotProve':['intermediate deformed visibility','albedo region/gradient semantics','a final Q or RGB improvement']};p=Path(__file__).resolve().parent/'face34/analysis/CPU_PATH_TESTS34.json';p.write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
