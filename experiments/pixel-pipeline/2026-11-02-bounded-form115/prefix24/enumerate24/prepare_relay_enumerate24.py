"""Reuse the official one-command relay transport with a stage2-only allowlist."""
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
s=(ROOT/'import-stage1/relay_step24.py').read_text().replace("['ImportPrefix24','Stage1Prefix24']","['PreEnumerate24','Stage2Prefix24','PostEnumerate24']")
a=s.index("if mode=='ImportPrefix24':");b=s.index('code=source.read_text',a)
s=s[:a]+'''case=json.loads((ROOT/'CASE.json').read_text());run=ROOT/'runs'/case['RunId'];prior=run/'stage-01'
assert sha(ROOT/'CASE.json')=='0bd1a3c7fbc3e30791cbcaa000854a6fafd79598f34a730b8a7e2e2c0559027b'
r=json.loads((prior/'COMPLETE.json').read_text());assert r['Success']and r['ExecutionKind']=='gpu-prefix'and r['StateEqual']and r['ResourcesReleased']and r['DispatchCalls']==1
assert r['SourceId']==case['SourceId']and r['ShaderSha256']==case['ShaderSha256']and r['CaseSha256']==sha(ROOT/'CASE.json')
assert not(prior/'FAILED.json').exists()and not list(prior.glob('PENDING-*.json'))
for output in r['Outputs']:
 assert output['File']==output['Name']+'.bin'and sha(prior/output['File'])==output['Sha256']
assert sha(PROJECT/case['ShaderAssetPath'])==case['ShaderSha256']
if mode in ['PreEnumerate24','PostEnumerate24']:
 phase='PRE'if mode=='PreEnumerate24'else'POST';source=H/(phase+'_STATE.command.cs.txt')
 row=next(x for x in json.loads((H/'CPU_COLLECTOR24.json').read_text())if x['name']=='Enumerate'+phase)
 assert sha(source)==row['sources'][source.name]
 text=source.read_text();assert 'shader.Dispatch('not in text and 'AssetDatabase.ImportAsset('not in text
else:
 source=ROOT/'STAGE2.command.cs.txt';row=next(x for x in json.loads((ROOT/'COMMANDS.json').read_text())['commands']if x['stage']==2);assert sha(source)==row['SHA256']
 state=json.loads((H/'pre/COMPLETE.json').read_text());assert state['StableEdit']and state['KernelGroup']=='64,1,1'and state['ShaderSha256']==case['ShaderSha256']
 assert not(run/'stage-02').exists(),'Prior stage2 attempt exists: inspect; no replay'
 text=source.read_text();assert text.count('shader.Dispatch(')==1 and 'Prefix24Host.Start(2,'in text
 for bad in ['EvaluateForm115','BoundRun115','AssetDatabase.ImportAsset','EnterPlaymode','WaitForCompletion']:assert bad not in text
''' +s[b:]
s=s.replace("0 if mode=='ImportPrefix24'else 1","1 if mode=='Stage2Prefix24'else 0")
with(H/'relay_enumerate24.py').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
