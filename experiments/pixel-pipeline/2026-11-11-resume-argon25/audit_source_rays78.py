"""Actual native source model audit, not a matting/segmentation implementation.

Reuse frozen76 connected supports and71 line fits. For each connected child,
test a shared pigment using actual centre bytes and symmetric native flanks at
3 fitted sigma. Flanks cancel an affine background only under the stated model;
they can include another stroke, tail, curved colour field or seam. No pure
background/opacity labels are inferred from the fit. Encoded and linear spaces
are separate hypotheses, not a threshold sweep.
"""
from pathlib import Path
import json,hashlib,numpy as np
from source_ridge70 import sample
from pigment_rays78 import intersect,gradient_profile
H=Path(__file__).resolve().parent;G=H/'face78'

def linear(rgb):return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)

def main():
 G.mkdir(exist_ok=True);src=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=src['rgba'][:,:,:3].astype(float)/255;mask=src['mask'];reg=np.load(H/'face76/SOURCE_REGIONS76.npz');labels=reg['labels'];parent=reg['parent'];compact=G/'INPUT_ROWS78.npz'
 if not compact.exists():
  ridge=np.load(H/'face70/RIDGE_EVIDENCE70.npz');profile=np.load(H/'face71/PROFILE71.npz');r=profile['rows'];nx0=ridge['nx'];ny0=ridge['ny'];np.savez_compressed(compact,rows=r,lineWins=profile['lineWins'],lineSigma=profile['lineSigma'],lineOffset=profile['lineOffset'],nx=nx0[r[:,0],r[:,1]],ny=ny0[r[:,0],r[:,1]])
 profile=np.load(compact);rows=profile['rows'];winning=profile['lineWins'];ny=profile['ny'];nx=profile['nx'];sigma=profile['lineSigma'];items=[]
 # Every row retains a connected76 support ID. Do not merge disconnected
 # hatches into one family or elevate their inferred endpoints to native RGB.
 y,x=rows[:,0],rows[:,1];dy=ny*3*sigma;dx=nx*3*sigma;points=np.stack([x,y],1);minus=points-np.stack([dx,dy],1);plus=points+np.stack([dx,dy],1);h,w=mask.shape
 valid=winning&(labels[y,x]>int(parent[mask].max()))
 for p in[minus,plus]:
  inside=(p[:,0]>=0)&(p[:,1]>=0)&(p[:,0]<=w-1)&(p[:,1]<=h-1);px=np.clip(np.rint(p[:,0]).astype(int),0,w-1);py=np.clip(np.rint(p[:,1]).astype(int),0,h-1);valid&=inside&mask[py,px]&(parent[py,px]==parent[y,x])
 profile_models={}
 for space,image in[('encodedRGB',rgb),('linearRGB',linear(rgb))]:
  observed=image[y,x];b=(sample(image,minus[:,0],minus[:,1])+sample(image,plus[:,0],plus[:,1]))*.5
  for label in np.unique(labels[y[valid],x[valid]]):
   ix=np.flatnonzero(valid&(labels[y,x]==label));a=intersect(b[ix],observed[ix]);a.update(space=space,connectedSupport=int(label),sourceRows=points[ix].tolist(),distinctNativeCentreRGB=int(len(np.unique(observed[ix],axis=0))),backgroundStatus='hypothesized from symmetric native flanks, not observed clean backing',pigmentStatus='numerical estimate only, never palette reference');items.append(a)
  # Reuse71 sigma/offset, not another scale/threshold search. Adding t*G can
  # only lower unconstrained SSE, so SSE reduction alone is not acceptance.
  t=np.arange(-4,5,dtype=float);sx=x[:,None]+t*nx[:,None];sy=y[:,None]+t*ny[:,None];profiles=sample(image,sx,sy);models=[];native_profile=winning.copy()
  for xx,yy in[(np.floor(sx),np.floor(sy)),(np.ceil(sx),np.floor(sy)),(np.floor(sx),np.ceil(sy)),(np.ceil(sx),np.ceil(sy))]:
   inside=(xx>=0)&(yy>=0)&(xx<w)&(yy<h);ix=np.clip(xx.astype(int),0,w-1);iy=np.clip(yy.astype(int),0,h-1);native_profile&=(inside&mask[iy,ix]).all(1)
  for j in np.flatnonzero(native_profile):
   # Half-code quantization is a stated source precision assumption, not a
   # measured AA model. Linear uses the maximum sRGB decode derivative so it
   # remains conservative. No search over tolerance/number of output colours.
   error=.5/255 if space=='encodedRGB'else (2.4/1.055)*.5/255
   r=gradient_profile(profiles[j],t,sigma[j],profile['lineOffset'][j],error);r['nativeXY']=points[j].tolist();models.append(r)
  admissible=[a for a in models if a.get('alphaInUnitInterval')and a.get('unitGamut')];not_disproven=[a for a in models if a['necessaryModelCompatible']];profile_models[space]={'profiles':len(models),'unsupportedNativeProfileRows':int(winning.sum()-native_profile.sum()),'alphaAndGamutNumericallyAdmissible':len(admissible),'notDisprovenByQuantizationBounds':len(not_disproven),'matteAccepted':False,'boundsAreNecessaryNotSufficient':True,'sigmaOffsetFrozenFrom71':True,'examples':models[:8]}
 result={'sourceSHA256':hashlib.sha256((H/'face28/SOURCE_NATIVE28.npz').read_bytes()).hexdigest(),'sourceRows':len(rows),'validLineRowsWithSameParentNativeFlanks':int(valid.sum()),'sourceRGBChanged':0,'newSemanticFamilies':0,'GPUExecuted':False,'paletteReferencesGenerated':False,'models':{},'rows':items}
 for space in['encodedRGB','linearRGB']:
  selected=[a for a in items if a['space']==space];unique=[a for a in selected if a['uniqueNumericalIntersection']];physical=[a for a in unique if a['unitGamut']and a['allRayParametersAtLeastOne']];result['models'][space]={'connectedSupports':len(selected),'rankDeficient':len(selected)-len(unique),'uniqueNumerical':len(unique),'gamutAndNonSuperopaque':len(physical),'rayDistanceIsNotPureBackgroundProof':True,'maxResidualAmongPhysical':max([a['maxRayDistance']for a in physical],default=None),'medianConditionAmongUnique':float(np.median([a['condition']for a in unique]))if unique else None}
 result['gradientCompositingModels']=profile_models;result['compactInputSHA256']=hashlib.sha256(compact.read_bytes()).hexdigest();result['supportInputSHA256']=hashlib.sha256((H/'face76/SOURCE_REGIONS76.npz').read_bytes()).hexdigest()
 (G/'ACTUAL_RAYS78.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in['rows','gradientCompositingModels']}));print(json.dumps({'profileModels':{s:{k:v for k,v in a.items()if k!='examples'}for s,a in profile_models.items()}}))
if __name__=='__main__':main()
