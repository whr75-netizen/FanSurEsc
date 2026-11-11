"""Runtime source-area resolver and bounded six-consecutive-frame observer."""
from pathlib import Path
import ctypes as C,hashlib,json,re,sys
H=Path(__file__).resolve().parent;G=H/'face36';sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cpu_hlsl():
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 raw=(H/'SourceArea36.compute').read_bytes();blob=C.c_void_p();error=C.c_void_p()
 try:
  hr=fn(raw,len(raw),b'SourceArea36',None,None,b'ResolveArea36',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(error));diag=api.blob(error).decode(errors='replace');(G/'CPU_HLSL36.txt').write_text(diag,encoding='utf-8');assert hr>=0,diag
  binary=api.blob(blob);audit=api.token_audit(binary);assert audit['threads']==[8,8,1]and not audit['privateArrayDeclarations'];(G/'SourceArea36.cpu.dxbc').write_bytes(binary);return audit
 finally:api.release(blob);api.release(error)
def main():
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True);(G/'shaders').mkdir(exist_ok=True);audit=cpu_hlsl()
 (G/'shaders/SourceArea36.compute').write_bytes((H/'SourceArea36.compute').read_bytes())
 old=(H/'face35/capture/RUN.cs.txt').read_text();code=re.sub(r'\b[A-Za-z_]\w*35\b',lambda m:m[0] if m[0].endswith('335') else m[0][:-2]+'36',old)
 # Preserve previously imported fine-light asset and its exact shader name.
 code=code.replace('Assets/EUnityValidation01/SourceBoundary36/FineSourceLight36.shader','Assets/EUnityValidation01/SourceBoundary35/FineSourceLight35.shader')
 def rep(a,b):
  nonlocal code
  assert code.count(a)==1,(a,code.count(a));code=code.replace(a,b)
 rep('QFields=new RTHandle[18]','QFields=new RTHandle[19]')
 rep('RTHandle depth,qDepth,fineDepth;Material[] fineMats;','RTHandle depth,qDepth,fineDepth;Material[] fineMats;ComputeShader area36;int areaKernel36;public int TargetFrame36{get;set;}')
 rep('if(stopped||Disposed||recorded)return;','if(stopped||Disposed||recorded)return;if(Time.frameCount<TargetFrame36)return;if(Time.frameCount>TargetFrame36){Fail(new InvalidOperationException("Missed requested consecutive source frame; no late substitute"));return;}')
 rep('fineMats=qOriginals.Select(m=>Clone(m,fineShader)).ToArray();','fineMats=qOriginals.Select(m=>Clone(m,fineShader)).ToArray();if(qOriginals.Count(m=>Mathf.RoundToInt(m.GetFloat("_Auto245Role"))==3)!=1)throw new InvalidOperationException("36 requires one verified face source slot");var areaAsset=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/SourceBoundary36/SourceArea36.compute");if(!areaAsset)throw new InvalidOperationException("36 source-area variant unavailable");area36=UnityEngine.Object.Instantiate(areaAsset);areaKernel36=area36.FindKernel("ResolveArea36");area36.GetKernelThreadGroupSizes(areaKernel36,out uint ax,out uint ay,out uint az);if(ax!=8||ay!=8||az!=1)throw new InvalidOperationException("36 ABI mismatch");')
 rep('fineDepth=Target(QROI.width*8,QROI.height*8,true);','fineDepth=Target(QROI.width*8,QROI.height*8,true);QFields[18]=Target(QROI.width,QROI.height,uav:true);')
 rep('QFields.Skip(13).Select','QFields.Skip(13).Take(5).Select')
 rep('foreach(var t in Fields.Concat(QFields))b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);','foreach(var t in Fields.Concat(QFields.Take(18)))b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);b.UseTexture(graph.ImportTexture(QFields[18]),AccessFlags.Write);')
 rep('submission.StageRecorded(8);','cmd.SetComputeTextureParam(area36,areaKernel36,"_InitialMask36",QFields[6].rt);cmd.SetComputeTextureParam(area36,areaKernel36,"_CurrentMeta36",QFields[7].rt);cmd.SetComputeTextureParam(area36,areaKernel36,"_FineQ36",QFields[16].rt);cmd.SetComputeTextureParam(area36,areaKernel36,"_FineMeta36",QFields[17].rt);cmd.SetComputeTextureParam(area36,areaKernel36,"_Area36",QFields[18].rt);cmd.SetComputeIntParams(area36,"_Size36",QROI.width,QROI.height);cmd.SetComputeIntParam(area36,"_FaceSteps36",eye.full.faceShadeSteps);cmd.DispatchCompute(area36,areaKernel36,(QROI.width+7)/8,(QROI.height+7)/8,1);submission.StageRecorded(8);')
 rep('if(classify)UnityEngine.Object.DestroyImmediate(classify);','if(classify)UnityEngine.Object.DestroyImmediate(classify);if(area36)UnityEngine.Object.DestroyImmediate(area36);')
 # Adapt the validated host: ONE cohort owns a view and six private producers.
 start=code.index('public sealed class SourceCaptureHost36 {');end=code.index('\n}\n}',start)+2;host=code[start:end]
 host=host.replace('SourceCaptureHost36','SourceSequenceHost36').replace('readonly SourceOutline36 producer;','readonly SourceOutline36[] producers;')
 host=host.replace('SourceOutline36 producer,Action','SourceOutline36[] producers,Action').replace('this.producer=producer??throw new ArgumentNullException(nameof(producer));','this.producers=producers??throw new ArgumentNullException(nameof(producers));if(producers.Length!=6||producers.Any(p=>p==null)||producers.Select(p=>p.Camera).Distinct().Count()!=1)throw new ArgumentException("36 six captures on one view required");')
 host=host.replace('producer.ViewIdentity','producers[0].ViewIdentity').replace('producer.Camera','producers[0].Camera').replace('producer.Failure!=null','producers.Any(p=>p.Failure!=null)').replace('producer.StopRecording();','foreach(var p in producers)p.StopRecording();')
 host=host.replace('camera.GetUniversalAdditionalCameraData().scriptableRenderer.EnqueuePass(producer);','foreach(var p in producers)if(p.TargetFrame36==Time.frameCount)camera.GetUniversalAdditionalCameraData().scriptableRenderer.EnqueuePass(p);')
 host=host.replace('producer.ReportFailure(e);','foreach(var p in producers)p.ReportFailure(e);').replace('()=>producer.CanRelease','()=>producers.All(p=>p.CanRelease)').replace('if(!producer.TryReleaseOwned())','if(!producers.All(p=>p.TryReleaseOwned()))').replace('producer.CanUsePixels','producers.All(p=>p.CanUsePixels)').replace('producer.Failure','producers.Select(p=>p.Failure).FirstOrDefault(e=>e!=null)')
 code=code[:end]+'\n'+host+code[end:]
 rep('SourceOutline36 producer;SourceCaptureHost36 host;','SourceOutline36 producer;SourceOutline36[] cohort;SourceSequenceHost36 host;int cohortRead;readonly Arr36 frames36=new Arr36();')
 code=code.replace('SourceCaptureHost36.PendingOwnerCount','SourceSequenceHost36.PendingOwnerCount')
 a='producer=new SourceOutline36(n.host.headEyes,Path.Combine(H,"producer/support/surface27/FACE_INPUT27.json"),@"C:\\Users\\15352\\Documents\\Codex\\2026-10-27\\task-2\\render-fix21\\renderer-family59\\SOURCE_REGISTRY59.json",id);host=new SourceCaptureHost36(producer,()=>{},Restore);host.Arm();'
 b='cohort=new SourceOutline36[6];try{for(int i=0;i<6;i++){cohort[i]=new SourceOutline36(n.host.headEyes,Path.Combine(H,"producer/support/surface27/FACE_INPUT27.json"),@"C:\\Users\\15352\\Documents\\Codex\\2026-10-27\\task-2\\render-fix21\\renderer-family59\\SOURCE_REGISTRY59.json",id+"/sequence"+i);cohort[i].TargetFrame36=Time.frameCount+1+i;}}catch{foreach(var p0 in cohort)if(p0!=null)p0.TryReleaseOwned();throw;}producer=cohort[0];host=new SourceSequenceHost36(cohort,()=>{},Restore);host.Arm();'
 rep(a,b)
 rep('if(producer.Failure!=null)throw new InvalidOperationException("Producer failed",producer.Failure);if(!producer.CanUsePixels)return;','if(host.ProducerError!=null)throw new InvalidOperationException("Producer failed",host.ProducerError);if(!host.Ready)return;')
 # Coarse evidence each frame; first frame additionally keeps fine Q/meta as an
 # independent CPU oracle of the actual runtime resolver. No CPU expectation upload.
 rep('foreach(int i in new[]{0,2})tasks.Add(new Plane(false,i,"source"+i,r.width*8,r.height*8));foreach(int i in new[]{0,3,4,5,6,7,8,9,10,11,12,16,17})','foreach(int i in (cohortRead==0?new[]{5,6,7,9,11,12,16,17,18}:new[]{6,7,9,12,18}))')
 rep('tasks.Add(new Plane(false,-1,"classification",r.width,r.height));','')
 rep('if(task==tasks.Count){packet=true;report["packetComplete"]=true;Save("packet-copied");Exit();return;}','if(task==tasks.Count){frames36.Add(new Obj36{["frame"]=producer.CapturedFrame,["sourceId"]=producer.FrameKey,["QROI"]=report["QROI"],["frameInfo"]=producer.FrameInfo36});if(++cohortRead<cohort.Length){producer=cohort[cohortRead];tasks=null;task=0;y=0;return;}report["frames"]=frames36;bool consecutive=cohort.Select((p0,i)=>p0.CapturedFrame==cohort[0].CapturedFrame+i).All(v=>v);report["actualConsecutive"]=consecutive;if(!consecutive)throw new InvalidOperationException("36 capture frame gap");packet=true;report["packetComplete"]=true;Save("six-packets-copied");Exit();return;}')
 rep('string name=p.name+"-row"','string name="frame"+producer.CapturedFrame+"-"+p.name+"-row"')
 rep('["name"]=p.name,["file"]=name','["frame"]=producer.CapturedFrame,["sourceId"]=producer.FrameKey,["name"]=p.name,["file"]=name')
 # Watch coordinates come from the actual35 counterexample, not a model design
 # constant. Later frames copy just the8x8 source footprint at that coordinate.
 rep('public int width,height;','public int width,height,ox,oy;')
 rep('var rect=new RectInt(0,row,p.width,rows);','var rect=new RectInt(p.ox,row+p.oy,p.width,rows);')
 rep('["bottomRow"]=row,["rows"]=rows','["bottomRow"]=row,["originX"]=p.ox,["originY"]=p.oy,["rows"]=rows')
 rep('report["frameInfo"]=producer.FrameInfo36;','if(cohortRead>0){var watch=Json36.Parse(File.ReadAllText(Path.Combine(H,"face36/WATCH36.json")));int wi=0;foreach(var wp in watch["points"]){int lx=(int)wp[0]-q.x,ly=q.y+q.height-1-(int)wp[1];if(lx<0||ly<0||lx>=q.width||ly>=q.height)throw new InvalidOperationException("36 watch outside current source ROI");foreach(int fi in new[]{16,17})tasks.Add(new Plane(true,fi,"q"+fi+"-watch"+wi,8,8){ox=lx*8,oy=ly*8});wi++;}}report["frameInfo"]=producer.FrameInfo36;')
 rep('["worldPixel"]=f.motion.camera.orthographicSize*2/272,','["worldPixel"]=f.motion.camera.orthographicSize*2/272,["deltaTime"]=Time.deltaTime,["evaluatedFrame"]=f.motion.evaluatedFrame,["renderedSource"]=f.motion.sourceFrame,')
 assert 'face36/import/COMPLETE.json' in code
 # Pin6 is a diagnostic sequence length, never an eye/region pixel budget.
 # Version335 is an existing product ABI, not a diagnostic35 identifier.
 # Keep EVERY original shader property string; a C# compile cannot detect a
 # misspelled property name. This guard precedes any import/Unity call.
 oldABI=set(re.findall(r'"(_[A-Za-z0-9_]+)"',old));newABI=set(re.findall(r'"(_[A-Za-z0-9_]+)"',code));assert oldABI<=newABI,oldABI-newABI
 assert 'renderedSerial335' in code and 'renderedSerial336' not in code
 for k in ['EvaluateForm115','BoundRun115']:assert k not in code
 p=G/'capture';p.mkdir(exist_ok=True);assert not(p/'REQUEST.json').exists();(p/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n');compile_source([p/'RUN.cs.txt'],G/'build/capture36.dll')
 # Reuse the import receipt/backup; only the new bounded compute asset is added.
 imp=(H/'face35/import/RUN.cs.txt').read_text();at=imp.rfind('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\ninternal class CommandScript');imp=imp[at:].replace('face35\\import','face36\\import').replace('face35\\shaders','face36\\shaders').replace('SourceBoundary35','SourceBoundary36');imp=imp.replace('new[]{"FineSourceLight35.shader"}','new[]{"SourceArea36.compute"}');a=imp.index('   var messages=');b=imp.index('   var checks=',a)
 imp=imp[:a]+'''   var messages=new Arr36();var cs=AssetDatabase.LoadAssetAtPath<ComputeShader>(Target+"/SourceArea36.compute");if(!cs)throw new InvalidOperationException("36 compute import missing");foreach(var m in ShaderUtil.GetComputeShaderMessages(cs)){messages.Add(m.message);if(m.severity.ToString()=="Error")throw new InvalidOperationException(m.message);}cs.GetKernelThreadGroupSizes(cs.FindKernel("ResolveArea36"),out uint tx,out uint ty,out uint tz);if(tx!=8||ty!=8||tz!=1)throw new InvalidOperationException("36 ABI mismatch");
'''+imp[b:]
 imp=re.sub(r'\b(?:Json|Obj|Arr|NativeSnapshot|CreateOnly)35\b',lambda m:m[0][:-2]+'36',imp);shared=code[:code.rfind('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\ninternal class CommandScript')]
 p=G/'import';p.mkdir(exist_ok=True);(p/'RUN.cs.txt').write_text(shared+'\n'+imp,encoding='utf-8',newline='\n');compile_source([p/'RUN.cs.txt'],G/'build/import36.dll')
 actual=json.loads((H/'face35/analysis/SOURCE_AREA35.json').read_text());watch={'basisSourceId':actual['sourceId'],'points':[p['xy']for p in actual['changedQCells']],'meaning':'diagnostic counterexample coordinates, no runtime design constraint'};(G/'WATCH36.json').write_text(json.dumps(watch,indent=2),encoding='utf-8',newline='\n')
 plan={'CPUCompile':'passed','HLSL':audit,'originalABIStringsPreserved':len(oldABI),'sourceSHA':sha(H/'SourceArea36.compute'),'captureSHA':sha(G/'capture/RUN.cs.txt'),'importSHA':sha(G/'import/RUN.cs.txt'),'sourceFrames':6,'areaDispatchPerFrame':'4x4groups*64=1024 threads /812valid;64fixed samples+28border comparisons, early-out nonface','newPrivateBuffers':0,'GPUExpectedUpload':False,'product77DefaultChanged':False};(G/'PREPARED36.json').write_text(json.dumps(plan,indent=2),encoding='utf-8',newline='\n');print(json.dumps(plan))
if __name__=='__main__':main()
