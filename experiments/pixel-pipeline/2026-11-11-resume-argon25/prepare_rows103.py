"""Prepare private CPU row work; retain actual91 palette and existing GPU work."""
from pathlib import Path
import json,re,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face103'

def main():
 name=sys.argv[1]if len(sys.argv)>1 else'rows64';count=int(sys.argv[2])if len(sys.argv)>2 else 64;poseEvery=120 if count>64 else 24;assert 1<=count<=1800;old=H/'face100/reasons32';root=G/name;(G/'build').mkdir(parents=True,exist_ok=True)
 for d in ['capture','preflight/final','post/final']:(root/d).mkdir(parents=True,exist_ok=True)
 assert not(root/'capture/REQUEST.json').exists();s=(old/'capture/RUN.cs.txt').read_text().replace(str(old),str(root)).replace('face100-reasons-','face103-rows-').replace('SourceFootprint100/SourceFootprint100.shader','SourceFootprint101B/SourceFootprint101B.shader')
 def once(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 once('motion40.FirstTarget,32,24,motion40.Snapshot','motion40.FirstTarget,'+str(count)+','+str(poseEvery)+',motion40.Snapshot');once('["plannedSourceFrames"]=32','["plannedSourceFrames"]='+str(count))
 if count>64:once('EditorApplication.timeSinceStartup-started>120)throw new TimeoutException("95 bounded source observation120s CPU-IO limit; no retry or time-based resource release")','EditorApplication.timeSinceStartup-started>900)throw new TimeoutException("103 planned30s simulated observation900s total CPU-IO budget; unchanged GPU completion ownership; no retry or time-based resource release")')
 for source,target in [('JointLine99C.cs','JointLine103.cs'),('CurveOpacity99.cs','CurveOpacity103.cs')]:
  a=(H/source).read_text();b=(H/target).read_text();once(a[a.index('namespace LineGeometry97'):],b[b.index('namespace LineGeometry97'):])
 once('var collector98=new LineGeometry97.CurveOpacity98(scene,raster);','var collector98=new LineGeometry97.CurveOpacity98(scene,raster);var strips103=new List<LineGeometry97.Strip103>();')
 once('raster.Add(new Triangle97(xy[0],xy[1],xy[3],z[0],z[1],z[3],new P97(),new P97(),new P97(),null){xyError=uncertainty97},edge,0,1,1);','strips103.Add(new LineGeometry97.Strip103(new Triangle97(xy[0],xy[1],xy[3],z[0],z[1],z[3],new P97(),new P97(),new P97(),null){xyError=uncertainty97},edge,0,1,1));')
 once('raster.Add(new Triangle97(xy[0],xy[3],xy[2],z[0],z[3],z[2],new P97(),new P97(),new P97(),null){xyError=uncertainty97},edge,0,1,0);','strips103.Add(new LineGeometry97.Strip103(new Triangle97(xy[0],xy[3],xy[2],z[0],z[3],z[2],new P97(),new P97(),new P97(),null){xyError=uncertainty97},edge,0,1,0));')
 once('  raster.FinishClearance99();','  var rowStats103=LineGeometry97.RowParallel103.Run(scene,raster,collector98,strips103);if(!rowStats103.allWorkersCompleted||!rowStats103.queryViewsReleased)throw new InvalidOperationException("103 incomplete CPU source work");FrameInfo40["profile103"]=new Obj40{["workers"]=rowStats103.workers,["splitRow"]=rowStats103.splitRow,["topCandidateCells"]=rowStats103.topCandidateCells,["bottomCandidateCells"]=rowStats103.bottomCandidateCells,["mainRowWallMs"]=rowStats103.mainMs,["workerRowWallMs"]=rowStats103.workerMs,["joinWallMs"]=rowStats103.joinMs,["rowPhaseWallMs"]=rowStats103.totalMs,["allCPUWorkCompleted"]=rowStats103.allWorkersCompleted,["queryViewsReleased"]=rowStats103.queryViewsReleased,["noUnityAPIsOnWorker"]=true};raster.FinishClearance99();')
 once('FrameInfo40["rawSourcePlaneCount100"]=15;','FrameInfo40["sourceColourProducer103"]="existing91, rejected102 address candidate not loaded";FrameInfo40["rawSourcePlaneCount100"]=15;')
 body=(H/'RowParallel103.cs').read_text();body=body[body.index('namespace LineGeometry97'):]
 for a,b in [('Stopwatch','System.Diagnostics.Stopwatch'),('TaskCreationOptions','System.Threading.Tasks.TaskCreationOptions'),('TaskScheduler','System.Threading.Tasks.TaskScheduler'),('CancellationToken','System.Threading.CancellationToken'),('Task','System.Threading.Tasks.Task')]:body=re.sub(r'(?<![A-Za-z0-9_.])'+a+r'\b',b,body)
 s+='\n'+body;assert'EvaluateForm115'not in s and'BoundRun115'not in s and s.count('cmd.RequestAsyncReadback(readbackPack93.rt')==1 and'SourceValue91/SourceValue91.shader'in s and'SourceValue101/SourceValue101.shader'not in s
 p=root/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/(name+'.dll'))
 for mode in ['preflight','post']:
  s=(old/mode/'final/RUN.cs.txt').read_text().replace('const string Root=@"'+str(old/mode)+'";','const string Root=@"'+str(root/mode)+'";')
  if mode=='post':s=s.replace(str(old/'capture/INPUT_BEFORE.json'),str(root/'capture/INPUT_BEFORE.json'))
  p=root/mode/'final/RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,G/'build'/(name+'-'+mode+'.dll'))
 print('103 full external runner CPU compiled; no new shader/compute/Assets/import or Unity execution')
if __name__=='__main__':main()
