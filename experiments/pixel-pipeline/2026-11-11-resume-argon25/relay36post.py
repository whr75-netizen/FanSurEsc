from pathlib import Path
import sys,contextlib,io,json
import relay33
assert sys.argv[1]in ['final','console'];relay33.G=Path(__file__).resolve().parent/'face36/post'
if sys.argv[1]=='console':
 with contextlib.redirect_stdout(io.StringIO()):relay33.main()
 result=json.loads((relay33.G/'console/REPLY.json').read_text());data=json.loads(result['result']['content'][0]['text']);print(json.dumps({'success':data['success'],'count':data['data']['totalCount'],'timestamps':sorted(set(r['timestamp']for r in data['data']['logs']))}))
else:relay33.main()
