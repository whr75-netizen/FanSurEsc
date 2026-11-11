"""Explicit single-step official relay. No automatic follow-up or retry."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time,sys
H=Path(__file__).resolve().parent;G=H/'face33';PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');PID=28080
def save(p,obj):p.write_text(json.dumps(obj,indent=2),encoding='utf-8',newline='\n')
def main():
 mode=sys.argv[1];assert mode in ['schema','console','console-after','details','import','capture','final'];root=G/mode;root.mkdir(parents=True,exist_ok=True)
 marker=root/'REQUEST.json';assert not marker.exists(),'Inspect original outcome; no duplicate request'
 info=json.loads((Path(r'C:\Users\15352\.unity\mcp\connections')/f'bridge-9eee322a-{PID}.json').read_text(encoding='utf-8-sig'));assert info['editor_pid']==PID and Path(info['project_path'])==PROJECT
 args=[r'C:\Users\15352\.unity\relay\relay_win.exe','--mcp','--instance-id',str(PID),'--project-path',str(PROJECT),'--name','Codex Shop Read Capture']
 p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW);q=queue.Queue();counter=0
 def reader():
  for line in p.stdout:
   try:q.put(json.loads(line))
   except ValueError:pass
 threading.Thread(target=reader,daemon=True).start()
 def rpc(method,params):
  nonlocal counter
  counter+=1;n=counter;p.stdin.write(json.dumps({'jsonrpc':'2.0','id':n,'method':method,'params':params})+'\n');p.stdin.flush();until=time.monotonic()+40
  while time.monotonic()<until:
   try:r=q.get(timeout=.3)
   except queue.Empty:continue
   if r.get('id')==n:return r
  raise TimeoutError('Outcome uncertain; no retry')
 try:
  r=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}});assert'error'not in r
  p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush();tools=rpc('tools/list',{}).get('result',{}).get('tools',[])
  selected=[t for t in tools if t['name']in ['Unity_GetConsoleLogs','Unity_RunCommand']];save(root/'SCHEMA.json',selected)
  if mode=='schema':print(json.dumps(selected));return
  if mode.startswith('console'):name='Unity_GetConsoleLogs';arguments=json.loads((root/'ARGS.json').read_text())
  else:
   code=(root/'RUN.cs.txt').read_text(encoding='utf-8');assert'EvaluateForm115'not in code and'BoundRun115'not in code
   name='Unity_RunCommand';arguments={'Code':code,'Title':{'details':'Read current scene and project dirty metadata only','import':'Import three owned source-diagnostic shaders only','capture':'One normal Play frame source diagnostic, acknowledged readback and normal restoration','final':'Read post-capture Editor state only'}[mode]}
  save(marker,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':PID,'tool':name,'codeSHA256':hashlib.sha256(arguments.get('Code','').encode()).hexdigest()})
  reply=rpc('tools/call',{'name':name,'arguments':arguments});save(root/'REPLY.json',reply);content=reply.get('result',{}).get('structuredContent',{});data=content.get('data',{})
  print(json.dumps({'success':content.get('success'),'compiled':data.get('isCompilationSuccessful'),'executed':data.get('isExecutionSuccessful'),'logs':data.get('executionLogs'),'error':content.get('error'),'text':reply.get('result',{}).get('content',[])if mode.startswith('console') else None}))
 except Exception as e:
  save(root/'ERROR.json',{'type':type(e).__name__,'message':str(e),'uncertain':isinstance(e,TimeoutError)});raise
 finally:
  p.stdin.close()
  try:p.wait(timeout=5);save(root/'RELAY_EOF.json',{'exitCode':p.returncode})
  except subprocess.TimeoutExpired:save(root/'RELAY_EOF.json',{'stillRunning':True,'notKilled':True})
if __name__=='__main__':main()
