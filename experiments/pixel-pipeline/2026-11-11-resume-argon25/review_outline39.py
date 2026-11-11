from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from test_outline39 import resolve
H=Path(__file__).resolve().parent;G=H/'face39';C=G/'capture';O=G/'analysis'
def cc(mask,eight=False):
 left=set(map(tuple,np.argwhere(mask)));sizes=[]
 while left:
  first=left.pop();todo=[first]
  for y,x in todo:
   for p in ([(y+dy,x+dx)for dx in [-1,0,1]for dy in [-1,0,1]if dx or dy]if eight else[(y-1,x),(y+1,x),(y,x-1),(y,x+1)]):
    if p in left:left.remove(p);todo.append(p)
  sizes.append(len(todo))
 return sorted(sizes)
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];O.mkdir(exist_ok=True)
 def field(name):
  rows=sorted([p for p in r['planes']if p['name']==name],key=lambda p:p['bottomRow']);assert rows and sum(p['rows']for p in rows)==rows[0]['height'];return np.concatenate([np.fromfile(C/p['file'],dtype='<f4').reshape(p['rows'],p['width'],4)for p in rows])
 before,after,meta,owner=map(field,['q19','q20','q21','q7']);on,off=field('source8'),field('source10');ink=np.asarray(r['frameInfo']['sourceOutlineRGB39'],np.float32);w,h=r['QROI'][2:];rx,ry,rw,rh=r['ROI'];qx,qy=r['QROI'][:2];dx,dy=rx-qx,h-(ry-qy)-rh;expected=before.copy();expectedMeta=np.zeros_like(meta)
 for y in range(rh):
  for x in range(rw):expected[y+dy,x+dx],expectedMeta[y+dy,x+dx]=resolve(on[8*y:8*y+8,8*x:8*x+8,3],off[8*y:8*y+8,8*x:8*x+8,3],before[y+dy,x+dx],ink)
 mismatch=int(np.any(expected!=after,axis=2).sum());metaMismatch=int(np.any(expectedMeta!=meta,axis=2).sum());assert mismatch==metaMismatch==0
 selected=meta[:,:,2]==1;changed=np.any(before!=after,axis=2);coords=[]
 for y,x in np.argwhere(selected):coords.append({'headXY':[int(qx+x),int(qy+h-1-y)],'onCoverage':float(meta[y,x,0]),'offCoverage':float(meta[y,x,1]),'sourceRole':int(round(owner[y,x,1]))-1,'originalRGBA':before[y,x].tolist(),'candidateRGBA':after[y,x].tolist()})
 native=field('source0');nativePerCell=(native[:,:,3].reshape(rh,8,rw,8).sum((1,3))/64);report={'actualSourceId':r['frameKey'],'actualFrame':r['capturedFrame'],'actualGPU':True,'wholeQCells':w*h,'RGBOracleMismatch':mismatch,'metaOracleMismatch':metaMismatch,'selectedCells':int(selected.sum()),'changedCells':int(changed.sum()),'sourcePaletteMismatch':int(np.any(after[selected,:3]!=ink,axis=1).sum()),'unselectedChanged':int(np.any(before[~selected]!=after[~selected],axis=1).sum()),'hairOccludedCells':int((meta[:,:,3]==3).sum()),'tieUnresolved':int((meta[:,:,3]==2).sum()),'visibilityContradictions':int((meta[:,:,3]<0).sum()),'CC4Sizes':cc(selected),'CC8Sizes':cc(selected,True),'nativeOriginalCoverageSum':float(nativePerCell.sum()),'nativeOriginalSelectedBySameHalfRule':int((nativePerCell>.5).sum()),'trialSourceWidthMetres':r['frameInfo']['nativeOutlineWidthMetres39'],'trialGridGeometryWidthMetres':r['frameInfo']['trialGeometryWidthMetres39'],'defaultProductModified':False,'minimumOneGridGeometryAdopted':False,'records':coords,'limitations':['This is actual isolated GPU MToon inverted-hull geometry and finite source ink composition, not geometric silhouette or full face UV palette completion.','The one-grid geometry minimum is an experimental style rule, not recovered original art intent.','Single held-pose frame, not motion or rotation validation.','Role is raw source centre role, not proof of final eye-part owner.']};(O/'ACTUAL_OUTLINE39.json').write_text(json.dumps(report,indent=2),encoding='utf-8',newline='\n')
 def rgb(a):
  a=np.clip(a[::-1,:,:3],0,1);a=np.where(a<=.0031308,12.92*a,1.055*a**(1/2.4)-.055);return Image.fromarray(np.uint8(np.rint(a*255)))
 board=Image.new('RGB',(720,310),(35,37,43));draw=ImageDraw.Draw(board)
 for k,(title,a)in enumerate([('Actual product77 head RGB',before),('GPU outline trial (not adopted)',after)]):
  im=rgb(a);board.paste(im,(360*k+10,28));board.paste(im.resize((280,280),Image.Resampling.NEAREST),(360*k+70,28));draw.text((360*k+5,7),title,fill='white')
 board.save(O/'OUTLINE_COMPARE39.png');colour=np.zeros((h,w,3),np.uint8);colour[selected]=[255,210,60];colour[meta[:,:,3]==3]=[230,60,80];colour[meta[:,:,3]==2]=[70,180,240];Image.fromarray(colour[::-1]).resize((w*12,h*12),Image.Resampling.NEAREST).save(O/'OUTLINE_VISIBILITY39.png');print(json.dumps({k:v for k,v in report.items()if k!='records'},indent=2))
if __name__=='__main__':main()
