from pathlib import Path
import json,struct,csv,collections
import numpy as np
ROOT=Path(__file__).parent;CAP=ROOT/'Full574'
def buf(path):
 d=path.read_bytes();w,h,x,y=struct.unpack_from('<4i',d);return x,y,np.frombuffer(d,'<f4',offset=16).reshape(h,w,4)
def holes(m):
 h,w=m.shape;remaining={(x,y)for y in range(h)for x in range(w)if not m[y,x]};closed=[]
 while remaining:
  p=min(remaining);remaining.remove(p);q=[p];border=False
  for x,y in q:
   border|=x in(0,w-1)or y in(0,h-1)
   for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
    n=x+dx,y+dy
    if n in remaining:remaining.remove(n);q.append(n)
  if not border:closed.append(q)
 return closed
rows=[];faceChanges=[]
for path in sorted(CAP.glob('*_ON.png')):
 f=int(path.stem[:3]);p=[CAP/f'{f:03}_{s}'for s in['OFF','ON']];params=[json.loads(Path(str(z)+'_PARAMS.json').read_text())for z in p]
 mask=[buf(Path(str(z)+'_MASK.bin'))for z in p];meta=[buf(Path(str(z)+'_META.bin'))for z in p];colour=[buf(Path(str(z)+'_FINAL.bin'))for z in p]
 assert mask[0][:2]==mask[1][:2]and meta[0][:2]==meta[1][:2]
 selected=[z[2][:,:,1]>.5 for z in mask];ox,oy=mask[0][:2];source=Path(str(p[0])+'_SOURCE_CURVES.bin').read_bytes()==Path(str(p[1])+'_SOURCE_CURVES.bin').read_bytes()
 owner=Path(str(p[1])+'_OWNERS.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',owner);o=np.frombuffer(owner,'<i4',count=w*h,offset=16).reshape(h,w);e=np.frombuffer(owner,'?',count=w*h,offset=16+4*w*h).reshape(h,w)
 expected=selected[1][y-oy:y-oy+h,x-ox:x-ox+w];assert np.array_equal(expected,o==1)and np.all((o>0)==e)
 same=np.all(meta[0][2]==meta[1][2],axis=2);nonhair=same&(meta[0][2][:,:,1]>0)&(meta[0][2][:,:,1]<12);rgb=np.any(colour[0][2]!=colour[1][2],axis=2)
 face=[np.isin(m[2][:,:,1],[4,5])for m in meta];faceDiff=face[0]!=face[1]
 for yy,xx in np.argwhere(faceDiff):
  mx,my=int(xx+meta[0][0]),int(yy+meta[0][1]);faceChanges.append({'frame':f,'main':[mx,my],'head':[mx-params[1]['offsetX'],my+params[1]['offsetY']],'before':meta[0][2][yy,xx].tolist(),'after':meta[1][2][yy,xx].tolist()})
 eyeInputs=[Path(str(z)+'_EYE_INPUT.txt').read_text()for z in p]
 eyeVisible=[buf(Path(str(z)+'_EYE_VISIBLE.bin'))[2]for z in p]
 outside=[int(((m[2][:,:,1]>=12)&(k[2][:,:,0]<.5)).sum())for k,m in zip(mask,meta)]
 row={'frame':f,'phaseExact':params[0]['phase']==params[1]['phase'],'sourceCurvesExact':source,'maskChanged':int(np.count_nonzero(selected[0]!=selected[1])),'addedHair':int(np.count_nonzero(selected[1]&~selected[0])),'removedHair':int(np.count_nonzero(selected[0]&~selected[1])),'closedHoles4':[len(holes(s))for s in selected],'singleOwnerExact':True,'outsideEnvelope':int(np.count_nonzero(expected&~e)),'outsideParent':outside,'RGBChanged':int(rgb.sum()),'sameNonHairMetaRGBChanged':int(np.count_nonzero(nonhair&rgb)),'faceCoverageChanged':int(faceDiff.sum()),'eyeSourceInputs':eyeInputs,'eyeVisibleBufferDiff':int(np.any(eyeVisible[0]!=eyeVisible[1],axis=2).sum())}
 if f in[71,72,73]:row['front232_45']=[bool(s[45-oy,232-ox])for s in selected]
 rows.append(row)
rayRows=[];witness=[];missing=[]
for frame in sorted({z['frame']for z in faceChanges}|{76}):
 file=CAP/f'{frame:03}_ON_FACE_SAME_RAY.csv'
 rays=list(csv.DictReader(file.open()))if file.exists()else[]
 rayRows.extend(dict(frame=frame,**r)for r in rays)
 lookup={(int(r['mainX']),int(r['mainY'])):r for r in rays}
 for z in faceChanges:
  if z['frame']!=frame:continue
  r=lookup.get(tuple(z['main']));witness.append({'change':z,'sameRay':r})
  if r is None:missing.append(z)
hit=[r for r in rayRows if r['skinCamZ']];front=[r for r in hit if r['skinFront']=='1'];anyfront=[r for r in rayRows if r['anyFront']=='1']
from PIL import Image
imageRows=[];timings={'OFF':[],'ON':[]};families=[]
for row in rows:
 f=row['frame'];im=[np.asarray(Image.open(CAP/f'{f:03}_{k}.png').convert('RGB'))for k in ['OFF','ON']];dif=np.any(im[0]!=im[1],axis=2);beyond=dif.copy();beyond[25:115,40:150]=False
 imageRows.append({'frame':f,'changedScreenPixels':int(dif.sum()),'changedOutsideHeadROI':int(beyond.sum())})
 for k in ['OFF','ON']:
  t={q.split('=')[0]:float(q.split('=')[1])for q in (CAP/f'{f:03}_{k}_AUTO.txt').read_text().split()}
  timings[k].append(t)
 with (CAP/f'{f:03}_ON_FAMILIES.tsv').open() as file:
  families.extend(dict(frame=f,**r)for r in csv.DictReader(file,delimiter='\t'))
aggregate={k:{field:{'median':float(np.median([t[field]for t in ts])),'p95':float(np.percentile([t[field]for t in ts],95)),'min':min(t[field]for t in ts),'max':max(t[field]for t in ts)}for field in ts[0]}for k,ts in timings.items()}
summary={'poses':len(rows),'samePoseAndSource':all(r['phaseExact']and r['sourceCurvesExact']for r in rows),'ownerExact':all(r['singleOwnerExact']for r in rows),'outsideEnvelope':sum(r['outsideEnvelope']for r in rows),'outsideParent':sum(sum(r['outsideParent'])for r in rows),'newClosedHoles':sum(max(0,r['closedHoles4'][1]-r['closedHoles4'][0])for r in rows),'sameNonHairMetaRGBChanges':sum(r['sameNonHairMetaRGBChanged']for r in rows),'faceCoverageChanges':len(faceChanges),'faceChangesMissingSameRayPacket':len(missing),'eyeSourceUnchanged':all('bitChannelDiff=0'in r['eyeSourceInputs'][1]for r in rows),'eyeVisibleBufferDiff':sum(r['eyeVisibleBufferDiff']for r in rows),'sourceFaceRayPackets':len(rayRows),'sourceFaceSkinHits':len(hit),'acceptedPacketsWithOpaqueSkinInFront':len(front),'acceptedPacketsWithAnyOpaqueFaceInFront':len(anyfront),'wholeBodyChangesOutsideHeadROI':sum(r['changedOutsideHeadROI']for r in imageRows),'timingsMeasuredDuringCaptureNotPlayerFPS':aggregate,'faceSourceRayWitness':witness,'missingFaceWitnesses':missing,'rows':rows,'faceChanges':faceChanges,'imageRows':imageRows,'families':families}
(ROOT/'FULL_REVIEW574.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items()if k not in['rows','faceChanges','faceSourceRayWitness','imageRows','families','timingsMeasuredDuringCaptureNotPlayerFPS']}))
print(json.dumps(aggregate))
