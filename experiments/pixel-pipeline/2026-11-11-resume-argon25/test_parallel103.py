"""CPU row concurrency/lifetime and exact4 original-input regressions."""
from pathlib import Path
import json,os,subprocess,zipfile,struct
H=Path(__file__).resolve().parent;G=H/'face103'

def main():
 build=G/'build';build.mkdir(parents=True,exist_ok=True);inputs=build/'fixtures';inputs.mkdir(exist_ok=True)
 with zipfile.ZipFile(H/'face99/CPU_FIXTURES99.zip')as z:
  assert set(z.namelist())=={'materials97.bin','frame102.bin','frame140.bin','frame148.bin','frame149.bin'}
  for info in z.infolist():assert info.file_size<=16777216;(inputs/info.filename).write_bytes(z.read(info))
 csc=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';rows=[]
 programs=[('Oracle',['JointLine103.cs','VisibilityOracle99.cs']),('Curve',['JointLine103.cs','CurveOpacity103.cs','CurveOpacityTests98.cs']),('Lifetime',['JointLine103.cs','CurveOpacity103.cs','RowParallel103.cs','RowLifetimeTests103.cs']),('Reference',['JointLine99C.cs','CurveOpacity99.cs','JointOpacityFixture99.cs']),('Parallel',['JointLine103.cs','CurveOpacity103.cs','RowParallel103.cs','JointOpacityFixture103.cs'])]
 for name,source in programs:
  exe=build/(name+'.exe');r=subprocess.run([str(csc),'/nologo','/utf8output','/optimize+','/out:'+str(exe),*[str(H/n)for n in source]],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
  if name not in ['Reference','Parallel']:
   r=subprocess.run([str(exe)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;rows.append({'test':name,'stdout':r.stdout.strip()})
 for source in sorted(inputs.glob('frame*.bin')):
  out=[];timings={}
  for name in ['Reference','Parallel']:
   dest=build/(source.stem+'.'+name+'.out97');cert=build/(source.stem+'.'+name+'.cert98');r=subprocess.run([str(build/(name+'.exe')),str(inputs/'materials97.bin'),str(source),str(dest),str(cert)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;data=dest.read_bytes();out.append((data[36:],cert.read_bytes()));timings[name+'MsWithIO']=struct.unpack_from('<d',data,28)[0]
  assert out[0]==out[1];rows.append({'fixture':source.name,'pixelsWitnessRadiusAndCertificateByteExact':True,**timings})
 result={'CPUOnly':True,'UnityOrGPUCalled':False,'parallelism':'one default-scheduler CPU task plus owner-thread disjoint rows; all joined before query leases release','rows':rows};(G/'CPU_PARALLEL103.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
