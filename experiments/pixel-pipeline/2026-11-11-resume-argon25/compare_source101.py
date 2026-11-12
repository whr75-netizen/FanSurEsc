"""Report actual100/101 input differences; never assume equal lighting."""
from pathlib import Path
import json,numpy as np
from actor_visibility96 import packet
H=Path(__file__).resolve().parent

def main():
 left=H/'face100/reasons32';right=H/'face101/source32';A=json.loads((left/'capture/COMPLETE.json').read_text())['stream77']['frames'];B=json.loads((right/'capture/COMPLETE.json').read_text())['stream77']['frames'];assert len(A)==len(B)==32;total=np.zeros(14,np.int64);sameInputs=0;rows=[]
 for f,g in zip(A,B):
  a,_,_=packet(left,f);b,_,_=packet(right,g);diff=(a[:14]!=b[:14]).any(3).sum((1,2));total+=diff;sameInputs+=int(not diff[[0,1,2,13]].any());rows.append({'ordinal':f['ordinal'],'frameA':f['frame'],'frameB':g['frame'],'selectedMetaUVClassNativeCellDifferingCells':diff[[0,1,2,13]].tolist(),'finalRGBDifferingCells':int(diff[7])})
 out={'actualSeparateRuns':True,'frames':len(A),'selectedMetaUVClassNativeCellFullyExactFrames':sameInputs,'allPlaneDifferingCellCounts':total.tolist(),'newMainAlternativeWasUnexercised':True,'rows':rows,'sameCompleteInputNotAssumed':True};(right/'PAIRED_SOURCE101.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items()if k!='rows'})
if __name__=='__main__':main()
