from pathlib import Path
import json,numpy as np
from final_contour41 import resolve,coordinates
H=Path(__file__).resolve().parent;G=H/'face41';G.mkdir(exist_ok=True)
def main():
 ink=np.array([.2,.1,.05],np.float32);line=np.tile(np.r_[ink,1],(9,1));proof=np.tile([5,1,.5,1],(9,1)).astype(np.float32);before=np.tile([.8,.7,.6,1],(9,1)).astype(np.float32);meta=np.tile([5,4,7,1],(9,1)).astype(np.float32);world=np.tile([6,.5,1,1],(9,1)).astype(np.float32);inside=np.ones(9,bool)
 meta[1,0]=4;world[2,0]=4;inside[3]=False;proof[4,3]=0;line[5,0]=.3;proof[6,0]=np.nan;meta[7,0]=0;world[8,0]=0
 a,g=resolve(line,proof,before,meta,world,inside,0,ink);assert np.flatnonzero(g[:,3]==1).tolist()==[0,7];assert np.array_equal(a[g[:,3]!=1],before[g[:,3]!=1]);assert np.array_equal(a[g[:,3]==1,:3],np.tile(ink,(2,1)))
 m,o,v=coordinates([3,7,4,5],[480,272],[8,-2],[1,2]);assert m[0,0].tolist()==[11,258]and o[-1,-1].tolist()==[15,264]and v.all()
 moved,_=resolve(line[:1],proof[:1],before[:1],meta[:1],world[:1],inside[:1],2,ink);assert np.array_equal(moved,before[:1])
 result={'assertions':5,'pixelCases':9,'sourceValidPreserved':True,'styleAndWorldOcclusionPreserved':True,'unknownNotSelected':True,'exactFiniteInk':True,'unselectedRGBUnchanged':True,'headTopLeftToTextureJoinAndOutputDelta':True,'GPUCalls':0};(G/'CPU_FINAL41.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
