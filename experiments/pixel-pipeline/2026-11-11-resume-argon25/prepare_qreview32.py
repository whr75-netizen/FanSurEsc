"""CPU-only shader parity review and owned-consumer lifetime integration."""
from pathlib import Path
import hashlib,json,difflib,subprocess,sys
H=Path(__file__).resolve().parent;G=H/'face32';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def patch(a,b,name):return ''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+name,tofile='b/'+name,n=0))
def main():
 G.mkdir(exist_ok=True);build=G/'build';build.mkdir(exist_ok=True)
 legacyPath=R/'Assets/EUnityValidation01/HeadRegion502/Shaders/Legacy502.shader';basePath=R/'Assets/EUnityValidation01/MinimalRestore335/Shaders/LegacySignals335.shader'
 legacy=legacyPath.read_text(encoding='utf-8-sig');base=basePath.read_text(encoding='utf-8-sig');start='O335 Eye333Fragment(';begin=base.index(start);end=base.index('\nENDHLSL',begin);fragment=base[begin:end]
 assert fragment.count('{FragmentInput f;')==1;fragment=fragment.replace('{FragmentInput f;','{Region502Clip(v);FragmentInput f;')
 oldStart=legacy.index(start);oldEnd=legacy.index('\nENDHLSL',oldStart);candidate=legacy[:oldStart]+fragment+legacy[oldEnd:]
 assert candidate.count('#pragma multi_compile _ _FORWARD_PLUS')==1;candidate=candidate.replace('#pragma multi_compile _ _FORWARD_PLUS','#pragma multi_compile _ _CLUSTER_LIGHT_LOOP')
 (G/'Legacy502_contract32.shader').write_text(candidate,encoding='utf-8',newline='\n');(G/'UNAPPLIED_Legacy502_32.patch').write_text(patch(legacy,candidate,legacyPath.relative_to(R).as_posix()),encoding='utf-8',newline='\n')
 # Build a review variant, retaining31 as the immutable base. No runner/import.
 sourcePath=H/'SourceOutline31.cs';source=sourcePath.read_text(encoding='utf-8');review=source
 def rep(a,b):
  nonlocal review
  assert review.count(a)==1,(a,review.count(a));review=review.replace(a,b)
 rep(' Submission31 submission;',' readonly ConsumerReads32 consumers32=new ConsumerReads32();\n Submission31 submission;')
 rep(' public readonly RTHandle[] Fields=',' readonly RTHandle[] Fields=')
 rep(' public RTHandle Classification{get;private set;}',' RTHandle Classification{get;set;}')
 rep('public bool CanRelease=>submission==null||submission.CanRelease;','public bool CanRelease=>(submission==null||submission.CanRelease)&&consumers32.CanRelease;')
 rep('submission!=null&&submission.CanUsePixels&&Failure==null;','submission!=null&&submission.CanUsePixels&&Failure==null&&!consumers32.HasError;')
 rep('  // These are execution-time capability gates.','  ReadbackPreflight32.RequireCapabilities();\n  // These are execution-time capability gates.')
 rep('  view=camera.worldToCameraMatrix;','  foreach(var t in Fields.Concat(QFields).Concat(new[]{Classification}))ReadbackPreflight32.RequireColourSource(t.rt,0,0,1,1);\n  view=camera.worldToCameraMatrix;')
 rep(' public void StopRecording(){stopped=true;submission?.Stop();}',' public void StopRecording(){stopped=true;consumers32.Seal();submission?.Stop();}')
 addition='''
 // No raw owned RT escapes this variant. Copy at most262144B into managed data
 // during the callback; borrowed NativeArray/request lifetime cannot escape.
 public void RequestFieldReadback32(bool qField,int index,RectInt rect,Action<byte[]> receive){
  var fields=qField?QFields:Fields;if(index<0||index>=fields.Length)throw new ArgumentOutOfRangeException(nameof(index));RequestOwned32(fields[index],rect,receive);
 }
 public void RequestClassificationReadback32(RectInt rect,Action<byte[]> receive){RequestOwned32(Classification,rect,receive);}
 void RequestOwned32(RTHandle target,RectInt rect,Action<byte[]> receive){
  RequireCompleted();if(receive==null)throw new ArgumentNullException(nameof(receive));
  int bytes=ReadbackPreflight32.RequireColourSource(target.rt,rect.x,rect.y,rect.width,rect.height);var ticket=consumers32.Begin(bytes);
  try{AsyncGPUReadback.Request(target.rt,0,rect.x,rect.width,rect.y,rect.height,0,1,r=>{
   bool done=false,error=true;int actual=0;
   try{done=r.done;error=r.hasError;if(done&&!error)actual=r.layerDataSize;
    if(!done||error||actual!=bytes)throw new InvalidOperationException("32 consumer readback incomplete/error/byte mismatch; retain resource");
    var data=r.GetData<byte>();if(data.Length!=bytes){actual=-1;throw new InvalidOperationException("32 unexpected payload length");}
    var copy=new byte[bytes];data.CopyTo(copy);receive(copy);
   }catch(Exception e){consumers32.Fail();Fail(e);}finally{consumers32.Complete(ticket,done,error,actual);}
  });}catch(Exception e){consumers32.Fail();Fail(e);throw;} // uncertain enqueue: no release/retry
 }
'''
 rep(' public void StopRecording()',addition+' public void StopRecording()')
 out=build/'SourceOutline31.review32.cs';out.write_text(review,encoding='utf-8',newline='\n');(G/'UNAPPLIED_ConsumerLifetime32.patch').write_text(patch(source,review,'experiments/pixel-pipeline/2026-11-11-resume-argon25/SourceOutline31.cs'),encoding='utf-8',newline='\n')
 hostPath=H/'SourceCaptureHost31.cs';host=hostPath.read_text();hostReview=host
 for a,b in [
  (' readonly SourceOutline31 producer;',' readonly EditorExitRequest32 exitRequest32=new EditorExitRequest32();\n readonly SourceOutline31 producer;'),
  ('public void Arm(){','public void Arm(){exitRequest32.RequireOwner();'),
  ('if(stopped||producer.Failure!=null||camera!=producer.Camera)return;','if(stopped||exitRequest32.Requested||producer.Failure!=null||camera!=producer.Camera)return;'),
  ('public void BeginExit(){exit.Begin(', 'void BeginExitOnEditor32(){exit.Begin('),
  (' public void PumpExit(){exit.Pump(',' public void BeginExit(){exitRequest32.Request();}\n public void PumpExit(){exitRequest32.RequireOwner();exitRequest32.Drain(BeginExitOnEditor32);exit.Pump(')]:
  assert hostReview.count(a)==1,(a,hostReview.count(a));hostReview=hostReview.replace(a,b)
 hostOut=build/'SourceCaptureHost31.review32.cs';hostOut.write_text(hostReview,encoding='utf-8',newline='\n')
 patchPath=G/'UNAPPLIED_ConsumerLifetime32.patch';patchPath.write_text(patch(source,review,'experiments/pixel-pipeline/2026-11-11-resume-argon25/SourceOutline31.cs')+patch(host,hostReview,'experiments/pixel-pipeline/2026-11-11-resume-argon25/SourceCaptureHost31.cs'),encoding='utf-8',newline='\n')
 own=[out,hostOut,H/'ProducerLifetime31.cs',H/'ProducerContracts30.cs',H/'Projection31.cs',H/'face31/Json58Reference31.cs',H/'ConsumerReads32.cs',H/'ReadbackPreflight32.cs']
 compile_source(own,build/'SourceReview32.dll')
 checks={
 'legacy502OriginalClassifierYIsRole': 'o.classifier=float4(shadow>.5?0:1,_Auto245Role+1,'in legacy,
 'layeredParityExactExceptRegionClip':fragment.replace('{Region502Clip(v);FragmentInput f;','{FragmentInput f;')==base[begin:end],
 'regionVertexAndClipRetained':'Varyings o=Region502Vertex(v)'in candidate and'Region502Clip(v);FragmentInput f;'in candidate,
 'clusterKeywordMatchesBase':'#pragma multi_compile _ _CLUSTER_LIGHT_LOOP'in candidate and'#pragma multi_compile _ _FORWARD_PLUS'not in candidate,
 'opaqueMRTBlendAlreadyUsed':'Blend One Zero'in base and'Blend One Zero'in candidate,
 'consumerPrivateTargets':'public readonly RTHandle[] Fields'not in review and'public RTHandle Classification'not in review,
 'consumerGatesReleaseAndOutput':'&&consumers32.CanRelease'in review and'&&!consumers32.HasError'in review,
 'consumerPayloadBoundedAndCopied':'ConsumerReads32.ColourBytes'in(H/'ReadbackPreflight32.cs').read_text()and'data.CopyTo(copy);receive(copy)'in review,
 'consumerCompleteAfterReceive':review.index('receive(copy)')<review.index('consumers32.Complete(ticket'),
 'consumerUnknownEnqueueNeverReleased':'uncertain enqueue: no release/retry'in review,
 'callbackQueuesExitNotEditorCall':'public void BeginExit(){exitRequest32.Request();}'in hostReview and'exitRequest32.Drain(BeginExitOnEditor32)'in hostReview,
 'noBlockingWaitOr115':'WaitForCompletion('not in review and'EvaluateForm115'not in review,
 }
 assert all(checks.values()),checks
 result={'baseSource31SHA256':sha(sourcePath),'baseHost31SHA256':sha(hostPath),'originalLegacy502SHA256':sha(legacyPath),'baseLegacy335SHA256':sha(basePath),'reviewSourceSHA256':sha(out),'reviewHostSHA256':sha(hostOut),'CPUCompile':'passed','staticChecks':checks,'actualShaderCompileImportOrGPU':False,'UnityGPUCalls':0,'AssetsWrites':0,'patchesApplied':False,'reviewFiles':{p.relative_to(H).as_posix():sha(p)for p in own if'build'not in p.parts}}
 (G/'CPU_REVIEW32.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'CPUCompile':'passed','staticChecks':len(checks),'AssetsWrites':0,'UnityGPUCalls':0}))
if __name__=='__main__':main()
