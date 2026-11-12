"""Six actual consecutive normal-input frames:3 walk,3 turn; fixed memory/read bounds."""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face63'
def main():
 p=G/'capture';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists()
 s=(H/'face62/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face62\\capture','resume-20261111\\face63\\capture').replace('face62-parent-outline-','face63-native-motion-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('cohort=new SourceOutline40[1];try{for(int i=0;i<1;i++)','cohort=new SourceOutline40[6];try{for(int i=0;i<6;i++)')
 rep('producers.Length!=1','producers.Length!=6');rep('56 one capture on one view required','63 six normal frames on one view required');rep('["plannedSourceFrames"]=1','["plannedSourceFrames"]=6')
 # Keep only fields needed for final RGB, primitive/UV/layer, native before and
 # actual eye children. Do not repeat fine8x/Q diagnostic readbacks per frame.
 a='var ec47=producer.FieldExtent40(false,16);tasks.Add(new Plane(false,16,"currentColour47",ec47.x,ec47.y));';rep(a,'')
 a='foreach(int field58 in new[]{0,1,4,5}){var ex58=producer.FieldExtent40(false,field58);tasks.Add(new Plane(false,field58,new[]{"nativeOutlineOn58","nativeOutlineMetaOn58","nativeOutlineOff58","nativeOutlineMetaOff58"}[field58<2?field58:field58-2],ex58.x,ex58.y));}';rep(a,'')
 a='foreach(int q58 in new[]{3,4}){var ex58=producer.FieldExtent40(true,q58);tasks.Add(new Plane(true,q58,q58==3?"initialAppliedQ58":"initialSurfaceMeta58",ex58.x,ex58.y));}';rep(a,'')
 rep('new[]{20,21,22,23,24,25,26,27}','new[]{22,23,24,25,26,27}')
 needle=' public int CapturedFrame=>frame;'
 rep(needle,' public long OwnedBytesUpper63=>owned.Where(t=>t!=null&&t.rt).Sum(t=>(long)t.rt.width*t.rt.height*16);public int OwnedCount63=>owned.Count;\n'+needle)
 needle='frame=Time.frameCount;FrameKey='
 rep(needle,'if(OwnedBytesUpper63>16L*1024*1024)throw new InvalidOperationException("63 per-frame owned RT upper bound exceeded; no commands submitted");\n  '+needle)
 rep('report["frameInfo"]=producer.FrameInfo40;','report["peakOwnedTextureBytesUpper63"]=cohort.Sum(p63=>p63.OwnedBytesUpper63);report["peakOwnedRTCount63"]=cohort.Sum(p63=>p63.OwnedCount63);report["shortRegressionOnly63"]=true;report["frameInfo"]=producer.FrameInfo40;')
 s=s.replace('Save("one-packet-copied")','Save("six-source-packets-copied")')
 assert 'EvaluateForm115'not in s and'BoundRun115'not in s
 (p/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');build=G/'build';build.mkdir(exist_ok=True);compile_unity_language(p/'RUN.cs.txt',build/'motion63.dll')
 result={'fullExternalCSharp9Compiled':True,'actualFramesPlanned':6,'normalInputStages':['walk','walk','walk','turn','turn','turn'],'perInstanceOwnedTextureByteUpper':16*1024*1024,'allSixOwnedTextureByteUpper':6*16*1024*1024,'readbackMaxBytesPerRequest':262144,'readPlanesPerFrame':13,'noInputSettingsReplacement':True,'noManualRenderOrPoseReset':True,'sameExistingShaders':True,'longTermStabilityClaimed':False,'GPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest()};(G/'CPU_PREPARED63.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
