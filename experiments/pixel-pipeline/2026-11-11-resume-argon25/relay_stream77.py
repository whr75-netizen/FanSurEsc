from pathlib import Path
import sys,json,hashlib
import relay33
H=Path(__file__).resolve().parent;kind=sys.argv[1];mode=sys.argv[2];assert kind in['probe2','probe3','long']and mode in['final','capture','post','console'];G=H/'face77'/kind;d=json.loads((G/'CPU_PREPARED77.json').read_text());assert d['CSharp9Compiled']and d['noNewShaderOrKernel']and d['readbackBytes']==(254800 if kind=='long'else 248832)and d['poolSlots']==6 and d['maxDispatchesPerFrame']==1;assert json.loads((H/'face77/CPU_LEASE77.json').read_text())['CPUChecks']==11
relay33.PID=json.loads((H/'face55/reopen/LAUNCHED.json').read_text(encoding='utf-8-sig'))['pid'];relay33.G=G
if mode=='capture':
 s=json.loads((G/'final/STATE.json').read_text());assert s['Edit']and s['inputJSONExact']and s['diagnosticRTs']==s['diagnosticMaterials']==s['commandUpdateObservers']==s['sourceFlatTexturesRemaining67']==0;assert hashlib.sha256((G/'capture/RUN.cs.txt').read_bytes()).hexdigest()==d['captureSHA256'];asset=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\SourceBoundary60\SourceNativeHull60.compute');assert hashlib.sha256(asset.read_bytes()).hexdigest()==d['shaderSHA256']
 if kind=='long':
  p=json.loads((H/'face77/probe3/ACTUAL_STREAM77.json').read_text());assert p['actualFrames']==12 and p['allCurrentRGBAndOwnerAndPaletteChecksPass']and p['poseHistoryCPUChecked']and p['restorationChecksPass']
if mode=='post':relay33.G=G/'post';mode='final'
relay33.TITLE_OVERRIDE={'final':'Read stable Edit/input/resource state only','capture':('Twelve-frame lifecycle probe'if kind.startswith('probe')else'Bounded120-frame normal walk/turn observation')+' using exact validated75 kernel, one1600-thread dispatch/frame, six acknowledged reused slots and<=254800-byte async readback. Current visibility first, source UV owner history only; stop on any error/backpressure. Normal Play exit and full restoration; no shader import/default switch/115','console':'Read Console Error/Exception only'}[mode];sys.argv=[sys.argv[0],mode];relay33.main()
