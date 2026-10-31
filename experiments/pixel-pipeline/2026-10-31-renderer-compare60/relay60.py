"""Official existing Unity relay. One named request, no automatic re-execution."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time,sys
R=Path(__file__).resolve().parent;P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game');PID=28304
mode=sys.argv[1];source=R/('RUN_'+mode+'.cs.txt');assert source.is_file()
marker=R/(mode+'_REQUEST.json');assert not marker.exists(),'Outcome must be inspected; this driver never repeats a request'
info=json.loads(Path(f'C:/Users/15352/.unity/mcp/connections/bridge-9eee322a-{PID}.json').read_text(encoding='utf-8-sig'))
assert info['editor_pid']==PID and Path(info['project_path'])==P
def save(name,v):(R/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
argv=['C:/Users/15352/.unity/relay/relay_win.exe','--mcp','--instance-id',str(PID),'--project-path',str(P),'--name','Codex Shop Read Capture']
p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf8',creationflags=subprocess.CREATE_NO_WINDOW)
q=queue.Queue();counter=0
def read():
 for line in p.stdout:
  try:q.put(json.loads(line))
  except json.JSONDecodeError:pass
threading.Thread(target=read,daemon=True).start();threading.Thread(target=lambda:[None for _ in p.stderr],daemon=True).start()
def rpc(method,params):
 global counter
 counter+=1;number=counter;p.stdin.write(json.dumps({'jsonrpc':'2.0','id':number,'method':method,'params':params})+'\n');p.stdin.flush();end=time.monotonic()+55
 while time.monotonic()<end:
  try:r=q.get(timeout=.5)
  except queue.Empty:continue
  if r.get('id')==number:return r
 raise TimeoutError('Outcome uncertain: inspect checkpoint files before any further action')
def unwrap(r):
 x=r.get('result',{})
 if x.get('structuredContent')is not None:return x['structuredContent']
 try:return json.loads(next(c['text']for c in x.get('content',[])if c.get('type')=='text'))
 except (StopIteration,json.JSONDecodeError):return r
try:
 init=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}});assert'error'not in init
 p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
 save(mode+'_CONSOLE_BEFORE.json',unwrap(rpc('tools/call',{'name':'Unity_GetConsoleLogs','arguments':{'maxEntries':70,'includeStackTrace':True}})))
 save(marker.name,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':PID,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
 reply=unwrap(rpc('tools/call',{'name':'Unity_RunCommand','arguments':{'Code':source.read_text(encoding='utf8'),'Title':'Isolated renderer60 approved single Play comparison and restoration: '+mode}}));save(mode+'_REPLY.json',reply)
 d=reply.get('data',{});print(json.dumps({'mode':mode,'success':reply.get('success'),'error':reply.get('error'),'compiled':d.get('isCompilationSuccessful'),'executed':d.get('isExecutionSuccessful'),'compileLogs':d.get('compilationLogs'),'logs':d.get('executionLogs')},ensure_ascii=False),flush=True)
 save(mode+'_CONSOLE_AFTER.json',unwrap(rpc('tools/call',{'name':'Unity_GetConsoleLogs','arguments':{'maxEntries':70,'includeStackTrace':True}})))
except Exception as e:save(mode+'_ERROR.json',{'error':str(e),'uncertain':isinstance(e,TimeoutError)});print(str(e),flush=True)
finally:
 p.stdin.close()
 try:p.wait(timeout=5);print(json.dumps({'relayEOF':True,'exitCode':p.returncode}),flush=True)
 except subprocess.TimeoutExpired:print(json.dumps({'ownedRelayStillRunning':p.pid,'notKilled':True}),flush=True)
