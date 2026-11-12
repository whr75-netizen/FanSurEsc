"""CPU regression of same-feature redundancy; never calls Unity or a GPU API."""
from pathlib import Path
import json,os,subprocess,struct,numpy as np
H=Path(__file__).resolve().parent;G=H/'face98'
def main():
 build=G/'build';build.mkdir(exist_ok=True);csc=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
 rows=[]
 for name,files in [('JointLineTests98',['JointLine97.cs','JointLineTests97.cs']),('CurveOpacityTests98B',['JointLine97.cs','CurveOpacity98B.cs','CurveOpacityTests98.cs']),('JointOpacityFixture98B',['JointLine97.cs','CurveOpacity98B.cs','JointOpacityFixture98.cs'])]:
  exe=build/(name+'.exe');r=subprocess.run([str(csc),'/nologo','/utf8output','/optimize+','/out:'+str(exe),*[str(H/n)for n in files]],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
  if name!='JointOpacityFixture98B':
   r=subprocess.run([str(exe)],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;rows.append({'name':name,'stdout':r.stdout.strip()})
 # The existing97 fixture generator reconstructs these exact original inputs
 # from committed96 evaluated meshes/UV and lossless captured alpha files.
 source=H/'face97/fixture'
 if not (source/'materials97.bin').exists():
  r=subprocess.run([__import__('sys').executable,'-B',str(H/'fixture_joint97.py')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 for p in sorted(source.glob('frame*.bin')):
  target=G/(p.stem+'.B.out97');cert=G/(p.stem+'.B.cert98');r=subprocess.run([str(build/'JointOpacityFixture98B.exe'),str(source/'materials97.bin'),str(p),str(target),str(cert)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
  assert target.read_bytes()[36:]==p.with_suffix('.out97').read_bytes()[36:],'97 original pixel selection changed'
  raw=cert.read_bytes();magic,frame,w,witnesses,checks=struct.unpack_from('<5i',raw);assert magic==9801;values=np.frombuffer(raw,offset=20,dtype=[('mask','<i4'),('edge','<i4'),('z','<f8')]);assert len(values)==w*w
  rows.append({'frame':frame,'original97PixelsExact':True,'curveWitnesses':witnesses,'continuityChecks':checks,'candidateMasks':int((values['mask']!=0).sum())})
 (G/'CPU_TESTS98.json').write_text(json.dumps({'CPUOnly':True,'rows':rows},indent=2));print(json.dumps(rows))
if __name__=='__main__':main()
