"""Generate review shaders and C# metadata compile. No Unity/GPU/import calls."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'face31';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True);build=G/'build';build.mkdir(exist_ok=True)
 source=R/'Assets/EUnityValidation01/MinimalRestore335/Shaders/LegacySignals335.shader';s=source.read_text(encoding='utf-8-sig')
 def replace(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 replace(s.splitlines()[0],'Shader "EValidation/QMeta31"')
 replace('float4 _ClipShift333,_Profile333;','float4 _ClipShift333,_Profile333,_QMetaRasterOrigin31;float4x4 _QMetaVP31;')
 replace('o.pos.xy+=_ClipShift333.xy*o.pos.w;','o.pos=mul(_QMetaVP31,float4(o.positionWS,1));')
 replace('float4 classifier:SV_Target3;','float4 classifier:SV_Target3;float4 sourceMeta31:SV_Target4;')
 replace('O335 Eye333Fragment(const Varyings v,bool facing:SV_IsFrontFace){','O335 Eye333Fragment(const Varyings raster31,bool facing:SV_IsFrontFace){Varyings v=raster31;v.pos.xy+=_QMetaRasterOrigin31.xy;')
 replace('O335 o;','O335 o;o.sourceMeta31=float4(-TransformWorldToView(v.positionWS).z,_Auto245Role+1,0,alpha);')
 s='\n'.join(line.rstrip()for line in s.splitlines())+'\n'
 (G/'QMeta31.shader').write_text('// REVIEW ONLY: paired initial Q and metadata, no Assets import.\n'+s,encoding='utf-8',newline='\n')
 # Preserve the verified physical29 pigment/outline ABI verbatim except the shader label.
 original=(H/'face29/physical-fix/SourceOutline29.shader').read_text(encoding='utf-8');assert original.count('Shader "EValidation/SourceBoundary29"')==1
 (G/'SourceOutline31.shader').write_text(original.replace('Shader "EValidation/SourceBoundary29"','Shader "EValidation/SourceBoundary31"'),encoding='utf-8',newline='\n')
 # Reuse only the unchanged bounded JSON helper, not the old runnable host or
 # any Forward113/115 producer assembly. The candidate is independently linkable.
 frozen=(H/'face29/physical-fix/RUN_Capture25.cs.txt').read_text(encoding='utf-8')
 start=frozen.index('public class Json58 :');end=frozen.index('// Offline66 candidate: no Unity/API/thread/process/GC actions.',start)
 header='using System;using System.Collections;using System.Collections.Generic;using System.Globalization;using System.Linq;using System.Text;\nnamespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\n'
 jsonSource=G/'Json58Reference31.cs';jsonSource.write_text(header+frozen[start:end]+'\n}\n',encoding='utf-8',newline='\n')
 crop=(H/'Projection31.cs').read_text();method=frozen[frozen.index(' public static Matrix4x4 Crop('):frozen.index('\n}\n',frozen.index(' public static Matrix4x4 Crop('))]
 assert method in crop,'Crop arithmetic must remain the tested26 implementation'
 own=[H/'SourceOutline31.cs',H/'SourceCaptureHost31.cs',H/'ProducerLifetime31.cs',H/'ProducerContracts30.cs',H/'Projection31.cs',jsonSource]
 compile_source(own,build/'SourceCandidate31.dll')
 a=(H/'SourceOutline31.cs').read_text();host=(H/'SourceCaptureHost31.cs').read_text();compute=(G/'LineClass31.compute').read_text()
 checks={
  'allOwnOutputsDependencyBeforeEndReadback':'Fields.Concat(QFields).Concat(new[]{Classification,depth,qDepth})'in a,
  'boundedSinglePixelCommandReadback':'cmd.RequestAsyncReadback(Classification.rt,0,0,1,0,1,0,1,'in a,
  'potentialCommandsMarkedBeforePasses':a.index('submission.BeforeCommands()')<a.index('graph.AddUnsafePass'),
  'partialFailureDoesNotSkipEndBarrier':'Deliberately runs even when a producer failed'in a,
  'releaseGuardBeforeRTRelease':a.index('if(!CanRelease||releaseAttempted)return false')<a.index('foreach(var t in owned)t?.Release()'),
  'singleFrameNoResourceReuse':'stopped||Disposed||recorded'in a,
  'sameFragmentFiveMRTPair':'sourceMeta31:SV_Target4'in s and s.count('o.sourceMeta31=')==1 and s.count('return o;')>=2,
  'sameDepthCoverageRequired':'q.z==m.x&&q.a==m.a'in compute,
  'noNative2xMetadataLookup':'2*p+1'not in compute and'_NativeMeta'not in compute,
  'fullRasterLightingPositionRestored':'v.pos.xy+=_QMetaRasterOrigin31.xy;'in s,
  'sameOriginalQFunctions':'ContinuousSurfaceLight335(v,m)'in s and'QuantizedSurfaceLight335(continuous'in s,
  'noShaderGlobalWrites':'cmd.SetGlobal'not in a,
  'noNewPlayOrRunnableCommand':'EnterPlaymode('not in host and'IRunCommand'not in host.replace('// REVIEW ONLY. No IRunCommand, EnterPlaymode, settings replacement, or automatic start.',''),
  'noBlockingGPUWait':'WaitForCompletion('not in a and'WaitAll'not in a and'CreateGraphicsFence('not in a,
  'no115Evaluation':'EvaluateForm115'not in a+host+compute and'BoundRun115'not in a+host+compute,
  'noLegacyRunnableHostDependency':'IRunCommand'not in jsonSource.read_text() and'Forward113'not in a+host and'LayerZero101'not in a+host,
 }
 assert all(checks.values()),checks
 extents=[(w,h)for w in range(1,481)for h in range(1,273)if w*h<=4096]
 maxGroups=max(((w+7)//8)*((h+7)//8)for w,h in extents);maxQArea=max(min(480,w+2)*min(272,h+2)for w,h in extents)
 budget={'logicalPixels':4096,'fine8xSamples':4096*64,'classifierDispatches':1,'classifierMaximumGroups':maxGroups,'classifierMaximumThreads':maxGroups*64,'fixedFineSamplesPerValidClassifierThread':64,'QHaloPixelsMaximum':maxQArea,'ownedRTCount':16,'conservativeRTBytesUpperBound':4096*64*(8*16+4)+4096*16+maxQArea*(5*16+4),'endReadbackRequests':1,'endReadbackBytes':16,'note':'CPU bounds, not GPU timing or driver allocation measurements. Raster primitive/lighting costs and shader variants remain runtime-unverified.'}
 (G/'BOUNDS31.json').write_text(json.dumps(budget,indent=2),encoding='utf-8',newline='\n')
 result={'baselineCommit':'abcbfe425f65ff749b8f89e55768aa00ac9103bd','CPUCompile':'passed','staticChecks':checks,'UnityGPUCalls':0,'AssetsWrites':0,'actualGPUAcknowledgementObserved':False,'runtimeValidated':False,'lifetimeAndExitIntegratedInReviewCandidate':True,'QMetaStage':'same-fragment initial Q, not ApplyShadeBoundary Qprime','shaderGPUCompileOrImportPerformed':False,'oldHostAssemblyDependency':False,'sourceFiles':{p.name:sha(p)for p in own+[source,G/'QMeta31.shader',G/'SourceOutline31.shader',G/'LineClass31.compute']}}
 (G/'CPU_INTEGRATION31.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'CPUCompile':'passed','staticChecks':len(checks),'actualUnityGPUCalls':0,'runtimeValidated':False}))
if __name__=='__main__':main()
