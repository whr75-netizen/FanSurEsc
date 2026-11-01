"""Recover a source-supported native-boundary -> authored-coordinate transform.

The existing source parent and native aperture have24 ordered vertices. Test
all cyclic/reversed matches in native3D to authored2D. The simpler2D reference
affine was tested and was insufficient; do not hide that depth-dependent term.
"""
from pathlib import Path
import json,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def bary2(tris,p):
 a=tris[:,0];u=tris[:,1]-a;v=tris[:,2]-a;d=np.asarray(p)-a;den=u[:,0]*v[:,1]-u[:,1]*v[:,0];safe=np.where(abs(den)>1e-14,den,1)
 b=(d[:,0]*v[:,1]-d[:,1]*v[:,0])/safe;c=(u[:,0]*d[:,1]-u[:,1]*d[:,0])/safe;w=np.stack([1-b-c,b,c],1);return (abs(den)>1e-14)&(w.min(1)>=-1e-8),w

def main():
 a=np.load(ROOT/'whole-eye52/SOURCE_SURFACES52.npz');b=json.loads((ROOT/'lid-evidence51/KEYFORM_BUNDLE51.json').read_text());binding=json.loads((ROOT/'whole-eye52/SOURCE_BINDING52.json').read_text());key=json.loads((ROOT/'whole-eye52/WHOLE_KEYFORM52.json').read_text());native=a['native_xyz_head'];uv=a['native_uv'];centres={e['eye']:native[e['nativeRingVertexIds']].mean(0)for e in b['eyes']};eyes=[];cells=[]
 for e in b['eyes']:
  owner=e['eye'];ring=native[e['nativeRingVertexIds']];old=np.array(next(x for x in binding['eyes']if x['eye']==owner)['projection3DToReference']);nativeRef=np.c_[ring,np.ones(len(ring))]@old;authored=np.array(e['parent']);trials=[]
  for rev in [False,True]:
   q=ring[::-1]if rev else ring
   for shift in range(len(q)):
    x=np.c_[np.roll(q,shift,0),np.ones(len(q))];T=np.linalg.lstsq(x,authored,rcond=None)[0];errors=np.linalg.norm(x@T-authored,axis=1);trials.append({'reverse':rev,'shift':shift,'T':T,'rms':float(np.sqrt(np.mean(errors**2))),'max':float(errors.max())})
  trials.sort(key=lambda t:t['rms']);best=trials[0];P=best['T'];n=np.cross(P[:3,0],P[:3,1]);n/=np.linalg.norm(n)
  assert best['max']<1e-3 and best['rms']*100<trials[1]['rms'];assert best['shift']==0 and not best['reverse']
  projected=np.c_[native,np.ones(len(native))]@P
  for c in key['states']['existing-open-reference']['cells']:
   if c['eye']!=owner or c['part']not in ['iris','sclera']:continue
   sm=c['role'];ix=a[f'native_role{sm}_tri'];means=native[ix].mean(1);own=np.array([min(centres,key=lambda o:float(np.dot(v-centres[o],v-centres[o])))for v in means]);valid,w=bary2(projected[ix],np.array(c['referenceXY'])+[.75,.25]);valid&=own==owner;hits=[]
   for j in np.where(valid)[0]:
    p=w[j]@native[ix[j]];hits.append({'primitive':int(j)+1,'triangleVertexIds':ix[j].tolist(),'barycentric':w[j].tolist(),'point':p.tolist(),'uv':(w[j]@uv[ix[j]]).tolist(),'frontDepthCoordinate':float(p@n)})
   hits.sort(key=lambda q:-q['frontDepthCoordinate']);cells.append({'cellId':c['cellId'],'eye':owner,'role':sm,'sourceXY':c['referenceXY'],'sourceRGBA8':c['rgba8'],'nativeMatches':hits,'nativeBinding':hits[0]if hits else None})
  T2=np.linalg.lstsq(np.c_[nativeRef,np.ones(len(ring))],authored,rcond=None)[0];error2=np.linalg.norm(np.c_[nativeRef,np.ones(len(ring))]@T2-authored,axis=1)
  eyes.append({'eye':owner,'originalNativeReferenceProjection':old.tolist(),'nativeToAuthoredProjection':P.tolist(),'fitMaxPixels':best['max'],'fitRMSPixels':best['rms'],'nextBestCyclicFitRMSPixels':trials[1]['rms'],'reference2DAffineRMSPixels':float(np.sqrt(np.mean(error2**2))),'allCandidateFits':[{'shift':v['shift'],'reverse':v['reverse'],'rms':v['rms']}for v in trials],'nativeRingVertexIds':e['nativeRingVertexIds'],'nativeReferenceRing':nativeRef.tolist(),'authoredParent':authored.tolist(),'sourceRegistrationViewingDirection':n.tolist()})
 out={'status':'SOURCE_BOUNDARY_REGISTRATION_ONLY_NOT_RENDERED','source':'Native ordered aperture indices and the existing authored parent; all48 cyclic/reversed3D to2D affine fits tested per eye.','eyes':eyes,'cells':cells,'unboundCells':[c['cellId']for c in cells if c['nativeBinding']is None],'limitations':['Exact boundary transform is recovered; interior native iris/white alpha and current deformed surface visibility must still be tested.','Source colour remains authored bank P; native geometric UV binding does not prove the bank originally sampled that native texel.','No skin-ignore, virtual-depth bias, fixed minimum size, GPU or product change.']};q=HERE/'REGISTRATION89.json';assert not q.exists();q.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'eyeFits':[{k:e[k]for k in ['eye','fitMaxPixels','fitRMSPixels','nextBestCyclicFitRMSPixels','reference2DAffineRMSPixels']}for e in eyes],'authoredCells':len(cells),'unbound':out['unboundCells'],'multipleMatches':[(c['cellId'],len(c['nativeMatches']))for c in cells if len(c['nativeMatches'])>1]},indent=2))
if __name__=='__main__':main()
