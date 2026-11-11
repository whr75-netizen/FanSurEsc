"""Read only completed actual GPU strips; never synthesize missing samples."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;G=H/'face33';C=G/'capture';O=G/'analysis'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete'] and r['restorationChecksPass'] and r['ownedResourcesReleased']
 assert all(r[k]for k in ['Edit','observerRemoved','optionsRestored','pipelineRestored','timeRestored','backgroundRestored','PlayerSettingsBackgroundSame','inputSameReferenceAndJSON','devicesPreserved'])and r['pendingOwners']==0 and not r['errors'] and not r['globalErrors']
 assert r['frameInfo']['frame']==r['capturedFrame'] and r['frameInfo']['sourceId']==r['frameKey']
 O.mkdir(exist_ok=True);fields={};files=[]
 for name in sorted({p['name']for p in r['planes']}):
  parts=sorted([p for p in r['planes']if p['name']==name],key=lambda p:p['bottomRow']);w,h=parts[0]['width'],parts[0]['height'];a=np.empty((h,w,4),np.float32);nextrow=0
  for p in parts:
   assert p['bottomRow']==nextrow and p['width']==w and p['height']==h
   path=C/p['file'];raw=path.read_bytes();assert len(raw)==p['bytes']==w*p['rows']*16
   a[nextrow:nextrow+p['rows']]=np.frombuffer(raw,dtype='<f4').reshape(p['rows'],w,4);nextrow+=p['rows'];files.append({'file':p['file'],'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
  assert nextrow==h and np.isfinite(a).all();fields[name]=a
 q0,meta,legacy,mask=fields['q3'],fields['q4'],fields['q5'],fields['q6'];rawmeta=fields['q7'];face=np.rint(rawmeta[:,:,1])==4;nativeface=np.rint(meta[:,:,1])==4
 sameDepth=(q0[:,:,2]==legacy[:,:,2])&(legacy[:,:,3]>0)&(q0[:,:,3]>0);valid=face&(legacy[:,:,3]>0)
 expected=np.where((mask[:,:,3]>0)&(np.abs(mask[:,:,0]-mask[:,:,1])>=.01),mask[:,:,0],mask[:,:,1]);actual=legacy[:,:,0]
 # A proposal of zero is valid. Do not count the absent alpha/metadata domain.
 paired=valid&(mask[:,:,2]==legacy[:,:,2]);coords=np.argwhere(paired&(np.abs(expected-actual)>.00001))
 qx,qy,qw,qh=r['QROI'];tohead=lambda y,x:[int(qx+x),int(qy+qh-1-y)]
 summary={'sourceId':r['frameKey'],'frame':r['capturedFrame'],'actualGPU':True,'newPixelAlgorithmApplied':False,'ROI':r['ROI'],'QROI':r['QROI'],'route':r['frameInfo'],'stripCount':len(files),'bytes':sum(p['bytes']for p in files),'nativeFaceCells':int(nativeface.sum()),'existingFaceCells':int(valid.sum()),'pairedExistingMaskCells':int(paired.sum()),'existingQ0QprimeChanges':int((paired&(mask[:,:,1]!=actual)).sum()),'existingQEquationMismatch':len(coords),'equationMismatchCoordinates':[tohead(y,x)for y,x in coords],'sameDepthSourceExisting':int((valid&sameDepth).sum()),'differentDepthSourceExisting':int((valid&~sameDepth).sum()),'nativeVsExistingQ0DifferenceOnSameDepth':int((valid&sameDepth&(q0[:,:,0]!=mask[:,:,1])).sum()),'sourceBoundaryClassCounts':{str(i):int((np.rint(fields['classification'][:,:,3])==i).sum())for i in np.unique(np.rint(fields['classification'][:,:,3])).astype(int)},'geometryLightDomainEquivalence':'Not assumed: clone source Q vs current product measured by paired depth; no0-error claim for unpaired cells.','finitePaletteLimitation':'No complete face-region/LUT binding is active. Unique colours alone do not establish off-palette contamination.'}
 # Evaluate the real face ShadeBoundary preconditions. Face role3 has no UV
 # membership texture branch; its region is exactly role3 in the current source.
 # No GPU replay or synthetic region is substituted for actual readback.
 normal=fields['q8'][:,:,:3];length=np.linalg.norm(normal,axis=2);nn=np.divide(normal,length[:,:,None],out=np.zeros_like(normal),where=length[:,:,None]>0)
 old=mask[:,:,1];cont=legacy[:,:,1];dirs=[(-1,0),(1,0),(0,-1),(0,1)];ring=[(-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
 gate=[]
 for y,x in np.argwhere(valid):
  q=old[y,x];m=rawmeta[y,x];safe=True;labels=[];same=0;opposite=q;why=set()
  def neighbour(xx,yy):
   if not(0<=xx<qw and 0<=yy<qh):why.add('outside captured halo');return False
   mm=rawmeta[yy,xx]
   if mm[0]<=0 or abs(mm[1]-m[1])>.1 or abs(mm[2]-m[2])>.1 or legacy[yy,xx,3]<.5:why.add('role/owner/alpha boundary');return False
   if np.dot(nn[y,x],nn[yy,xx])<=.94:why.add('normal discontinuity');return False
   if abs(legacy[yy,xx,2]-legacy[y,x,2])>=r['frameInfo']['worldPixel']*2:why.add('depth discontinuity');return False
   return True
  for dy in [-1,0,1]:
   for dx in [-1,0,1]:
    if dx==0 and dy==0:continue
    safe=neighbour(x+dx,y+dy) and safe;v=old[np.clip(y+dy,0,qh-1),np.clip(x+dx,0,qw-1)];labels.append(v)
    if abs(dx)+abs(dy)==1:
     if abs(v-q)<.01:same+=1
     else:opposite=v
  step=1/(max(2,r['frameInfo']['faceSteps'])-1);bits=[old[np.clip(y+dy,0,qh-1),np.clip(x+dx,0,qw-1)]for dx,dy in ring];transitions=sum(abs(bits[i]-bits[(i+1)%8])>.01 for i in range(8));span=max([q]+labels)-min([q]+labels)
  tip=same==1 and transitions==2 and abs(span-step)<.01;uncertain=abs(cont[y,x]-(q+opposite)*.5)<=step*.1
  back=False
  if safe and tip and uncertain:
   back=any(neighbour(x+dx,y+dy) and neighbour(x+2*dx,y+2*dy) and abs(old[y+dy,x+dx]-q)<.01 and abs(old[y+2*dy,x+2*dx]-q)<.01 for dx,dy in dirs)
  gate.append({'xy':tohead(y,x),'Q0':float(q),'continuous':float(cont[y,x]),'safe':safe,'sameCardinal':same,'ringTransitions':int(transitions),'tip':bool(tip),'uncertain':bool(uncertain),'back':back,'unsafeCauses':sorted(why)})
 summary['schemaCorrection']={'q7':'raw[5]=(viewDepth, role+1, instanceId, primitiveId+1). Its W is NOT alpha. FrameInfo inherited caption raw role-owner-depth-alpha is inaccurate; analysis uses actual producer source.', 'q8':'raw[2]=(effective MToon normal including normal map, front/back flag); not geometric-only normal.', 'q9':'raw[6]=(source UV, primitiveId+1, renderer+1).'}
 summary['actualFaceProposalGates']={'safe':sum(g['safe']for g in gate),'tipTopology':sum(g['tip']for g in gate),'safeAndTip':sum(g['safe']and g['tip']for g in gate),'safeTipUncertain':sum(g['safe']and g['tip']and g['uncertain']for g in gate),'eligible':sum(g['safe']and g['tip']and g['uncertain']and g['back']for g in gate)}
 summary['actualFaceQ0Values']=sorted(map(float,np.unique(old[valid])));summary['actualFaceContinuousRange']=[float(cont[valid].min()),float(cont[valid].max())]
 summary['sourceBoundaryCoverage']={name:{'positiveCells':int((fields['classification'][:,:,i]>0).sum()),'fullyCoveredCells':int((fields['classification'][:,:,i]>=1).sum()),'sumCellEquivalent':float(fields['classification'][:,:,i].sum()),'maxCoverage':float(fields['classification'][:,:,i].max())}for i,name in enumerate(['sourceOutline','sourcePigment'])}
 (O/'FACE_GATE_CELLS33.json').write_text(json.dumps(gate,indent=2),encoding='utf-8',newline='\n')
 for name,a in fields.items():
  if name=='classification':continue
  if name.startswith('source'):
   im=np.zeros_like(a);im[:,:,:3]=np.maximum(a[:,:,:3],0);im[:,:,3]=np.clip(a[:,:,3],0,1)
  elif name=='q0':im=a.copy()
  else:continue
  rgb=np.clip(im[:,:,:3],0,1);rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*np.power(rgb,1/2.4)-.055);rgba=np.concatenate([rgb,im[:,:,3:4]],axis=2);img=Image.fromarray(np.uint8(np.rint(rgba[::-1]*255)),'RGBA');img.save(O/(name+'.png'));img.resize((img.width*4,img.height*4),Image.Resampling.NEAREST).save(O/(name+'-nearest4.png'))
 panels=[]
 for label,a,cmap in [('Q0 existing',mask[:,:,1],False),('Qprime existing',actual,False),('Q0 clone',q0[:,:,0],False),('paired Q difference',(valid&sameDepth&(q0[:,:,0]!=mask[:,:,1])).astype(float),True),('source outline coverage',fields['classification'][:,:,0],False),('source pigment coverage',fields['classification'][:,:,1],False)]:
  v=np.clip(a[::-1],0,1);rgb=np.repeat(v[:,:,None],3,axis=2);img=Image.fromarray(np.uint8(np.rint(rgb*255)),'RGB');img=img.resize((224,232),Image.Resampling.NEAREST);panel=Image.new('RGB',(244,266),(35,37,43));panel.paste(img,(10,26));ImageDraw.Draw(panel).text((10,7),label,fill='white');panels.append(panel)
 board=Image.new('RGB',(3*244,2*266),(35,37,43))
 for i,p in enumerate(panels):board.paste(p,((i%3)*244,(i//3)*266))
 board.save(O/'ACTUAL_Q_BOUNDARY33.png');summary['sourceInitialRGBUniqueFace']=int(len(np.unique(fields['q0'][nativeface,:3],axis=0)));summary['inputFiles']=files
 (O/'ACTUAL33.json').write_text(json.dumps(summary,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in summary.items()if k not in ['route','inputFiles']},indent=2))
if __name__=='__main__':main()
