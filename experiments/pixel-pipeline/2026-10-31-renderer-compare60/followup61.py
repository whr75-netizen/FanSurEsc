"""Read-only/offline interpretation of restoration and the stored frame."""
from pathlib import Path
import hashlib,json,re,struct,subprocess
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
d=json.loads((R/'RESTORE_READ61.json').read_text());done=json.loads((R/'RESULT60.json').read_text());old24=json.loads((R/'PREFLIGHT60.json').read_text());baseline=json.loads((R/'DISK_BASELINE60.json').read_text())
mesh=json.loads((R/'FACE_NATIVE_AFTER60.json').read_text())['Mesh'];poses=json.loads((R/'BINDPOSE_READ61.json').read_text());cells=json.loads((R/'CELL_AUDIT60.json').read_text())['cells'];pal={p['draw']:p for p in done['palettes']}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def lab(rgb):
 v=np.asarray(rgb,dtype=float)/255;v=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4)
 lms=v@np.array([[.4122214708,.2119034982,.0883024619],[.5363325363,.6806995451,.2817188376],[.0514459929,.1073969566,.6299787005]])
 return np.cbrt(lms)@np.array([[.2104542553,1.9779984951,.0259040371],[.793617785,-2.428592205,.7827717662],[-.0040720468,.4505937099,-.808675766]])
def encode(v):
 v=np.maximum(v,0);return np.clip(np.floor(np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055)*255+.5),0,255).astype('uint8')
colours={
 'source-unlit':np.array([c['sourceRGBA8'][:3]for c in cells],dtype='uint8'),
 'source-medoid':np.array([pal[c['draw']]['reference']['rgb8']for c in cells],dtype='uint8'),
 'P-Q-before-line':np.array([c['expectedRGB8']for c in cells],dtype='uint8'),
 'candidate-final':np.array([c['finalRGB8']for c in cells],dtype='uint8'),
 'product-control':encode(np.array([c['controlRGBLinear'][:3]for c in cells]))}
stats={name:{'uniqueRGB8':len(set(map(tuple,v.tolist()))),'OKLabLmin':float(lab(v)[:,0].min()),'OKLabLmedian':float(np.median(lab(v)[:,0])),'OKLabLmax':float(lab(v)[:,0].max())}for name,v in colours.items()}
groups=[]
for draw in sorted(set(c['draw']for c in cells)):
 idx=[i for i,c in enumerate(cells)if c['draw']==draw];s=colours['source-unlit'][idx];ref=pal[draw]['reference']['rgb8'];p=pal[draw]['palette']['rgb8'];q=[cells[i]['paletteIndex']for i in idx]
 groups.append({'draw':draw,'visibleCells':len(idx),'visibleSourceUniqueRGB8':len(set(map(tuple,s.tolist()))),'referenceRGB8':ref,'visibleSourceMedianL':float(np.median(lab(s)[:,0])),'referenceL':float(lab([ref])[0,0]),'paletteRGB8':p,'occupiedQCounts':{str(k):q.count(k)for k in sorted(set(q))},'sourceReferenceSelection':'32 evenly spaced triangle-centroid samples per material, including offscreen source; not area/saliency-weighted or per-painted-pattern references'})
x,y,w,h=done['hairRectBottomLeft'];zoom=8;canvas=Image.new('RGB',(max(5*(w*zoom+12),900),h*zoom+70),(24,26,31));pen=ImageDraw.Draw(canvas)
for col,(name,rgb)in enumerate(colours.items()):
 image=Image.new('RGB',(w,h),(0,0,0));pix=image.load()
 for i,c in enumerate(cells):pix[c['x']-x,h-1-(c['yBottom']-y)]=tuple(rgb[i])
 image=image.resize((w*zoom,h*zoom),Image.Resampling.NEAREST);canvas.paste(image,(col*(w*zoom+12),35));pen.text((col*(w*zoom+12),8),name,fill='white');pen.text((col*(w*zoom+12),45+h*zoom),'RGB8 '+str(stats[name]['uniqueRGB8']),fill='white')
canvas.save(R/'COLOUR_COMPONENTS61.png')
nativePose=np.array([[[p[f'e{i}{j}']for j in range(4)]for i in range(4)]for p in mesh['m_BindPose']],dtype=np.float32);apiPose=np.array(poses['bindposesRowMajor'],dtype=np.float32).reshape(-1,4,4)
yaml=(P/'Assets/EUnityValidation01/EyeContoursLayers202/Meshes/FaceSourceOwner202.asset').read_text();block=yaml.split('  m_BindPose:',1)[1].split('  m_BoneNameHashes:',1)[0];entries=re.findall(r'\be[0-3][0-3]:[ \t]*([^\n]+)',block);diskPose=np.array([float(v)for v in entries],dtype=np.float32).reshape(-1,4,4)
face={'vertexAttributeBytesExactSince60':d['faceMesh']['vertexSHA256']==hashlib.sha256(bytes.fromhex(mesh['m_VertexData']['_typelessdata'])).hexdigest(),'indexBytesExactSince60':d['faceMesh']['indexSHA256']==hashlib.sha256(bytes(mesh['m_IndexBuffer'])).hexdigest(),
 'bindposeFloat32Values':int(apiPose.size),'bindposeNumericMismatchSince60':int(np.count_nonzero(nativePose!=apiPose)),'bindposeNumericMismatchAgainstDisk':int(np.count_nonzero(diskPose!=apiPose)),
 'bindposeRawHashLimit':'Raw API hash differs from JSON re-encoding; all Float32 numbers are equal. JSON loses signed-zero bit distinctions. Do not report a content regression based on that raw hash alone.',
 'blendShapeNamesFrameCountsWeightsExactSince60':all(v['name']==mesh['m_Shapes']['channels'][i]['name']and v['frameCount']==mesh['m_Shapes']['channels'][i]['frameCount']and v['weights']==mesh['m_Shapes']['fullWeights'][mesh['m_Shapes']['channels'][i]['frameIndex']:mesh['m_Shapes']['channels'][i]['frameIndex']+v['frameCount']]for i,v in enumerate(d['faceMesh']['blendShapes'])),
 'meshMutationCause':'Unconfirmed: runtime CurrentSurface330/ScaleBake378 writes owned baked meshes; EyeFeature348 writes Instantiate(original) sampleFace. No direct setter of the persistent source asset was identified in the inspected path. Engine/BakeMesh cache marking is a hypothesis, not proven.',
 'limit':'No full pre-Play native Mesh baseline. Blendshape delta arrays and every native cache field were not re-exported.'}
current={v['path']:v for v in d['dirty']};prior={v['path']:v for v in done['after']['dirty']};oldIDs={v['path']:v['entityId']for v in old24['state']['dirty']}
settings=[]
for p,cause in [('ProjectSettings/EditorSettings.asset','Compare60.Execute sets enterPlayModeOptions; Finish assigns original options'),('ProjectSettings/GraphicsSettings.asset','NativePlayer395.OnEnable/Source329WalkView.Apply/Gameplay397.BeginGameplay assign pipeline; Compare60.Finish restores oldG'),('ProjectSettings/TimeManager.asset','NativePlayer395.Initialise and Gameplay397.BeginGameplay change Time.timeScale; Compare60.Finish restores original timeScale/captureDeltaTime')]:
 settings.append({'path':p,'nativeHashUnchangedSince60Finish':d['smallSettings'][p]['sha256']==prior[p]['sha256'],'APIValuesMatchActualBackup':True,'codeSupportedDirtyTrigger':cause,'dirtyFlagCleared':False})
def git(*args):
 r=subprocess.run(['git','-C',str(P),*args],capture_output=True);assert r.returncode==0,r.stderr;return r.stdout
newShader='Assets/Rendering/PixelArt/DeskLivePixelProbe.shader'
alloldfiles=done['after']['files'];fileChanges=[v['path']for v in alloldfiles if sha(P/v['path'])!=v['sha256']]
protected=[p for p,h in baseline['protected'].items()if sha(P/p)!=h]
apiKeys=['optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath']
memoryDelta={k:d['memoryAfter'][k]-d['memoryBefore'][k]for k in ['GetTotalAllocatedMemoryLong','GetTotalReservedMemoryLong','GetMonoUsedSizeLong']}
report={'utc':d['utc'],'noNewPlayOrRender':True,'settersExecuted':0,'cleanupsExecuted':0,
 'globals':{'currentGettersRead':len(d['currentGlobals']),'originalValuesRecoverableThroughPermittedAPI':False,'comparableOriginalValueCount':0,'getterMismatchCount':None,'bufferBindingsChanged':False,'exactReason':'Compare60 saved original values only in private instance dictionaries; report exported count, not values. Finish unsubscribed its update observer. No public retrieval handle or persistent export was established. SDK retention/GC status is not proven and no reflection/heap access was attempted. No guessed restoration.'},
 'Editor':{'playing':d['playing'],'paused':d['paused'],'domain':d['domain'],'liveRendererCount':d['liveNativeCount'],'APIEqualActualBefore':{k:d[k]==old24[k]for k in apiKeys},'sceneRootsPathCleanEqual60Finish':all(next((v for v in d['scenes']if v['path']==o['path']),None)=={k:v for k,v in o.items()if k in ['path','dirty','roots','active']}for o in done['after']['scenes'])},
 'dirty':{'count':len(d['dirty']),'original24EntityIdsAndDirtyPreserved':all(current.get(p,{}).get('entityId')==v for p,v in oldIDs.items()),'nativeShaderHashesNotReserializedThisFollowup':True,'settings3':settings,'face':face,'newSince60Finish':[v for p,v in current.items()if p not in prior],'newShaderDiskDiff':git('diff','--numstat','--',newShader,newShader+'.meta').decode('utf8'),'newShaderCause':'Unconfirmed; shader already dirty at start of the read-only snapshot, no setter used. Preserve it.'},
 'disk':{'originalFileChangesSince60Finish':fileChanges,'protectedUserModifiedFilesChanged':protected,'EditorGraphicsTrackedDiff':git('diff','--numstat','--','ProjectSettings/EditorSettings.asset','ProjectSettings/GraphicsSettings.asset').decode('utf8')},
 'settingsRepresentationLimit':'Static API enabled=false/options=None matches pre-Play API backup; native/disk serialized m_EnterPlayModeOptionsEnabled=1/options=0 agree with each other. Public bindings are extern; no proven explanation for representation difference and no guessed field rewrite.',
 'resourceLifetime':{'liveCandidateMaterials':len(d['liveCandidateMaterials']),'liveCandidateComputeClones':len(d['liveCandidateComputeClones']),'renderTextureCount':len(d['renderTextures']),'publicProductCaches':d['publicProductCaches'],'readOnlyAuditInternalCounterDeltaBytes':memoryDelta,'privateFixedArrayBytesFromExistingCode':{'ClothRegion524.coloursAndAtlas540':2*480*272*16},'sourceReasoning':'Compare60 has no static large-array fields. GPU buffers/material/compute clones are released and lists cleared. Capture float arrays are synchronous method locals, not exported as array references or captured by callbacks. Actual managed roots/SDK retention cannot be proven with allowed APIs. Existing product fixed caches are not experiment-owned and were not cleared. No evidence proves them the source of +353.31MiB.'},
 'colour':{'stageStatistics':stats,'materialReferenceGroups':groups,'representativeSelectionEffect':'All visible unlit texel variations inside one material collapse to one medoid before Q. Three visible material anchors substitute for many source colours; painted/gradient features are not independently preserved.',
 'brightnessHueEffect':'Old product HairFinal335 multiplies HairBase by channel gain (.0852688534,.1188193462,.249105814) and shade floor. Candidate bypasses that strong darkening/blue bias and uses warm original texture medoids as bright endpoints. This explains a real pipeline difference, not an sRGB-white multiplication bug.',
 'stepIntervalEffect':'Two levels inherited from actual surfaceShadeSteps, threshold .5. darkLRatio .55/darkCRatio .6 are diagnostic parameters; they alter contrast and relative region brightness, not source identity. No alternative parameters were applied.',
 'lineEffect':'52 cells are exactly linear P*.55. This only darkens edge RGB; it cannot explain brighter warm interior or disappearance of texture patterns.',
 'causalLimit':'Stored stages and code separate these transformations, but no new GPU ablation was executed. This is not a new aesthetic success claim.'}}
(R/'FOLLOWUP61.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'editor':report['Editor'],'dirtyCount':len(d['dirty']),'newDirtySince60Finish':report['dirty']['newSince60Finish'],'settings':settings,'mesh':face,'disk':report['disk'],'resourceCounts':{k:report['resourceLifetime'][k]for k in ['liveCandidateMaterials','liveCandidateComputeClones','renderTextureCount']},'colour':stats},ensure_ascii=False,indent=2))
