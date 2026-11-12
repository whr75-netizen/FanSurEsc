"""Remove one idle observer tick per completed bounded read, not the120s deadline."""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face64'

def main():
 old=json.loads((H/'face63/capture/FAILED.json').read_text())
 assert old['restorationChecksPass'] and old['ownedResourcesReleased'] and old['pendingOwners']==0 and old['Edit'] and not old['errors']
 assert old['error'].startswith('System.TimeoutException: Bounded one-frame observation')
 root=G/'capture';root.mkdir(parents=True,exist_ok=True);assert not(root/'REQUEST.json').exists()
 s=(H/'face63/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face63\\capture','resume-20261111\\face64\\capture').replace('face63-native-motion-','face64-native-motion-')
 before='if(inRead){if(!readDone||producer.ConsumerPending40)return;inRead=false;readDone=false;var completed=tasks[task];y+=Math.Max(1,16384/completed.width);if(y>=completed.height){task++;y=0;}return;}'
 after=before[:-8]+'}'
 assert before.endswith('return;}') and after.endswith('if(y>=completed.height){task++;y=0;}}')
 assert s.count(before)==1;s=s.replace(before,after)
 assert s.count('EditorApplication.timeSinceStartup-started>120')==1
 assert 'EvaluateForm115' not in s and 'BoundRun115' not in s
 (root/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');build=G/'build';build.mkdir(exist_ok=True);compile_unity_language(root/'RUN.cs.txt',build/'motion64.dll')
 # A completed read is consumed once. A pending callback/consumer retains its
 # request and resources. Submit at most one following request in this tick.
 cases=[]
 for done in [False,True]:
  for consumer in [False,True]:
   for last in [False,True]:
    blocked=not done or consumer
    consumed=not blocked
    next_submitted=consumed and not last
    exit_requested=consumed and last
    assert not(next_submitted and exit_requested)
    assert blocked or int(next_submitted)+int(exit_requested)==1
    cases.append({'done':done,'consumerPending':consumer,'last':last,'consumed':consumed,'nextSubmitted':next_submitted,'exit':exit_requested})
 result={'CSharp9Compiled':True,'CPUReadStates':cases,'sameDeadlineSeconds':120,'sameMaxInFlightReadbacks':1,'sameMaxReadBytes':262144,'sameSixFrameOwnedByteUpper':100663296,'sameShadersDispatchesAndInput':True,'noTimeoutExtension':True,'previousFailurePreserved':str(H/'face63/capture/FAILED.json'),'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'GPUExecuted':False}
 (G/'CPU_PREPARED64.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 # Root is a directory, not the complete final filename. Keep all existing
 # receipts create-only, including the earlier mis-targeted read-only check.
 out=G/'final';out.mkdir(exist_ok=True)
 code=(H/'face62/final/RUN.cs.txt').read_text().replace('resume-20261111\\face62"','resume-20261111\\face64"')
 needle='File.ReadAllText(Path.Combine(Root,"capture","INPUT_BEFORE.json"))'
 assert code.count(needle)==1
 code=code.replace(needle,'File.ReadAllText(@"'+str(H/'face63/capture/INPUT_BEFORE.json')+'")')
 assert 'const string Root=@"'+str(G)+'"' in code
 (out/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n')
 compile_unity_language(out/'RUN.cs.txt',build/'preflight64.dll')

if __name__=='__main__':main()
