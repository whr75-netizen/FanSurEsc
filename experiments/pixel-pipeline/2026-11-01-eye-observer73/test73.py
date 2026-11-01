"""Offline protocol reproduction; each invocation only creates a unique folder."""
from pathlib import Path
import datetime,json,subprocess,hashlib
R=Path(__file__).resolve().parent
def main():
 out=R/('.verification73-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False);csc=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe');data=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data');base=[str(csc),'/nologo']
 cp=subprocess.run(base+['/out:'+str(out/'test.exe'),str(R/'EyeReadback73.cs'),str(R/'TestEyeReadback73.cs')],capture_output=True,text=True);assert cp.returncode==0,cp.stdout+cp.stderr
 run=subprocess.run([str(out/'test.exe'),str(out/'fixtures')],capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr
 api=subprocess.run(base+['/target:library','/out:'+str(out/'adapter.dll'),'/r:'+str(data/'Managed/UnityEngine/UnityEngine.CoreModule.dll'),'/r:'+str(data/'MonoBleedingEdge/lib/mono/4.8-api/Facades/netstandard.dll'),str(R/'EyeReadback73.cs'),str(R/'UnityEyeBuffer70.cs')],capture_output=True,text=True);assert api.returncode==0,api.stdout+api.stderr
 result={'passed':run.stdout.count('PASS '),'UnityCalls':0,'GPUCalls':0,'compiledAgainstActualUnityDLL':True,'sourceSHA256':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['EyeReadback73.cs','UnityEyeBuffer70.cs','TestEyeReadback73.cs']}}
 with (out/'TEST.json').open('x') as f:json.dump(result,f,indent=2)
 with (out/'TEST.txt').open('x') as f:f.write(run.stdout)
 print(json.dumps(result));print('New test folder:',out)
if __name__=='__main__':main()
