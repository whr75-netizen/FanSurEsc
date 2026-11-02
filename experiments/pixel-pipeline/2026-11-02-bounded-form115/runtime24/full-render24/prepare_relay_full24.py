from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent.parent/'prefix24'
s=(P/'import-stage1/relay_step24.py').read_text().replace("['ImportPrefix24','Stage1Prefix24']","['ImportFull24','CaptureFull24']")
a=s.index("if mode=='ImportPrefix24':");b=s.index('code=source.read_text',a)
s=s[:a]+'''if mode=='ImportFull24':
 source=H/'RUN_ImportFull24.cs.txt';record=json.loads((H/'CPU_IMPORT24.json').read_text());assert sha(source)==record['sources'][source.name]
 assert not(PROJECT/'Assets/EUnityValidation01/Direct24Geometry').exists(),'Existing import must be inspected'
 assert 'shader.Dispatch('not in source.read_text()
else:
 source=H/'RUN_CaptureFull24.cs.txt';record=json.loads((H/'CPU_COMPILE_FULL24.json').read_text());assert record['cpuCSharpSuccess']and sha(source)==record['commandSHA256']
 imported=json.loads((H/'import/COMPLETE.json').read_text());assert imported['Status']=='complete'and imported['StateEqual']and not imported['Error']
 assert not(H/'import/FAILED.json').exists()
 assert sha(PROJECT/'Assets/EUnityValidation01/Direct24Geometry/ForwardEye113_Geometry24.compute')==record['shaderSHA256']
 assert not(H/'CAPTURE_STARTED76.json').exists(),'Existing execution: inspect, never replay'
 text=source.read_text();assert 'if(captured76>=1)'in text
 for bad in ['EvaluateForm115','BoundRun115','Shader.SetGlobalBuffer(','SaveAssets(','ClearDirty(','File.Delete(','File.Move(']:assert bad not in text
''' +s[b:]
s=s.replace("0 if mode=='ImportPrefix24'else 1","0")
# This value is an operational scope label only; capture is a normal live graph,
# not one compute dispatch. Do not represent it as a one-dispatch operation.
s=s.replace("'maxDispatches':0,","'operationScope':('shader-only import'if mode=='ImportFull24'else'one Play/one captured open state; runtime graph dispatches'),")
with(H/'relay_full24.py').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
