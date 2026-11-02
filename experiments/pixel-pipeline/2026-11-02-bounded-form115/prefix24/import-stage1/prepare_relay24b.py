"""Keep the existing official one-command relay protocol; replace phase gates only."""
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H.parent/'import-stage1-b'
s=(H/'relay_step24.py').read_text()
s=s.replace("['ImportPrefix24','Stage1Prefix24']","['ReadDecode24','ImportPrefix24B','Stage1Prefix24']")
start=s.index("if mode=='ImportPrefix24':");end=s.index("code=source.read_text",start)
s=s[:start]+'''if mode=='ReadDecode24':
 source=H/'ReadDecode24.cs.txt';record=json.loads((H/'READ_CPU_COMPILE24.json').read_text());assert sha(source)==record['sources'][source.name]
 text=source.read_text();assert 'shader.Dispatch('not in text and 'AssetDatabase.ImportAsset('not in text and 'AssetDatabase.CreateFolder('not in text
elif mode=='ImportPrefix24B':
 source=H/'ImportPrefix24B.cs.txt';record=json.loads((ROOT/'import-stage1/IMPORT_FIX_CPU24.json').read_text());assert sha(source)==record['sources'][source.name]
 read=json.loads((H/'decode-output/DECODE_COMPLETE24.json').read_text());assert read['Status']=='complete'and read['SchemaEqual']and read['StateCollected']and read['MatchesCurrentBaseline']
 assert not(H/'decode-output/DECODE_FAILED24.json').exists()
 assert not(PROJECT/'Assets/EUnityValidation01/Direct24Prefix').exists()
 assert 'Dispatch('not in source.read_text()
else:
 source=ROOT/'STAGE1.command.cs.txt';case=json.loads((ROOT/'CASE.json').read_text())
 receipt=json.loads((H/'IMPORT_COMPLETE24.json').read_text());assert receipt['Status']=='complete'and receipt['StateEqual']and not receipt['NewErrors']
 assert not(H/'IMPORT_FAILED24.json').exists()
 assert sha(PROJECT/case['ShaderAssetPath'])==case['ShaderSha256']
 commands=json.loads((ROOT/'COMMANDS.json').read_text());assert sha(source)==commands['commands'][0]['SHA256']
 assert not(ROOT/'runs'/case['RunId']).exists(),'Stage claim/result already exists'
 text=source.read_text();assert text.count('shader.Dispatch(')==1 and 'Prefix24Host.Start(1,'in text
 for bad in ['EvaluateForm115','BoundRun115','AssetDatabase.ImportAsset','EnterPlaymode','WaitForCompletion']:assert bad not in text
''' +s[end:]
s=s.replace("0 if mode=='ImportPrefix24'else 1","1 if mode=='Stage1Prefix24'else 0")
with(OUT/'relay_step24b.py').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
print('Prepared independent explicit phases; automatic next0')
