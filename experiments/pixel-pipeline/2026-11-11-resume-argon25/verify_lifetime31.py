"""Run managed lifetime/lattice regressions; never loads a Unity assembly."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;G=H/'face31'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True);refs=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0');dll=G/'LifecycleTests31.dll'
 args=['/nologo','/nostdlib+','/target:exe','/langversion:latest','/utf8output','/out:'+str(dll)]+['/reference:'+str(p)for p in refs.glob('*.dll')]+[str(H/'ProducerLifetime31.cs'),str(H/'LifecycleTests31.cs')]
 rsp=G/'compile.rsp';rsp.write_text('\n'.join('"'+v+'"'for v in args),encoding='utf-8',newline='\n');dotnet=r'C:\Program Files\dotnet\dotnet.exe';compiler=r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll'
 p=subprocess.run([dotnet,'exec',compiler,'/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');(G/'CPU_DIAGNOSTICS31.txt').write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n');assert p.returncode==0,p.stdout+p.stderr
 (G/'LifecycleTests31.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}),encoding='utf-8',newline='\n')
 p=subprocess.run([dotnet,str(dll)],capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr;r=json.loads(p.stdout);r['sources']={n:sha(H/n)for n in ['ProducerLifetime31.cs','LifecycleTests31.cs']};(G/'CPU_LIFETIME31.json').write_text(json.dumps(r,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'managedChecks':r['checks'],'UnityGPUCalls':0,'actualReadbackObserved':False}))
if __name__=='__main__':main()
