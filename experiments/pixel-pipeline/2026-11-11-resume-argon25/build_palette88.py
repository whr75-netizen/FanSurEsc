from pathlib import Path
import os,json,struct,subprocess,numpy as np
from palette_round88 import solve
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face88'

def main():
 (G/'build').mkdir(exist_ok=True);data=np.load(G/'SOURCE_VALUE88.npz');refs=data['colours'][data['referenceIndices']];spec=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());settings=spec['settingsFromExisting58'];levels=settings['count'];inp=G/'build/palette-input.bin';inp.write_bytes(struct.pack('<ii4d',len(refs),levels,*[settings[k]for k in ['darkLRatio','darkCRatio','gamma','intervalScale']])+refs.astype('<i4').tobytes());source58=next(p for p in [H.parent/'source-palette58/SourcePalette58.cs',H.parent/'2026-10-31-source-palette58/SourcePalette58.cs']if p.exists());exe=G/'build/targets88.exe';csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';subprocess.run([str(csc),'/nologo','/optimize+','/target:exe','/out:'+str(exe),str(H/'PaletteTargets88.cs'),str(source58)],check=True,capture_output=True);detail=G/'build/palette-targets.bin';subprocess.run([str(exe),str(inp),str(detail)],check=True);raw=detail.read_bytes();n,k=struct.unpack_from('<ii',raw);assert(n,k)==(len(refs),levels);d=np.frombuffer(raw,offset=8,dtype=np.dtype([('target','<f8',(3,)),('old','u1',(3,))])).reshape(n,k);address=data['colourAddress'];edges=sorted(set((int(address[a]),int(address[b]))for a,b in data['orders']));p=np.zeros((n,k,3),np.uint8);rows=[]
 for i in range(k):
  target=d['target'][:,i];before=d['old'][:,i];row={'shade':i,'oldRoundedOrderViolations':sum(luminance(before[a])>=luminance(before[b])for a,b in edges),'continuousTargetOrderViolations':sum(luminance(target[[a]])[0]>=luminance(target[[b]])[0]for a,b in edges)};s=solve(target,edges);row['floorCeilFeasible']=s['feasible']
  if s['feasible']:p[:,i]=s['rgb8'];row.update({'newOrderViolations':sum(luminance(p[a,i])>=luminance(p[b,i])for a,b in edges),'changedRGBEntries':int(np.count_nonzero((p[:,i]!=before).any(1))),'maxTargetCodeError':s['maxTargetCodeError']})
  else:row['witness']=s['witness']
  rows.append(row)
 result={'sourceValueReferences':n,'levels':k,'sameOriginal58ContinuousTargets':True,'settingsUnchanged':settings,'allFloorCeilFeasible':all(r['floorCeilFeasible']for r in rows),'newArtParameters':False,'newGPUExecution':False,'rows':rows};(G/'PALETTE_ROUND88.json').write_text(json.dumps(result,indent=2,default=lambda x:x.item()));print(json.dumps(result,default=lambda x:x.item()));assert result['allFloorCeilFeasible'];p.tofile(G/'PALETTE88.rgb');assert np.array_equal(p[:,-1],refs);np.savez_compressed(G/'PALETTE_TARGETS88.npz',targets=d['target'],old=d['old'])
if __name__=='__main__':main()
