"""Evaluate only same-source-edge diagonal continuity, not new curve merging."""
from pathlib import Path
import os,subprocess,json,struct,numpy as np
H=Path(__file__).resolve().parent;G=H/'face105';B=G/'build'

def compile105(name,curve,program):
 exe=B/(name+'.exe');csc=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
 r=subprocess.run([str(csc),'/nologo','/utf8output','/optimize+','/out:'+str(exe),*[str(H/p)for p in['JointLine103.cs',curve,'RowParallel103.cs',program]]],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;return exe

def main():
 B.mkdir(parents=True,exist_ok=True);cases={};rows=[]
 for name,curve in[('baseline','CurveOpacity103.cs'),('candidate','CurveOpacity105.cs')]:
  exe=compile105(name+'Cases',curve,'OpacityCases105.cs');r=subprocess.run([str(exe)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;v={}
  for line in r.stdout.splitlines():
   k,value=line.split(':');v[k]=np.array(list(map(int,value.split(',')))).reshape(8,8)
  assert len(v)==288;cases[name]=v
 assert cases['baseline'].keys()==cases['candidate'].keys();changed=[];symmetry={}
 def transform(mask,rot,reflect):
  out=np.zeros_like(mask)
  for y,x in np.ndindex(mask.shape):
   nx,ny=(7-x,y)if reflect else(x,y);value=0
   for dy in[-1,0,1]:
    for dx in[-1,0,1]:
     if int(mask[y,x])&(1<<((dy+1)*3+dx+1)):
      u,v=(-dx,dy)if reflect else(dx,dy)
      for _ in range(rot):u,v=-v,u
      value|=1<<((v+1)*3+u+1)
   for _ in range(rot):nx,ny=7-ny,nx
   out[ny,nx]=value
  return out
 for name,values in cases.items():
  failures=[]
  for key,value in values.items():
   phase,rot,reflect,width,cover=key.split(',');base=values[','.join([phase,'0','0',width,cover])];expected=transform(base,int(rot),int(reflect))
   if not np.array_equal(value,expected):failures.append({'case':key,'differentMaskCells':int((value!=expected).sum()),'differentSelectedCellSet':int(((value!=0)!=(expected!=0)).sum())})
  symmetry[name]=failures
 for key,new in cases['candidate'].items():
  before=cases['baseline'][key];phase,rot,reflect,width,cover=key.split(',');assert np.all((before==0)|(new!=0))
  if float(width)>=1 or int(cover)==1:assert np.array_equal(before,new)
  if np.any(new!=before):changed.append({'case':key,'baselineMaskCells':int((before!=0).sum()),'candidateMaskCells':int((new!=0).sum())})
 fixture=H/'face103/build/fixtures'
 for name,curve in[('baseline','CurveOpacity103.cs'),('candidate','CurveOpacity105.cs')]:
  exe=compile105(name,curve,'JointOpacityFixture103.cs')
  for source in sorted(fixture.glob('frame*.bin')):
   output=B/(name+'-'+source.stem+'.out');cert=B/(name+'-'+source.stem+'.cert');r=subprocess.run([str(exe),str(fixture/'materials97.bin'),str(source),str(output),str(cert)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 for source in sorted(fixture.glob('frame*.bin')):
  name=source.stem;before=(B/('baseline-'+name+'.out')).read_bytes();after=(B/('candidate-'+name+'.out')).read_bytes();assert before[36:]==after[36:];before=np.frombuffer((B/('baseline-'+name+'.cert')).read_bytes()[20:],dtype=[('mask','<i4'),('edge','<i4'),('z','<f8')]);after=np.frombuffer((B/('candidate-'+name+'.cert')).read_bytes()[20:],dtype=before.dtype);assert np.array_equal(before['edge'],after['edge'])and np.array_equal(before['z'],after['z']);rows.append({'fixture':name,'pixelsWitnessDepthRadiusExact':True,'newMaskCells':int(((after['mask']!=0)&(before['mask']==0)).sum()),'changedMaskCells':int((after['mask']!=before['mask']).sum())})
 out={'CPUOnly':True,'UnityOrGPUExecuted':False,'sourceRule':'Only two triangular halves of the identical authored edge. Split path at their exact shared diagonal; both source and destination depth/alpha paths must be clear. No joining separate source curves.','syntheticCases':len(cases['baseline']),'D4MaskFailures':symmetry,'casesWithAdditionalRedundancy':changed,'actualFrozenFixtures':rows,'generalOpacitySolved':False,'adopted':False};(G/'CPU_OPACITY105.json').write_text(json.dumps(out,indent=2));print(json.dumps({**out,'casesWithAdditionalRedundancy':len(changed)},indent=2))

if __name__=='__main__':main()
