"""CPU-only reproduction of final99C against retained97/98B fixtures."""
from pathlib import Path
import json,os,subprocess,zipfile
H=Path(__file__).resolve().parent

def main():
 build=H/'face99/build';build.mkdir(exist_ok=True);csc=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';tests=[];fixtures=build/'fixtures99';fixtures.mkdir(exist_ok=True)
 with zipfile.ZipFile(H/'face99/CPU_FIXTURES99.zip')as z:
  assert set(z.namelist())=={'materials97.bin','frame102.bin','frame140.bin','frame148.bin','frame149.bin'}
  for info in z.infolist():
   assert info.file_size<=16777216;(fixtures/info.filename).write_bytes(z.read(info))
 for name,files in [('OracleFinal99',['JointLine99C.cs','VisibilityOracle99.cs']),('CurveFinal99',['JointLine99C.cs','CurveOpacity99.cs','CurveOpacityTests98.cs']),('FixtureReference98B',['JointLine97.cs','CurveOpacity98B.cs','JointOpacityFixture98.cs']),('FixtureFinal99',['JointLine99C.cs','CurveOpacity99.cs','JointOpacityFixture99.cs'])]:
  exe=build/(name+'.exe');q=subprocess.run([str(csc),'/nologo','/utf8output','/optimize+','/out:'+str(exe),*[str(H/f)for f in files]],capture_output=True,text=True,encoding='utf-8');assert q.returncode==0,q.stdout+q.stderr
  if not name.startswith('Fixture'):
   q=subprocess.run([str(exe)],capture_output=True,text=True);assert q.returncode==0,q.stdout+q.stderr;tests.append({'test':name,'stdout':q.stdout.strip()})
 for source in sorted(fixtures.glob('frame*.bin')):
  outputs=[]
  for name in ['FixtureReference98B','FixtureFinal99']:
   dest=build/(source.stem+'.'+name+'.out97');cert=build/(source.stem+'.'+name+'.cert98');q=subprocess.run([str(build/(name+'.exe')),str(source.parent/'materials97.bin'),str(source),str(dest),str(cert)],capture_output=True,text=True);assert q.returncode==0,q.stdout+q.stderr;outputs.append((dest.read_bytes()[36:],cert.read_bytes()))
  assert outputs[0]==outputs[1];tests.append({'fixture':source.name,'pixelsWitnessRadiusAnd98BCertificatesExact':True,'stdout':q.stdout.strip()})
 assert len(tests)==6;out={'CPUOnly':True,'runtimeGeometry':'JointLine99C.cs','runtimeOpacity':'CurveOpacity99.cs','tests':tests};(H/'face99/CPU_REPRODUCIBLE99.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
