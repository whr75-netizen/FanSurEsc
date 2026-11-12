"""Persist complete Library identities and report unsupported local xattrs."""
from pathlib import Path
import sys,json,subprocess
H=Path(__file__).resolve().parent
payload=json.load(sys.stdin);result=payload['result'];data=result.get('structuredContent')
if not data:
 for part in result.get('content',[]):
  if part.get('type')=='text':
   try:data=json.loads(part['text']);break
   except ValueError:pass
rows=data['results'];assert len(rows)==len(payload['localPaths']);metadata=[]
for path,row in zip(payload['localPaths'],rows):
 assert row['status']=='succeeded'and row.get('library_file_id')
 p=subprocess.run([sys.executable,str(H/'face96/library-current96/library_file_transfer.py'),'apply-xattrs',path,row['library_file_id']],input=json.dumps(row.get('xattrs',[])),text=True,capture_output=True)
 metadata.append({'originalLocalPath':path,'library_file_id':row['library_file_id'],'file_id':row.get('file_id'),'version':row.get('current_version_number'),'libraryPath':row.get('path'),'localXattrsApplied':p.returncode==0,'metadataHelperExit':p.returncode,'metadataHelperOutput':p.stdout,'metadataHelperError':p.stderr})
out=H/'face105/DELIVERY105.json';assert not out.exists()
with out.open('x',encoding='utf-8')as f:json.dump({**payload,'identityMetadata':metadata},f,indent=2)
print(json.dumps([{k:v for k,v in row.items()if k not in['metadataHelperOutput','metadataHelperError']}for row in metadata],indent=2))
