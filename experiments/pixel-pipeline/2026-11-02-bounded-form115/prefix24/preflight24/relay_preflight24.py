"""One read-only official Unity command. No import, dispatch or retry."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time
H=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
PID=22952
assert not(H/'REQUEST24.json').exists(),'Prior outcome must be inspected; no replay'
assert not(H/'EDITOR_STATE24.json').exists(),'Preflight already has an outcome'
valid=False
for path in Path(r'C:\Users\15352\.unity\mcp\connections').glob('*.json'):
 try:
  d=json.loads(path.read_text(encoding='utf-8-sig'))
  valid|=Path(d.get('project_path',''))==PROJECT and d.get('editor_pid')==PID
 except (KeyError,ValueError):pass
assert valid,'Current official connection absent'
source=H/'ReadPrefix24.cs.txt';code=source.read_text(encoding='utf-8')
for bad in ['Dispatch(', 'AsyncGPUReadback', 'ImportAsset', 'Refresh(', 'SaveAssets', 'SaveAssetIfDirty', 'EnterPlaymode', 'ExitPlaymode', 'Destroy', 'SetGlobal', 'System.Reflection', 'InputSystem.settings=']:
 assert bad not in code,bad
def scrub(v):
 if isinstance(v,dict):return{k:('[redacted]'if any(x in k.lower()for x in ['token','secret','password','credential','nonce'])else scrub(x))for k,x in v.items()}
 if isinstance(v,list):return[scrub(x)for x in v]
 return v
def save(name,v):
 with(H/name).open('x',encoding='utf-8')as f:json.dump(scrub(v),f,ensure_ascii=False,indent=2)
args=[r'C:\Users\15352\.unity\relay\relay_win.exe','--mcp','--instance-id',str(PID),'--project-path',str(PROJECT),'--name','Codex Shop Read Capture']
p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
q=queue.Queue();counter=0
def reader():
 for line in p.stdout:
  try:q.put(json.loads(line))
  except ValueError:pass
threading.Thread(target=reader,daemon=True).start()
threading.Thread(target=lambda:[None for _ in p.stderr],daemon=True).start()
def rpc(method,params):
 global counter
 counter+=1;number=counter
 p.stdin.write(json.dumps({'jsonrpc':'2.0','id':number,'method':method,'params':params})+'\n');p.stdin.flush()
 until=time.monotonic()+40
 while time.monotonic()<until:
  try:reply=q.get(timeout=.5)
  except queue.Empty:continue
  if reply.get('id')==number:return reply
 raise TimeoutError('Outcome uncertain; no resubmission')
try:
 init=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}})
 assert'error'not in init
 p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
 inv=rpc('tools/list',{}).get('result',{}).get('tools',[])
 assert any(t['name']=='Unity_RunCommand'for t in inv)
 save('REQUEST24.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':PID,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'purpose':'read-only preflight','dispatches':0})
 reply=rpc('tools/call',{'name':'Unity_RunCommand','arguments':{'Code':code,'Title':'Read current prefix24 preflight state'}})
 save('REPLY24.json',reply)
 result=reply.get('result',{});value=result.get('structuredContent')
 if value is None:
  try:value=json.loads(next(c['text']for c in result.get('content',[])if c.get('type')=='text'))
  except(ValueError,StopIteration):value={'unparsed':True,'isError':result.get('isError')}
 print(json.dumps(scrub(value),ensure_ascii=False),flush=True)
except Exception as e:
 save('ERROR24.json',{'error':str(e),'uncertain':isinstance(e,TimeoutError)});print(str(e),flush=True)
finally:
 p.stdin.close()
 try:p.wait(timeout=5);print(json.dumps({'relayEOF':True,'exitCode':p.returncode}),flush=True)
 except subprocess.TimeoutExpired:print(json.dumps({'ownedRelayStillRunning':p.pid,'notKilled':True}),flush=True)
