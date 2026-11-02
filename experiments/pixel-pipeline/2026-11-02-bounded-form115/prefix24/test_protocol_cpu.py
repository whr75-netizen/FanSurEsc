from pathlib import Path
import json,subprocess,uuid
H=Path(__file__).resolve().parent;OUT=H/'build';SDK=Path(r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll');DOT=Path(r'C:\Program Files\dotnet\dotnet.exe')
REF=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0')
def main():
    work=OUT/('cpu-test-'+uuid.uuid4().hex);work.mkdir()
    args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:exe','/out:'+str(work/'CpuTests24.dll')]
    args+=['/reference:'+str(p)for p in REF.glob('*.dll')]+['/reference:'+str(OUT/'Prefix24Protocol.dll'),str(H/'CpuTests24.cs'),str(H/'CaseLock24.cs'),str(H/'PrefixMetadata24.cs'),str(H/'metadata24/Json58Linear24.cs')]
    rsp=work/'CpuTests24.rsp';rsp.write_text('\n'.join('"'+a+'"'for a in args)+'\n',encoding='utf-8')
    result=subprocess.run([str(DOT),'exec',str(SDK),'/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');print(result.stdout+result.stderr);assert result.returncode==0
    (work/'Prefix24Protocol.dll').write_bytes((OUT/'Prefix24Protocol.dll').read_bytes())
    (work/'CpuTests24.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}})+'\n')
    result=subprocess.run([str(DOT),str(work/'CpuTests24.dll')],capture_output=True,text=True,encoding='utf-8');print(result.stdout+result.stderr);assert result.returncode==0
    data=json.loads((work/'CPU_TEST_RESULT.json').read_text());assert data['Passed']==28 and not data['ProductionRunRootCreated']and data['ProductionRunBytesPreserved']and data['ActualGpuPredecessorValidated']and not data['HostAssemblyExecuted']and not data['GPUDeviceCreated']
    (H/'CPU_TEST_LATEST.json').write_text(json.dumps({'result':str(work/'CPU_TEST_RESULT.json'),'summary':data},indent=2)+'\n')
if __name__=='__main__':main()
