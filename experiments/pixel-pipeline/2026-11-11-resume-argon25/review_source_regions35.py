"""Direct fine source-light region evidence; no colour or RGB averaging."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;G=H/'face35';C=G/'capture';O=G/'analysis'
def load(name,r):
 rows=sorted([p for p in r['planes']if p['name']==name],key=lambda p:p['bottomRow']);w,h=rows[0]['width'],rows[0]['height'];a=np.empty((h,w,4),np.float32);at=0
 for p in rows:
  raw=(C/p['file']).read_bytes();assert p['bottomRow']==at and len(raw)==p['rows']*w*16;a[at:at+p['rows']]=np.frombuffer(raw,'<f4').reshape(p['rows'],w,4);at+=p['rows']
 assert at==h and np.isfinite(a).all();return a
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];O.mkdir(exist_ok=True)
 old=load('q6',r)[:,:,1];meta=load('q7',r);uv=load('q9',r);fine,fmeta=load('q16',r),load('q17',r);h,w=old.shape;assert fine.shape==(h*8,w*8,4)
 fq=fine.reshape(h,8,w,8,4).transpose(0,2,1,3,4);fm=fmeta.reshape(h,8,w,8,4).transpose(0,2,1,3,4);face=(np.rint(meta[:,:,1])==4);fineface=(np.rint(fm[:,:,:,:,1])==4)&(fq[:,:,:,:,3]>.5)&(fm[:,:,:,:,0]>0)
 support=fineface.sum((2,3));full=face&(support==64);candidate=old.copy();records=[];changed=[];ties=[]
 for y,x in np.argwhere(face):
  values,counts=np.unique(fq[y,x,:,:,0][fineface[y,x]],return_counts=True);maximum=counts.max() if len(counts) else 0;choices=values[counts==maximum];q=old[y,x]
  if full[y,x]and len(choices)==1:q=choices[0]
  if full[y,x]and len(choices)>1:ties.append([int(x),int(y)])
  candidate[y,x]=q;entry={'xy':[int(r['QROI'][0]+x),int(r['QROI'][1]+h-1-y)],'old':float(old[y,x]),'sourceAreaProposal':float(q),'visibleFaceSamples':int(support[y,x]),'fineQCounts':{str(float(a)):int(b)for a,b in zip(values,counts)},'fineContinuousRange':[float(fq[y,x,:,:,1][fineface[y,x]].min()),float(fq[y,x,:,:,1][fineface[y,x]].max())]if support[y,x]else None,'fullSurfaceCell':bool(full[y,x])};records.append(entry)
  if q!=old[y,x]:changed.append(entry)
 def components(q):
  result={}
  for v in np.unique(old[face]):
   m=face&(q==v);seen=np.zeros_like(m);sizes=[]
   for y,x in np.argwhere(m):
    if seen[y,x]:continue
    todo=[(y,x)];seen[y,x]=True
    for yy,xx in todo:
     for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
      b,a=yy+dy,xx+dx
      if 0<=b<h and 0<=a<w and m[b,a]and not seen[b,a]:seen[b,a]=True;todo.append((b,a))
    sizes.append(len(todo))
   result[str(float(v))]=sorted(sizes,reverse=True)
  return result
 result={'sourceId':r['frameKey'],'frame':r['capturedFrame'],'directFineFragmentLight':True,'fineScale':8,'coarseFaceCells':int(face.sum()),'full64FaceCells':int(full.sum()),'partialFaceCellsProtected':int((face&~full).sum()),'changedQCells':changed,'tiesKeepOriginal':ties,'componentsBefore':components(old),'componentsCandidate':components(candidate),'actualFinalRGBModified':False,'hypothesis':'cell-area coverage of source Q regions rather than8-neighbor plane checks; fully visible same role only','notClaimed':['No source-colour gradient/AA semantics inferred.','No topology guarantee or final colour/outline/temporal success from this proposal.'],'records':records};(O/'SOURCE_AREA35.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
 panels=[]
 for title,a in [('fine continuous',fine[:,:,1]),('fine Q',fine[:,:,0]),('coarse Q0',old),('source-area proposal',candidate)]:
  rgb=np.repeat(np.clip(a[::-1],0,1)[:,:,None],3,axis=2);im=Image.fromarray(np.uint8(np.rint(rgb*255)));im=im.resize((224,232),Image.Resampling.NEAREST);p=Image.new('RGB',(244,266),(35,37,43));p.paste(im,(10,26));ImageDraw.Draw(p).text((10,7),title,fill='white');panels.append(p)
 board=Image.new('RGB',(976,266),(35,37,43))
 for i,p in enumerate(panels):board.paste(p,(244*i,0))
 board.save(O/'SOURCE_LIGHT_REGIONS35.png');print(json.dumps({k:v for k,v in result.items()if k!='records'},indent=2))
if __name__=='__main__':main()
