from pathlib import Path
import json,subprocess,hashlib,numpy as np
import review_hull60 as api
H=Path(__file__).resolve().parent;G=H/'face65';C=G/'capture';BASE=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\experiments\pixel-pipeline\2026-11-02-face-region-lut')
def main():
 api.C=C;r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete'] and r['restorationChecksPass']
 fixtures=[]
 for f in r['frames']:
  w=f['QROI'][2];b=api.plane(r,f,'ownerReceipts47');a=api.plane(r,f,'atlas40');info=f['frameInfo'];sf=info['sourceCarrier48'];own=info['sourceOwner45'];assert info['layeredSurface'] and info['styleEnabled'] and not info['headRegionEnabled']
  stamp={'actor':own['featureOwnerInstance'],'view':info['view'],'sourceId':f['sourceId'],'stage':'selected-surface/after-Restore-Join-Resolve','producer':'Restore335.class.x->PreparedUV.z->GridJoin367->Resolve333->SourceNativeHull60.receipt1','frame':f['frame'],'serial':info['nativeComposite42']['presentSerialExecuted'],'width':f['QROI'][2],'height':f['QROI'][3]}
  fixtures.append({'stamp':stamp,'registeredRole':sf['registeredRole'],'triangleCount':sf['triangleCount'],'levels':info['faceSteps'],'layeredSurface':True,'styleEnabled':True,'headRegionEnabled':False,'selectedUV':b[:,w:2*w].ravel().tolist(),'selectedSource':b[:,2*w:3*w].ravel().tolist(),'nativeOwner':b[:,:w].ravel().tolist(),'carrier':b[:,3*w:4*w].ravel().tolist(),'nativeCell':a[:,14*w:15*w].ravel().tolist()})
 fixture=G/'SELECTED_INPUT65.json';fixture.write_text(json.dumps(fixtures,separators=(',',':')))
 build=G/'build';exe=build/'Selected65.exe'
 sources=[BASE/'candidate/SourcePalette58.cs',BASE/'ResolvedRegionInput.cs',H/'ResolvedShade52.cs',H/'SelectedShade65.cs',H/'SelectedShadeTests65.cs']
 args=[r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe','/nologo','/utf8output','/target:exe','/main:SelectedShadeTests65','/r:System.Core.dll','/r:System.Web.Extensions.dll','/out:'+str(exe),*map(str,sources)]
 p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr
 p=subprocess.run([str(exe),str(fixture),str(BASE/'FIXTURE58.json')],capture_output=True);assert p.returncode==0,p.stdout.decode('utf-8',errors='replace')+p.stderr.decode('cp949',errors='replace')
 result=json.loads(p.stdout);result['fixtureSHA256']=hashlib.sha256(fixture.read_bytes()).hexdigest();result['sourceFunctions']=['RestoreStyle335.compute::Restore copies selected cls.x to PreparedUV.z','GridJoin367.compute::JoinBare copies all4 UV channels','Prepare333.compute::Resolve copies PreparedUV to ResolvedUV','SourceNativeHull60.compute copies SurfaceUV into receipt1 at main q'];result['notIndependentDualProducerCapture']=True;result['finalRGBQEquivalenceNotClaimed']=True;result['confirmedColourRegionStillRequired']=True
 (G/'CPU_SELECTED_SHADE65.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
