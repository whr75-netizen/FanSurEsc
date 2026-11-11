"""One read-only official relay request; no Play/import, no retry or stale PID."""
from pathlib import Path
import datetime,hashlib,json,queue,subprocess,threading,time,sys
H=Path(__file__).resolve().parent
PROJECT=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
PID=28080
def save(name,obj):
    (H/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
def scrub(v):
    if isinstance(v,dict):return {k:('[redacted]'if any(t in k.lower()for t in ['token','secret','credential','password','nonce','certificate'])else scrub(x))for k,x in v.items()}
    if isinstance(v,list):return [scrub(x)for x in v]
    return v
def main():
    scene='--scene-detail'in sys.argv;mode='SCENE'if scene else'READ'
    assert not (H/(mode+'_REQUEST.json')).exists(),'Already submitted: inspect existing outcome, never repeat'
    descriptor=Path(r'C:\Users\15352\.unity\mcp\connections')/f'bridge-9eee322a-{PID}.json'
    info=json.loads(descriptor.read_text(encoding='utf-8-sig'))
    assert info['editor_pid']==PID and Path(info['project_path'])==PROJECT
    code=(H/('ReadScenes.cs.txt'if scene else'ReadState.cs.txt')).read_text(encoding='utf-8')
    args=[r'C:\Users\15352\.unity\relay\relay_win.exe','--mcp','--instance-id',str(PID),'--project-path',str(PROJECT),'--name','Codex Shop Read Capture']
    p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
    q=queue.Queue();counter=0
    def reader():
        for line in p.stdout:
            try:q.put(json.loads(line))
            except ValueError:pass
    threading.Thread(target=reader,daemon=True).start()
    def rpc(method,params):
        nonlocal counter
        counter+=1;number=counter;p.stdin.write(json.dumps({'jsonrpc':'2.0','id':number,'method':method,'params':params})+'\n');p.stdin.flush()
        until=time.monotonic()+30
        while time.monotonic()<until:
            try:r=q.get(timeout=.3)
            except queue.Empty:continue
            if r.get('id')==number:return r
        raise TimeoutError('Read outcome unknown; no automatic repeat')
    try:
        reply=rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'Codex Shop Read Capture','version':'1.0'}})
        assert 'error'not in reply,reply
        p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n');p.stdin.flush()
        inventory=rpc('tools/list',{});names=[t['name']for t in inventory.get('result',{}).get('tools',[])]
        save('INVENTORY.json',{'tools':names,'pid':PID});assert 'Unity_RunCommand'in names,'Existing RunCommand not available'
        save(mode+'_REQUEST.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':PID,'codeSHA256':hashlib.sha256(code.encode()).hexdigest(),'readOnly':True})
        reply=rpc('tools/call',{'name':'Unity_RunCommand','arguments':{'Code':code,'Title':'Read current Editor state only; no Play or settings changes'}})
        save(mode+'_REPLY.json',scrub(reply));content=reply.get('result',{}).get('structuredContent',{});data=content.get('data',{})
        print(json.dumps({'success':content.get('success'),'compiled':data.get('isCompilationSuccessful'),'executed':data.get('isExecutionSuccessful'),'logs':data.get('executionLogs'),'error':content.get('error')},ensure_ascii=False))
    except Exception as e:
        save(mode+'_ERROR.json',{'type':type(e).__name__,'message':str(e),'uncertain':isinstance(e,TimeoutError)})
        print(json.dumps({'error':type(e).__name__,'message':str(e),'uncertain':isinstance(e,TimeoutError)}))
    finally:
        p.stdin.close()
        try:p.wait(timeout=5);save(mode+'_RELAY_EOF.json',{'pid':p.pid,'exitCode':p.returncode})
        except subprocess.TimeoutExpired:save(mode+'_RELAY_EOF.json',{'pid':p.pid,'stillRunning':True,'notKilled':True})
if __name__=='__main__':main()
