"""Same official one-command transport, narrow phase allowlist, no auto-next."""
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
s=(ROOT/'import-stage1/relay_step24.py').read_text().replace("['ImportPrefix24','Stage1Prefix24']","['PreRW24','Reduce24','MidRW24','Write24','PostRW24']")
a=s.index("if mode=='ImportPrefix24':");b=s.index('code=source.read_text',a)
s=s[:a]+'''case=json.loads((ROOT/'CASE.json').read_text());run=ROOT/'runs'/case['RunId']
assert sha(ROOT/'CASE.json')=='0bd1a3c7fbc3e30791cbcaa000854a6fafd79598f34a730b8a7e2e2c0559027b'
def completed(stage):
 path=run/('stage-'+str(stage).zfill(2));r=json.loads((path/'COMPLETE.json').read_text())
 assert r['Success']and r['ExecutionKind']=='gpu-prefix'and r['StateEqual']and r['ResourcesReleased']and r['DispatchCalls']==1 and r['Stage']==stage and not r['Error']
 assert r['SourceId']==case['SourceId']and r['ShaderSha256']==case['ShaderSha256']and r['CaseSha256']==sha(ROOT/'CASE.json')
 assert not(path/'FAILED.json').exists()and not list(path.glob('PENDING-*.json'))
 for output in r['Outputs']:
  assert output['File']==output['Name']+'.bin'and sha(path/output['File'])==output['Sha256']
  spec=next(x for x in case['InputFiles']if x['Stage']==stage and x['Name']==output['Name']);assert output['Sha256']==spec['Sha256']
 return r
completed(2)
assert sha(PROJECT/case['ShaderAssetPath'])==case['ShaderSha256']
if mode in ['PreRW24','MidRW24','PostRW24']:
 phase={'PreRW24':'PRE','MidRW24':'MID','PostRW24':'POST'}[mode]
 if mode=='MidRW24':completed(3)
 if mode=='PostRW24':completed(4)
 source=H/(phase+'_STATE.command.cs.txt');row=next(x for x in json.loads((H/'CPU_COLLECTORS24.json').read_text())if x['name']=='ReduceWrite'+phase)
 assert sha(source)==row['sources'][source.name]
 assert 'shader.Dispatch('not in source.read_text()and 'AssetDatabase.ImportAsset('not in source.read_text()
else:
 stage=3 if mode=='Reduce24'else 4;completed(stage-1)
 source=ROOT/('STAGE'+str(stage)+'.command.cs.txt');row=next(x for x in json.loads((ROOT/'COMMANDS.json').read_text())['commands']if x['stage']==stage);assert sha(source)==row['SHA256']
 phase='pre'if stage==3 else'mid';state=json.loads((H/phase/'COMPLETE.json').read_text());assert state['StableEdit']and state['ShaderSha256']==case['ShaderSha256']
 if stage==3:assert state['KernelGroup']=='Reduce113:64,1,1;Write113:8,8,1'
 if stage==4:assert(H/'pre/STATE.json').read_bytes()==(H/'mid/STATE.json').read_bytes()
 assert not(run/('stage-'+str(stage).zfill(2))).exists(),'Prior attempt exists; never resubmit'
 text=source.read_text();assert text.count('shader.Dispatch(')==1 and 'Prefix24Host.Start('+str(stage)+','in text
 for bad in ['EvaluateForm115','BoundRun115','AssetDatabase.ImportAsset','EnterPlaymode','WaitForCompletion']:assert bad not in text
''' +s[b:]
s=s.replace("0 if mode=='ImportPrefix24'else 1","1 if mode in ['Reduce24','Write24']else 0")
with(H/'relay_rw24.py').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
