"""Finish our exact staged checkpoint after formatting new Unity .meta blanks."""
from pathlib import Path
import json,hashlib,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from archive96 import HERE,REPO,DEST,DOC,REL,ASSET,BASE,sha,git,preserve
assert git('rev-parse','HEAD').strip()==BASE
previous=json.loads((DEST/'ARTIFACTS96.json').read_text())['files'];expected={REL+'/'+x['path']for x in previous}|{REL+'/ARTIFACTS96.json',DOC,ASSET,ASSET+'.meta'};actual=set(git('diff','--cached','--name-only','-z').strip('\x00').split('\x00'));assert actual==expected
preserve();p=REPO/(ASSET+'.meta');before=p.read_bytes();backup=HERE/'META_BEFORE_FORMAT96.txt';assert not backup.exists();backup.write_bytes(before);text=before.decode('utf-8');assert 'guid: ddf6b0eb46bb0c048bc994b6df13671c'in text
after=('\n'.join(line.rstrip()for line in text.splitlines())+'\n').encode();p.write_bytes(after);(DEST/'ASSET_WholeEye96.compute.meta').write_bytes(after)
r=json.loads((DEST/'PRESERVATION96.json').read_text());r['metaSHA256']=sha(p);(DEST/'PRESERVATION96.json').write_text(json.dumps(r,indent=2)+'\n');(DEST/'finish_commit96.py').write_bytes(Path(__file__).read_bytes())
files=[{'path':x.relative_to(DEST).as_posix(),'SHA256':sha(x),'bytes':x.stat().st_size}for x in sorted(DEST.rglob('*'))if x.is_file()and x.name!='ARTIFACTS96.json'];(DEST/'ARTIFACTS96.json').write_text(json.dumps({'files':files},indent=2)+'\n')
git('add','--',REL,DOC,ASSET,ASSET+'.meta');expected={REL+'/'+x['path']for x in files}|{REL+'/ARTIFACTS96.json',DOC,ASSET,ASSET+'.meta'};actual=set(git('diff','--cached','--name-only','-z').strip('\x00').split('\x00'));assert actual==expected
for x in files:assert hashlib.sha256(git('show',':'+REL+'/'+x['path'],binary=True)).hexdigest()==x['SHA256']
assert git('diff','--cached','--numstat','--',DOC).strip().split('\t')[1]=='0';git('diff','--cached','--check','--',DOC,ASSET,ASSET+'.meta');print(git('commit','-m','Add isolated GPU whole-eye selection and validate against live source frames'))
assert not git('diff','--cached','--name-only').strip();preserve();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30
r={'commit':git('rev-parse','HEAD').strip(),'files':len(actual),'default':77,'user30Preserved':True,'protected32Preserved':True,'metaChange':'Only removed empty YAML value trailing spaces; GUID unchanged','push':False};(HERE/'COMMIT96.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
