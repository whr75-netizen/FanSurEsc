from pathlib import Path
import json,hashlib,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;RUN=HERE/'run'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
s=load(sorted(RUN.glob('STATE80*'))[-1]);before=load(RUN/'CURRENT80.json');after=load(RUN/'POST80.json');verify=load(RUN/'VERIFY80.json')
assert s['inputSmokePassed']and not s.get('error')and not s.get('restorationError')and s['PlayEntries']==1
assert len(s['samples'])==12 and len(s['inputUpdates'])==12
assert all(x['type']=='Dynamic'for x in s['inputUpdates'])
assert all(s['restoration'].values())and all(x['equal']is True for x in verify['nativeComparisons'])
keys=['dirty','scenes','domain','playing','paused','optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','runInBackground','playerRunInBackground','input']
assert all(before[k]==after[k]for k in keys)
repeated=[]
for i in range(6):
 a,b=s['samples'][i],s['samples'][i+6]
 assert a['requested']==a['actualInput']==b['requested']==b['actualInput']
 assert abs(a['actualStepLength']-b['actualStepLength'])<1e-6
 assert abs(a['facingAfterAngle']-b['facingAfterAngle'])<1e-4
 repeated.append({'step':i,'input':a['actualInput'],'displacementLengthDifference':abs(a['actualStepLength']-b['actualStepLength']),'facingAngleDifference':abs(a['facingAfterAngle']-b['facingAfterAngle'])})
failures=[]
for suffix,run in [('81',ROOT/'eye-motion81/run'),('82',ROOT/'eye-motion81/run82')]:
 st=load(sorted(run.glob('STATE'+suffix+'*'))[-1]);ver=load(run/('VERIFY'+suffix+'.json'));a=load(run/('CURRENT'+suffix+'.json'));b=load(run/('POST'+suffix+'.json'))
 assert st['PlayExited']and not st.get('restorationError')and st['motionRestoration'+suffix]['allRestored']
 assert st.get('error')and len(st.get('sequencePackets',[]))==0
 assert all(a[k]==b[k]for k in keys)and all(x['equal']is True for x in ver['nativeComparisons'])
 failures.append({'attempt':suffix,'PlayEntries':st['PlayEntries'],'validPackets':0,'failure':'First actual game input differed from requested Down/S after5 warmup frames','restored':True,'exactNativeContents':45,'settingsId':st['editInputRestoration'+suffix]['nativeId'],'RTbefore':st['beforeMemory']['renderTextureCount'],'RTafter':st['afterMemory']['renderTextureCount'],'dynamicTrace':st.get('dynamicInput'+suffix,[]),'pauseRemoved':suffix=='82'})
result={'status':'INPUT_SMOKE_PASSED_VISUAL_MOTION_BLOCKED','actualSmokeFrames':12,'scriptCycles':2,'movementAndReleasePass':True,'normalDynamicOnly':True,'resolvedKeys':[s['resolvedUpKey'],s['resolvedRightKey']],'repeatedMapping':repeated,'maximumMoveStepErrorMetres':max(abs(x['actualStepLength']-x['expectedStepLength'])for x in s['samples']if x['requested']!=[0,0]),'minimumMovementDirectionDot':min(x['directionDot']for x in s['samples']if x['requested']!=[0,0]),'releasedHorizontalDisplacement':max(x['actualStepLength']for x in s['samples']if x['requested']==[0,0]),'smokeRT':[s['beforeRTCount'],s['afterRTCount']],'settingsId':s['afterSettingsId'],'settingsSHA':hashlib.sha256(s['afterSettingsJSON'].encode()).hexdigest(),'settingsObjectCounts':[s['beforeSettingsObjectCount'],s['afterSettingsObjectCount']],'restoration':s['restoration'],'exactNativeContents':45,'dirtyAssets':len(before['dirty']),'failedVisualRuns':failures,'noPlayPathFailure':'Capture82 failed on first CreateNew due generated directory substitution; no options/Play were changed; corrected source is Capture82Fixed.cs','diagnosticParserCorrection':'Verify80 failed before comparison on Json58->Obj58 cast; explicit rows fixed in VerifyContent80, no state mutation','causalStatus':{'old78ManualUpdate':'Possible cause, not proven by these different input cohorts','pauseHypothesis':'Not sufficient: removing observer pause in82 did not restore S key delivery','confirmed':'Up/Right/release normal smoke works; initial held S in movement observer remainsfalse in6 Dynamic updates even enabled/current; whether event delivery/reset/timestamp caused it was not captured'},'visualResults':{'validImages':0,'movementAesthetics':'NOT_VALIDATED','temporalEyeStability':'NOT_VALIDATED','productChanges':0},'nextMinimumEvidence':'Track only owned queue/event timestamp+type/key payload, onBefore/After Dynamic and owned device reset/removal; distinguish queue receipt and state reset in a small smoke before any eye readback. Do not change settings pointer, bindings or device types.'}
(HERE/'VALIDATION80_82.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({k:result[k]for k in ['status','actualSmokeFrames','maximumMoveStepErrorMetres','minimumMovementDirectionDot','releasedHorizontalDisplacement','settingsId','settingsSHA','dirtyAssets','exactNativeContents']},ensure_ascii=False,indent=2))
