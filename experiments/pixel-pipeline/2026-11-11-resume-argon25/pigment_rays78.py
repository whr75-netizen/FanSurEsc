"""Test an explicit source-only hypothesis; never generate a palette reference.

C_i=B_i+a_i(P-B_i) gives a ray from B_i through observed C_i. A constant
pigment P must lie on every ray, with t_i=1/a_i >= 1. Variable native flanks
are only a candidate B, not an observed hidden background. Rank deficient or
inconsistent rays are evidence against identifying P, not permission to invent
an endpoint. No runtime lighting, Q, RGB output, semantic labels or GPU calls.
"""
import numpy as np

def intersect(background,observed):
 b=np.asarray(background,dtype=float);c=np.asarray(observed,dtype=float)
 if b.shape!=c.shape or b.ndim!=2 or b.shape[1]!=3 or not np.isfinite(b).all()or not np.isfinite(c).all():raise ValueError('finite corresponding Nx3 source samples required')
 d=c-b;length=np.linalg.norm(d,axis=1);valid=length>0;b=b[valid];c=c[valid];d=d[valid];length=length[valid]
 if not len(b):return {'samples':0,'rank':0,'uniqueNumericalIntersection':False,'point':None}
 u=d/length[:,None];a=np.eye(3)[None,:,:]-u[:,:,None]*u[:,None,:];lhs=a.sum(0);rhs=np.einsum('nij,nj->i',a,b);eigen=np.linalg.eigvalsh(lhs);rank=int(np.linalg.matrix_rank(lhs));result={'samples':len(b),'rank':rank,'eigenvalues':eigen.tolist(),'uniqueNumericalIntersection':rank==3,'point':None}
 if rank<3:return result
 p=np.linalg.solve(lhs,rhs);t=np.einsum('ni,ni->n',p-b,d)/(length*length);distance=np.linalg.norm(np.einsum('nij,nj->ni',a,p-b),axis=1)
 result.update(point=p.tolist(),condition=float(np.linalg.cond(lhs)),maxRayDistance=float(distance.max()),rmsRayDistance=float(np.sqrt(np.mean(distance**2))),minRayParameter=float(t.min()),maxRayParameter=float(t.max()),unitGamut=bool(((p>=0)&(p<=1)).all()),allRayParametersAtLeastOne=bool((t>=1-1e-12).all()))
 return result

def gradient_profile(observed,t,sigma,offset=0,sample_error=0):
 """Check the stronger compositing model without assuming pure flank samples.

 C(t)=(1-a*G)(B0+B1*t)+a*G*P
     =B0+B1*t+A*G+D*t*G; D=-a*B1; A=a*(P-B0).
 The 4-column fit alone is not a matte. The cross-channel D=-a*B1,
 alpha/gamut, quantization and constant-pigment assumptions must also hold.
 A flat background leaves alpha and pigment inseparable.
 """
 c=np.asarray(observed,float);t=np.asarray(t,float)
 if c.shape!=(len(t),3)or len(t)<4 or sigma<=0 or sample_error<0 or not np.isfinite(c).all():raise ValueError('finite transverse RGB profile required')
 g=np.exp(-.5*((t-offset)/sigma)**2);m=np.column_stack([np.ones(len(t)),t,g,t*g]);inverse=np.linalg.pinv(m);coefficient=inverse@c;b0,b1,a,d=coefficient;residual=c-m@coefficient;den=float(b1@b1)
 result={'profileSSE':float((residual**2).sum()),'modelCondition':float(np.linalg.cond(m)),'backgroundSlopeNorm':float(np.sqrt(den)),'alpha':None,'point':None,'crossChannelConstraintResidual':None}
 # Conservative necessary constraints, no artistic error threshold. If source
 # samples are known within +/-sample_error, each LS coefficient is within
 # error*row-L1(pseudoinverse). Intersect alpha inequalities before estimating P.
 # Nonempty means only "not disproven by these bounds", not a valid matte.
 numerical=64*np.finfo(float).eps*result['modelCondition']*max(1,float(abs(c).max()));error=sample_error+numerical;bound=error*abs(inverse).sum(1);e0,e1,ea,ed=bound;lo,hi=0.,1.;constraints=[]
 for k in range(3):constraints.extend([(b1[k]-e1,ed-d[k]),(-b1[k]-e1,ed+d[k]),(b0[k]-1-e0,ea-a[k]),(-b0[k]-e0,ea+a[k])])
 for slope,limit in constraints:
  if slope>0:hi=min(hi,float(limit/slope))
  elif slope<0:lo=max(lo,float(limit/slope))
  elif limit<0:lo,hi=1.,0.
 projection=np.eye(len(t))-m@inverse;residual_bounds=error*abs(projection).sum(1);residual_possible=bool((abs(residual)<=residual_bounds[:,None]).all());compatible=lo<=hi and residual_possible
 result.update(sampleErrorBound=float(sample_error),alphaInterval=[lo,hi]if lo<=hi else None,linearModelWithinSampleBounds=residual_possible,necessaryModelCompatible=compatible,matteIdentified=False)
 if den<=np.finfo(float).eps**2:return result
 alpha=-float(d@b1)/den;result['alpha']=alpha;result['crossChannelConstraintResidual']=float(np.linalg.norm(d+alpha*b1));result['alphaInUnitInterval']=0<alpha<=1
 if alpha!=0:
  p=b0+a/alpha;result['point']=p.tolist();result['unitGamut']=bool(((p>=0)&(p<=1)).all())
 return result
