"""Offline identity, legacy-frame and output-contract regressions. No Unity API."""
from pathlib import Path
from collections import Counter
import hashlib,json,math
import numpy as np
from PIL import Image,ImageDraw
from region62 import build_regions,structure_components,lab,palette,texel,frame_metrics,shade_index

R=Path(__file__).resolve().parent
cache=json.loads((R/'CACHE62.json').read_text())
band=cache['bandMeasuredFromOldNativePalette']
models={}
for m in cache['materials']:
 a=np.load(R/f"source-{m['materialId']}-regions62.npz")
 models[m['materialId']]={'labels':a['labels'],'anchors':a['anchors'],'rows':m['regions']}

def lookup(mid,uv,q,n=4,interval=1):
 m=models[mid];h,w=m['labels'].shape;x,y=texel(uv,w,h,True);i=int(m['labels'][y,x])
 if not i:return None,None
 return palette(m['anchors'][i],n,band,interval)[q],(mid,i)

# One material contains two separated equal-colour motifs and a one-texel accent.
# Connectivity and geometry identities must survive even if palette references agree.
fixture=np.zeros((9,15,4),np.uint8);fixture[:]=[50,28,29,255]
fixture[2:4,2:4,:3]=[94,55,48];fixture[2:4,10:12,:3]=[94,55,48]
fixture[6,7,:3]=[201,143,111]
snapshot=hashlib.sha256(fixture.tobytes()).hexdigest()
f=build_regions(fixture,np.ones((9,15),bool),band)
a,b,c=[int(f['labels'][y,x])for x,y in [(2,2),(10,2),(7,6)]]
motifIds=[a,b]
assert a!=b and c not in [a,b]
assert np.array_equal(f['anchors'][a],f['anchors'][b])
assert int((f['labels']==c).sum())==1
assert hashlib.sha256(fixture.tobytes()).hexdigest()==snapshot
positions=np.array([[0,0,0],[1,0,0],[0,1,0],[3,0,0],[4,0,0],[3,1,0]],np.float32)
structures=structure_components(np.array([[0,1,2],[3,4,5]]),positions)
assert structures[0]!=structures[1]
assert (a,int(structures[0]))!=(a,int(structures[1]))
im=Image.fromarray(fixture);im.resize((450,270),Image.Resampling.NEAREST).save(R/'IDENTITY_FIXTURE62.png')
fixedLabels=f['labels'].copy();g=np.array([.1,.35,.5,.7,.9]);q1=[shade_index(v,[.3,.6])for v in g];q2=[shade_index(v,[.4,.8])for v in g]
pf=palette(f['anchors'][a],3,band);ps=palette(f['anchors'][a],3,band,.5)
assert q1!=q2 and not np.array_equal(pf,ps)
assert np.array_equal(fixedLabels,f['labels'])
assert np.array_equal(pf,palette(f['anchors'][a],3,band))
assert all(np.array_equal(pf[q],palette(f['anchors'][a],3,band)[q])for q in q2)
independenceFixture={'g':g.tolist(),'thresholds1':[.3,.6],'thresholds2':[.4,.8],'Q1':q1,'Q2':q2,'paletteRGB8':pf.tolist(),'intervalHalfRGB8':ps.tolist(),'labelsChanged':0,'thresholdChangePaletteChanged':False,'intervalChangeQChanged':False}

current=json.loads((R/'CELLS62.json').read_text());intervalChecks=0;directChecks=0
for i,r in enumerate(current['rows']):
 p,key=lookup(r['materialId'],[(r['nativeTexel'][0]+.5)/models[r['materialId']]['labels'].shape[1],1-(r['nativeTexel'][1]+.5)/models[r['materialId']]['labels'].shape[0]],r['Q'],2)
 assert np.array_equal(p,current['beforeLineRGB8'][i]);directChecks+=1
 m=models[r['materialId']];anchor=np.array(r['anchorRGB8']);p1=palette(anchor,2,band,1);p2=palette(anchor,2,band,.5)
 assert np.array_equal(p1[-1],p2[-1])
 # Q is a lookup input only. Changing it cannot mutate the immutable source labels.
 before=hashlib.sha256(m['labels'].tobytes()).hexdigest()
 for q in range(2):palette(anchor,2,band,.5)[q]
 assert hashlib.sha256(m['labels'].tobytes()).hexdigest()==before;intervalChecks+=1

# Reuse the *actual* old frame/source and actual frozen Q, never frame60 coordinates.
bindings=json.loads((R/'LEGACY_INPUT62.json').read_text())
assert bindings['modelSHA256']==cache['modelSHA256']
rows=bindings['rows']
known=set(bindings['knownIndices'])
assert len(rows)==368 and len(known)==358
coords=[{'x':r['index']%32,'y':r['index']//32}for r in rows]
oldImage=np.array(Image.open(R/'LEGACY_PROTECTED_INPUT62.png').convert('RGBA'))
v3Image=np.array(Image.open(R/'LEGACY_V3_INPUT62.png').convert('RGBA'))
old=np.array([oldImage[2*c['y'],2*c['x'],:3]for c in coords],np.uint8)
v3=np.array([v3Image[2*c['y'],2*c['x'],:3]for c in coords],np.uint8)
for i,r in enumerate(rows):
 if r['index']in known:
  assert r['rgb']==old[i].tolist() and r['v3RGB8']==v3[i].tolist()
out=[];meta=[]
for i,r in enumerate(rows):
 p,key=lookup(r['sample']['materialId'],r['sample']['uv'],r['shadeK']) if r['index']in known else (None,None)
 # Ten missing source records are frozen legacy output, not fabricated source.
 out.append(old[i].tolist()if p is None else p.tolist())
 meta.append({'index':r['index'],'sourceRegion':key,'Q':r.get('shadeK'),'sourceKnown':p is not None,'outputRGB8':out[-1]})
out=np.array(out,np.uint8)
selected=np.array([r['index']in known for r in rows]);knownCoords=[c for c,k in zip(coords,selected)if k]
# Legacy singleton184/components214 counted the 358 source-known cells only.
# Keep the full368 export and the ten unknown outputs, but compare equal scopes.
oldMetrics=frame_metrics(knownCoords,old[selected]);v3Metrics=frame_metrics(knownCoords,v3[selected]);newMetrics=frame_metrics(knownCoords,out[selected])
assert oldMetrics['singleCells']==184 and oldMetrics['RGB4Components']==214
assert v3Metrics['singleCells']==106
by={r['index']:i for i,r in enumerate(rows)}
def edges(rgb):
 count=added=merged=pairs=0
 for i,r in enumerate(rows):
  if r['index']not in known:continue
  for j in [r['index']+1 if r['index']%32<31 else -1,r['index']+32]:
   if j not in by:continue
   k=by[j];s=rows[k]
   if j not in known:continue
   if r['appearance']!=s['appearance']or r['shadeK']!=s['shadeK']:continue
   pairs+=1;different=not np.array_equal(rgb[i],rgb[k]);previous=r['oldRGB8']!=s['oldRGB8']
   count+=different;added+=different and not previous;merged+=previous and not different
 return {'sameAppearanceSameQPairs':pairs,'visibleBoundaries':int(count),'additionalVsV2':int(added),'mergedV2Boundaries':int(merged)}
v3Edges=edges(v3);assert v3Edges['additionalVsV2']==113
bounded=bindings['bounded']
assert bounded['visibleChangedCells']==0 and bounded['before']==bounded['after']
coherent=bindings['coherent']
prior=bindings['prior']
feature=json.loads((R/'FEATURE_TESTS62.json').read_text())
protected=[v for v in feature if v['id']in [0,2,3,5,6,7,8]]
equalQ=next(v for v in feature if v['id']==4)
assert all(all(q['notCollapsed']and q['sameSourceDirection']for q in v['equalQ'])for v in protected)
assert all(q['notCollapsed']and q['sameSourceDirection']for q in equalQ['equalQ'])

# Exact original changes are a regression witness, not an assertion that every
# disappearing boundary is a real semantic feature. Keep source contrast attached.
oldChangeWitness=[]
for change in coherent.get('changes',[]):
 i=change['index'];r=next(x for x in rows if x['index']==i)
 for j in [i-1,i+1,i-32,i+32]:
  if j not in known or abs(i%32-j%32)+abs(i//32-j//32)!=1:continue
  n=rows[by[j]];beforeGap=float(lab([change['beforeRGB8']])[0,0]-lab([n['rgb']])[0,0]);afterGap=float(lab([change['afterRGB8']])[0,0]-lab([n['rgb']])[0,0])
  if abs(afterGap)<abs(beforeGap)-1e-12:
   oldChangeWitness.append({'cell':[i%32,i//32],'neighbour':[j%32,j//32],'beforeRGB8':change['beforeRGB8'],'afterRGB8':change['afterRGB8'],'neighbourBeforeRGB8':n['rgb'],'beforeAbsDeltaL':abs(beforeGap),'afterAbsDeltaL':abs(afterGap),'sourceDeltaL':abs(r['sourceLab'][0]-n['sourceLab'][0]),'note':'source contrast loss witness, not automatic semantic certification'})
for w in oldChangeWitness:
 i=w['cell'][1]*32+w['cell'][0];j=w['neighbour'][1]*32+w['neighbour'][0]
 w['candidate62RGB8']=[out[by[i]].tolist(),out[by[j]].tolist()]
 w['candidate62AbsDeltaL']=float(abs(lab([out[by[i]]])[0,0]-lab([out[by[j]]])[0,0]))
 w['candidate62NotCollapsed']=not np.array_equal(out[by[i]],out[by[j]])

canvas=Image.new('RGB',(4*288,360),(24,26,31));pen=ImageDraw.Draw(canvas)
for col,(title,colours)in enumerate([('v3: original 113 extra edges',v3),('protected64: 184 singletons',old),('source regions62 / old Q',out)]):
 a=np.zeros((40,32,4),np.uint8)
 for r,c in zip(coords,colours):a[r['y'],r['x']]=[*c,255]
 im=Image.fromarray(a);im.resize((256,320),Image.Resampling.NEAREST).save(R/f'LEGACY62-{col}-8x.png');im.save(R/f'LEGACY62-{col}-1x.png')
 canvas.paste(im.resize((256,320),Image.Resampling.NEAREST),(col*288,30),im.resize((256,320),Image.Resampling.NEAREST));pen.text((col*288,5),title,fill='white')
# Bounded result actually performs zero changes and is deliberately shown equal.
im=Image.open(R/'LEGACY62-1-8x.png');canvas.paste(im,(864,30),im);pen.text((864,5),'region40 bounded: zero change',fill='white')
canvas.save(R/'LEGACY_COMPARE62.png')

report={'sourceId':bindings['sourceId'],'distinctFromFrame60':bindings['sourceId']!=current['sourceId'],'minimumCounterexamples':{'twoDisconnectedMotifsOneMaterial':{'regionIds':motifIds,'sameNativeReference':True},'sameColourDifferentStructures':structures.tolist(),'oneTexelAccentPreserved':True,'sourceMutations':0},'currentDirectPChecks':directChecks,'currentIntervalAndQIndependenceChecks':intervalChecks,'oldFrame':{'totalCells':368,'knownSourceCells':358,'unknownFrozenCells':10,'v3':v3Metrics,'protected64':oldMetrics,'candidate62':newMetrics,'v3Edges':v3Edges,'protected64Edges':edges(old),'candidate62Edges':edges(out),'changedCells':int(np.any(out!=old,axis=1).sum())},'region40Witnesses':{'originalChangedCells':prior['visibleChangedCells'],'coherentChangedCells':coherent['visibleChangedCells'],'contrastBoundedChangedCells':bounded['visibleChangedCells'],'contrastBoundedRejections':len(bounded.get('contrastRejections',[])),'coherentLocalContrastLoss':oldChangeWitness},'featureCertificates':{'protectedSevenNotCollapsedAllFourQ':True,'protectedSevenDirectionAllFourQ':True,'strictLegacyMinimumContrastAllQPassIds':[v['id']for v in protected if all(q['legacyStrictMinContrast']for q in v['equalQ'])],'strictLegacyMinimumContrastAllQFailIds':[v['id']for v in protected if not all(q['legacyStrictMinContrast']for q in v['equalQ'])],'equalQCancellationNotCollapsed':True,'equalQStrictMinimumPassQ':[q['Q']for q in equalQ['equalQ']if q['legacyStrictMinContrast']],'weakPair1NotForced':True},'acceptance':False,'reason':'identity/direct palette contracts pass; strict legacy contrast and pixel-art cleanup are incomplete. Native point vs recorded filtered source and RGB8 rounding are separate limitations.'}
(R/'REGRESSION62.json').write_text(json.dumps(report,indent=2),encoding='utf8')
(R/'INDEPENDENCE_FIXTURE62.json').write_text(json.dumps(independenceFixture,indent=2),encoding='utf8')
(R/'LEGACY_CELLS62.json').write_text(json.dumps({'sourceId':bindings['sourceId'],'cells':meta},indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items()if k!='region40Witnesses'},indent=2))
