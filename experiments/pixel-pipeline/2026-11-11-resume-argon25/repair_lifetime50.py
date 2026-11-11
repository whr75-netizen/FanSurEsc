from pathlib import Path
import json,difflib,sys
from prepare_final41 import compile_unity_language
import test_carrier43 as compiler
H=Path(__file__).resolve().parent;G=H/'face50';B=G/'build';B.mkdir(parents=True,exist_ok=True)
def main():
 original=(H/'face49/capture/RUN.cs.txt').read_text();start=original.index(' void RecordFinal41(RenderGraph graph,ContextContainer context){');end=original.index(' void ProduceFinal41(UnsafeGraphContext context)',start);old=original[start:end];needle='   using(var b=graph.AddUnsafePass<Data>("42 end barrier after actual native presentation"';a=old.index(needle);b=old.index('\n  }catch(Exception e){Fail(e);}',a);barrier=old[a:b];candidate=old[:a]+old[b:];candidate=candidate.replace(' void RecordFinal41(', ' void RecordFinalCandidate50(',1)
 wrapper=''' bool completionRecorded50;
 void RecordFinal41(RenderGraph graph,ContextContainer context){
  if(!RequiresFinal41)return;
  CompletionScope50.Record(()=>RecordFinalCandidate50(graph,context),Fail,()=>RecordCompletion50(graph));
 }
 void RecordCompletion50(RenderGraph graph){
  if(completionRecorded50||submission==null||!submission.CommandsPossible)return;
  completionRecorded50=true; // Mark before an uncertain graph API; never resubmit.
'''+barrier+'''
 }
'''
 # Remove the candidate's swallowing catch: the outer scope owns failure+finally.
 candidate=candidate.replace('  try{\n','  {\n',1).replace('  }catch(Exception e){Fail(e);}','  }',1)
 code=original[:start]+wrapper+candidate+original[end:]+'\n'+(H/'CompletionScope50.cs').read_text().replace('using System;','')
 # HeadLocal367.Initialise explicitly sets samplesOnly=true. That selects the
 # samples pass, while DeferredEyes calls EyeRenderer367.Dispatch itself. The
 # early feature's candidateEnabled/samplesOnly flags are not final production
 # readiness. Require the actual direct-dispatch host/full/current RT instead.
 token='||!eye.candidateEnabled||eye.samplesOnly||eye.full!=host41.head';assert code.count(token)==1;code=code.replace(token,'||eye.full!=host41.head||host41.headEyes!=eye||!host41.headEnabled||!host41.headReady')
 p=G/'REVIEW_ONLY_PATCHED_SOURCE50.cs.txt';p.write_text('// REVIEW ONLY. Original49 STARTED guard remains locked. No live source replacement.\n'+code,encoding='utf-8',newline='\n');compile_unity_language(p,B/'lifetime50.dll');(G/'lifetime50.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),code.splitlines(True),fromfile='executed49/RUN.cs.txt',tofile='review-only50/RUN.cs.txt')),encoding='utf-8',newline='\n')
 s=original.index('public sealed class Submission40 {');depth=0;e=None
 for i in range(original.index('{',s),len(original)):
  if original[i]=='{':depth+=1
  if original[i]=='}':
   depth-=1
   if depth==0:e=i+1;break
 assert e is not None
 text='using System;\n'+original[s:e]+'\n'+(H/'CompletionScope50.cs').read_text().replace('using System;','')+'\n'+(H/'CompletionTests50.cs').read_text().replace('using System;','');p=B/'unit50.cs.txt';p.write_text(text,encoding='utf-8');compiler.B=B;result=compiler.compile_run('unit50',str(p.relative_to(H)));result['fullPatchedSourceCPU_CSharp9']=True;result['patchAppliedToRunning49']=False;result['futureModeGuardMatchesDirectHeadDispatch']=True;(G/'CPU_LIFETIME50.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
