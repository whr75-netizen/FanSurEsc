"""Separate canonical allocation from same-pose destination occlusion sampling."""
from pathlib import Path
import collections,json,sys,numpy as np
H=Path(__file__).resolve().parent;R=H.parent;sys.path.insert(0,str(R))
from report_full24 import read,plane,buffer
from trace_carrier24 import origins
sys.path.insert(0,str(R.parents[2]/'eye-failures114'));from trace114 import geometry,matrix

def main():
 s=read(next((R/'motion24').glob('STATE113-*-finished.json')));rows=[];bycell=collections.defaultdict(list);start=None
 for packet in s['sequencePackets'][:10]:
  p=Path(packet['output']);m=read(p/'RAW_MANIFEST.json');roi=m['grid102']['eyeTopLeftROI'];w,h=roi[2:];cw=m['forward102']['canonicalSize'][0]//4
  origin,_=origins(m,p);ids=buffer(p/'curve-identity.f32').reshape(-1,4);q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4);v=buffer(p/'ASSIGNED-visibility24.f32').reshape(q.shape)
  hm=plane(p/'S4-meta.plane')[1];hc=plane(p/'S4-rgba.plane')[1];eo=plane(p/'F-EyeOwner.plane')[1];fo=plane(p/'F-FinalOwner.plane')[1]
  raw=geometry(p,m);view=raw['view'];skinIds=np.unique(raw['triangles'][(raw['sources'][:,0]==1)&(raw['sources'][:,1]==3),:3]);world=raw['world4'][skinIds]
  if start is None:start=(view,world,skinIds,raw['world4'])
  assert np.array_equal(start[2],skinIds)
  row={'frame':packet['frame'],'sourceId':packet['sourceId'],'phase':m['motion82']['requestedPhase'],
       'headViewBasisDelta':float(abs(view[:3,:3]-start[0][:3,:3]).max()),'nativeSkinWorldDelta':float(abs(world-start[1]).max()),
       'allRendererWorldDelta':{str(int(k)):float(abs(raw['world4'][np.unique(raw['triangles'][raw['sources'][:,0]==k,:3])]-start[3][np.unique(raw['triangles'][raw['sources'][:,0]==k,:3])]).max())for k in np.unique(raw['sources'][:,0])},'samples':[]}
  for y in range(h):
   for x in range(w):
    cx,cy=np.floor(np.array([roi[0]+x+.5,272-(272-roi[1]-roi[3]+y+.5)],np.float32)-origin).astype(int)
    if min(cx,cy)<0 or cx>=cw or cy>=len(ids)//cw:continue
    ident=ids[cy*cw+cx]
    if ident[0]!=4:continue
    coverage=np.float32(0);fronts=[];margins=[]
    for i in range(16):
     yy,xx=y*4+i//4,x*4+i%4;sample=hm[yy,xx];colour=hc[yy,xx]
     if sample[0]<=0 or sample[3]<=0 or colour[3]<=0:continue
     depth=q[y,x,i,2];isfront=depth>0 and sample[0]<depth-np.float32(3e-5)
     margins.append(float(depth-sample[0]));fronts.append(i)if isfront else None
     if isfront:coverage=np.float32(coverage+np.clip(sample[3],0,1))
    own=int(ident[1]);key=(own,int(cx),int(cy));visible=fo[y,x,0]==5 and fo[y,x,1]==own
    centre=np.array([roi[0]+x+.5,272-(272-roi[1]-roi[3]+y+.5)],np.float32)
    r={'canonical':[int(cx),int(cy)],'owner':own,'tile':[x,y],'sourceOrigin':origin.tolist(),'destinationCentre':centre.tolist(),
       'commonEyeGridSnapDelta':(centre-origin-np.array([cx+.5,cy+.5])).tolist(),'preHairRoleOwner':eo[y,x,:2].tolist(),'finalRoleOwner':fo[y,x,:2].tolist(),
       'faceVisibility16':v[y,x,:,:2].sum(0).tolist(),'hairCoverage16':float(coverage),'frontSampleIndices':fronts,
       'nearestHairDepthMargin':min((abs(z)for z in margins),default=None),'whiteVisible':bool(visible)}
    row['samples'].append(r);bycell[key].append({'phase':row['phase'],'frame':row['frame'],**r})
  rows.append(row)
 changes=[{'key':list(k),'phases':v}for k,v in bycell.items()if len({q['whiteVisible']for q in v})>1]
 report={'actualFrames':10,'canonicalFormConstant':True,'nativeSkinWorldMaxDelta':max(r['nativeSkinWorldDelta']for r in rows),
         'headViewBasisMaxDelta':max(r['headViewBasisDelta']for r in rows),
         'allRendererWorldMaxDelta':{k:max(r['allRendererWorldDelta'][k]for r in rows)for k in rows[0]['allRendererWorldDelta']},'changedWhiteCells':changes,'rows':rows,
         'classification':'Inspect preHairRoleOwner versus finalRoleOwner and measured hairCoverage16. These are recorded producer samples, not independent alpha/geometry queries.',
         'sourceLocalHistoryUsedForFinalOcclusion':False,'UnityOrGPUCalls':0}
 (H/'PHASE_EXPOSURE24.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'skinWorldDelta':report['nativeSkinWorldMaxDelta'],'viewBasisDelta':report['headViewBasisMaxDelta'],'changed':[{ 'key':x['key'],'coverage':[p['hairCoverage16']for p in x['phases']],'preRoles':[p['preHairRoleOwner']for p in x['phases']],'finalRoles':[p['finalRoleOwner']for p in x['phases']]}for x in changes]},ensure_ascii=False))
if __name__=='__main__':main()
