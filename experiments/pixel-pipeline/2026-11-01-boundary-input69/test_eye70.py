from pathlib import Path
import datetime,json,subprocess,hashlib
R=Path(__file__).resolve().parent
def main():
 csc=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe');data=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data');out=R/('.verification70-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();exe=out/'test.exe';base=[str(csc),'/nologo']
 cp=subprocess.run(base+['/out:'+str(exe),str(R/'EyeReadback70.cs'),str(R/'TestEyeReadback70.cs')],capture_output=True,text=True);assert cp.returncode==0,cp.stdout+cp.stderr
 run=subprocess.run([str(exe),str(out/'fixtures')],capture_output=True,text=True);assert run.returncode==0,run.stdout+run.stderr;(R/'EYE_TEST70.txt').write_text(run.stdout,encoding='utf-8')
 api=subprocess.run(base+['/target:library','/out:'+str(out/'adapter.dll'),'/r:'+str(data/'Managed/UnityEngine/UnityEngine.CoreModule.dll'),'/r:'+str(data/'MonoBleedingEdge/lib/mono/4.8-api/Facades/netstandard.dll'),str(R/'EyeReadback70.cs'),str(R/'UnityEyeBuffer70.cs')],capture_output=True,text=True);assert api.returncode==0,api.stdout+api.stderr
 report={'compiledPureProtocol':True,'compiledAgainstActualUnity6000_5CoreModule':True,'executedOffline':True,'passed':run.stdout.count('PASS '),'UnityCalls':0,'GPUCalls':0,'structBytes':{'Feature19':48,'Pixel348':256},'testedCountRowBytes':336,'testedRecordRowBytes':8448,'maximumPossibleRecordRowBytes':122880,'payloadBudgetBytes':1048576,'partialFailureFilesRetained':True,'sourceSHA256':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['EyeReadback70.cs','UnityEyeBuffer70.cs','TestEyeReadback70.cs']},'limits':'Adapter compiled only; actual GPU content, dynamic Unity SDK compilation and caller integration remain unexecuted'};(R/'EYE_TEST70.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(run.stdout);print('Actual Unity CoreModule adapter compile passed without assembly execution')
if __name__=='__main__':main()
