"""Same-frame77 stage attribution. CPU-only, no inferred colour families."""
from pathlib import Path
import hashlib,json,sys,collections
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent;G=H/'face28'
sys.path.insert(0,str(R/'bounded-form115/runtime24/full-render24'))
from report_full24 import read,plane,rgba
def stage(p,name):
 a=np.zeros((272,480,4),np.float32);cover=np.zeros(272,int);identity=None
 for q in sorted(p.glob('ST28-'+name+'-y*.plane')):
  m,v=plane(q);x,y,w,h=m['roi'];assert x==0 and w==480 and 0<h<=32
  key=(m['sourceId'],m['frame'],m['serial']) if 'frame'in m else m['sourceId']
  if identity is None:identity=key
  assert identity==key
  a[y:y+h]=v;cover[y:y+h]+=1
 assert np.all(cover==1),name
 return a
def stats(a,mask):
 x=a[mask];u=rgba(a)[mask,:3]
 return {'cells':len(x),'linearRGBExact':len(np.unique(x[:,:3],axis=0)),'sRGB8':len(np.unique(u,axis=0)),'alphaValues':np.unique(x[:,3]).tolist()}
def main():
 root=G/'capture-stages';s=read(next(root.glob('STATE113-*-finished.json')))
 keys=['PlayExited','optionsRestored','pipelineRestored','timeRestored','backgroundRestored','playerSettingsRunInBackgroundRestored','observerRemoved']
 assert all(s[k]for k in keys)and not s.get('error')and not s.get('restorationError')and not s['globalRestoreErrors']
 assert s['motionRestoration82']['allRestored']and all(x['equal']for x in s['nativeComparisons72'])
 assert len(s['sequencePackets'])==1;p=Path(s['sequencePackets'][0]['output']);m=read(p/'RAW_MANIFEST.json')
 assert hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text().strip()
 assert m['frameUnchangedDuringReadback']and m['stageContract28']['newDispatches']==0
 fields=['beforeStyle','prepared','postLine','final','meta','uv','owner','audit'];data={v:{k:stage(p,v+'-'+k)for k in fields}for v in ['M','H']}
 rows={};changes={}
 for view,d in data.items():
  role=np.rint(d['meta'][...,1]).astype(int)-1;valid=d['meta'][...,0]>0
  rows[view]={}
  for label,select in [('face',role==3),('iris',role==1),('sclera',role==4),('nativeLid',role==6),('hair',role>=11)]:
   scope=valid&select;rows[view][label]={k:stats(d[k],scope)for k in fields[:4]}
   if view=='M':rows[view][label]['beforeStyle']={'notComparable':'before JoinBare, whereas role mask is after JoinBare; pre-join body/head domains differ'}
  # A label/geometry match does not assert that beforeStyle (pre-JoinBare) has
  # the same domain. Only prepared -> postLine is the actual joined line pair.
  changed=np.any(d['prepared']!=d['postLine'],axis=2);line=d['audit'][...,0]>0
  changes[view]={'preparedToPostLineCells':int(changed.sum()),'byPreparedRole':dict(collections.Counter(map(str,role[changed]))),'faceCellsChanged':int(np.count_nonzero(changed&valid&(role==3))),'auditReasons':dict(collections.Counter(map(str,np.rint(d['audit'][...,0]).astype(int)[valid]))),'allChangedHaveLineAudit':bool(np.all(line[changed]))}
  changes[view]['meaning']='actual joined OwnerLines colour pair'if view=='M'else'Includes MainToHead reproject/copy of main postLine; NOT an independent head line pass or a line-error count'
  for k in fields[:4]:Image.fromarray(rgba(d[k][::-1])).save(G/f'{view}-{k}28.png')
 main=data['M'];role=np.rint(main['meta'][...,1]).astype(int)-1;face=(role==3)&(main['meta'][...,0]>0)
 ys,xs=np.nonzero(face);x0,x1=max(0,xs.min()-4),min(480,xs.max()+5);y0,y1=max(0,ys.min()-5),min(272,ys.max()+6)
 # Actual source UV -> native evidence. This does not assign a family, infer
 # alpha for baked AA, or use RGB/shading to decide a destination label.
 evidence=np.load(G/'SOURCE_EXTREMA28.npz');source=np.load(G/'SOURCE_NATIVE28.npz');source_rows=[]
 for y,x in zip(ys,xs):
  uv=main['uv'][y,x,:2];assert np.isfinite(uv).all()
  ptex=np.array([uv[0]*1024-.5,(1-uv[1])*1024-.5]);ix,iy=np.floor(ptex).astype(int);fx,fy=ptex-[ix,iy];witness=[]
  for dy in range(2):
   for dx in range(2):
    tx,ty=(ix+dx)%1024,(iy+dy)%1024;cx,cy=tx-4,ty-7
    if 0<=cx<source['mask'].shape[1]and 0<=cy<source['mask'].shape[0]and source['mask'][cy,cx]:
     weight=(fx if dx else 1-fx)*(fy if dy else 1-fy)
     witness.append({'textureXY':[int(tx),int(ty)],'weight':float(weight),'nativeRGB8':source['rgba'][cy,cx,:3].tolist(),'positiveExtremum':bool(evidence['positive'][cy,cx]),'scaleBits':int(evidence['scaleBits'][cy,cx])})
  source_rows.append({'pixelBottomLeft':[int(x),int(y)],'UV':uv.tolist(),'primitive':float(main['meta'][y,x,3]),'independentLitBit':float(main['uv'][y,x,2]),'sourceWitnesses':witness,'evidenceWeight':sum(z['weight']for z in witness if z['positiveExtremum']),'regionOrFamilyAssigned':False})
 (G/'VISIBLE_SOURCE_EVIDENCE28.json').write_text(json.dumps({'sourceId':m['sourceId'],'sourceBinding':'registry59 mesh0/primitive3/material3, Unity V flip; texture1024x1024, native crop offset4,7; identity UV transform/repeat/linear filter','cells':source_rows,'meaning':'Bilinear native witness weights only; evidence does not establish a whole-cell colour feature or a closed source region.'},indent=2),encoding='utf-8')
 b=(int(x0),int(272-y1),int(x1),int(272-y0));scale=8;w,h=(x1-x0)*scale,(y1-y0)*scale
 board=Image.new('RGB',(w*3,h+34),'#202020');draw=ImageDraw.Draw(board)
 for i,k in enumerate(['prepared','postLine','final']):
  im=Image.fromarray(rgba(main[k][::-1])).convert('RGB').crop(b).resize((w,h),Image.Resampling.NEAREST);board.paste(im,(i*w,28));draw.text((i*w+5,6),k+' / actual77',fill='white')
 board.save(G/'FACE_STAGES28.png')
 result={'sourceId':m['sourceId'],'frame':m['frameIndex'],'serial':m['mainSerial'],'stageContract':m['stageContract28'],'stageColourCounts':rows,'lineAttribution':changes,'faceCropTopLeft':b,'visibleSourceEvidence':{'faceCells':len(source_rows),'cellsWithPositiveNativeWitness':sum(z['evidenceWeight']>0 for z in source_rows),'regionFamilyBindingsAdded':0},'paletteStatus':'Face/lid source-region LUT is not connected; unique colours are measurements, not a valid outside-LUT verdict. Eye candidate LUT is separately validated27.','restoration':{k:s[k]for k in keys},'nativeEqual':len(s['nativeComparisons72']),'input':s['editInputRestoration82'],'beforeMemory':s['beforeMemory'],'afterMemory':s['afterMemory'],'default77Changed':False,'GPUClassifierOrFixAdded':False}
 (G/'STAGES28.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'sourceId':result['sourceId'],'lineAttribution':changes,'faceCounts':rows['M']['face'],'memoryDeltaMiB':{k:(s['afterMemory'][k]-s['beforeMemory'][k])/1048576 for k in ['allocated','reserved','mono']}}))
if __name__=='__main__':main()
