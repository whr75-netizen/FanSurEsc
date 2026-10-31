from pathlib import Path
import copy,json
from capture_contract64 import validate,require
R=Path(__file__).resolve().parent
I=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
packet={'sourceId':'synthetic-contract64','viewId':'synthetic-main','frameIndex':7,'renderSerial':12,'poseDigest':'0'*64,'sourceColorSpace':'synthetic linear RGB fixture','gDefinition':{'producerFunction':'fixture scalar','units':'fixture only'},'modeFlags':{'fixture':True},'meshFiles':[{'path':'fixture.mesh','sha256':'0'*64}],'camera':{k:I for k in ['view','projection','effectiveProjection','gpuProjection','gpuEffectiveProjection']},'grid':{'logicalSize':[480,272],'nativeSize':[960,544],'viewport':[0,0,960,544],'clipShift':[0,0,0,0],'nativeShift':[0,0,0,0],'subsampleDefinition':{'producerFunction':'synthetic fixture only'},'yConvention':'top-left'},'samples':[{'sampleId':1,'sourceId':'synthetic-contract64','viewId':'synthetic-main','frameIndex':7,'renderSerial':12,'renderer':0,'submesh':0,'primitive':0,'barycentric':[.2,.3,.5],'uv':[.1,.2],'world':[0,0,0],'screen':[220.1,52.3],'sourceRGBA':[.1,.1,.1,1],'independentG':.3,'Q':1,'owner':[0,0],'depth':2,'coverage':1}],'requiredBackingSampleIds':[1],'cleanBacking':[{'sampleId':1,'sourceId':'synthetic-contract64','viewId':'synthetic-main','frameIndex':7,'renderSerial':12,'RGBA':[.1,.1,.1,1],'owner':[0,0],'depth':2,'coverage':1,'uv':[.1,.2],'colorSpace':'linear-rt-fixture','rgbaStage':'synthetic-pre-eye-not-unlit','producerPass':'fixture pre-eye','preEyeApplication':True}],'globalJournal':{'externalBackupWrittenAndVerified':True,'mutations':[{'name':'fixture-vector','kind':'vector','restorable':True}],'unidentifiedRendererGlobalWrites':False},'largestOwnedReadbackBytes':6144*16,'simultaneousReadbacks':1}
require(packet);tests=[]
for name,edit,needle in [
 ('missing-clean-backing',lambda p:p['cleanBacking'][0].pop('RGBA'),'incomplete clean backing'),
 ('empty-backing',lambda p:p.update(cleanBacking=[]),'missing required backing destinations'),
 ('mixed-source',lambda p:p['samples'][0].update(sourceId='old-source'),'mixed sample source/frame/serial'),
 ('mixed-view',lambda p:p['samples'][0].update(viewId='other-camera'),'mixed sample source/frame/serial'),
 ('mixed-frame',lambda p:p['samples'][0].update(frameIndex=6),'mixed sample source/frame/serial'),
 ('unbacked-buffer',lambda p:p['globalJournal']['mutations'].append({'name':'_BodyScope551','kind':'buffer','restorable':False,'exactOriginalBindingRecoverable':False}),'unbacked buffer mutation:_BodyScope551'),
 ('large-readback',lambda p:p.update(largestOwnedReadbackBytes=8355840),'readback exceeds one-MiB packet-plane bound'),
 ('guessed-backing',lambda p:p['cleanBacking'][0].update(synthesised=True),'backing is not real pre-eye input')]:
 p=copy.deepcopy(packet);edit(p);errors=validate(p);assert needle in errors,(name,errors);tests.append({'name':name,'rejected':True,'errors':errors})
assert packet['samples'][0]['screen']==[220.1,52.3]
capture=(R/'CpuSourceCapture64.cs').read_text();journal=(R/'GlobalJournal64.cs').read_text()
for banned in ['EnterPlaymode','SaveAssets','Camera.Render','BakeMesh(','.SetGlobal','GC.Collect','ToArray(']:
 # Comments intentionally explain why BakeMesh and ToArray are absent; check
 # executable-looking tokens only after removing line comments.
 code='\n'.join(l.split('//')[0]for l in capture.splitlines())
 assert banned not in code,banned
assert 'SetGlobalBuffer('not in journal and 'SetGlobalConstantBuffer('not in journal
assert 'public static GlobalJournal64 Active'in journal
out={'syntheticPacketPass':True,'rejectionTests':tests,'fractionalScreenCoordinatesPreserved':True,'captureHelperNoRendererOrGlobalMutation':True,'globalBufferSetterAbsent':True,'externalJournalAndPublicHandlePrepared':True,'csharpCompiled':False,'csharpExecuted':False,'realPacketCaptured':False,'normalPlayPreflightBlockedByUnbackedBodyScope551':True,'newUnityCalls':0}
(R/'CAPTURE_TEST64.json').write_text(json.dumps(out,indent=2),encoding='utf8');print(json.dumps(out,indent=2))
