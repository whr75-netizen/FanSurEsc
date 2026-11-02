"""Audit actual runtime24 source/destination depth before proposing a change."""
from pathlib import Path
import collections,json,sys
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent;sys.path.insert(0,str(R))
from report_full24 import read,plane,buffer

def origins(m,p):
 n=m['forward102']['nativeRegistration'];c=read(p/'SOURCE_TRANSFORMS111.json')['carrier']
 return(np.array(n['anchor'],np.float32)+np.array(n['bounds'][:2],np.float32),
        np.array(c['anchor'],np.float32)+np.array(c['bounds'][:2],np.float32))
def points(roi,x,y):
 return np.array([[np.float32(roi[0]+x+(i%4+.5)/4),np.float32(272-((272-roi[1]-roi[3])+y+(i//4+.5)/4))]for i in range(16)],np.float32)
def direct(meta,xy,origin,owner):
 q=np.floor((xy-origin)*np.float32(8)).astype(int);out=np.zeros(16,np.float32)
 good=(q[:,0]>=0)&(q[:,1]>=0)&(q[:,0]<meta.shape[1])&(q[:,1]<meta.shape[0])
 for i in np.flatnonzero(good):
  m=meta[q[i,1],q[i,0]]
  if m[0]>0 and round(float(m[2]))==owner:out[i]=m[0]
 return out
def main():
 rows=[];verified=0;gpuDepthMismatch=[];face=[];memory=[]
 for key,root in [('open',R),('close',R/'sequence24'),('motion',R/'motion24')]:
  s=read(next(root.glob('STATE113-*-finished.json')))
  memory.append({'run':key,'before':s['beforeMemory'],'after':s['afterMemory'],
                 'nativeBeforeCount':len(s['nativeComparisons72']),'faceCompared':any('FaceSourceOwner202'in r['path']for r in s['nativeComparisons72'])})
  for pkt in s['sequencePackets']:
   p=Path(pkt['output']);m=read(p/'RAW_MANIFEST.json');a,c=origins(m,p);roi=m['grid102']['eyeTopLeftROI'];w,h=roi[2:]
   cw=m['forward102']['canonicalSize'][0]//4
   ids=buffer(p/'curve-identity.f32').reshape(-1,4);decision=buffer(p/'curve-decision.f32').reshape(-1,4)
   cells=buffer(p/'REGION113-cells.f32').reshape(512,7,4)
   q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4)
   owner=plane(p/'F-FinalOwner.plane')[1]
   metas={part:plane(p/f'C-part{part}-meta.plane')[1][::-1]for part in [1,2,3]}
   for y in range(h):
    for x in range(w):
     centre=np.array([roi[0]+x+.5,272-(272-roi[1]-roi[3]+y+.5)],np.float32)
     cx,cy=np.floor(centre-a).astype(int)
     if min(cx,cy)<0 or cx>=cw or cy>=len(ids)//cw:continue
     at=cy*cw+cx;ident=ids[at];role,eye=map(lambda v:round(float(v)),ident[:2]);part={1:1,4:2,6:3}.get(role,0)
     if part==0 or decision[at,0]<0:continue
     xy=points(roi,x,y);z=direct(metas[part],xy,c,eye);known=z>0;lo,hi=m['runtime24']['ringDepthRanges'][(eye-1)*2:eye*2]
     total=np.float32(0)
     for zi in z:
      if zi>0:total=np.float32(total+zi)
     fill=np.float32(total/np.float32(known.sum()))if known.any()else ident[2]if lo<=ident[2]<=hi else np.float32(0)
     expected=np.where(known,z,fill);actual=q[y,x,:,2]
     #Summation order can differ at float32 last bits; compare recorded values
     #with an explicit depth-unit error rather than declaring zero on no pairs.
     error=float(abs(expected-actual).max());verified+=16
     if error>2e-6:gpuDepthMismatch.append({'frame':pkt['frame'],'run':key,'tile':[x,y],'maxDepthError':error})
     if not actual.any():
      channel=4 if role==6 else 3;component=3 if role==6 else 1 if role==1 else 2
      denseIndex=int(cells[at,5,1])-1;denseWidth=m['forward102']['denseSize'][0]
      denseMeta=plane(p/'D-lid-meta.plane')[1][::-1].reshape(-1,4)
      denseVisibility=buffer(p/'dense-lid-visibility.f32').reshape(-1,4)
      witness={'selectedDenseIndex':denseIndex,'meta':denseMeta[denseIndex].tolist(),'visibility':denseVisibility[denseIndex].tolist()}if denseIndex>=0 else {'sourceCurveFallback':float(cells[at,5,3])}
      if denseIndex>=0:
       assert denseMeta[denseIndex,0]==ident[2]and round(float(denseMeta[denseIndex,2]))==eye
       assert denseVisibility[denseIndex,0]>0 and denseVisibility[denseIndex,0]==denseVisibility[denseIndex,1]
      rows.append({'run':key,'frame':pkt['frame'],'sourceId':pkt['sourceId'],'packet':str(p),'stage':pkt['testStage82'],'sourceWitness':witness,
        'tile':[x,y],'canonical':[int(cx),int(cy)],'sourceOrigin':a.tolist(),'carrierOrigin':c.tolist(),
        'role':role,'eye':eye,'selectedSourceDepth':float(ident[2]),'matchingCellSourceDepth':float(cells[at,channel,component]),
        'sourcePolicy':cells[at,5].tolist(),'sourceCellLid':cells[at,4].tolist(),'ringDepthRange':[lo,hi],
        'signedDistanceOutsideRing':float(max(lo-ident[2],ident[2]-hi,0)),'destinationMeasuredCount':int(known.sum()),
        'destinationXY':xy.tolist(),'finalStatus':float(owner[y,x,3]),'finalOwner':owner[y,x].tolist()})
 report={'actualFrames':41,'checkedAssignedDepthSamples':verified,'depthMismatch':gpuDepthMismatch,
         'zeroAssignedDepthCells':rows,'memory':memory,'UnityOrGPUCalls':0}
 (H/'TRACE_CARRIER24.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'samples':verified,'mismatchCount':len(gpuDepthMismatch),'zeroDepth':[ {k:v for k,v in r.items()if k not in ['packet','destinationXY']}for r in rows]},ensure_ascii=False))
if __name__=='__main__':main()
