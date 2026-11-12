from pathlib import Path
import json,math,numpy as np
from source_profile71 import fit_profiles
H=Path(__file__).resolve().parent
def main():
 n=33;y,x=np.indices((n,n));nx=np.ones((n,n));ny=np.zeros((n,n));px=x.astype(float);py=y.astype(float);rows=np.array([[16,16]]);tests=0;stats={}
 models={'flat':np.full((n,n,3),100.),'affine':np.repeat((100+.1*x+.1*y)[:,:,None],3,2),'line':np.repeat((110+.1*x-6*np.exp(-.5*((x-16)/2)**2))[:,:,None],3,2),'AAstep':np.repeat((100+6*np.vectorize(math.erf)((x-16)/np.sqrt(2)/2))[:,:,None],3,2)}
 for name,rgb in models.items():
  fit=fit_profiles(rgb,rows,nx,ny,px,py);wins=bool(fit['lineWins'][0]);assert wins==(name=='line'),(name,wins);tests+=1;stats[name]={k:(bool(v[0])if v.dtype==bool else np.asarray(v[0]).tolist())for k,v in fit.items()}
 assert stats['line']['lineSigma']==2;tests+=1
 result={'CPUChecks':tests,'nativeRegressionFile':'CPU_PROFILE71.json','models':stats,'noSemanticTruthOrClosedRegionClaim':True};(H/'face71/TEST_PROFILE_MODELS71.json').write_text(json.dumps(result,indent=2));print(json.dumps({'CPUChecks':tests,'lineSigmaRecovered':2,'flatAffineAAstepNotLines':True}))
if __name__=='__main__':main()
