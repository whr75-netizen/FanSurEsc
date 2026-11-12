"""Six distinct immutable owners read concurrently, each retaining one bounded ticket."""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face65'

def main():
 old=json.loads((H/'face64/capture/FAILED.json').read_text());assert old['Edit'] and old['restorationChecksPass'] and old['ownedResourcesReleased'] and old['pendingOwners']==0 and not old['errors']
 assert old['error'].startswith('System.TimeoutException:')
 root=G/'capture';root.mkdir(parents=True,exist_ok=True);assert not(root/'REQUEST.json').exists()
 s=(H/'face64/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face64\\capture','resume-20261111\\face65\\capture').replace('face64-native-motion-','face65-native-motion-')
 needle=' List<Plane> tasks;MotionContour40 motion40;'
 assert s.count(needle)==1
 s=s.replace(needle,' sealed class ReadCursor65 {public SourceOutline40 source;public List<Plane> planes;public int task,row;public volatile bool pending,done;}\n List<ReadCursor65> reads65;\n'+needle)
 start=s.index('   if(tasks==null){var r=producer.ROI;')
 end=s.index('\n  }catch(Exception e){report["error"]=e.ToString();Exit();}',start)
 block=s[start:end]
 build=block[:block.index('\n   if(inRead)')]
 # Reuse the exact13-field task constructor and per-frame metadata, but bind
 # every callback to its own immutable source rather than the mutable cursor.
 build=build.replace('if(tasks==null){','{').replace('Save("producer-acknowledged");}', 'reads65.Add(new ReadCursor65{source=producer,planes=tasks});frames36.Add(new Obj40{["frame"]=producer.CapturedFrame,["sourceId"]=producer.FrameKey,["QROI"]=report["QROI"],["frameInfo"]=producer.FrameInfo40});tasks=null;}')
 assert 'reads65.Add' in build
 replacement='''   if(reads65==null){reads65=new List<ReadCursor65>();foreach(var source65 in cohort){producer=source65;
'''+build+'''
    }report["frames"]=frames36;report["maxInFlightReads65"]=cohort.Length;Save("six-owner-readbacks-started");}
   foreach(var cursor65 in reads65){
    var source65=cursor65.source;
    if(cursor65.pending){if(!cursor65.done||source65.ConsumerPending40)continue;cursor65.pending=false;cursor65.done=false;var completed65=cursor65.planes[cursor65.task];cursor65.row+=Math.Max(1,16384/completed65.width);if(cursor65.row>=completed65.height){cursor65.task++;cursor65.row=0;}}
    if(cursor65.task==cursor65.planes.Count)continue;
    var plane65=cursor65.planes[cursor65.task];int row65=cursor65.row;int rows65=Math.Min(plane65.height-row65,Math.Max(1,16384/plane65.width));var rect65=new RectInt(plane65.ox,row65+plane65.oy,plane65.width,rows65);
    string name65="frame"+source65.CapturedFrame+"-"+plane65.name+"-row"+row65.ToString("D4")+".f32";cursor65.pending=true;cursor65.done=false;
    Action<byte[]> receive65=bytes=>{using(var file65=new FileStream(Path.Combine(Root,name65),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){file65.Write(bytes,0,bytes.Length);file65.Flush(true);}lock(ioSync){planes.Add(new Obj40{["frame"]=source65.CapturedFrame,["sourceId"]=source65.FrameKey,["name"]=plane65.name,["file"]=name65,["width"]=plane65.width,["height"]=plane65.height,["bottomRow"]=row65,["originX"]=plane65.ox,["originY"]=plane65.oy,["rows"]=rows65,["bytes"]=bytes.Length,["format"]="linear RGBAFloat32 little-endian; bottom-left storage"});}cursor65.done=true;};
    if(plane65.index<0)source65.RequestClassificationReadback40(rect65,receive65);else source65.RequestFieldReadback40(plane65.q,plane65.index,rect65,receive65);
   }
   if(reads65.All(c65=>!c65.pending&&c65.task==c65.planes.Count)){bool consecutive=cohort.Select((p0,i)=>p0.CapturedFrame==cohort[0].CapturedFrame+i).All(v=>v);report["actualConsecutive"]=consecutive;if(!consecutive)throw new InvalidOperationException("65 frame gap");packet=true;report["packetComplete"]=true;Save("six-source-packets-copied");Exit();return;}
'''
 s=s[:start]+replacement+s[end:]
 assert s.count('EditorApplication.timeSinceStartup-started>120')==1 and 'readonly ConsumerReads40 consumers32=new ConsumerReads40();' in s
 assert 'EvaluateForm115' not in s and 'BoundRun115' not in s
 (root/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');build=G/'build';build.mkdir(exist_ok=True);compile_unity_language(root/'RUN.cs.txt',build/'motion65.dll')
 result={'CSharp9Compiled':True,'frames':6,'planesEach':13,'maxOnePendingPerOwner':True,'maxPendingAcrossSixDistinctOwners':6,'maxReadBytesEach':262144,'maxInFlightByteUpper':6*262144,'sameGPUShadersAndDraws':True,'same120SecondDeadline':True,'same96MiBTextureUpper':True,'sourceIdentityCapturedPerCallback':True,'CPUChecks':'existing ConsumerReads40 one-ticket guard retained; per-callback immutable source, plane and row; COMPLETE requires every cursor and actual consecutive frames','GPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest()}
 (G/'CPU_PREPARED65.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 out=G/'final';out.mkdir(exist_ok=True)
 code=(H/'face64/final/RUN.cs.txt').read_text().replace('resume-20261111\\face64"','resume-20261111\\face65"').replace('resume-20261111\\face63\\capture\\INPUT_BEFORE.json','resume-20261111\\face64\\capture\\INPUT_BEFORE.json')
 assert 'const string Root=@"'+str(G)+'"' in code
 (out/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n');compile_unity_language(out/'RUN.cs.txt',build/'preflight65.dll')

if __name__=='__main__':main()
