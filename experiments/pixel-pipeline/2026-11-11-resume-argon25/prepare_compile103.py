"""Compile the entire private runner without instantiating its capture owner."""
from pathlib import Path
import re
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent
root=H/'face103/compileB/details'
root.mkdir(parents=True,exist_ok=True)
assert not(root/'REQUEST.json').exists()
s=(H/'face103/rows64B/capture/RUN.cs.txt').read_text(encoding='utf-8')
assert s.count('internal class CommandScript : IRunCommand {')==1
s=re.sub(r'\bCommandScript\b','DormantCapture103',s)
s=s.replace('internal class DormantCapture103 : IRunCommand {','internal class DormantCapture103 {')
s+='''
namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {
internal class CommandScript : IRunCommand {
 public void Execute(ExecutionResult result) {
  UnityEngine.Debug.Log("103 full source compilation only: capture owner not instantiated; no Play, GPU or state mutation");
 }
}
}
'''
assert s.count(': IRunCommand')==1
p=root/'RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n')
compile_unity_language(p,H/'face103/build/compileB.dll')
print('103 compile-only source prepared')
