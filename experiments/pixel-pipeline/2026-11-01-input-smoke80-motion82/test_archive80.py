from pathlib import Path
import json,hashlib,re
HERE=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
for row in load(HERE/'MANIFEST.json'):
 p=HERE/row['path'];assert p.stat().st_size==row['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
v=load(HERE/'VALIDATION80_82.json');assert v['status']=='INPUT_SMOKE_PASSED_VISUAL_MOTION_BLOCKED'
assert v['actualSmokeFrames']==12 and v['scriptCycles']==2 and v['exactNativeContents']==45 and v['dirtyAssets']==29
assert all(v['restoration'].values())and v['visualResults']['validImages']==0
for suffix,folder in [('80','smoke'),('81','motion'),('82','motion')]:
 a=load(HERE/folder/('CURRENT'+suffix+'.json'));b=load(HERE/folder/('POST'+suffix+'.json'));verify=load(HERE/folder/('VERIFY'+suffix+'.json'))
 for key in ['dirty','scenes','domain','playing','paused','options','optionsEnabled','input','runInBackground','playerRunInBackground','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath']:assert a[key]==b[key],(suffix,key)
 assert len(verify['nativeComparisons'])==45 and all(x['equal']is True for x in verify['nativeComparisons'])
 assert verify['settingsId']==v['settingsId']and verify['settingsAlive']
 assert hashlib.sha256(verify['settingsJSON'].encode()).hexdigest()==v['settingsSHA']
for p in [HERE/'Smoke80.cs',HERE/'motion/FAILED_TESTED_MotionScope81.cs',HERE/'motion/FAILED_TESTED_MotionScope82.cs']:
 s=p.read_text();assert not re.search(r'InputSystem\.settings\s*=(?!=)',s)
 assert 'InputSystem.Update('not in s and 'DestroyImmediate('not in s and 'Instantiate('not in s
for suffix in ['81','82']:
 st=load(HERE/'motion'/('STATE'+suffix+'.json'));assert st['PlayEntries']==1 and st['PlayExited']and st.get('error')and not st.get('restorationError');assert not st.get('sequencePackets');assert st['motionRestoration'+suffix]['allRestored']
print('Archive hashes, actual smoke, all restoration cohorts and failed/no-image distinctions PASS')
