"""Replay the new guard against actual individual samples, plus failure cases."""
from pathlib import Path
import sys,json
import numpy as np
HERE=Path(__file__).resolve().parent
def supported(old,owner,domain,samples,points,composed_owner=None):
 role=int(round(owner[0]));source={2:2,5:1,7:3}.get(role)
 if source is None or old[3]<=0 or owner[2]<=0 or(role in (2,5)and domain[0]<=.5):return False,0,0
 def cov(m):return m[0]>0 and m[1]>.5 and m[3]>1e-6
 if composed_owner is None:composed_owner=[owner[0],1,0,0]
 if role!=7 and round(composed_owner[0])!=role:return False,0,0
 total=0.;sid=0;best=1e30
 for i,m in enumerate(samples[source]):
  if not cov(m)or points[source][i,3]<=.5 or not .5<m[2]<2.5:continue
  if role!=7 and round(m[2])!=round(composed_owner[1]):continue
  visible=float(np.clip(m[3],0,1))
  for other in ([2,3]if source==1 else [3]if source==2 else []):
   z=samples[other][i]
   if cov(z)and z[0]<m[0]:visible*=1-float(np.clip(z[3],0,1))
  for s in (0,4,5,6):
   z=samples[s][i]
   if cov(z)and z[0]<m[0]:visible=0 if s==6 else visible*(1-float(np.clip(z[3],0,1)))
  if visible<=0:continue
  total+=visible;d=abs(float(m[0]-owner[2]))
  if d<best:best=d;sid=round(float(m[2]))
 return total>0 and sid>0,sid,total

def fixture():
 s=[np.zeros((16,4),np.float32)for _ in range(7)];p=[np.zeros((16,4),np.float32)for _ in range(4)]
 s[2][:]=[10,2,1,1];p[2][:,3]=1
 return np.array([.1,.2,.3,1]),np.array([2,6,10,0]),np.array([1,1,0,0]),s,p
def main():
 sys.path.insert(0,str(HERE.parent/'apply-capture66'));from analyse_capture68 import Reader,plane
 tests=[]
 def ck(n,v):assert v,n;tests.append(n)
 old,own,dom,s,p=fixture();ck('visible authored iris retained',supported(old,own,dom,s,p)[0]);ck('outside authored aperture not extended',not supported(old,own,np.zeros(4),s,p)[0])
 ck('domain colour-support never used as eye ID',supported(old,own,np.array([1,2,0,0]),s,p,[2,1,10,1])[0]);ck('wrong composed part rejected',not supported(old,own,dom,s,p,[5,1,10,1])[0])
 s[0][:]=[9,4,1,1];ck('fully front skin/closed lid not ignored',not supported(old,own,dom,s,p)[0]);s[0][:,3]=.5;ck('partial skin is fractional not whole-cell veto',supported(old,own,dom,s,p)[0]);s[4][:]=[8,12,1,1];ck('actual front hair blocks support',not supported(old,own,dom,s,p)[0]);s[4][:]=0;s[6][:]=[8,8,1,1];ck('body blocks support',not supported(old,own,dom,s,p)[0])
 old,own,dom,s,p=fixture();s[2][:,2]=2;ck('other eye source is not used',not supported(old,own,dom,s,p)[0]);own[0]=4;ck('generic face is not treated as eyelid',not supported(old,own,dom,s,p)[0]);own[0]=7;ck('line needs actual S3 not colour role only',not supported(old,own,dom,s,p)[0]);s[3][0]=[10,7,2,.3];p[3][0,3]=1;ck('native precomposed line can keep partial support',supported(old,own,np.zeros(4),s,p)[0])
 state=json.loads(sorted((HERE/'run-b').glob('STATE76-*.json'))[-1].read_text());packet=Path(state['output']);r=Reader(packet/'baseline76.buffer');r.s();r.s();r.s();r.i();r.i();x,y,w,h=[r.i()for _ in range(4)];r.i();b=r.a(w*h*24).reshape(h,w,6,4)
 a={q.stem:plane(q)[1]for q in packet.glob('S*.plane')};rx,rt,rw,rh=state['eyeFeature']['roiTopLeft'];ry=272-rt-rh;result=[]
 for yy in range(rh):
  for xx in range(rw):
   sm=[a[f'S{i}-meta'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(7)];pt=[a[f'S{i}-point'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(4)]
   v=b[yy+ry-y,xx+rx-x];ok,sid,weight=supported(v[0],v[1],v[4],sm,pt,[v[1,0],v[2,2],0,0])
   if ok:result.append({'xyTopLeft':[xx+rx,271-(yy+ry)],'role':round(float(v[1,0])),'eye':sid,'visibleWeight':weight})
 positions={tuple(q['xyTopLeft'])for q in result};ck('actual lost line21752 has current native support',(217,52)in positions);ck('actual iris21753 has current native support',(217,53)in positions);ck('actual iris22352 has current native support',(223,52)in positions)
 out={'sourceId':state['sourceId'],'tests':tests,'passed':len(tests),'sourcePredictionEyeId':'baselineMeta.z for this prediction only; final GPU validation requires actual old-eye-owner plane','expectedProtectedCells':result,'remaining':['Preserves already composed source features only; new whole-eye state design and temporal correspondence remain separate','No current Close or rotation frame is used as if observed']};(HERE/'TEST_FINAL76.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
