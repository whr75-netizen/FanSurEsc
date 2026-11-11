"""Recover only proven native-face source carriers; never decode canonical tags as triangles."""
from pathlib import Path
import json,numpy as np
from surface_paths34 import native
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face47';C=G/'capture'
def existing_role(binding_ordinal):
 # Full319View335.cs::Initialise line44: existing pipeline material-slot adapter,
 # not a guessed source colour or a mesh triangle band.
 i=binding_ordinal
 return ([7,8,9,10][i]if i<4 else i-4 if i<11 else i)+1
def main():
 r=json.loads((C/'COMPLETE.json').read_text());surface,binding=native();rows=[];total=0;known=0
 for f in r['frames']:
  def read(name):
   p=next(p for p in r['planes']if p['frame']==f['frame']and p['name']==name);return np.fromfile(C/p['file'],dtype='<f4').reshape(p['height'],p['width'],4)
  w=f['QROI'][2];a=read('atlas40');b=read('ownerReceipts47');raw=a[:,7*w:8*w];uv=a[:,8*w:9*w];owner=b[:,:w];selectedUV=b[:,w:2*w];info=f['frameInfo']['nativeComposite42'];g=geometry(C/f"geometry-frame{f['frame']}.bin");assert g['sourceId']==f['sourceId']and np.array_equal(g['indices'][binding['subMesh']],surface.indices)
  eligible=(a[:,15*w:16*w,0]==2)&(owner[:,:,0]==existing_role(binding['bindingOrdinal']));current=eligible&(raw[:,:,1]==owner[:,:,0])&(raw[:,:,2]==owner[:,:,1])&(raw[:,:,3]>0)&(raw[:,:,3]<=len(surface.indices))&np.all(uv[:,:,:2]==selectedUV[:,:,:2],2)&(abs(raw[:,:,0]+info['depthOffset']-owner[:,:,2])<=.0001);n=0;depthError=[];baryMin=[]
  for y,x in np.argwhere(current):
   triangle=int(round(raw[y,x,3]))-1;point=uv[y,x,:2].astype(float);v=surface.inv[triangle]@(point-surface.tri[triangle,0]);bary=np.r_[1-v.sum(),v];baryMin.append(float(bary.min()))
   if not surface.good[triangle]or bary.min()<-2e-7:continue
   p=bary@g['points']['world'][surface.indices[triangle]].astype(float);depth=-float(g['view'][2,:3]@p+g['view'][2,3])+info['depthOffset'];depthError.append(abs(depth-float(owner[y,x,2])));n+=1
  assert not depthError or max(depthError)<2e-5
  total+=int(eligible.sum());known+=n;rows.append({'frame':f['frame'],'nativeFacePixels':int(eligible.sum()),'sourceReceiptConsistent':int(current.sum()),'UVTriangleCarriersVerified':n,'maxDepthResidualMetres':max(depthError,default=0),'minBarycentric':min(baryMin,default=None)})
 result={'actualSavedFrames':6,'nativeFacePixels':total,'verifiedSourceCarriers':known,'newGPUOrUnityCalls':0,'canonicalOwnerIsNotPrimitive':True,'firstLoss':'Canonical333.CanonicalMetadata uses global=0 outside clothing roles; Prepare333 uses canonical m.w as owner.w; Resolve and Native395 preserve that canonical tag, not raw native primitive. Prepared/raw metadata remain separate.','binding':binding,'rows':rows};(G/'RECOVERED_CARRIERS47.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
