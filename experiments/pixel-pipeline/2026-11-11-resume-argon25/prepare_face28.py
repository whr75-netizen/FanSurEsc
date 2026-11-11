"""One-frame colour-stage observation, reusing the verified27 external runner.

No shader/Assets edits, no new GPU dispatch or altered classifier. Normal Play
and the existing external restoration contract only when relay is invoked.
"""
from pathlib import Path
import hashlib,json,sys,shutil
H=Path(__file__).resolve().parent;G=H/'face28';P=H/'producer/support/surface27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 target=G/'capture-stages';target.mkdir(exist_ok=True)
 assert not(target/'PHASE_REQUEST.json').exists(),'Submitted capture is immutable'
 source=P/'pigment-run/RUN_Capture25.cs.txt'
 assert sha(source)=='cb5043361d5ac50ee07a845f4c5ac55e91fac1c2fafb9781ad060ae0c5e33975'
 s=source.read_text(encoding='utf-8')
 old='const string Root=@"'+str(P/'pigment-run')+'";'
 assert s.count(old)==1;s=s.replace(old,'const string Root=@"'+str(target)+'";')
 assert s.count('if(captured76>=4)')==1;s=s.replace('if(captured76>=4)','if(captured76>=1)')
 assert s.count('  CaptureColumns26();')==1
 s=s.replace('  CaptureColumns26();','  CaptureStages28(n,hf);CaptureColumns26();')
 anchor=' struct GroupRead113{'
 stage='''  void CaptureStages28(NativePlayer395 n,CpuSourceCapture64.Frame hf){
   var main=n.host.main;var head=n.host.head;
   report["stageContract28"]=new Obj58{["frame"]=Time.frameCount,["mainSerial"]=main.renderedSerial335,["headSerial"]=head.renderedSerial335,["headSplit"]=HeadLocal367.Split(main),["lineTone"]=main.lineTone,["usePalette"]=main.usePalette,["linesAsset"]=AssetDatabase.GetAssetPath(main.lines),["linesSHA"]=SHA(AssetDatabase.GetAssetPath(main.lines)),["order"]="Restore -> JoinBare -> main OwnerLines -> MainToHead -> head eyes -> EyesToMain; head has no independent OwnerLines",["newDispatches"]=0};
   foreach(var pair in new[]{new{v=main,n="M"},new{v=head,n="H"}}){
    var v=pair.v;var frame=Frame(v,pair.n+"-stages28",main.renderedSerial335);
    foreach(var t in new[]{new{n="beforeStyle",t=v.beforeStyle},new{n="prepared",t=v.prepared},new{n="postLine",t=v.postLine},new{n="final",t=v.colour},new{n="meta",t=v.preparedMeta},new{n="uv",t=v.preparedUV},new{n="owner",t=v.owner},new{n="audit",t=v.audit}})
     FullStrips113(frame,"ST28-"+pair.n+"-"+t.n,t.t,"existing runtime77 stage; recorded after normal frame","raw linear values; classify using matching meta/UV, no inferred palette");
   }
  }
'''
 assert s.count(anchor)==1;s=s.replace(anchor,stage+anchor)
 assert 'EvaluateForm115'not in s and 'BoundRun115'not in s
 out=target/'RUN_Capture25.cs.txt';out.write_text(s,encoding='utf-8',newline='\n')
 shutil.copyfile(P/'pigment-run/GLOBAL_NAMES66.json',target/'GLOBAL_NAMES66.json')
 sys.path.insert(0,str(H/'producer'));from prepare_live import compile_cs
 compile_cs(out)
 relay=(P/'relay_pigment.py').read_text(encoding='utf-8')
 relay=relay.replace("H=Path(__file__).resolve().parent;PID=28080","H=Path(__file__).resolve().parent;PID=28080")
 relay=relay.replace("root=H/'pigment-run'","root=H/'capture-stages'")
 relay=relay.replace("contract=load(H/'PIGMENT_PREPARED.json')","contract=load(H/'PREPARED28.json')")
 relay=relay.replace("done=load(H/'import/COMPLETE.json')","done=load(Path(r'"+str(P/'import/COMPLETE.json')+"'))")
 relay=relay.replace('Four evaluated Open Close75 Close100 reopen states then normal exit and restore','One normal frame of existing77 colour stages; no new dispatch; normal exit and restore')
 (G/'relay28.py').write_text(relay,encoding='utf-8',newline='\n')
 result={'captureSourceSHA256':sha(out),'source27SHA256':sha(source),'newShaders':0,'newDispatches':0,'frames':1,'maxSimultaneousReadbackBytes':480*32*16,'stagesPerView':8,'viewCount':2,'stageUncompressedBytes':480*272*16*16,'externalCompile':'passed','default77Changed':False}
 (G/'PREPARED28.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
