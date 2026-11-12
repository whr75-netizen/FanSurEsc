"""Apply original58 targets + CPU92 native constraints; CPU only."""
from pathlib import Path
import struct,json,subprocess,os,numpy as np
from palette_constraints92 import constrained
H=Path(__file__).resolve().parent;G=H/'face92'
def main():
 d=np.load(G/'SOURCE_VALUE92.npz');refs=d['colours'][d['referenceIndices']];a=d['colourAddress'];pairs=d['pairs'];delta=d['colours'][pairs[:,0]].astype(np.int64)-d['colours'][pairs[:,1]];vectors=np.column_stack([a[pairs[:,0]],a[pairs[:,1]],delta]);edges=np.fromfile(G/'ORDERS92.i32','<i4').reshape(-1,2);live=json.loads((H/'face89/fix2/capture/RUNTIME_PALETTE89.json').read_text());ratio=live['adaptedLabRatio'];build=G/'build';build.mkdir(exist_ok=True);inp=build/'targets-input92.bin';out=build/'targets-output92.bin';inp.write_bytes(struct.pack('<ii4d',len(refs),3,ratio,ratio,1,1)+refs.astype('<i4').tobytes());source58=next(p for p in [H.parent/'source-palette58/SourcePalette58.cs',H.parent/'2026-10-31-source-palette58/SourcePalette58.cs']if p.exists());csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';exe=build/'targets92.exe';compile_run=subprocess.run([str(csc),'/nologo','/optimize+','/target:exe','/out:'+str(exe),str(H/'PaletteTargets88.cs'),str(source58)],capture_output=True,text=True);assert compile_run.returncode==0,compile_run.stdout+compile_run.stderr;subprocess.run([str(exe),str(inp),str(out)],check=True);raw=out.read_bytes();n,k=struct.unpack_from('<ii',raw);assert(n,k)==(len(refs),3);targets=np.frombuffer(raw,offset=8,dtype=np.dtype([('target','<f8',(3,)),('old','u1',(3,))]))['target'].reshape(n,3,3);palette=np.zeros((n,3,3),np.uint8);rows=[]
 for k in range(3):
  result=constrained(targets[:,k],edges,vectors);row={name:value for name,value in result.items()if name!='rgb8'};row['shade']=k;rows.append(row)
  if result['feasible']:palette[:,k]=result['rgb8']
 complete=all(row['feasible']for row in rows);r={'CPUOnly':True,'sameOriginal58ContinuousTargets':True,'sameObserved89LinearFloor':live['liveLinearFloor'],'perChannelFloorCeilOnly':True,'nativeConstraints':len(vectors),'allLevelsFeasible':complete,'rows':rows,'actualGPUOrRuntimeCSharpPortTested':False,'artAdopted':False};(G/'PALETTE_CONSTRAINTS92.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
 if complete:palette.tofile(G/'CONSTRAINED92.rgb');np.savez_compressed(G/'PALETTE_CONSTRAINT_INPUT92.npz',targets=targets,orders=edges,vectors=vectors)
if __name__=='__main__':main()
