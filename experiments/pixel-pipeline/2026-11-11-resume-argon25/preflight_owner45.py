from pathlib import Path
import json,sys,subprocess,hashlib
import relay33
H=Path(__file__).resolve().parent;G=H/'face45/preflight';R=relay33.PROJECT
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='474de71131ddf4d31185b28d9ed2b3971887697b'
users=json.loads((H/'RESUME_STATUS.json').read_text())['userTrackedFiles'];assert len(users)==30 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in users.items())
p=G/'final';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists();(p/'RUN.cs.txt').write_text((H/'face45/final/RUN.cs.txt').read_text().replace('face45\\final','face45\\preflight\\final'),encoding='utf-8',newline='\n');relay33.G=G;sys.argv=[sys.argv[0],'final'];relay33.main();r=json.loads((p/'REPLY.json').read_text())['result'];c=r.get('structuredContent')or next(json.loads(x['text'])for x in r['content']if x.get('type')=='text');assert c['success'],c.get('error');print((p/'PUBLIC_AFTER.txt').read_text())
