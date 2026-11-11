"""Managed/Node CPU regression only. Never loads Unity or creates a GPU device."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent;G=H/'face32'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True)
 p=subprocess.run(['node',str(H/'QPrime32.cjs')],capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr;r=json.loads(p.stdout);r['sourceSHA256']=sha(H/'QPrime32.cjs');(G/'CPU_Q32.json').write_text(json.dumps(r,indent=2),encoding='utf-8',newline='\n')
 refs=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0');dll=G/'ConsumerTests32.dll';sources=[H/'ProducerLifetime31.cs',H/'ConsumerReads32.cs',H/'ConsumerTests32.cs']
 args=['/nologo','/nostdlib+','/target:exe','/langversion:latest','/utf8output','/out:'+str(dll)]+['/reference:'+str(v)for v in refs.glob('*.dll')]+[str(v)for v in sources]
 rsp=G/'compile.rsp';rsp.write_text('\n'.join('"'+v+'"'for v in args),encoding='utf-8',newline='\n');dotnet=r'C:\Program Files\dotnet\dotnet.exe';compiler=r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll'
 p=subprocess.run([dotnet,'exec',compiler,'/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');(G/'CPU_DIAGNOSTICS32.txt').write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n');assert p.returncode==0,p.stdout+p.stderr
 (G/'ConsumerTests32.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}),encoding='utf-8',newline='\n')
 p=subprocess.run([dotnet,str(dll)],capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr;c=json.loads(p.stdout);c['sources']={v.name:sha(v)for v in sources};(G/'CPU_CONSUMER32.json').write_text(json.dumps(c,indent=2),encoding='utf-8',newline='\n')
 print(json.dumps({'QScenarios':r['checks'],'binaryRings':r['exhaustiveRingPatterns'],'legacySchemaRangeCases':r['legacySchemaRangeCases'],'consumerChecks':c['checks'],'UnityGPUCalls':0}))
if __name__=='__main__':main()
