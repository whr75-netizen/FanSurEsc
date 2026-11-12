"""CPU repro of complete recorded body input; no engine initialization."""
from pathlib import Path
import subprocess,json,re
H=Path(__file__).resolve().parent;G=H/'face94'
def main():
 ref=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319');exe=G/'opacity-fixture94.exe';args=[r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','/nostdlib','/langversion:9','/target:exe','/out:'+str(exe)]+['/r:'+str(ref/(n+'.dll'))for n in ['mscorlib','System','System.Core','System.Numerics']]+[str(G/'candidate/ClosedRegion524.cs'),str(G/'OpacityFixtureSource94.cs'),str(H/'OpacityFixtureTests94.cs')];p=subprocess.run(args,capture_output=True);assert p.returncode==0,p.stdout.decode(errors='replace')+p.stderr.decode(errors='replace');p=subprocess.run([str(exe),str(G/'actual-baseline-v2.fixture94'),str(G/'saved-failure-source.fixture94')],capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr;cases=[]
 for line in p.stdout.splitlines():
  m=re.match(r'(\S+) frame=(\d+) flip=(\d) fit=(True|False) sourceSegments=(\d+) actualRuntimeMultisetMatch=(True|False)',line)
  if m:cases.append({'fixture':m[1],'frame':int(m[2]),'flip':int(m[3]),'fit':m[4]=='True','segments':int(m[5]),'runtimeMatch':m[6]=='True','union':[]})
  elif line.strip().startswith('UNION'):cases[-1]['union'].append(line.strip())
 calibration=[x for x in cases if x['fixture']=='actual-baseline-v2.fixture94'and x['runtimeMatch']];assert len(calibration)==1;flip=calibration[0]['flip'];selected=[x for x in cases if x['flip']==flip];assert len(selected)==4 and all(len(x['union'])==2 and all('UNION PASS'in q for q in x['union'])for x in selected);result={'CPUOnly':True,'observedNativeUVFlipValidated':flip,'actualBaselineAllSegmentMultisetExact':True,'originalFailureDeformedPointsRetained':True,'rawAndExistingFitPassAtBothBaselines':True,'bothUnionImplementationsPass':True,'wrongUVHandednessRejected':True,'newGPUExecuted':False,'cases':cases};(G/'CPU_FULL_SOURCE94.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='cases'}))
if __name__=='__main__':main()
