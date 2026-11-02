"""One explicit approved phase. No automatic follow-up or uncertain retry."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time,sys
H=Path(__file__).resolve().parent;ROOT=H.parent
PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');PID=22952
mode=sys.argv[1];assert mode=='CaptureFull24'
marker=H/(mode+'_REQUEST.json');assert not marker.exists(),'Prior outcome exists: inspect; no resubmission'
assert not(H/(mode+'_REPLY.json')).exists()
valid=False
for pth in Path(r'C:\Users\15352\.unity\mcp\connections').glob('*.json'):
 try:
  d=json.loads(pth.read_text(encoding='utf-8-sig'));valid|=Path(d.get('project_path',''))==PROJECT and d.get('editor_pid')==PID
 except(KeyError,ValueError):pass
assert valid,'Current official connection missing'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if mode=='ImportFull24':
 source=H/'RUN_ImportFull24.cs.txt';record=json.loads((H/'CPU_IMPORT24.json').read_text());assert sha(source)==record['sources'][source.name]
 assert not(PROJECT/'Assets/EUnityValidation01/Direct24Geometry').exists(),'Existing import must be inspected'
 assert 'shader.Dispatch('not in source.read_text()
else:
 source=H/'RUN_CaptureFull24.cs.txt';record=json.loads((H/'CPU_COMPILE_FULL24.json').read_text());assert record['cpuCSharpSuccess']and sha(source)==record['commandSHA256']
 imported=json.loads((H.parent/'import/COMPLETE.json').read_text());assert imported['Status']=='complete'and imported['StateEqual']and not imported['Error']
 assert not(H.parent/'import/FAILED.json').exists()
 assert sha(PROJECT/'Assets/EUnityValidation01/Direct24Geometry/ForwardEye113_Geometry24.compute')==record['shaderSHA256']
 assert not(H/'CAPTURE_STARTED76.json').exists(),'Existing execution: inspect, never replay'
 text=source.read_text();assert 'if(captured76>=1)'not in text and 'new Sequence111('in text
 for bad in ['EvaluateForm115','BoundRun115','Shader.SetGlobalBuffer(','SaveAssets(','ClearDirty(','File.Delete(','File.Move(']:assert bad not in text
code=source.read_text(encoding='utf-8')
def scrub(v):
 if isinstance(v,dict):return{k:('[redacted]'if any(t in k.lower()for t in ['token','secret','password','credential','nonce'])else scrub(x))for k,x in v.items()}
 if isinstance(v,list):return[scrub(x)for x in v]
 return v
def save(name,value):
 with(H/name).open('x',encoding='utf-8')as f:json.dump(scrub(value),f,ensure_ascii=False,indent=2)
args=[r'C:\Users\15352\.unity\relay\relay_win.exe','--mcp','--instance-id',str(PID),'--project-path',str(PROJECT),'--name','Codex Shop Read Capture']
p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
q=queue.Queue();counter=0
def reader():
 for line in p.stdout:
  try:q.put(json.loads(line))
  except ValueError:pass
threading.Thread(target=reader,daemon=True).start();threading.Thread(target=lambda:[None for _ in p.stderr],daemon=True).start()
def rpc(method,params):
 global counter
 counter+=1;number=counter;p.stdin.write(json.dumps({'jsonrpc':'2.0','id':number,'method':method,'params':params})+'\n');p.stdin.flush()
 until=time.monotonic()+45
 while time.monotonic()<until:
  try:reply=q.get(timeout=.5)
  except queue.Empty:continue
  if reply.get('id')==number:return reply
 raise TimeoutError('Outcome uncertain. Inspect disk markers/process; never resubmit.')
try:
 init=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}});assert'error'not in init
 p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
 inv=rpc('tools/list',{}).get('result',{}).get('tools',[]);assert any(t['name']=='Unity_RunCommand'for t in inv)
 save(marker.name,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':mode,'pid':PID,'sourceSHA256':sha(source),'operationScope':('shader-only import'if mode=='ImportFull24'else'one Play/existing12 evaluated Close and hair states; runtime graph dispatches'),'autoNext':False})
 reply=rpc('tools/call',{'name':'Unity_RunCommand','arguments':{'Code':code,'Title':mode+' isolated reviewed operation'}});save(mode+'_REPLY.json',reply)
 result=reply.get('result',{});value=result.get('structuredContent')
 if value is None:
  try:value=json.loads(next(c['text']for c in result.get('content',[])if c.get('type')=='text'))
  except(ValueError,StopIteration):value={'unparsed':True,'isError':result.get('isError')}
 data=value.get('data',{});print(json.dumps({'mode':mode,'success':value.get('success'),'error':value.get('error'),'compiled':data.get('isCompilationSuccessful'),'executed':data.get('isExecutionSuccessful'),'compileLogs':data.get('compilationLogs'),'executionLogs':data.get('executionLogs')},ensure_ascii=False),flush=True)
except Exception as e:
 save(mode+'_ERROR.json',{'error':str(e),'uncertain':isinstance(e,TimeoutError)});print(str(e),flush=True)
finally:
 p.stdin.close()
 try:p.wait(timeout=5);print(json.dumps({'relayEOF':True,'exitCode':p.returncode}),flush=True)
 except subprocess.TimeoutExpired:print(json.dumps({'ownedRelayStillRunning':p.pid,'notKilled':True}),flush=True)
