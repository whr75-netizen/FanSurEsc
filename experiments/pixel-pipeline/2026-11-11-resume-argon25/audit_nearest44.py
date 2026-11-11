from pathlib import Path
import hashlib,json
import numpy as np

H=Path(__file__).resolve().parent
def read_case(name):
 root=H/'face44'/name;r=json.loads((root/'capture/COMPLETE.json').read_text());a=json.loads((root/'analysis/ACTUAL_NATIVE44.json').read_text())
 assert r['restorationChecksPass'] and r['ownedResourcesReleased'] and r['pendingOwners']==0 and not r['errors'] and a['CPUExactFrames']==6
 assert all(x['outOfSourceT']==x['invalid']==x['paletteMismatch']==x['unselectedNativeRGBChanged']==0 for x in a['rows'])
 return root,r,a
def plane(root,r,f):
 p=next(p for p in r['planes'] if p['frame']==f['frame'] and p['name']=='atlas40')
 x=np.fromfile(root/'capture'/p['file'],dtype='<f4').reshape(p['height'],p['width'],4);w=f['QROI'][2]
 return [x[:,i*w:(i+1)*w]for i in range(15)]
def main():
 base,b,ba=read_case('');world,w,wa=read_case('world');rows=[]
 for bf,wf in zip(b['frames'],w['frames']):
  assert bf['frame']==wf['frame'];x,y=plane(base,b,bf),plane(world,w,wf)
  rows.append({'frame':bf['frame'],'sourceIdsDifferAsRequired':bf['sourceId']!=wf['sourceId'],'sameQROI':bf['QROI']==wf['QROI'],'sameHairOnLineMask':np.array_equal(x[3][:,:,3],y[3][:,:,3]),'sameHairOffLineMask':np.array_equal(x[5][:,:,3],y[5][:,:,3]),'sameSourceEdgeIDs':np.array_equal(x[4][:,:,1],y[4][:,:,1])})
 assert all(all(v for k,v in x.items() if k!='frame')for x in rows)
 (H/'face44/WORLD_INDEPENDENCE44.json').write_text(json.dumps(rows,indent=2),encoding='utf-8',newline='\n')
 old=json.loads((H/'face43/ACTUAL_CARRIER43.json').read_text());new=json.loads((H/'face43/nearest44/ACTUAL_CARRIER43.json').read_text());assert old['unknownSamples']==88 and new['sourceSamples']==176 and new['unknownSamples']==0
 def data(p):
  r=json.loads(p.read_text())['result'];o=r.get('structuredContent') or next(json.loads(c['text'])for c in r['content']if c.get('type')=='text');assert o['success'];return o['data']
 assert data(H/'face44/console/REPLY.json')==data(H/'face33/console/REPLY.json')
 assert 'playing=False' in(H/'face44/final/PUBLIC_AFTER.txt').read_text()
 results={}
 for name,r,a in [('base',b,ba),('world',w,wa)]:
  before,after=r['beforeMemory'],r['afterMemory']
  results[name]={'utc':r['utc'],'actualConsecutiveFrames':len(r['frames']),'sourceSamples':[x['sourceLineCells']for x in a['rows']],'selected':[x['selected']for x in a['rows']],'worldRejected':[x['worldRejected']for x in a['rows']],'pairedLegacy':[x.get('pairedLegacySameInput')for x in a['rows']],'CPUExactFrames':a['CPUExactFrames'],'restored':True,'nativeEqual':sum(x.get('equal')is True for x in r['nativeChecks']),'nativeTotal':len(r['nativeChecks']),'beforeMemory':before,'afterMemory':after,'allocatedMiBChange':(after['allocated']-before['allocated'])/1048576}
  if name=='world':assert r['worldFixture41After']['disposed']and not any(r['worldFixture41After'][k]for k in ['ownedGoAlive','ownedMaterialAlive','ownedMeshAlive'])
 result={'baselineCommit':'1f31f2e5895216e3d9697547c5b2edbf1f15561e','cases':results,'old42Provenance':{'sourceSamples':old['sourceSamples'],'unknownOutsideSourceSegment':old['unknownSamples']},'fixed44Provenance':{'sourceSamples':new['sourceSamples'],'unknown':new['unknownSamples'],'maxDepthResidual':new['maxDepthResidual'],'twoUVCarriersRetained':new['UVSeamSamples']},'newComputeKernels':0,'shaderOnlyImport':1,'projectCSharpImport':0,'consoleSameAs33':True,'product77Changed':False,'ownerHistoryReplaced':False,'sourceKeyIsActorViewHistoryKey':False,'fullPixelFootprintVisibilityProven':False,'facePaletteComplete':False,'variableThicknessComplete':False,'artTemporalStabilityPassed':False,'GPUTimeMeasured':False,'GPU115':0,'CUA':0,'SaveAssets':0,'killResetDriverGC':0,'push':False}
 (H/'face44/STATUS44.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'frames':12,'validSourceSamples':176,'unknown':0,'worldSourceIndependent':6,'allocatedMiB':[x['allocatedMiBChange']for x in results.values()],'GPUCallsThisAudit':0}))
if __name__=='__main__':main()
