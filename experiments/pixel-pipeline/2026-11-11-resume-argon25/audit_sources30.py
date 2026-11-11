"""Read-only static obligations, never a live URP/job-state probe."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;G=H/'face30';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 urp=next((R/'Library/PackageCache').glob('com.unity.render-pipelines.universal@*'))/'Runtime';f=(urp/'ForwardLights.cs').read_text(encoding='utf-8-sig');u=(urp/'UniversalRenderPipelineRenderGraph.cs').read_text(encoding='utf-8-sig')
 p=f[f.index('internal void PreSetup('):f.index('static ProfilingSampler s_SetupForwardLights')]
 checks={'PreSetupChecksIsCompletedBeforeMemClear':p.index('m_CullingHandle.IsCompleted')<p.index('UnsafeUtility.MemClear(m_ZBins.GetUnsafePtr()'),
 'LightingCompleteIsInExecutionCallback':f.index('data.forwardLights.SetupLights(rgContext.cmd')<f.index('internal void SetupLights(')<f.index('m_CullingHandle.Complete();',f.index('internal void SetupLights(')),
 'ClusteringDependenciesIncludeBothBranches':'minMaxZs.Dispose(zBinningHandle)'in f and'tileRanges.Dispose(tilingHandle)'in f,
 'CleanupAlsoCompletesHandle':'m_CullingHandle.Complete();'in f[f.index('internal void Cleanup()'):],
 'RecordingBeforeGraphExecute':u.index('renderer.RecordRenderGraph(renderGraph, context);')<u.index('renderGraph.EndRecordingAndExecute();'),
 'GraphCatchLogsResetNotForwardLightsCleanup':'ResetGraphAndLogException(e)'in u and'm_CullingHandle.Complete'not in u}
 assert all(checks.values()),checks
 rows=[]
 specs=[(urp/'ForwardLights.cs',['m_CullingHandle.IsCompleted','UnsafeUtility.MemClear(m_ZBins.GetUnsafePtr()','m_CullingHandle.Complete();','data.forwardLights.SetupLights','internal void Cleanup()']),
 (urp/'UniversalRenderPipelineRenderGraph.cs',['renderer.RecordRenderGraph','EndRecordingAndExecute','ResetGraphAndLogException']),
 (R/'Assets/EUnityValidation01/MinimalRestore335/Runtime/Full319View335.cs',['nativeShift=motion.clipShift']),
 (R/'Assets/EUnityValidation01/HeadLocal367/Runtime/FullFeature367.cs',['d.part==0?v.motion.clipShift:v.nativeShift','SetGlobalVector("_ClipShift331",v.nativeShift)'])]
 for path,needles in specs:
  raw=path.read_bytes();lines=raw.decode('utf-8-sig').splitlines();rows.append({'path':str(path.relative_to(R)),'SHA256':hashlib.sha256(raw).hexdigest(),'evidence':[{'line':i+1,'text':line.strip()}for i,line in enumerate(lines)if any(v in line for v in needles)]})
 original=(H/'face29/run/RUN_Capture25.cs.txt').read_text(encoding='utf-8');a=original.index('var pigment=joint.DenseNative.Handles96[3][0]');b=original.index('29 typed source silhouette/pigment/Q inputs');assert a<b
 results={'staticObligations':checks,'staticObligationsPassed':len(checks),'installedSource':rows,'observedRoot':'Saved29 SourceOutline29.Record guard error precedes ZBinningJob safety errors; the classifier pass was not recorded.','mechanism':'Own recording exception skips EndRecordingAndExecute and therefore the recorded SetupLights callback. Next PreSetup passed IsCompleted then failed at MemClear/GetUnsafePtr. Execution completion and NativeContainer ownership recovery are distinct.','inferenceLimit':'Explains the observed failure sequence. Does not observe whether the present private handle remains uncompleted, nor prove GPU reset or the transient memory spike cause.','nativeShiftFinding':'Do not call2p+1 an unconditional quarter-cell bug: nativeShift adds a half-native-pixel compensation on X and a backend-flip term on Y. Actual Q/meta lattice still needs complete producer descriptors/validation.','newSafetyGaps':['Producer command-recorded flags are not GPU completion evidence.','Draw/classify failure can occur after partial command recording; unconditional Dispose has no explicit end-barrier proof.','BeginExit sets exiting before Release76; making Dispose throw on pending work would skip ExitPlaymode unless exit flow is refactored.','Classify depends on hair-ON textures only; an end barrier there must not be assumed to cover an unordered hair-OFF producer.','Q role metadata sample phase/geometry/alpha must be proven against the Q producer, not just matched texture dimensions.'],'officialAPIRule':{'URL':'https://docs.unity3d.com/2021.2/Documentation/Manual/JobSystemTroubleshooting.html','section':'Call JobHandle.Complete to regain ownership','scope':'General API rule, cross-checked against installed17.5 source; not an observed live handle or version-specific issue claim'},'UnityGPUCalls':0}
 G.mkdir(exist_ok=True);(G/'SOURCE_AUDIT30.json').write_text(json.dumps(results,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'staticObligationsPassed':len(checks),'currentPrivateJobStateObserved':False,'UnityGPUCalls':0}))
if __name__=='__main__':main()
