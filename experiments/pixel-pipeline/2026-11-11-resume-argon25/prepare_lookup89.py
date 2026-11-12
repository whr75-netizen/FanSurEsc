"""Reproduce only the missing validity evidence, not an algorithm change.

Same89 shader/table and initial pulse input,64-frame cap. On a rejected GPU
result, preserve the already-completed readback in a separate invalid-input
record. No extra readback, successful marker or partial-colour acceptance.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face89/lookup64'
def main():
 for d in ['capture','build','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final'])
 s=(H/'face89/motion192/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face89\\motion192\\capture','resume-20261111\\face89\\lookup64\\capture').replace('face89-source-value-RGB192-','face89-invalid-lookup-input-').replace('motion40.FirstTarget,192,24,motion40.Snapshot','motion40.FirstTarget,64,16,motion40.Snapshot').replace('["plannedSourceFrames"]=192','["plannedSourceFrames"]=64')
 old='if(BitConverter.ToSingle(bytes,b89)<0)throw new InvalidOperationException("89 incomplete visible source lookup; reject whole frame");';assert s.count(old)==1
 new='''if(BitConverter.ToSingle(bytes,b89)<0){string stem89="FAILED_INPUT89-frame"+receipt["frame"].ToString();var diagnostic89=FrameBytes77.Encode(bytes);using(var fw89=new FileStream(Path.Combine(root77,stem89+".r77"),FileMode.CreateNew,FileAccess.Write,FileShare.Read)){fw89.Write(diagnostic89,0,diagnostic89.Length);fw89.Flush(true);}string hash89;using(var hd89=SHA256.Create())hash89=BitConverter.ToString(hd89.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();CreateOnly40.Text(Path.Combine(root77,stem89+".json"),new Obj40{["validCapture"]=false,["reason"]="89 rejected source lookup; diagnostic only",["localXY"]=new Arr40(xx,yy),["bytes"]=bytes.Length,["SHA256"]=hash89,["rawFile"]=stem89+".r77",["frameInfo"]=receipt}.ToString());throw new InvalidOperationException("89 incomplete source lookup preserved as invalid diagnostic; reject whole frame");}''';s=s.replace(old,new)
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/lookup89.dll')
 for mode in ['final','post/final']:
  t=(H/'face89/motion192'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face89\\motion192','resume-20261111\\face89\\lookup64');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'89.dll'))
 (G/'console/ARGS.json').write_text((H/'face89/motion192/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'targetFrames':64,'sameInitialInputAsFailed192':True,'sourceShaderOrAlgorithmChanged':False,'extraGPUReadback':False,'failureAlreadyCompletedReadbackPreserved':True,'invalidDiagnosticCannotBeSuccessfulCapture':True,'GPUExecuted':False};(G/'CPU_PREPARED_LOOKUP89.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
