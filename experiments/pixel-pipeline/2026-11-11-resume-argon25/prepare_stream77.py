"""Small six-slot, acknowledged runtime stream; shader75 is NOT changed.

First use12 frames as a lifecycle/ABI probe. Only after actual completion,
preservation and CPU/data checks may the same code run a bounded long sequence.
No GPU operation or Unity call occurs in this generator/CPU compiler.
"""
from pathlib import Path
import sys,json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 mode=sys.argv[1];assert mode in['probe','probe2','probe3','long','loop120'];target=12 if mode.startswith('probe') else 120;pose=1;G=H/'face77'/mode
 for p in['capture','final','post/final','console','build']:(G/p).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists();s=(H/'face75/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face75\\capture','resume-20261111\\face77\\'+mode+'\\capture').replace('face75-source-owner-history-','face77-bounded-runtime-stream-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('SourceSequenceHost40 host;','StreamHost77 host;')
 rep('SourceOutline40 producer;SourceOutline40[] cohort;StreamHost77 host;int cohortRead;readonly Arr40 frames36=new Arr40();','SourceOutline40 producer=null;StreamHost77 host;')
 rep('int domain,sequence,task,y;','int domain,sequence;')
 rep('volatile bool inRead,readDone;bool packet;','bool packet;')
 a=s.index('  sealed class Plane{',s.index('internal class CommandScript : IRunCommand')) if '  sealed class Plane{'in s else s.index(' sealed class Plane{',s.index('internal class CommandScript : IRunCommand'));b=s.index('SourceFlatResource67 sharedSource67;',a);s=s[:a]+s[b:]
 rep('List<Plane> tasks;MotionContour40 motion40;float runtimeTime37;bool held37;void RestoreHold37(){motion40?.Dispose();if(motion40!=null)report["motionRestoration40"]=motion40.RestoreReport;if(held37){Time.timeScale=runtimeTime37;held37=false;}}','MotionContour40 motion40;void RestoreHold37(){motion40?.Dispose();if(motion40!=null)report["motionRestoration40"]=motion40.RestoreReport;}')
 rep('public bool CanRelease=>(submission==null||submission.CanRelease)&&consumers32.CanRelease;','public bool CanRelease=>(submission==null||submission.CanRelease)&&consumers32.CanRelease&&(!lite77||(!Pending77&&BorrowerCount77==0));')
 # Capture pose data only at declared keyframes. This is the same immutable
 # input uploaded to the kernel, not CPU selected output or regenerated colour.
 rep('projection75.SetPixelData(data,0);projection75.Apply(false,true);','projection75.SetPixelData(data,0);projection75.Apply(false,true);if(SavePose77){using(var output=new BinaryWriter(new FileStream(Path.Combine(EvidenceRoot40,"pose-frame"+frame+".bin"),FileMode.CreateNew))){output.Write("projected-source75/v1");output.Write(frame);output.Write(data.Length);foreach(var v in data){output.Write(v.x);output.Write(v.y);output.Write(v.z);output.Write(v.w);}}}')
 # Original motion control, no settings-object replacement. Turn is delayed to
 #32 so the long sequence contains an actual walk segment before turning.
 rep('Time.frameCount>=FirstTarget+2','Time.frameCount>=FirstTarget+32')
 # The actual turn arrives the update after queueing at end-of-frame+32. Keep
 # the expected-input receipt aligned; this changes no key/event dispatch.
 assert s.count('index<3')==2;s=s.replace('index<3','index<33')
 if mode=='loop120':
  # Normal bound actions form an eight-update-per-side square. No teleport,
  # camera manipulation, speed or InputSettings object replacement. End-frame
  # event arrives on the next Dynamic update; expected index uses that delay.
  rep('bool started,disposed,turned;int direction;','bool started,disposed;int loopPhase77;int direction;')
  rep('void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(!turned&&Time.frameCount>=FirstTarget+32){Queue(direction+2);turned=true;}}','void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(Time.frameCount<FirstTarget)return;int phase=(Time.frameCount-FirstTarget+1)/8;if(phase!=loopPhase77){Queue(direction+2*phase);loopPhase77=phase;}}')
  rep('var expected=D[((index<33?direction:direction+2)+8)%8];','var expected=D[(direction+2*Math.Max(0,index/8)+8)%8];')
  rep('["stage"]=index<33?"walk":"turn",','["stage"]="bounded-loop-side-"+(Math.Max(0,index/8)%4),')
 a=s.index(' void Tick(){',s.index('internal class CommandScript : IRunCommand'));b=s.index(' void Exit(){',a)
 tick='''  void Tick(){
   if(finished)return;try{
    if(exiting){if(host!=null){host.PumpExit();if(restored&&host.ResourcesReleased)Finish();}else{earlyExit.Pump(!EditorApplication.isPlaying&&!EditorApplication.isPlayingOrWillChangePlaymode&&!EditorApplication.isCompiling&&!EditorApplication.isUpdating,()=>producer==null||producer.CanRelease,()=>{if(producer!=null&&!producer.TryReleaseOwned())throw new InvalidOperationException("77 retain producer");},Restore);if(restored&&earlyExit.Released)Finish();}return;}
    if(AppDomain.CurrentDomain.Id!=domain)throw new InvalidOperationException("77 unexpected domain reload");lock(ioSync){if(errors.Count()>0)throw new InvalidOperationException("77 new Console error; stop");}if(EditorApplication.timeSinceStartup-started>120)throw new TimeoutException("77 bounded observation limit; no extension or retry");if(!EditorApplication.isPlaying)return;
    var n=UnityEngine.Object.FindObjectsByType<NativePlayer395>(FindObjectsSortMode.None).FirstOrDefault();var g=UnityEngine.Object.FindObjectsByType<Gameplay397>(FindObjectsSortMode.None).FirstOrDefault(p=>p.player==n);if(n&&!String.IsNullOrEmpty(n.failure))throw new InvalidOperationException(n.failure);if(g&&!String.IsNullOrEmpty(g.failure))throw new InvalidOperationException(g.failure);if(EditorApplication.isPaused)throw new InvalidOperationException("77 unexpected pause");
    if(host==null){if(!n||!n.ready||!g||!g.connected||n.host.main.renderedSerial335<=0)return;if(g.runInputTest||!n.host.headEnabled)throw new InvalidOperationException("77 supported normal head path required");sharedSource67=new SourceFlatResource67(Path.Combine(H,"face67"),n.host.headEyes);report["sourcePalette67"]=sharedSource67.Info();motion40=new MotionContour40(n,Root);motion40.Start();host=new StreamHost77(n.host.headEyes,sharedSource67,Root,id,motion40.FirstTarget,TARGET77,POSE77,motion40.Snapshot,RestoreHold37,Restore);host.Arm();Save("await-bounded-stream");return;}
    if(host.ProducerError!=null)throw new InvalidOperationException("77 producer failed",host.ProducerError);
    if(EditorApplication.timeSinceStartup-lastTrace>5){lastTrace=EditorApplication.timeSinceStartup;report["submitted77"]=host.Submitted;report["received77"]=host.Received;Save("stream-progress");}
    if(!host.Ready)return;report["stream77"]=host.Summary();report["actualConsecutive"]=report["stream77"]["actualConsecutive"];if(!(bool)report["actualConsecutive"])throw new InvalidOperationException("77 discontinuous frames");packet=true;report["packetComplete"]=true;Save("bounded-stream-copied");Exit();
   }catch(Exception e){report["error"]=e.ToString();if(host!=null)report["stream77"]=host.Summary();Exit();}
  }
'''.replace('TARGET77',str(target)).replace('POSE77',str(pose))
 s=s[:a]+tick+s[b:]
 rep('SourceSequenceHost40.PendingOwnerCount','StreamHost77.PendingOwnerCount') if s.count('SourceSequenceHost40.PendingOwnerCount')==1 else None
 # Two references exist in the inherited Execute and Finish; both are the new
 # host's own roots, while the unused old host declaration stays unchanged.
 s=s.replace('SourceSequenceHost40.PendingOwnerCount','StreamHost77.PendingOwnerCount')
 rep('void Finish(){sharedSource67?.Dispose();','void Finish(){if(host!=null)report["stream77"]=host.Summary();sharedSource67?.Dispose();')
 rep('["plannedSourceFrames"]=6,','["plannedSourceFrames"]='+str(target)+',')
 stream=(H/'Stream77.cs.txt').read_text()
 if not mode.startswith('probe'):
  #35x35x13x16=254800 bytes: keep ONE bounded request while adding the actual
  # source-width scalar plane required for complete selection recomputation.
  stream=stream.replace('const int W77=36;','const int W77=35;').replace('W77*12','W77*13').replace('12*W77*W77*16','13*W77*W77*16').replace('bottom-left12layers','bottom-left13layers').replace('x1-x0>30||y1-y0>30','x1-x0>29||y1-y0>29').replace('["maxReadbackBytes"]=248832','["maxReadbackBytes"]=254800')
  needle='cmd.CopyTexture(main41.domain.rt,0,0,QROI.x+join41.x,272-QROI.y-W77+join41.y,W77,W77,Fields[13].rt,0,0,11*W77,0);';assert stream.count(needle)==1;stream=stream.replace(needle,needle+'cmd.CopyTexture(Fields[15].rt,0,0,5*W77,0,W77,W77,Fields[13].rt,0,0,12*W77,0);')
 if mode=='loop120':
  needle='data.CopyTo(bytes);var encoded=FrameBytes77.Encode(bytes);';assert stream.count(needle)==1
  stream=stream.replace(needle,'data.CopyTo(bytes);int actorCount77=0,faceCount77=0;for(int y77=0;y77<W77;y77++)for(int x77=0;x77<W77;x77++){bool actor77=BitConverter.ToSingle(bytes,16*(y77*W77*13+5*W77+x77)+8)==1;if(actor77){actorCount77++;if(BitConverter.ToSingle(bytes,16*(y77*W77*13+6*W77+x77))==sourceFlat67.MappedRole72)faceCount77++;}}receipt["observedActorCells77"]=actorCount77;receipt["observedFaceCells77"]=faceCount77;if(actorCount77==0)Fail(new InvalidOperationException("77 character not observed; stop and drain, no temporal art claim"));var encoded=FrameBytes77.Encode(bytes);')
 s+='\n'+stream+'\n'+(H/'FrameBytes77.cs').read_text();(G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/stream77.dll')
 for phase in['final','post/final']:
  text=(H/('face75/'+phase+'/RUN.cs.txt')).read_text().replace('resume-20261111\\face75','resume-20261111\\face77\\'+mode);(G/phase/'RUN.cs.txt').write_text(text,encoding='utf-8',newline='\n');compile_unity_language(G/phase/'RUN.cs.txt',G/'build'/('post77.dll'if phase.startswith('post')else'pre77.dll'))
 readbytes=248832 if mode.startswith('probe')else 254800
 (G/'console/ARGS.json').write_text((H/'face75/console/ARGS.json').read_text());result={'mode':mode,'CSharp9Compiled':True,'shaderSHA256':json.loads((H/'face75/CPU_PREPARED75.json').read_text())['computeSHA256'],'captureSHA256':sha(G/'capture/RUN.cs.txt'),'targetFrames':target,'poseEvery':pose,'poolSlots':6,'readbackBytes':readbytes,'maxThreadsPerFrame':1600,'maxDispatchesPerFrame':1,'noNewShaderOrKernel':True,'rawFrameBytesTotalUpper':target*readbytes,'compressedFramesStored':True,'GPUExecuted':False,'normalExitAfterAllACK':True};(G/'CPU_PREPARED77.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
