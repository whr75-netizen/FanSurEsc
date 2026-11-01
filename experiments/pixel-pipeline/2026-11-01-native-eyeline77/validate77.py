from pathlib import Path
import sys,json,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;P76=HERE.parent/'whole-eye76'
sys.path.insert(0,str(P76));from validate_final76 import packet,full
from test76 import supported
sys.path.insert(0,str(HERE.parent/'apply-capture66'));from analyse_capture68 import geometry,rgb8
from analyse77 import valid,cov
from source_candidate77 import components
def iris_allocation(c):
 ir=np.float32(np.float32(c[...,2]+c[...,3])+c[...,4]);area=np.float32(0)
 for v in ir.flat:area=np.float32(area+np.float32(v/16))
 k=int(np.floor(np.float32(area+.5)));order=[];mask=np.zeros(ir.shape,bool)
 for y,x in np.argwhere(ir>0):order.append((float(np.float32(max(c[y,x,1],c[y,x,5],c[y,x,6])-ir[y,x])),float(c[y,x,8]),float(c[y,x,9]),int(y),int(x)))
 for r in sorted(order)[:k]:mask[r[-2],r[-1]]=True
 return mask
def main():
 mode=sys.argv[1];run=HERE/mode;OUT=HERE/('result-'+mode);OUT.mkdir(exist_ok=False);st=json.loads(sorted(run.glob('STATE77-*.json'))[-1].read_text());assert st['stage']=='finished'and st['PlayExited']and not st.get('error')and not st.get('restorationError');entries=st['sequencePackets'];expected=4 if mode=='final'else 8 if mode in ['blinksettle','gpucache'] else 6;assert len(entries)==expected;assert [r['frame']for r in entries]==list(range(entries[0]['frame'],entries[0]['frame']+expected));native=np.load(HERE.parent/'whole-eye52/SOURCE_SURFACES52.npz');rows=[];images=[]
 for entry in entries:
  root=Path(entry['output']);d=packet(root);a=d['arrays'];b=d['baseline'];rec=d['records'];c=d['counts'];x,y,w,h=d['roi'];rx,ry,rw,rh=d['eyeROI'];e=d['manifest']['eyeFeature'];parts,labels=components(native['native_xyz_head'],native['native_role6_tri'],e['centres'],e['axesY']);runtime=d['manifest']['nativeSource77']['components'];
  for q in parts:
   found=next(v for v in runtime if v['label']==q['component']+1);assert found['eyeId']==q['eyeId']and found['upper']==(q['part']=='upper');assert np.max(abs(np.array(found['meanRest'])-q['meanRest']))<2e-6
  gi,meshes=geometry(root/'evaluated-source.geometry');assert gi==d['identity'];assert np.array_equal(meshes[1]['submeshes'][6]['indices'],native['native_role6_tri']);morph=dict(meshes[1]['morphs']);protected=rec[...,14,2]>.5;pred=np.zeros((rh,rw),bool);proto=np.zeros((rh,rw),bool);expectedNative=np.zeros((rh,rw),bool);tag=np.zeros((2,rh,rw),np.float32)
  for yy in range(rh):
   for xx in range(rw):
    v=b[yy+ry-y,xx+rx-x];sm=[a[f'S{i}-meta'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(7)];pt=[a[f'S{i}-point'][yy*4:yy*4+4,xx*4:xx*4+4].reshape(16,4)for i in range(4)];ok,sid,weight=supported(v[0],v[1],v[4],sm,pt,a['old-eye-owner'][yy+ry-y,xx+rx-x]);pred[yy,xx]=ok
    if not ok:continue
    assert np.array_equal(rec[yy,xx,0],v[0]);ei=next(i for i,z in enumerate(e['centres'])if int(z[3])==sid);role=int(round(float(v[1,0])));kind=2 if role==2 else 3 if role==5 else 1 if parts[labels[int(round(float(rec[yy,xx,6,2])))-1]]['part']=='upper'else 4;tag[ei,yy,xx]=kind
  if mode in ['gpucache','final']:
   cache=d['manifest']['gpuSourceCache77'];assert cache['header']==77 and cache['sourceXYZUnchanged'] and not cache['cpuInjectedMetadata'];assert d['manifest']['productCacheBeforeObserver77']==77 and d['manifest']['headMainRestDistinct77'];assert d['manifest']['productShaderSHA77']==json.loads((HERE/'PRODUCT_SOURCE77.json').read_text())['afterSHA'];assert np.array_equal(np.where(tag==4,1,tag),c[...,10]);nativeMask=(tag==1)|(tag==4)
   assert np.array_equal(c[...,11][nativeMask],np.broadcast_to(rec[None,...,3,3]+1,c[...,11].shape)[nativeMask]);assert (c[...,11][~nativeMask]==0).all();c=c.copy();c[...,10]=tag
   for q in parts:
    ids=np.where(labels==q['component'])[0];sparse=(ids[0]+1)*(1 if q['part']=='upper'else -1);assert np.array_equal(np.array(cache['nativeTriangleLabels'])[ids],np.full(len(ids),sparse));cg=next(z for z in cache['components']if z['label']==sparse);assert cg['eyeId']==q['eyeId']and max(abs(np.array(cg['meanRest'])-q['meanRest']))<2e-6
  assert np.array_equal(pred,protected)and np.array_equal(tag,c[...,10]);eyeRows=[];m=a['S3-meta'];p=a['S3-point'];u=a['S3-uv'];primitive=np.rint(u[...,2]).astype(int)-1;component=np.where(primitive>=0,labels[np.maximum(primitive,0)],-1)
  for q in parts:
   if q['part']!='upper':continue
   ei=q['eyeIndex'];sid=q['eyeId'];intr=np.where(valid(m,p,sid)&(component==q['component']),np.clip(m[...,3],0,1),0).astype(np.float32);sk=a['S0-meta'];intr*=np.where(valid(sk,a['S0-point'],sid)&(sk[...,0]<m[...,0]),1-np.clip(sk[...,3],0,1),1);visible=intr.copy()
   for source in [4,5,6]:
    z=a[f'S{source}-meta'];visible*=np.where(cov(z)&(z[...,0]<m[...,0]),0 if source==6 else 1-np.clip(z[...,3],0,1),1)
   cellIntr=intr.reshape(rh,4,rw,4).sum((1,3))
   if mode in ['gpucache','final']:c[ei,...,11]=cellIntr
   assert np.max(abs(cellIntr-c[ei,...,11]))<2e-5;rawArea=np.float32(0)
   for v in c[ei,...,11].flat:rawArea=np.float32(rawArea+np.float32(v/16))
   budget=int(np.floor(np.float32(rawArea+.5)));reserved=int((tag[ei]==1).sum());blocked=protected|iris_allocation(c[ei]);candidates=[]
   centre=np.array(q['meanRest'])
   for yy in range(rh):
    for xx in range(rw):
     if blocked[yy,xx]:continue
     weights=visible[yy*4:yy*4+4,xx*4:xx*4+4];total=float(weights.sum())
     if total<=0:continue
     mean=(p[yy*4:yy*4+4,xx*4:xx*4+4,:3]*weights[...,None]).sum((0,1))/total;delta=mean-centre;dx=np.dot(delta,e['axesX'][ei][:3])/e['axesX'][ei][3];dy=np.dot(delta,e['axesY'][ei][:3])/e['axesY'][ei][3];candidates.append((float(dx*dx+dy*dy),*mean.tolist(),yy,xx,total))
   candidates.sort();selected=candidates[:max(0,budget-reserved)]
   for row in selected:expectedNative[row[-3],row[-2]]=True
   eyeRows.append({'eye':sid,'intrinsicArea':float(rawArea),'visibleArea':float(visible.sum()/16),'budget':budget,'reserved':reserved,'selected':[[int(t[-2]+rx),int(271-(t[-3]+ry))]for t in selected],'scoreMargin':float(candidates[1][0]-candidates[0][0])if len(candidates)>1 else None})
  actualNative=rec[...,14,3]==77;assert np.array_equal(expectedNative,actualNative),'Source-ranked GPU assignment differs from offline'
  old=d['original'][ry-y:ry-y+rh,rx-x:rx-x+rw];changed=np.max(abs(old[...,0,:]-rec[...,0,:]),axis=2)>1e-6;allowed=actualNative|np.isin(np.rint(old[...,3,0]),[5,7]);assert not(changed&~allowed&~protected).any();assert np.array_equal(old[...,0,:][protected],rec[...,0,:][protected]);
  rows.append({'identity':d['identity'],'sourceFrame':d['manifest']['sourceFrame'],'closeMorphWeight':morph.get('Fcl_EYE_Close'),'protectedCells':int(protected.sum()),'irisCells':int(np.isin(np.rint(rec[...,3,0]),[2,3,4]).sum()),'sourceNativeNewCells':int(actualNative.sum()),'eyes':eyeRows,'sameInputNonNativeRGBChanges':int((changed&~allowed&~protected).sum()),'requestedBlinkWeight':d['manifest'].get('requestedBlinkWeight77')});images.append((d,old))
 # This is the actual same-frame compute comparison, not two Play runs.
 d,old=images[0];base=d['baseline'][...,0,:];left=base.copy();right=base.copy();left[ry-y:ry-y+rh,rx-x:rx-x+rw]=old[...,0,:];right[ry-y:ry-y+rh,rx-x:rx-x+rw]=d['records'][...,0,:];sheet=Image.new('RGB',(w*18*3,h*18+24),'#161b20');draw=ImageDraw.Draw(sheet)
 for i,(title,v)in enumerate([('PRE348',base),('76 GPU',left),('77 GPU',right)]):
  im=Image.fromarray(np.flipud(rgb8(v[...,:3])));im.save(OUT/(title.replace(' ','_')+'.png'));sheet.paste(im.resize((w*18,h*18),Image.Resampling.NEAREST),(i*w*18,24));draw.text((i*w*18+4,5),title,fill='white')
 sheet.save(OUT/'comparison-nearest18.png');strip=Image.new('RGB',(w*10*len(images),h*10+26),'#161b20');draw=ImageDraw.Draw(strip)
 for i,(d,old)in enumerate(images):
  im=Image.fromarray(np.flipud(rgb8(d['arrays']['head-final'][...,:3])));strip.paste(im.resize((w*10,h*10),Image.Resampling.NEAREST),(i*w*10,26));draw.text((i*w*10+4,5),str(rows[i]['identity']['frameIndex'])+' close '+str(rows[i]['closeMorphWeight']),fill='white')
 strip.save(OUT/'sequence-nearest10.png');Image.fromarray(np.flipud(rgb8(full(images[0][0]['arrays'],images[0][0]['headers'])[...,:3]))).save(OUT/'full.png')
 post=json.loads((run/'POST77.json').read_text());before=json.loads((run/'CURRENT77.json').read_text());keys=['dirty','scenes','domain','playing','paused','optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','runInBackground','playerRunInBackground'];equal={k:before[k]==post[k]for k in keys};assert all(equal.values());assert st['ownedRestDisposed77']and st['borrowedRestReferenceRestored77'];result={'mode':mode,'rows':rows,'restore':equal,'nativeUnverified':[q for q in st['nativeComparisons72']if q.get('equal')is not True],'RTbefore':st['beforeMemory']['renderTextureCount'],'RTafter':st['afterMemory']['renderTextureCount'],'ownedRestDisposed':st['ownedRestDisposed77'],'borrowedRestReferenceRestored':st['borrowedRestReferenceRestored77'],'afterPoseHookRestored':st.get('afterPoseHookRestored77'),'blinkWeightRestored':st.get('blinkWeightRestored77'),'internalAllocatedDeltaMiB':(st['afterMemory']['allocated']-st['beforeMemory']['allocated'])/1048576,'captureOnlyAllocatedDeltaMiB':(st['afterCaptureReleaseMemory']['allocated']-st['readyMemory']['allocated'])/1048576,'limits':[('77 compute and helpers are applied to the current product working tree; product cache was verified before observer' if mode in ['gpucache','final']else '77 is an isolated runtime candidate; default product remains76'),'Existing adapter source submesh6 and stable native upper components required','Native visible-point support still uses current4x samples, not exact continuous occlusion','Intrinsic area can still cross half-cell thresholds; no universal motion stability claimed']};(OUT/'RESULT77.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
