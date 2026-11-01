from pathlib import Path
import hashlib,json,zipfile,numpy as np
HERE=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
for row in load(HERE/'MANIFEST.json'):
 p=HERE/row['path'];assert p.stat().st_size==row['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
failed=(HERE/'FAILED_MotionScope83.cs').read_text();fixed=(HERE/'FIXED_MotionScope83.cs').read_text();assert fixed==failed.replace('#if UNITY_EDITOR\n','').replace('#endif\n','')
assert load(HERE/'SOURCE_SYMBOL83.json')['UNITY_EDITOR']is False
a=load(HERE/'state/STATE83.json');b=load(HERE/'state/STATE84.json');assert a.get('error')and not a.get('restorationError')and b['inputProbePassed83']and not b.get('error')
assert a['inputProbe83'][0]['requested']==b['inputProbe83'][0]['requested']==[0,1];assert a['inputProbe83'][0]['actual']==[0,0]
badEvents=[x for x in a['events83']if x['stage']=='owned-event-received'];goodEvents=[x for x in b['events83']if x['stage']=='owned-event-received'];assert len(badEvents)==1 and badEvents[0]['updateType']=='Editor';assert len(goodEvents)==9 and all(x['updateType']=='Dynamic'and not x['handledOnEntry']for x in goodEvents)
assert len(b['inputProbe83'])==12 and all(x['actual']==x['requested']for x in b['inputProbe83'])
for revision in ['83','84','85']:
 before=load(HERE/'state'/('CURRENT'+revision+'.json'));after=load(HERE/'state'/('POST'+revision+'.json'));verify=load(HERE/'state'/('VERIFY'+revision+'.json'))
 for key in ['dirty','scenes','domain','playing','paused','optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','runInBackground','playerRunInBackground','input']:assert before[key]==after[key],(revision,key)
 assert not after['playing']and len(after['dirty'])==29
 assert len(verify['nativeComparisons'])==45 and all(x['equal']is True for x in verify['nativeComparisons']);assert verify['settingsAlive']and verify['settingsId']=='568105589213679894'
 assert hashlib.sha256(verify['settingsJSON'].encode()).hexdigest()=='ca3f68bea248d3f95f9daef0889228a710740dd1efc8867ffda63b97b07f4286'
index=load(HERE/'fixtures/INDEX.json');assert len(index)==24;protected=0;phaseLabels=[]
with zipfile.ZipFile(HERE/'fixtures/actual-geometry-camera-manifests.zip')as z:
 for row in index:
  with np.load(HERE/'fixtures'/row['fixture'],allow_pickle=False)as d:
   assert hashlib.sha256(d['counts'].tobytes()).hexdigest()==row['countsSHA'];assert hashlib.sha256(d['records'].tobytes()).hexdigest()==row['recordsSHA'];r=d['records'];mask=r[...,14,2]>.5;x,y,w,h=row['roi'];rx,ry,rw,rh=row['eyeROI'];base=d['baseline'][ry-y:ry-y+rh,rx-x:rx-x+rw];assert np.array_equal(r[...,0,:][mask],base[...,0,:][mask]);protected+=int(mask.sum())
   if row['stage']=='phase':phaseLabels.append(r[...,3,:2].copy())
  raw=z.read(str(row['frame'])+'/RAW_MANIFEST.json');marker=z.read(str(row['frame'])+'/RAW_COMPLETE76.marker').decode('utf-8');assert hashlib.sha256(raw).hexdigest()==marker==row['rawManifestSHA'];m=json.loads(raw);assert m['frameIndex']==row['frame']and m['mainSerial']==row['serial']and m['frameUnchangedDuringReadback']
assert protected==233 and len(phaseLabels)==6 and all(np.array_equal(x,phaseLabels[0])for x in phaseLabels)
t=load(HERE/'TEMPORAL85.json');assert all(e['sameFrame76To77IrisShapeEqual']for r in t['rows']for e in r['eyes']);assert all(e['upperOutputCells']==1 for r in t['rows'][:14]for e in r['eyes']);assert max(x['eyeRecordRGB8MaxAbsDelta']for x in t['phaseChecks'])==5
assert max(t['phaseDeliveredDeltaPeakToPeakCells'])<.001 # evidence that the display phase sweep is inadequate
source=load(HERE/'SOURCE_TRACE85.json');assert source['newNativeSourcePixelsChecked']==19 and all(x['maxLinearError']<1e-6 for x in source['pigments']);assert all(x['before']['finalEqualsPre348']and x['after']['finalEqualsPre348']for x in source['phaseColourExamples'])
print('PASS: routing causal A/B; same settings/assets;24 actual fixture identities/protected233; residual iris/colour/phase limits retained')
