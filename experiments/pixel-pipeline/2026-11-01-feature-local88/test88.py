from pathlib import Path
import json,hashlib,numpy as np
from feature_layer88 import *
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def main():
 tests=[]
 def ck(name,v):assert v,name;tests.append(name)
 source=[SourcePixel(10,10,1,4,0),SourcePixel(11,10,1,1,1),SourcePixel(10,11,1,4,0),SourcePixel(11,11,1,1,1),SourcePixel(12,11,1,4,0)];P=np.array([[.2,.3,.4],[.8,.2,.1]],np.float32);cache=FeatureCache();signatures=set();nativeShapes=set();anchors=[]
 for py in np.linspace(0,1,17):
  for px in np.linspace(0,1,17):
   H=np.array([[1,0,px],[0,1,py],[0,0,1]],float);s=cache.update(source,{1:H},('modelA','viewA','bankA','open'));signatures.add(json.dumps(s['rows'],sort_keys=True));anchors.append(s['anchor']);im,ids,cov=raster(s['rows'],s['anchor'],P,[6,6],(24,24),2);yy,xx=np.where(im[...,3]>0);nativeShapes.add(tuple(sorted((int(x-xx.min()),int(y-yy.min()),int(ids[y,x,1]),int(ids[y,x,2]))for y,x in zip(yy,xx))))
 ck('49 continuous anchor, not floor(delta+.5)',np.max(abs((anchors[1]-anchors[0])-[1/16,0]))<1e-12)
 ck('joint source support and parts invariant through289 phases',len(signatures)==1 and cache.builds==1)
 ck('final2x raster only translates complete group without changing relations',len(nativeShapes)==1)
 original=s['rows'];changedP=P.copy();changedP[0]=[.1,.8,.7];im2,ids2,_=raster(original,s['anchor'],changedP,[6,6],(24,24),2);im,ids,_=raster(original,s['anchor'],P,[6,6],(24,24),2)
 ck('palette change does not rebuild support or move parts',np.array_equal(ids,ids2)and not np.array_equal(im,im2))
 ck('no RGB interpolation/palette escape',all(tuple(v)in set(map(tuple,P.tolist()))for v in im[im[...,3]>0,:3].tolist()))
 # Same input roles are one exclusive occupancy map; there is no iris-first
 # overwrite pass or independent per-part top-K selector (74 regression).
 ck('74 iris and sclera cannot claim the same canonical output cell',len({tuple(r['xy'])for r in original})==len(original)and {r['part']for r in original}=={1,4})
 cache.update(source,{1:H},('modelB','viewA','bankA','open'));ck('model change invalidates owned source support',cache.builds==2)
 cache.update(source,{1:H},('modelB','viewB','bankA','open'));ck('different view cannot borrow old cache',cache.builds==3)
 H2=H.copy();H2[0,1]=.12;cache.update(source,{1:H2},('modelB','viewB','bankA','open'));ck('actual projection deformation rebuilds',cache.builds==4)
 try:cache.update(source,{1:H2},('modelB','viewB','bankA','closed'),False);raise AssertionError('invented closed art')
 except Unsupported:ck('unregistered Close invalidates, no open substitution',not cache.rows and cache.vertices is None)
 cache.dispose();cache.dispose()
 try:cache.update(source,{1:H},('x',));raise AssertionError('reuse disposed owner')
 except RuntimeError:tests.append('double disposal safe; disposed owner cannot reuse')
 other=FeatureCache();ck('multiple renderer lifetime independent',len(other.update(source,{1:np.eye(3)},('renderer2',))['rows'])>0)
 z={s:np.zeros(4)for s in [0,3,4,5,6]};z[4]=np.array([9,12,0,.25]);fraction,why=fragment_visibility(z,10,1);ck('53 partial front fragment remains fractional, not whole-cell veto',fraction==.75 and why==16)
 z[4][3]=1;ck('actual opaque front hair remains blocked',fragment_visibility(z,10,1)[0]==0);z[4][0]=11;ck('behind hair does not block',fragment_visibility(z,10,1)[0]==1)
 z[4][:]=0;z[0]=np.array([9,4,1,1]);ck('actual closed lid/front skin is not ignored',fragment_visibility(z,10,1)[0]==0)
 # Real53 destination source masks: any(front) rejected entire cell. Keep exact
 # observed fragment masks and merely test nonzero remainder, not its unknown
 # source-surface projected shape or full visible-cell adoption.
 fixture=ROOT/'partial-occlusion55/cell-fixtures.json'
 if not fixture.exists():fixture=HERE/'regressions/cell-fixtures55.json'
 cells=json.loads(fixture.read_text())['cells'];partial=[]
 for cell in cells:
  weights=[]
  for y in range(4):
   for x in range(4):
    metas={s:np.zeros(4)for s in [0,3,4,5,6]}
    for si in [4,5,6]:metas[si]=np.array(cell['destinationExternal'][f'S{si}META'][y][x])
    weights.append(fragment_visibility(metas,cell['representativeDepth53'],1)[0])
  ck('53 real destination partial mask frame'+str(cell['frame']),0<sum(weights)<16);partial.append({'frame':cell['frame'],'fractionOfUnoccludedDestinationSamples':sum(weights)/16,'notClaimed':'This is not source native visible area or clean backing proof.'})
 actual=json.loads((HERE/'validated/RESULT88.json').read_text());sweep=[r for r in actual['frames']if r['stage']=='sweep'];ck('87 actual saved pure-phase canonical support has1 signature',actual['sweepCanonicalSignatures']==1);ck('source texel20 is not forced visible/native pixel count',actual['sweepIntrinsicNativePixelCounts']==[100]and actual['originalPixels']==20)
 ck('same pose translation never rebuilds the feature',not any(r['rebuild']for r in sweep[1:]));ck('small important source parts retained jointly',all({(v['owner'],v['part'])for v in r['cells']}=={(1,1),(1,4),(2,1),(2,4)}for r in sweep))
 result={'passed':len(tests),'cases':tests,'actual53FragmentCounterexample':partial,'actual87Source':actual['source87'],'remainingFailure':'Actual sampled4x visibility still changes during pure phase; canonical stability is not full final temporal stability. Native lid remains observed occluding geometry, not a new whole-eye authored form.','UnityCalls':0};q=HERE/'TEST88.json';assert not q.exists();q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
