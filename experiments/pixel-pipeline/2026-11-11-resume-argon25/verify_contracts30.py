"""Use saved inputs and managed .NET only. Never loads Unity or creates GPU device."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
H=Path(__file__).resolve().parent;G=H/'face30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True);p=H/'producer/support/surface27/pigment-run';s=json.loads(next(p.glob('STATE113-*-finished.json')).read_text(encoding='utf-8'));packet=Path(s['sequencePackets'][0]['output']);raw=packet/'RAW_MANIFEST.json';m=json.loads(raw.read_text(encoding='utf-8'));assert sha(raw)==(packet/'RAW_COMPLETE76.marker').read_text().strip()
 roi=m['grid102']['eyeTopLeftROI'];x,y,w,h=roi
 crop=np.eye(4);crop[0,0]=480/w;crop[0,3]=(480-2*x-w)/w;crop[1,1]=272/h;crop[1,3]=(2*y+h-272)/h
 projection=np.array(m['grid102']['headProjection']).reshape(4,4,order='F');view=np.array(m['grid102']['headView']).reshape(4,4,order='F')
 physical=(crop@projection@view).astype(np.float32).ravel(order='F').tolist();canonical=m['forward102']['nativeRegistration']['canonicalGPUProjection']
 fixture={'sourceId':m['sourceId'],'frame':m['frameIndex'],'modelKey':json.loads((H/'face28/SOURCE_INPUT28.json').read_text())['modelSHA256'],'roi':roi,'denseSize':m['forward102']['denseSize'],'physicalClip':physical,'canonicalClip':canonical,'provenance':{'actualManifestSHA256':sha(raw),'actualCanonicalDimensions':True,'positivePhysicalBinding':'SYNTHETIC descriptor calculated from recorded camera/ROI; not a physical29 GPU output or actual backend GPUProjectionMatrix'}}
 f=G/'FIXTURE30.json';f.write_text(json.dumps(fixture,indent=2),encoding='utf-8',newline='\n')
 refs=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0');assert refs.is_dir()
 args=['/nologo','/nostdlib+','/target:exe','/langversion:latest','/utf8output','/out:'+str(G/'ContractTests30.dll')]+['/reference:'+str(p)for p in refs.glob('*.dll')]+[str(H/'ProducerContracts30.cs'),str(H/'ContractTests30.cs')]
 rsp=G/'compile.rsp';rsp.write_text('\n'.join('"'+v+'"'for v in args),encoding='utf-8',newline='\n')
 compiler=Path(r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll');dotnet=r'C:\Program Files\dotnet\dotnet.exe'
 r=subprocess.run([dotnet,'exec',str(compiler),'/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');(G/'CPU_DIAGNOSTICS30.txt').write_text(r.stdout+r.stderr,encoding='utf-8',newline='\n');assert r.returncode==0,r.stdout+r.stderr
 (G/'ContractTests30.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}),encoding='utf-8',newline='\n')
 r=subprocess.run([dotnet,str(G/'ContractTests30.dll'),str(f)],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;result=json.loads(r.stdout);result['sourceFiles']={p.name:sha(p)for p in [H/'ProducerContracts30.cs',H/'ContractTests30.cs']};result['fixtureSHA256']=sha(f);(G/'CPU_CONTRACT30.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'checks':result['checks'],'CPUExecution':'passed','UnityGPUCalls':0,'liveDisposeGateIntegrated':False}))
if __name__=='__main__':main()
