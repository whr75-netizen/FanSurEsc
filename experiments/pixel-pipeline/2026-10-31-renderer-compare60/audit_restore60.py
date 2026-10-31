from pathlib import Path
import collections,hashlib,json,re,subprocess
import numpy as np
R=Path(__file__).resolve().parent;P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
d=json.loads((R/'RESULT60.json').read_text());post=json.loads((R/'POSTFLIGHT60.json').read_text());base=json.loads((R/'DISK_BASELINE60.json').read_text());p0=json.loads((R/'PREFLIGHT60.json').read_text())
def named(items):return{x['path']:x for x in items}
a=named(d['before']['dirty']);b=named(post['state']['dirty']);old24=named(p0['state']['dirty'])
oldf=named(d['before']['files']);newf=named(post['state']['files'])
mesh=json.loads((R/'FACE_NATIVE_AFTER60.json').read_text())['Mesh'];path='Assets/EUnityValidation01/EyeContoursLayers202/Meshes/FaceSourceOwner202.asset';y=(P/path).read_text()
def value(name):
 m=re.search(r'(?m)^\s*'+re.escape(name)+r':[ \t]*([^\n]*)',y);assert m,name;return m[1].strip()
vertex=bytes.fromhex(value('_typelessdata'));nativeVertex=bytes.fromhex(mesh['m_VertexData']['_typelessdata']);index=bytes.fromhex(value('m_IndexBuffer'));nativeIndex=bytes(mesh['m_IndexBuffer'])
meshChecks={'vertexAttributeBytes':len(vertex),'vertexAttributeBytesExactAgainstDisk':vertex==nativeVertex,'indexBytes':len(index),'indexBytesExactAgainstDisk':index==nativeIndex,
 'vertexCountExact':int(value('m_VertexCount'))==mesh['m_VertexData']['m_VertexCount'],'indexFormatExact':int(value('m_IndexFormat'))==mesh['m_IndexFormat'],
 'isReadableExact':bool(int(value('m_IsReadable')))==mesh['m_IsReadable'],'keepVerticesExact':bool(int(value('m_KeepVertices')))==mesh['m_KeepVertices'],'keepIndicesExact':bool(int(value('m_KeepIndices')))==mesh['m_KeepIndices'],
 'limits':'Checked against saved disk after Play, not a full pre-Play native Mesh snapshot. Blendshape/bindpose and every native cache field are not proven identical by these checks. No Save/reimport/ClearDirty performed.'}
def logs(file):return json.loads((R/file).read_text())['data'].get('logs',[])
before=logs('compare3_CONSOLE_BEFORE.json');after=logs('postflight_CONSOLE_AFTER.json');seen=collections.Counter((v.get('message'),v.get('stackTrace'),v.get('type'))for v in before);new=[]
for v in after:
 k=(v.get('message'),v.get('stackTrace'),v.get('type'))
 if seen[k]>0:seen[k]-=1
 else:new.append(v)
cells=json.loads((R/'CELL_AUDIT60.json').read_text())['cells'];outside=[c for c in cells if not c['familyPaletteMember']]
def decode(v):
 v=np.asarray(v,dtype=float)/255;return np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
errors=[float(np.max(np.abs(np.array(c['candidateRGBLinear'][:3])-decode(c['expectedRGB8'])*.55)))for c in outside]
outline={'code':'Assets/EUnityValidation01/GameMapIntegration333/Shaders/OwnerLines333.compute:35','actualConfiguredPrefab':'Assets/EUnityValidation01/OriginalIntegration399/Export/ValidatedPresentation399.prefab:3105','configuredLineTone':.55,'outsideCells':len(outside),'allOutsideMatchLinearTimesLineTone':all(e<1e-6 for e in errors),'maximumLinearError':max(errors),'examples':[{'cell':[c['x'],c['yBottom']],'paletteRGB8':c['expectedRGB8'],'finalRGB8':c['finalRGB8'],'factor':.55}for c in outside[:3]]}
protectedChanges=[p for p,h in base['protected'].items()if hashlib.sha256((P/p).read_bytes()).hexdigest()!=h]
settings=['ProjectSettings/EditorSettings.asset','ProjectSettings/GraphicsSettings.asset'];diskDiff=subprocess.run(['git','-C',str(P),'diff','--numstat','--',*settings],capture_output=True,encoding='utf8');assert diskDiff.returncode==0
fields=['optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath']
r={'PlayEntries':d['playEntries'],'domainBefore':d['before']['domain'],'domainAfter':post['state']['domain'],'Edit':not post['state']['playing'],'liveRendererCount':post['liveNativeCount'],
 'original24NativeHashesAndIdentityExact':all(b.get(p)==o for p,o in old24.items()),'latest25NativeHashesAndIdentityExact':all(b.get(p)==o for p,o in a.items()),'missingOriginalDirty':list(a.keys()-b.keys()),'addedDirtyAfterPlay':list(b.keys()-a.keys()),'additionalDirtyBeforePlay':list(a.keys()-old24.keys()),'originalDiskFileSubsetExact':all(newf.get(p)==o for p,o in oldf.items()),'protectedDiskChanges':protectedChanges,'EditorGraphicsSettingsTrackedDiff':diskDiff.stdout,
 'selectedSettingsAPIValuesEqualBefore':{k:p0[k]==post[k]for k in fields},'sceneStateExact':d['before']['scenes']==post['state']['scenes'],'buildScenesExact':d['buildScenesExact'],'RTCountBefore':d['before']['rtIds'].Count if False else len(d['before']['rtIds']),'RTCountAfter':len(post['state']['rtIds']),
 'meshAudit':meshChecks,'outlineAudit':outline,'newConsoleWindowEntries':new,'newConsoleTypes':dict(collections.Counter(v.get('type')for v in new)),'consoleBeforeWindowEntries':len(before),'consoleAfterWindowEntries':len(after),'shaderUtilWarnings':d['shaderMessages'],
 'internalMemoryDeltaBytesAtObserverFinish':{k:d['memoryAfter'][k]-d['memoryBefore'][k]for k in ['GetTotalAllocatedMemoryLong','GetTotalReservedMemoryLong','GetMonoUsedSizeLong']},'memoryCounterLimit':'Unity internal counters, not physical working set or a leak determination; all experiment-owned buffers/materials/computes released and RT count returned, but retained allocation increase is not explained',
 'ShaderGlobalsRestore':'63 statically discovered scalar/vector/matrix/texture setters executed without error; original values were not exported and no getter roundtrip was recorded. Static global buffer bindings not backed up. Do not claim complete global-state equivalence.',
 'approvalsReviewDenial':'Original connection-descriptor printing rejected before process creation. Replaced with an expressly safer sanitized PID/project-only read; no raw descriptor or credentials exposed.',
 'NoSaveAssets':True,'NoDirtyFlagClearing':True,'NoSecondPlay':True}
(R/'RESTORE_AUDIT60.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:r[k]for k in ['Edit','liveRendererCount','original24NativeHashesAndIdentityExact','latest25NativeHashesAndIdentityExact','addedDirtyAfterPlay','originalDiskFileSubsetExact','protectedDiskChanges','selectedSettingsAPIValuesEqualBefore','sceneStateExact','RTCountBefore','RTCountAfter','meshAudit','outlineAudit','newConsoleTypes','internalMemoryDeltaBytesAtObserverFinish']},ensure_ascii=False,indent=2))
