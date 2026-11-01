from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'eye-observer73';BASE=HERE.parent/'apply-capture66';U=HERE.parent/'uv-features64'
sys.path.insert(0,str(HERE.parent/'boundary-input69'));from prepare73 import bundle
mode=sys.argv[1];assert mode in ['Compile76','Capture76','Post76']
deps=[BASE/'Json58Linear66.cs',BASE/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',OLD/'EyeReadback73.cs',OLD/'UnityEyeBuffer70.cs',OLD/'CreateOnly73.cs',OLD/'NativeSnapshot73.cs']
if mode=='Post76':
 s=(HERE/'Read76.cs').read_text().replace('CURRENT76.json','POST76.json');(HERE/'Post76.cs').write_text(s,encoding='utf-8');bundle(deps+[HERE/'Post76.cs'],HERE/'RUN_Post76.cs.txt');raise SystemExit
s=(OLD/'Capture73.cs').read_text(encoding='utf-8')
s=s.replace('eye-observer73','whole-eye76').replace('eye73-','eye76-').replace('STATE73-','STATE76-').replace('TRACE73-','TRACE76-').replace('CAPTURE_STARTED73','CAPTURE_STARTED76')
s=s.replace(' GlobalJournal64 journal;', ''' struct Baseline76 {public Vector4 colour,owner,meta,uv,domain,stamp;}
 EyeFeature348 probeEye;ComputeShader probeShader,oldShader;ComputeBuffer probeBuffer,probeVisits;RectInt probeROI;NativePlayer395 native;int armedSerial;
 void CameraBegin76(ScriptableRenderContext context,Camera camera){if(!native||!probeShader||camera!=native.host.headCamera)return;probeShader.SetInt("_ProbeFrame76",Time.frameCount);probeShader.SetInt("_ProbeSerialBefore76",native.host.main.renderedSerial335);probeVisits.SetData(new uint[1]);}
 void Arm76(NativePlayer395 n){native=n;probeEye=n.host.headEyes;if(!probeEye||!n.host.headEnabled)throw new InvalidOperationException("Head deferred path required");oldShader=probeEye.candidateShader;probeShader=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/BaselineProbe76.compute"));probeShader.hideFlags=HideFlags.DontSave;
 var r=probeEye.roi;probeROI=new RectInt(Math.Max(0,r.x-4),Math.Max(0,272-r.y-r.height-4),r.width+8,r.height+8);if(probeROI.xMax>480||probeROI.yMax>272)throw new InvalidOperationException("Probe near grid boundary");probeBuffer=new ComputeBuffer(probeROI.width*probeROI.height,96);probeVisits=new ComputeBuffer(1,4);probeVisits.SetData(new uint[1]);int k=probeShader.FindKernel("Evaluate");probeShader.SetBuffer(k,"_Baseline76",probeBuffer);probeShader.SetBuffer(k,"_ProbeVisits76",probeVisits);probeShader.SetInts("_ProbeROI76",probeROI.x,probeROI.y,probeROI.width,probeROI.height);probeEye.candidateShader=probeShader;armedSerial=n.host.main.renderedSerial335;RenderPipelineManager.beginCameraRendering+=CameraBegin76;
 }
 void Release76(){RenderPipelineManager.beginCameraRendering-=CameraBegin76;if(probeEye&&oldShader)probeEye.candidateShader=oldShader;probeBuffer?.Dispose();probeBuffer=null;probeVisits?.Dispose();probeVisits=null;if(probeShader)UnityEngine.Object.DestroyImmediate(probeShader);probeShader=null;report["ownedProbeReleased76"]=true;}
 GlobalJournal64 journal;''')
needle='   EditorApplication.isPaused=true;readyAllocated='
assert needle in s
s=s.replace(needle,'''   if(!probeShader){EditorApplication.isPaused=true;Arm76(n);Save("probe-armed-on-live-head-next-normal-frame");EditorApplication.isPaused=false;return;}
   if(n.host.main.renderedSerial335<=armedSerial)return;
   EditorApplication.isPaused=true;readyAllocated=''',1)
s=s.replace('exiting=true;Save("normal-Play-exit-requested")','exiting=true;Release76();Save("normal-Play-exit-requested")')
start=s.index(' void Capture(NativePlayer395 n,Gameplay397 gp)');s=s[:start]+(HERE/'capture_body76.txt').read_text()+'\n}\n'
if mode=='Compile76':
 needle=' public void Execute(ExecutionResult result)\n {';s=s.replace(needle,needle+'\n result.Log("76 entire observer compiled only; no Play/options/buffers");return;\n }\n void PreparedExecution76(ExecutionResult result)\n {',1)
if '--sequence6' in sys.argv:
 s=s.replace(' GlobalJournal64 journal;', ' string sequenceDirectory,sequenceId;Arr58 packetList76=new Arr58();int captured76,previousFrame76=-1;\n GlobalJournal64 journal;')
 needle='   Capture(n,gp);report["afterCaptureReleaseMemory"]=Memory();BeginExit();'
 assert needle in s
 replacement='''   if(previousFrame76>=0&&Time.frameCount!=previousFrame76+1)throw new InvalidOperationException("Observed frames are not consecutive");
   if(captured76==0){sequenceDirectory=output;sequenceId=sourceId;}
   sourceId=sequenceId+"-frame"+Time.frameCount;output=Path.Combine(sequenceDirectory,"frame-"+Time.frameCount);if(Directory.Exists(output))throw new IOException("Unique frame output required");Directory.CreateDirectory(output);planes=new Arr58();report["sourceId"]=sourceId;report["output"]=output;report["sequenceId"]=sequenceId;
   Capture(n,gp);report["afterCaptureReleaseMemory"]=Memory();previousFrame76=Time.frameCount;captured76++;packetList76.Add(new Obj58{["sourceId"]=sourceId,["output"]=output,["frame"]=Time.frameCount,["serial"]=n.host.main.renderedSerial335,["deltaTime"]=Time.deltaTime});report["sequencePackets"]=packetList76;
   if(captured76<6){armedSerial=n.host.main.renderedSerial335;EditorApplication.isPaused=false;return;}BeginExit();'''
 s=s.replace(needle,replacement)
 s=s.replace('oldShader=probeEye.candidateShader;', 'oldShader=probeEye.candidateShader;report["actualRuntimeProductShaderPath"]=AssetDatabase.GetAssetPath(oldShader);')
if '--frozen-original' in sys.argv:
 method=(HERE/'FrozenOriginal76.cs').read_text(encoding='utf-8');s=s.replace(' void Capture(NativePlayer395 n,Gameplay397 gp)',method+'\n void Capture(NativePlayer395 n,Gameplay397 gp)')
 needle='  var sampleROI=new RectInt(0,0,e.roi.width*4,e.roi.height*4);';assert needle in s;s=s.replace(needle,'  FrozenOriginal76(e,frame);\n'+needle)
out=HERE
if len(sys.argv)>2:
 out=HERE/sys.argv[2];out.mkdir(exist_ok=False)
 s=s.replace(str(HERE),str(out))
 (out/'relay76.py').write_text((HERE/'relay76.py').read_text(),encoding='utf-8')
 (out/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
(out/(mode+'.cs')).write_text(s,encoding='utf-8');bundle(deps+[out/(mode+'.cs')],out/('RUN_'+mode+'.cs.txt'))
full=(out/('RUN_'+mode+'.cs.txt')).read_text();
for bad in ['File.Move(','Directory.Move(','File.Delete(','Directory.Delete(','File.WriteAllText(','File.AppendAllText(','FileMode.Create,','File.Create(']:assert bad not in full,bad
print('Prepared',mode,'without execution')
