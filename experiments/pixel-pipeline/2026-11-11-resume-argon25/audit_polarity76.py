"""Reject the76 model's global-parent representative, not tune its thresholds."""
from pathlib import Path
import json,numpy as np
H=Path(__file__).resolve().parent;G=H/'face76'
def luminance(rgb):
 x=np.asarray(rgb,float)/255;x=np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4);return x@np.array([.2126,.7152,.0722])
def main():
 a=np.load(H/'face70/RIDGE_EVIDENCE70.npz');nx,ny,px,py=[a[k]for k in['nx','ny','px','py']];f=np.load(H/'face71/PROFILE71.npz');sigma=f['lineSigma'];native=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=native['rgba'][:,:,:3];mask=native['mask'];partition=np.load(G/'SOURCE_REGIONS76.npz');refs=json.loads((G/'SOURCE_REFERENCES76.json').read_text());parent=partition['parent'];labels=partition['labels'];index={tuple(row):i for i,row in enumerate(f['rows'])};rows=[]
 for sid,ref in refs.items():
  p=ref['parent']
  if p is None or str(p)not in refs:continue
  x,y=ref['texel'];j=index.get((y,x))
  if j is None:continue
  n=np.array([nx[y,x],ny[y,x]]);centre=np.array([px[y,x],py[y,x]]);d=2*sigma[j];points=[np.rint(centre-sign*d*n).astype(int)for sign in[-1,1]]
  if any(q[0]<0 or q[0]>=mask.shape[1]or q[1]<0 or q[1]>=mask.shape[0]or not mask[q[1],q[0]]or parent[q[1],q[0]]!=p for q in points):continue
  c=rgb[y,x];bg=np.array([rgb[q[1],q[0]]for q in points]);observed=float(luminance(c));lo,hi=sorted(luminance(bg));native_sign=-1 if observed<lo else 1 if observed>hi else 0;output_diff=float(luminance(ref['RGB8'])-luminance(refs[str(p)]['RGB8']));output_sign=int(np.sign(output_diff));rows.append({'child':int(sid),'parent':p,'nativeForegroundXY':[x,y],'nativeForegroundRGB':c.tolist(),'nativeFlankXY':[q.tolist()for q in points],'nativeFlankRGB':bg.tolist(),'nativePolarity':native_sign,'globalParentRepresentativeRGB':refs[str(p)]['RGB8'],'candidateChildRGB':ref['RGB8'],'candidatePolarity':output_sign,'polarityInverted':bool(native_sign!=0 and output_sign!=0 and native_sign!=output_sign)})
 result={'sameParentBothNativeFlanksPairs':len(rows),'robustNativeDarkOrBrightPairs':sum(r['nativePolarity']!=0 for r in rows),'invertedByConstantParentReference':sum(r['polarityInverted']for r in rows),'sourceRGBChanged':0,'GPUExecuted':False,'candidate76Rejected':True,'notProofAutomaticSegmentationImpossible':True,'missingModelDimension':'a source parent can be a varying colour field, not one constant RGB; local pigment contrast and source tone must be distinguished from runtime light Q','rows':rows};(G/'POLARITY_FAILURE76.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
