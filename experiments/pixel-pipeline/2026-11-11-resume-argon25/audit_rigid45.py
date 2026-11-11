from pathlib import Path
import json,numpy as np
from trace_contour40 import geometry
from surface_paths34 import native
H=Path(__file__).resolve().parent
def main():
 surface,_=native();ids=np.unique(surface.indices);c=H/'face45/capture';r=json.loads((c/'COMPLETE.json').read_text());gs=[geometry(c/f"geometry-frame{f['frame']}.bin")for f in r['frames']];rows=[]
 for f,g in zip(r['frames'],gs):
  p=gs[0]['points']['world'][ids].astype(float);q=g['points']['world'][ids].astype(float);pc=p-p.mean(0);qc=q-q.mean(0);u,_,v=np.linalg.svd(pc.T@qc);rot=u@v
  if np.linalg.det(rot)<0:u[:,-1]*=-1;rot=u@v
  e=pc@rot-qc;anchor0=np.asarray(r['frames'][0]['frameInfo']['sourceAnchor']['head']);anchor=np.asarray(f['frameInfo']['sourceAnchor']['head']);res=(g['points']['head'][ids].astype(float)-anchor)-(gs[0]['points']['head'][ids].astype(float)-anchor0);rows.append({'frame':f['frame'],'rigidFitMaxMetres':float(np.linalg.norm(e,axis=1).max()),'anchorRelativeScreenMaxCells':float(np.linalg.norm(res,axis=1).max()),'anchor':anchor.tolist(),'rotationDegrees':float(np.degrees(np.arccos(np.clip((np.trace(rot)-1)/2,-1,1))))})
 (H/'face45/RIGID_PHASE45.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))
if __name__=='__main__':main()
