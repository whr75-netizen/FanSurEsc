"""One explicit bounded capture using the already imported113 shaders. No retry."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time
H=Path(__file__).resolve().parent;ROOT=H/'phase-run';PRE=H.parent;PID=28080
PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 marker=ROOT/'PHASE_REQUEST.json';assert not marker.exists()and not(ROOT/'CAPTURE_STARTED76.json').exists(),'Inspect outcome; never resubmit'
 expected=read(H/'PREPARED26.json')['captureSourceSHA256'];source=ROOT/'RUN_Capture25.cs.txt';code=source.read_text()
 assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
 done=read(PRE/'import/COMPLETE.json');assert done['Status']=='complete'and done['StateEqual']
 assert hashlib.sha256((PROJECT/'Assets/EUnityValidation01/HeadHair25/ForwardEye113_HeadHair25.compute').read_bytes()).hexdigest()==read(PRE/'LIVE_PREPARED.json')['computeSHA256']
 d=read(Path(r'C:\Users\15352\.unity\mcp\connections')/f'bridge-9eee322a-{PID}.json');assert d['editor_pid']==PID and Path(d['project_path'])==PROJECT
 for bad in ['EvaluateForm115','BoundRun115','SaveAssets(','ClearDirty(','Shader.SetGlobalBuffer(']:assert bad not in code
 p=subprocess.Popen([r'C:\Users\15352\.unity\relay\relay_win.exe','--mcp','--instance-id',str(PID),'--project-path',str(PROJECT),'--name','Codex Shop Read Capture'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
 q=queue.Queue();counter=0
 def reader():
  for line in p.stdout:
   try:q.put(json.loads(line))
   except ValueError:pass
 threading.Thread(target=reader,daemon=True).start()
 def rpc(method,params):
  nonlocal counter
  counter+=1;number=counter;p.stdin.write(json.dumps({'jsonrpc':'2.0','id':number,'method':method,'params':params})+'\n');p.stdin.flush();deadline=time.monotonic()+45
  while time.monotonic()<deadline:
   try:r=q.get(timeout=.3)
   except queue.Empty:continue
   if r.get('id')==number:return r
  raise TimeoutError('Outcome unknown; do not resubmit or release pending resources')
 try:
  first=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}});assert 'error'not in first
  p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
  save(marker,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':PID,'sourceSHA256':expected,'mode':'bounded-two-frame-support-regression'})
  r=rpc('tools/call',{'name':'Unity_RunCommand','arguments':{'Code':code,'Title':'Verify complete candidate output ROI in two normal phase frames, then exit and restore'}});save(ROOT/'PHASE_REPLY.json',r)
  x=r.get('result',{}).get('structuredContent',{});data=x.get('data',{});print(json.dumps({'success':x.get('success'),'compiled':data.get('isCompilationSuccessful'),'executed':data.get('isExecutionSuccessful'),'logs':data.get('executionLogs'),'error':x.get('error')}))
 except Exception as e:save(ROOT/'PHASE_ERROR.json',{'type':type(e).__name__,'message':str(e),'uncertain':isinstance(e,TimeoutError)});print(type(e).__name__,str(e))
 finally:
  p.stdin.close()
  try:p.wait(timeout=5);save(ROOT/'PHASE_RELAY_EOF.json',{'pid':p.pid,'exitCode':p.returncode})
  except subprocess.TimeoutExpired:save(ROOT/'PHASE_RELAY_EOF.json',{'pid':p.pid,'stillRunning':True,'notKilled':True})
if __name__=='__main__':main()
