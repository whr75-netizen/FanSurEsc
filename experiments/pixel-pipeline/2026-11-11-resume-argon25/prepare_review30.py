"""CPU-only producer integration. No command runner/Unity import or execution."""
from pathlib import Path
import hashlib,json,subprocess,sys
H=Path(__file__).resolve().parent;G=H/'face30';REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compile_source(source,out,extra=()):
 editor=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data');refs=[editor/'NetStandard/ref/2.1.0/netstandard.dll',editor/'NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll']+sorted((editor/'Managed/UnityEngine').glob('*.dll'))+sorted((REPO/'Library/ScriptAssemblies').glob('*.dll'))+list(extra)
 args=['/nologo','/nostdlib+','/utf8output','/preferreduilang:en-US','/target:library','/langversion:latest','/out:'+str(out)]+['/reference:'+str(p)for p in refs]+[str(p)for p in source]
 rsp=out.with_suffix('.rsp');rsp.write_text('\n'.join('"'+v+'"'for v in args),encoding='utf-8',newline='\n');p=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');out.with_suffix('.diagnostics.txt').write_text(p.stdout+p.stderr,encoding='utf-8',newline='\n');assert p.returncode==0,p.stdout+p.stderr
def main():
 G.mkdir(exist_ok=True);build=G/'build';build.mkdir(exist_ok=True)
 old=H/'face29/physical-fix/SourceOutline29.cs';s=old.read_text(encoding='utf-8')
 # Rename the C# type only. Shader asset paths and GPU property names are ABI,
 # not C# symbols; a broad replacement silently made both invalid.
 for before,after in [('public sealed class SourceOutline29 :','public sealed class SourceOutline30 :'),('public SourceOutline29(','public SourceOutline30('),('public SourceOutline29 owner;','public SourceOutline30 owner;')]:
  assert s.count(before)==1,(before,s.count(before));s=s.replace(before,after)
 s=s.replace(' Exception failure;int classifierKernel;',' readonly FailureBoundary30 boundary30=new FailureBoundary30();int classifierKernel;')
 field=' readonly string bindingModel30,packetSequence30,view30;readonly Camera camera30;int renderSequence30;\n'
 token=' RTHandle depth;';assert s.count(token)==1;s=s.replace(token,field+token)
 oldctor='public SourceOutline30(EyeFeature348 e,string bindingPath,string registryPath){';assert s.count(oldctor)==1;s=s.replace(oldctor,'public SourceOutline30(EyeFeature348 e,string bindingPath,string registryPath,string packetSequence){\n  if(String.IsNullOrEmpty(packetSequence))throw new ArgumentException("30 source packet sequence required");packetSequence30=packetSequence;camera30=e.full.motion.camera;view30=camera30.GetEntityId().ToString()+"/"+e.GetEntityId().ToString()+"/"+Guid.NewGuid().ToString("N");')
 token='var registry=Json58.Parse(File.ReadAllText(registryPath));';assert s.count(token)==1;s=s.replace(token,token+'bindingModel30=(string)registry["modelSHA256"];')
 s=s.replace('failure!=null','boundary30.Failure!=null').replace('failure=e;','boundary30.Remember(e);')
 s=s.replace('var f=eye.full;if(eye.modelTopologySHA256!=topology)','var f=eye.full;if(f.motion.camera!=camera30)throw new InvalidOperationException("30 camera identity invalidated");if(eye.modelTopologySHA256!=topology)')
 oldrecord='if(Disposed||boundary30.Failure!=null)return;try{RecordChecked(graph,unused);}catch(Exception e){boundary30.Remember(e);}'
 assert s.count(oldrecord)==1;s=s.replace(oldrecord,'if(Disposed)return;boundary30.Run(()=>RecordChecked(graph,unused));')
 oldcheck='if(boundary30.Failure!=null)throw new InvalidOperationException("29 deferred source failure outside RenderGraph",failure);'
 assert s.count(oldcheck)==1;s=s.replace(oldcheck,'boundary30.ThrowOutsideGraph();')
 token='  foreach(bool hair in new[]{true,false})';assert s.count(token)==1
 before='''  var producerFrame30=packetSequence30+"-frame"+Time.frameCount;renderSequence30=checked(renderSequence30+1);
  float[] Copy30(Matrix4x4 m)=>Enumerable.Range(0,16).Select(i=>m[i]).ToArray();
  GridBinding30 Describe30(Matrix4x4 matrix,RTHandle target)=>new GridBinding30(producerFrame30,view30,bindingModel30,GridSpace30.PhysicalHead,Time.frameCount,renderSequence30,ROI.x,ROI.y,ROI.width,ROI.height,8,target.rt.width,target.rt.height,Copy30(matrix));
  var expected30=Describe30(vp,Fields[0]);var outline30=Describe30(ink.GetMatrix("_ProbeGPUVP29"),Fields[0]);var pigment30=Describe30(pigmentMat.GetMatrix("_ProbeGPUVP29"),Fields[2]);
  GridBinding30.RequirePair(expected30,outline30,pigment30); // Before any AddUnsafePass.
'''
 s=s.replace(token,before+token)
 token='  Info=new Obj58{';assert s.count(token)==1;s=s.replace(token,'  Info=new Obj58{["sourceId30"]=producerFrame30,["view30"]=view30,["renderSequence30"]=renderSequence30,["GPUCompletionStamp30"]=false,')
 assert 'joint.DenseNative'not in s and 'Exception failure;'not in s
 abiChecks={
  'existingOutlineAssetPathRetained':'Assets/EUnityValidation01/SourceBoundary29/SourceOutline29.shader'in s,
  'existingOutlinePropertyRetained':'ink.SetVector("_SourceOutline29",sourceInk)'in s,
  'existingClassifierAssetRetained':'Assets/EUnityValidation01/SourceBoundary29/LineClass29.compute'in s,
  'existingClassifierKernelRetained':'FindKernel("Classify29")'in s,
  'noInventedOutlineAssetOrProperty':'SourceOutline30.shader'not in s and'"_SourceOutline30"'not in s,
  'gridGuardBeforeAllOwnPasses':s.index('GridBinding30.RequirePair')<s.index('graph.AddUnsafePass')}
 assert all(abiChecks.values()),abiChecks
 header='// CPU REVIEW ONLY. Not runtime ready: GPU completion/Dispose gates are not integrated.\nusing System;using System.IO;using System.Linq;using UnityEditor;using UnityEngine;using UnityEngine.Rendering;using UnityEngine.Rendering.Universal;using UnityEngine.Rendering.RenderGraphModule;\nnamespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\n'
 out=G/'SourceOutline30.cs';out.write_text(header+s+'\n}\n',encoding='utf-8',newline='\n')
 # Metadata dependency only. This library has no runnable entry point and is
 # never loaded into an Editor/AppDomain by this script.
 dep=build/'Host29Metadata.dll';compile_source([H/'face29/physical-fix/RUN_Capture25.cs.txt'],dep)
 compile_source([out,H/'ProducerContracts30.cs'],build/'SourceOutline30.dll',[dep])
 result={'sourceSHA256':sha(out),'contractsSHA256':sha(H/'ProducerContracts30.cs'),'metadataDependencySHA256':sha(dep),'CPUCompile':'passed','shaderABIStaticChecks':abiChecks,'UnityCalls':0,'AssetsChanges':0,'producerGridGuardIntegrated':True,'managedFailureBoundaryIntegrated':True,'liveGpuCompletionDisposeGateIntegrated':False,'runtimeReady':False,'noCommandRunnerGenerated':True,'limitations':['GPU frame-stamp/fence acknowledgement not implemented in runner.','Failure exit still releases resources without an explicit pending-work proof; do not activate this candidate.','Q/meta raster phase and source-domain equivalence need actual producer descriptors; do not assume2x sample matching.','Same-object material/texture content generation invalidation incomplete.']}
 (G/'CPU_INTEGRATION30.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
