from pathlib import Path
import numpy as np,json,struct,sys
O=Path(__file__).resolve().parent;R=O/sys.argv[1];out=sys.argv[2]
def read(p):
 b=p.read_bytes();w,h,x,y=struct.unpack_from('<4i',b);o=np.zeros((272,480,4),np.float32);o[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return o
rows=[];faceownership=[]
for pose in sorted(R.glob('*_pose.json')):
 f=json.loads(pose.read_text())['frame'];a=read(R/f'{f:03d}_OFF_FINAL.bin');am=read(R/f'{f:03d}_OFF_META.bin');au=read(R/f'{f:03d}_OFF_UV.bin');ap=read(R/f'{f:03d}_OFF_PREPARED.bin');al=read(R/f'{f:03d}_OFF_POSTLINE.bin')
 for mode in (['CLOTH','BODY']if(R/f'{f:03d}_BODY_FINAL.bin').exists()else['CLOTH']):
  b=read(R/f'{f:03d}_{mode}_FINAL.bin');bm=read(R/f'{f:03d}_{mode}_META.bin');bu=read(R/f'{f:03d}_{mode}_UV.bin');bp=read(R/f'{f:03d}_{mode}_PREPARED.bin');bl=read(R/f'{f:03d}_{mode}_POSTLINE.bin');active=([9,10,11]if mode=='CLOTH'else[8,9,10,11]);d=(np.max(np.abs(a-b),axis=2)>1e-6)&(a[:,:,3]>.5)&(b[:,:,3]>.5)&~np.isin(np.rint(am[:,:,1]),active)&~np.isin(np.rint(bm[:,:,1]),active)
  face=((am[:,:,1]>=1)&(am[:,:,1]<=7))|((bm[:,:,1]>=1)&(bm[:,:,1]<=7))
  for y,x in np.argwhere((np.max(np.abs(a-b),axis=2)>1e-6)&face):
   faceownership.append({'frame':f,'mode':mode,'xy':[int(x),int(y)],'baseMeta':am[y,x].tolist(),'altMeta':bm[y,x].tolist(),'baseUV':au[y,x].tolist(),'altUV':bu[y,x].tolist(),'basePrepared':ap[y,x].tolist(),'altPrepared':bp[y,x].tolist(),'baseFinal':a[y,x].tolist(),'altFinal':b[y,x].tolist()})
  for y,x in np.argwhere(d):
   same=bool(np.max(np.abs(am[y,x]-bm[y,x]))<2e-6 and np.max(np.abs(au[y,x,:2]-bu[y,x,:2]))<2e-6);pd=float(np.max(np.abs(ap[y,x]-bp[y,x])));ld=float(np.max(np.abs(al[y,x]-bl[y,x])));first='PREPARED'if pd>1e-6 else'OWNERLINES'if ld>1e-6 else'POSTLINE_TO_FINAL'
   rows.append({'frame':f,'mode':mode,'xy':[int(x),int(y)],'sameResolvedSurface':same,'firstChangedSavedStage':first,'baseMeta':am[y,x].tolist(),'altMeta':bm[y,x].tolist(),'baseUV':au[y,x].tolist(),'altUV':bu[y,x].tolist(),'basePrepared':ap[y,x].tolist(),'altPrepared':bp[y,x].tolist(),'basePostLine':al[y,x].tolist(),'altPostLine':bl[y,x].tolist(),'baseFinal':a[y,x].tolist(),'altFinal':b[y,x].tolist()})
result={'samples':rows,'count':len(rows),'firstStages':{s:sum(r['firstChangedSavedStage']==s for r in rows)for s in ['PREPARED','OWNERLINES','POSTLINE_TO_FINAL']},'sameSurface':sum(r['sameResolvedSurface']for r in rows),'faceOwnership':faceownership}
(O/out).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='samples'}));print(json.dumps([{k:r[k]for k in ['frame','mode','xy','sameResolvedSurface','firstChangedSavedStage','baseFinal','altFinal']}for r in rows if round(r['baseMeta'][1])<=7 or round(r['altMeta'][1])<=7]))
