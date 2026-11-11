from pathlib import Path
import sys,json,hashlib
import relay33
assert sys.argv[1]in ['import','capture','final','console'];root=Path(__file__).resolve().parent/'face40';case='authored'if'--authored'in sys.argv else'directed'if'--directed'in sys.argv else'motion'if'--motion'in sys.argv else'compat'if'--compat'in sys.argv else'';relay33.G=root/case
if sys.argv[1]=='capture':
 imported=root/'compat/import/COMPLETE.json'if case in ['motion','directed']else relay33.G/'import/COMPLETE.json';assert imported.exists(),'Successful actual import marker required before capture submission'
 if case=='authored':
  control=json.loads((root/'directed/capture/COMPLETE.json').read_text());assert control['restorationChecksPass']and control['ownedResourcesReleased']and control['pendingOwners']==0
  assert hashlib.sha256((relay33.PROJECT/'Assets/EUnityValidation01/SourceBoundary40Authored/GeoContour40Authored.shader').read_bytes()).digest()==hashlib.sha256((root/'authored/shaders/GeoContour40Authored.shader').read_bytes()).digest()
 if case in ['motion','directed']:
  control=json.loads((root/('motion'if case=='directed'else'compat')/'capture/COMPLETE.json').read_text());assert control['restorationChecksPass']and control['ownedResourcesReleased']and control['pendingOwners']==0
  for name in ['GeoContour40.shader','GeoResolve40.compute']:assert hashlib.sha256((relay33.PROJECT/'Assets/EUnityValidation01/SourceBoundary40'/name).read_bytes()).digest()==hashlib.sha256((root/'shaders'/name).read_bytes()).digest()
relay33.main()
r=json.loads((relay33.G/sys.argv[1]/'REPLY.json').read_text());result=r.get('result',{}).get('structuredContent')
if not result:
 for block in r.get('result',{}).get('content',[]):
  if block.get('type')=='text':
   try:result=json.loads(block['text'])
   except ValueError:continue
   if isinstance(result,dict)and'success'in result:break
assert isinstance(result,dict)and result.get('success')is True,{'success':result.get('success')if isinstance(result,dict)else None,'error':result.get('error')if isinstance(result,dict)else'Unrecognized result; inspect original; no retry'}
