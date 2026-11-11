"""Explicit one-stage official relay. No automatic retry/next stage."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,sys,threading,time
H=Path(__file__).resolve().parent;PID=28080
PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
def main():
    mode=sys.argv[1];assert mode in ['phase']
    root=H/'pigment-run';source=root/('RUN_Import25.cs.txt'if mode=='import'else'RUN_Capture25.cs.txt')
    marker=root/(mode.upper()+'_REQUEST.json');assert not marker.exists(),'Inspect prior outcome; never resubmit'
    contract=load(H/'PIGMENT_PREPARED.json');expected=contract['importSourceSHA256'if mode=='import'else'captureSourceSHA256']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected,'Reviewed command changed'
    if mode=='phase':
        done=load(H/'import/COMPLETE.json');assert done['Status']=='complete'and done['StateEqual']and not(H/'import/FAILED.json').exists()
    descriptor=load(Path(r'C:\Users\15352\.unity\mcp\connections')/f'bridge-9eee322a-{PID}.json')
    assert descriptor['editor_pid']==PID and Path(descriptor['project_path'])==PROJECT
    code=source.read_text(encoding='utf-8');assert 'EvaluateForm115'not in code and 'BoundRun115'not in code
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
        raise TimeoutError('Outcome unknown; inspect original markers before any further call')
    try:
        result=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}});assert 'error'not in result,result
        p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
        save(marker,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':PID,'mode':mode,'sourceSHA256':expected})
        result=rpc('tools/call',{'name':'Unity_RunCommand','arguments':{'Code':code,'Title':'Import one isolated shared-skin shader without Play'if mode=='import'else'Four evaluated Open Close75 Close100 reopen states then normal exit and restore'}})
        save(root/(mode.upper()+'_REPLY.json'),result)
        content=result.get('result',{}).get('structuredContent',{});data=content.get('data',{})
        print(json.dumps({'success':content.get('success'),'compiled':data.get('isCompilationSuccessful'),'executed':data.get('isExecutionSuccessful'),'logs':data.get('executionLogs'),'error':content.get('error')},ensure_ascii=False))
    except Exception as e:
        save(root/(mode.upper()+'_ERROR.json'),{'type':type(e).__name__,'message':str(e),'uncertain':isinstance(e,TimeoutError)});print(type(e).__name__,str(e))
    finally:
        p.stdin.close()
        try:p.wait(timeout=5);save(root/(mode.upper()+'_RELAY_EOF.json'),{'pid':p.pid,'exitCode':p.returncode})
        except subprocess.TimeoutExpired:save(root/(mode.upper()+'_RELAY_EOF.json'),{'pid':p.pid,'stillRunning':True,'notKilled':True})
if __name__=='__main__':main()
