from pathlib import Path
import json
H=Path(__file__).resolve().parent

def main():
 runs=[]
 for name in['face103/rows64B','face103/rows64C','face103/long1800','face105/edge64']:
  root=H/name;r=json.loads((root/'capture/COMPLETE.json').read_text());before=json.loads((root/'preflight/final/STATE.json').read_text());after=json.loads((root/'post/final/STATE.json').read_text());assert before['dirty']==after['dirty']and before['inputId']==after['inputId']and after['Edit']and after['inputJSONExact'];b,a=r['beforeMemory'],r['afterMemory'];runs.append({'run':name,'actualFrames':len(r['stream77']['frames']),'simulatedSeconds':sum(f['deltaTime']for f in r['stream77']['frames']),'before':b,'after':a,'allocatedDeltaMiB':(a['allocated']-b['allocated'])/1048576,'inputSameObjectAndValues':r['inputSameReferenceAndJSON'],'dirtyList31ExactlyPreserved':True,'nativeExact':sum(x['equal']is True for x in r['nativeChecks']),'nativeUnavailable':[x['type']for x in r['nativeChecks']if x['equal']is None],'globals74Errors':r['globalErrors'],'normalEditRestored':r['restorationChecksPass']and after['Edit'],'ownedRTMaterialObservers':[after['diagnosticRTs'],after['diagnosticMaterials'],after['commandUpdateObservers']],'RTCount':after['allRTCount'],'alphaBytesAfterRelease':r['stream77']['sourceAlpha97ManagedBytesAfterRelease'],'widthEntriesAfterRelease':r['stream77']['sourceWidth99EntriesAfterRelease']})
 out={'runs':runs,'newActualGPUFrames':sum(x['actualFrames']for x in runs),'102ColourCandidateRejected':json.loads((H/'face102/ACTUAL_INPUT_COUNTERFACTUAL102.json').read_text()),'103Long':json.loads((H/'face103/long1800/ACTUAL_ROWS103.json').read_text()),'104WorldSamples':json.loads((H/'face103/long1800/WORLD_SAMPLE104.json').read_text()),'105LineComparison':json.loads((H/'face105/edge64/PAIRED_LINE105.json').read_text()),'memoryConclusion':'Unity Profiler allocation counters, not physical working set. RT/material/observer ownership and task joins verified; between-run allocation falls do not prove absence of retention. Host rows/report are managed metadata until unreachable; no live private-reference inspection or forced GC performed.','product77DefaultChanged':False,'allArtOrLongTermStabilityCompleted':False,'newUnityShaderImports':0,'newGPUKernels':0,'oldDeniedBulkArchiveRetried':False}
 (H/'face105/SUMMARY105.json').write_text(json.dumps(out,indent=2));print(json.dumps({'actualFrames':out['newActualGPUFrames'],'runs':[{'name':x['run'],'allocatedDeltaMiB':x['allocatedDeltaMiB']}for x in runs],'allPreserved':all(x['normalEditRestored']for x in runs)},indent=2))
 target=H/'face103/long1800/ACTUAL_FACE_LINE_30S_103.png'
 if not target.exists():
  with target.open('xb')as f:f.write((H/'face103/long1800/ACTUAL_LONG99.png').read_bytes())
 assert target.read_bytes()==(H/'face103/long1800/ACTUAL_LONG99.png').read_bytes()

if __name__=='__main__':main()
