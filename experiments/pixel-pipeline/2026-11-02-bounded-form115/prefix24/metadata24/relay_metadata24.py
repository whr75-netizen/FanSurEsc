"""One explicit approved phase. No automatic follow-up or uncertain retry."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time,sys
H=Path(__file__).resolve().parent;ROOT=H.parent
PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');PID=22952
mode=sys.argv[1];assert mode in ['ReadMetadata24','ImportMetadata24','Stage1Prefix24','PostState24']
marker=H/(mode+'_REQUEST.json');assert not marker.exists(),'Prior outcome exists: inspect; no resubmission'
assert not(H/(mode+'_REPLY.json')).exists()
valid=False
for pth in Path(r'C:\Users\15352\.unity\mcp\connections').glob('*.json'):
 try:
  d=json.loads(pth.read_text(encoding='utf-8-sig'));valid|=Path(d.get('project_path',''))==PROJECT and d.get('editor_pid')==PID
 except(KeyError,ValueError):pass
assert valid,'Current official connection missing'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files={'ReadMetadata24':'ReadMetadataState24.command.cs.txt','ImportMetadata24':'ImportMetadata24.command.cs.txt','Stage1Prefix24':'STAGE1_METADATA24.command.cs.txt','PostState24':'POST_STATE24.command.cs.txt'}
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
 save(marker.name,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':mode,'pid':PID,'sourceSHA256':sha(source),'maxDispatches':1 if mode=='Stage1Prefix24'else 0,'autoNext':False})
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
