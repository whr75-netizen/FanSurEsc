"""CPU counterfactual using frozen84 geometry and actual selected producer g."""
from pathlib import Path
import json,numpy as np
from frame_bytes77 import decode
from selected_light84 import geometry
from shade_history85 import choose,prior_address
H=Path(__file__).resolve().parent;G=H/'face84';C=G/'capture'
def source_valid(a):
 cls,meta,normal,uv,addr,hu,hm,mask=a[8:16]
 return(meta[:,:,1]==4)&(cls[:,:,3]>.5)&(meta==hm).all(2)&(uv[:,:,:2]==hu[:,:,:2]).all(2)&(hu[:,:,2]==cls[:,:,0])
def main():
 r=json.loads((C/'COMPLETE.json').read_text());previous=None;rows=[]
 for f in r['stream77']['frames']:
  w,h=f['QROI'][2:];a=np.frombuffer(decode((C/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(h,16,w,4).transpose(1,0,2,3);valid=source_valid(a);q=a[8,:,:,0].copy();changed=np.zeros((h,w),bool);reject={};mapped=0;events=[];geo=geometry(C/f"geometry-frame{f['frame']}.bin")
  if previous is not None:
   old,oldf,oldg,oldvalid,oldq=previous;assert f['frame']==oldf['frame']+1 and geo['model']==oldg['model']
   for y,x in np.argwhere(valid):
    primitive=int(a[9,y,x,3]);uv=a[11,y,x,:2];p,why=prior_address(oldg,primitive,uv,oldf['QROI'])
    if p is None:reject[why]=reject.get(why,0)+1;continue
    px,py=p;consistent=oldvalid[py,px]and np.array_equal(old[9,py,px,1:],a[9,y,x,1:])
    if not consistent:reject['carrier']=reject.get('carrier',0)+1;continue
    mapped+=1;chosen,used=choose(q[y,x],a[8,y,x,1],oldq[py,px],f['light84']['faceSteps'])
    if used:q[y,x]=chosen;changed[y,x]=True;events.append({'localXY':[int(x),int(y)],'UV':uv.tolist(),'primitive':primitive,'oldLocalXY':[px,py],'previousQ':float(oldq[py,px]),'currentQ':float(a[8,y,x,0]),'candidateQ':chosen,'g':float(a[8,y,x,1]),'currentlyVisibleOrdinary':bool(a[12,y,x,3]==1)})
  rows.append({'frame':f['frame'],'sourceValid':int(valid.sum()),'mappedSameCarrier':mapped,'sourceQChanges':int(changed.sum()),'visibleQChanges':int((changed&(a[12,:,:,3]==1)).sum()),'rejectedHistory':reject,'events':events});previous=a,f,geo,valid,q
 out={'CPUCounterfactualOnly':True,'newGPUHistoryExecuted':False,'sameFrozen84Input':True,'sourceChanges':sum(x['sourceQChanges']for x in rows),'visibleChanges':sum(x['visibleQChanges']for x in rows),'fullColourOrArtAdopted':False,'rows':rows};(G/'HISTORY_CANDIDATE85.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=='__main__':main()
