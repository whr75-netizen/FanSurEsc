from pathlib import Path
import numpy as np
from history75 import preference
from correspondence68 import read_geometry
import review_width72 as audit
H=Path(__file__).resolve().parent;G=H/'face75';C=G/'capture'
def prepare(report,f):
 info=f['frameInfo']['runtimeHistory75'];previous=[p for p in report['frames']if p['frame']==f['frame']-1]
 if not previous:assert info['previousActualFrame']==-1 and not info['readPreviousGPUOwnerAtlas'];return None
 old=previous[0];assert info['previousActualFrame']==old['frame']and info['previousSourceId']==old['sourceId']and info['readPreviousGPUOwnerAtlas']
 current=read_geometry(C/f"all-source-frame{f['frame']}.bin")[3][1];before=read_geometry(C/f"all-source-frame{old['frame']}.bin")[3][1];vertices,indices=current;oldvertices,oldindices=before;assert np.array_equal(indices[3],oldindices[3])and np.array_equal(vertices[:,3:5],oldvertices[:,3:5]);uv=vertices[:,3:5][indices[3]]
 def grid(v,frame):
  join=np.asarray(frame['frameInfo']['nativeComposite42']['joinOffset']);out=v[:,5:7].copy().astype(float);out[:,0]=out[:,0]-.5+join[0];out[:,1]=272-out[:,1]-.5+join[1];q=frame['QROI'];return out[indices[3]],np.array([q[0]+join[0],272-q[1]-q[3]+join[1]])
 now,origin=grid(vertices,f);previous,oldorigin=grid(oldvertices,old);w=old['QROI'][2];atlas=audit.api.plane(report,old,'atlas40');owner=atlas[:,15*w:16*w];role=info['currentMappedRole']
 return lambda yy,xx,y,x,key:preference(np.array([xx,yy])+origin,np.array([x,y])+origin,key,uv,now,previous,owner,oldorigin,role)
audit.G=G;audit.C=C;audit.HALO=2;audit.SUFFIX=75;audit.CASE2_MAPPED=True;audit.HISTORY_PREPARE=prepare
audit.main()
