"""Compile/run only the pure guard. No Unity DLL reference, MSBuild or GPU API."""
from pathlib import Path
import hashlib,json,subprocess,uuid
H=Path(__file__).resolve().parent
def main():
    dot=Path(r'C:\Program Files\dotnet\dotnet.exe');csc=Path(r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll');refs=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0')
    out=H/'build'/('bounds-'+uuid.uuid4().hex);out.mkdir();sources=[H/'DispatchBounds24.cs',H/'BoundsTests24.cs.txt']
    args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:exe','/out:'+str(out/'BoundsTests24.dll')]+['/reference:'+str(p)for p in refs.glob('*.dll')]+[str(p)for p in sources]
    rsp=out/'compile.rsp';rsp.write_text('\n'.join('"'+a+'"'for a in args)+'\n',encoding='utf-8')
    p=subprocess.run([str(dot),'exec',str(csc),'/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');assert p.returncode==0,p.stdout+p.stderr
    (out/'BoundsTests24.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}})+'\n')
    p=subprocess.run([str(dot),str(out/'BoundsTests24.dll'),str(H/'BOUNDS_INPUT24.bin')],capture_output=True,text=True,encoding='utf-8');print(p.stdout+p.stderr);assert p.returncode==0 and 'PASSED=18;'in p.stdout
    (H/'BOUNDS_TEST24.json').write_text(json.dumps({'passedGroups':18,'sourceSHA256':{s.name:hashlib.sha256(s.read_bytes()).hexdigest()for s in sources},'inputSHA256':hashlib.sha256((H/'BOUNDS_INPUT24.bin').read_bytes()).hexdigest(),'GPUOrUnityCalls':0,'compiledUnityHostExecuted':False,'UnityReferences':[],'stdout':p.stdout},indent=2)+'\n')
if __name__=='__main__':main()
