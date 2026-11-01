"""Single exact official relay command; journal before dispatch, no automatic retries."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time,sys
HERE=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
mode=sys.argv[1]
assert mode in ('Read76','Import76','Compile76','Capture76','Post76','Cache77','ImportRevision77','CacheRevision77','CacheFinal77','ImportFinal77','CacheOwned77','ImportOwned77','ImportProduct77','ImportReview77','CacheReview77','Warnings77','WarningsRead77','Compile78Final','InputStatus78','InputDomainBackup78','ManagedInput78','Restore79','Compile79','Verify79','Read80','Compile80','Smoke80','Post80','Verify80','VerifyContent80','Compile81','Capture81','Read81','Post81','Verify81','Read82','Compile82','Capture82','Post82','Verify82','Capture82Fixed','Read83','Compile83','Probe83','Post83','Verify83','Compile83Fixed','Symbol83','Compile84','Read84','Probe84','Post84','Verify84','Read85','Compile85','Capture85','Post85','Verify85','Read86','Compile86','Capture86','Post86','Verify86','Read87','Compile87','Capture87','Post87','Verify87','Read89','Compile89','Capture89','Post89','Verify89','CompileForward89','ReadStart89','Compile89B','Capture89B','Read89B','Post89B','Verify89B','Compile89C','Capture89C','Read89C','Post89C','Verify89C','Compile89D','Capture89D','Read89D','Post89D','Verify89D','Compile89E','Capture89E','Read89E','Post89E','Verify89E','PreImportScreen89','ImportScreen89','Compile89F','Capture89F','Read89F','Post89F','Verify89F','PreImportFinal89','ImportFinal89','ReadFinal89','CompileFinal89','FinalGPU89','PostFinal89','VerifyFinal89','FinalState89','ReadAlpha90','FocusGPU90','ReadAlpha91','PreImport91','Import91','Read91','Compile91','Capture91','Post91','Verify91','PreImport91B','Import91B','Read91B','Compile91B','Capture91B','Post91B','Verify91B','CompileGeom91B','PreImport92','Import92','Read92','Compile92','Capture92','Post92','Verify92','Read93','Compile93','Capture93','Post93','Verify93','CompileFinal93','Read93B','Compile93B','Capture93B','Post93B','Verify93B','Read94','Compile94','Capture94','Post94','Verify94','Read95','Compile95','Capture95','Post95','Verify95','Read95B','Compile95B','Capture95B','Post95B','Verify95B','Read97','Compile97','Capture97','Post97','Verify97','Read98','Compile98','Capture98','Post98','Verify98','Import98')
marker=HERE/(mode+'_REQUEST.json')
if marker.exists():
 assert sys.argv[2:]==['--retry-compile-failure-once'],'Previous request exists: inspect outcome first, do not repeat'
 previous=json.loads((HERE/(mode+'_REPLY.json')).read_text(encoding='utf-8'))
 data=previous.get('data',{})
 assert data.get('isCompilationSuccessful') is False and data.get('isExecutionSuccessful') is False, 'Execution not known absent'
 for suffix in ('REQUEST.json','REPLY.json'):
  original=HERE/(mode+'_'+suffix);target=HERE/(mode+'_COMPILE_FAILURE1_'+suffix)
  assert not target.exists(),'Already retried compile failure'
  target.write_bytes(original.read_bytes())
connections=[]
for path in Path(r'C:\Users\15352\.unity\mcp\connections').glob('*.json'):
 try:
  data=json.loads(path.read_text(encoding='utf-8-sig'))
  if Path(data['project_path'])==PROJECT:connections.append((data['created_date'],data))
 except (KeyError,ValueError):pass
assert connections,'No existing official bridge descriptor'
info=max(connections,key=lambda p:p[0])[1];pid=info['editor_pid']
source=HERE/('RUN_'+mode+'.cs.txt');code=source.read_text(encoding='utf-8')
def scrub(value):
 if isinstance(value,dict):return {k:('[redacted]' if any(t in k.lower() for t in ('token','secret','password','credential','certificate','nonce')) else scrub(v)) for k,v in value.items()}
 if isinstance(value,list):return [scrub(v) for v in value]
 return value
def save(name,value):(HERE/name).write_text(json.dumps(scrub(value),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
args=[r'C:\Users\15352\.unity\relay\relay_win.exe','--mcp','--instance-id',str(pid),'--project-path',str(PROJECT),'--name','Codex Shop Read Capture']
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
 end=time.monotonic()+45
 while time.monotonic()<end:
  try:reply=q.get(timeout=.5)
  except queue.Empty:continue
  if reply.get('id')==number:return reply
 raise TimeoutError('Outcome unknown. Inspect output/request before any repeat.')
def unwrap(reply):
 result=reply.get('result',{})
 if result.get('structuredContent') is not None:return result['structuredContent']
 try:return json.loads(next(c['text'] for c in result.get('content',[]) if c.get('type')=='text'))
 except (ValueError,StopIteration):return reply
try:
 initialize=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}})
 assert 'error' not in initialize,initialize
 p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
 inv=rpc('tools/list',{}).get('result',{}).get('tools',[])
 assert any(t['name']=='Unity_RunCommand' for t in inv)
 console=unwrap(rpc('tools/call',{'name':'Unity_GetConsoleLogs','arguments':{'maxEntries':50,'includeStackTrace':True}}));save(mode+'_CONSOLE_BEFORE.json',console)
 save(marker.name,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':pid,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest()})
 reply=unwrap(rpc('tools/call',{'name':'Unity_RunCommand','arguments':{'Code':code,'Title':mode+' reviewed existing Unity project operation'}}))
 save(mode+'_REPLY.json',reply)
 data=reply.get('data',{})
 print(json.dumps({'mode':mode,'pid':pid,'success':reply.get('success'),'error':reply.get('error'),'compiled':data.get('isCompilationSuccessful'),'executed':data.get('isExecutionSuccessful'),'compileLogs':data.get('compilationLogs'),'logs':data.get('executionLogs')},ensure_ascii=False),flush=True)
 console=unwrap(rpc('tools/call',{'name':'Unity_GetConsoleLogs','arguments':{'maxEntries':50,'includeStackTrace':True}}));save(mode+'_CONSOLE_AFTER.json',console)
except Exception as e:
 save(mode+'_ERROR.json',{'error':str(e),'uncertain':isinstance(e,TimeoutError)});print(str(e),flush=True)
finally:
 p.stdin.close()
 try:p.wait(timeout=5);print(json.dumps({'relayEOF':True,'exitCode':p.returncode}),flush=True)
 except subprocess.TimeoutExpired:print(json.dumps({'ownedRelayStillRunning':p.pid,'notKilled':True}),flush=True)
