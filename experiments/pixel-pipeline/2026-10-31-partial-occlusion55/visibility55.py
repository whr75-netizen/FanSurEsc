"""Per-sample external visibility only; no logical-cell winner or colour."""
import numpy as np

def joint_visibility(alpha,depth,externals):
    alpha=np.asarray(alpha,np.float32);depth=np.asarray(depth,np.float32)
    trans=np.ones_like(alpha);fronts={}
    for key,raw in externals.items():
        ext=np.asarray(raw,np.float32)
        front=(alpha>0)&(ext[...,0]>0)&(ext[...,1]>.5)&(ext[...,3]>1e-6)&(ext[...,0]<depth)
        fronts[key]=front
        trans*=np.where(front,1-np.clip(ext[...,3],0,1),1).astype(np.float32)
    return (alpha*trans).astype(np.float32),trans,fronts

def calculate(case):
    src=np.array(case['S3META'],np.float32);point=np.array(case['S3POINT'],np.float32)
    valid=(src[...,0]>0)&(src[...,1]>.5)&(np.rint(src[...,2])==case['eye'])&(src[...,3]>1e-6)&(point[...,3]>.5)
    alpha=np.where(valid,np.clip(src[...,3],0,1),0).astype(np.float32)
    externals={k:np.array(v,np.float32)for k,v in case['destinationExternal'].items()}
    visible,trans,fronts=joint_visibility(alpha,src[...,0],externals)
    skin=np.array(case['S0META'],np.float32);sp=np.array(case['S0POINT'],np.float32)
    sv=(skin[...,0]>0)&(skin[...,1]>.5)&(np.rint(skin[...,2])==case['eye'])&(sp[...,3]>.5)&(skin[...,0]<src[...,0])
    internal=(alpha*np.where(sv,1-np.clip(skin[...,3],0,1),1)).astype(np.float32)
    internal_visible,_,_=joint_visibility(internal,src[...,0],externals)
    constant_front={key:(v[...,0]>0)&(v[...,1]>.5)&(v[...,3]>1e-6)&(v[...,0]<case['representativeDepth53'])for key,v in externals.items()}
    area=lambda x:float(np.sum(x,dtype=np.float64)/16)
    any_front=any(np.any(v)for v in constant_front.values())
    return dict(frame=case['frame'],sourceId=case['sourceId'],sourceXY=case['sourceXY'],targetXY=case['targetXY'],
        oldAnyFront=any_front,oldRuleVisibleArea=0. if any_front else area(alpha),
        oldFrontSampleCounts={k:int(v.sum())for k,v in constant_front.items()},
        exactFrontSampleCounts={k:int(v.sum())for k,v in fronts.items()},
        nativeAlpha=alpha,nativeDepth=src[...,0],destinationTransmittance=trans,visibleAlpha=visible,
        visibleAlphaWithOriginalSourceSkin=internal_visible,sourceNativeArea=area(alpha),sourceNativeAfterSkinArea=area(internal),
        perSampleExternalVisibleArea=area(visible),perSampleAfterSourceSkinVisibleArea=area(internal_visible),
        blanketZeroRefuted=bool(any_front and area(visible)>0),blanketZeroRefutedEvenWithOriginalSourceSkin=bool(any_front and area(internal_visible)>0),
        finalLogicalOwnerDecided=False,styleCandidateAApproved=False)
