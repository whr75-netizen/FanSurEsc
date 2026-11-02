from pathlib import Path
H=Path(__file__).resolve().parent
s=(H.parent/'import-stage1/relay_step24.py').read_text().replace("['ImportPrefix24','Stage1Prefix24']","['ReadMetadata24','ImportMetadata24','Stage1Prefix24','PostState24']")
a=s.index("if mode=='ImportPrefix24':");b=s.index('code=source.read_text',a)
s=s[:a]+'''files={'ReadMetadata24':'ReadMetadataState24.command.cs.txt','ImportMetadata24':'ImportMetadata24.command.cs.txt','Stage1Prefix24':'STAGE1_METADATA24.command.cs.txt','PostState24':'POST_STATE24.command.cs.txt'}
source=H/files[mode];compiled=json.loads((H/'METADATA_CPU24.json').read_text())
if mode=='PostState24':assert sha(source)==json.loads((H/'POST_CPU24.json').read_text())['sources'][source.name]
else:assert sha(source)==compiled['commands'][source.name]
case=json.loads((ROOT/'CASE.json').read_text());assert sha(ROOT/'CASE.json')=='0bd1a3c7fbc3e30791cbcaa000854a6fafd79598f34a730b8a7e2e2c0559027b'
if mode in ['ReadMetadata24','PostState24']:
 text=source.read_text();assert 'shader.Dispatch('not in text and 'AssetDatabase.ImportAsset('not in text
elif mode=='ImportMetadata24':
 read=json.loads((H/'decode-output/DECODE_COMPLETE24.json').read_text());assert read['Status']=='complete'and read['SchemaEqual']and read['StateCollected']and read['MatchesCurrentBaseline']
 assert not(H/'decode-output/DECODE_FAILED24.json').exists()
 assert not(PROJECT/'Assets/EUnityValidation01/Direct24Prefix').exists()
 assert 'shader.Dispatch('not in source.read_text()
else:
 receipt=json.loads((H/'IMPORT_COMPLETE24.json').read_text());assert receipt['Status']=='complete'and receipt['StateEqual']and not receipt['NewErrors']
 assert not(H/'IMPORT_FAILED24.json').exists()
 assert sha(PROJECT/case['ShaderAssetPath'])==case['ShaderSha256']
 assert not(ROOT/'runs'/case['RunId']).exists(),'Stage claim/result already exists'
 text=source.read_text();assert text.count('shader.Dispatch(')==1 and 'Prefix24Host.Start(1,'in text
 for bad in ['EvaluateForm115','BoundRun115','AssetDatabase.ImportAsset','EnterPlaymode','WaitForCompletion']:assert bad not in text
''' +s[b:]
s=s.replace("0 if mode=='ImportPrefix24'else 1","1 if mode=='Stage1Prefix24'else 0")
with(H/'relay_metadata24.py').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
