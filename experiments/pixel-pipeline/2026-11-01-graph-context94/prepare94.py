from pathlib import Path
import hashlib,json,sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
OLD=ROOT/'visibility-backing91'
sys.path.insert(0,str(ROOT/'boundary-input69'))
from prepare73 import bundle
B=ROOT/'apply-capture66'; O=ROOT/'eye-observer73'; U=ROOT/'uv-features64'
base=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']

def make():
    assert not (HERE/'capture').exists(), 'New request folder required; never reuse uncertain results'
    out=HERE/'capture'; out.mkdir()
    motion=(OLD/'capture92/MotionScope92.cs').read_text().replace('MotionScope92','MotionScope94').replace('Values={0,0,0}','Values={0,0,100,0}').replace('source-light','source-light-open-close-reopen')
    assert 'Values={0,0,100,0}' in motion
    (HERE/'MotionScope94.cs').write_text(motion,encoding='utf-8')
    source=(OLD/'capture92/Capture92.cs').read_text().replace(str(OLD/'capture92'),str(out)).replace('MotionScope92','MotionScope94').replace('CurrentRasters91','GraphSources93').replace('current91.Render();','current91.AssertRendered();').replace('STATE92-','STATE94-').replace('TRACE92-','TRACE94-').replace('eye92-','eye94-')
    source=source.replace('92 production-S3 metadata trace only; no final-art evaluation; defaults restored','94 graph-context original baseline then metadata open/Close/reopen; product77 unchanged')
    source=source.replace('Bounded24-frame observation budget exhausted','Bounded four-frame graph observation budget exhausted')
    source=source.replace('endCameraRendering for the exact head camera, current source light context','normal same-head-camera RenderGraph pass, explicit shadow read dependencies; endCamera only verifies completion')
    (out/'Capture94.cs').write_text(source,encoding='utf-8')
    compile_only=source.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("94 four-frame UnsafePass source comparison compiled only; no Play");return;}\n void Prepared94(ExecutionResult result)\n {',1)
    assert 'void Prepared94' in compile_only
    (out/'Compile94.cs').write_text(compile_only,encoding='utf-8')
    deps=base[:2]+[U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'native-feature89/NativeRetarget89.cs',OLD/'GraphSources93.cs',HERE/'MotionScope94.cs']
    for mode in ['Compile94','Capture94']:
        bundle(deps+[out/(mode+'.cs')],out/('RUN_'+mode+'.cs.txt'))
    for mode in ['Read','Post','Verify']:
        text=(OLD/'capture93b'/(mode+'93B.cs')).read_text().replace(str(OLD/'capture93b'),str(out)).replace('CURRENT93B.json','CURRENT94.json').replace('POST93B.json','POST94.json').replace('VERIFY93B.json','VERIFY94.json')
        if mode=='Read':
            # Read current public state and compare the previous known 47 contents
            # before any Play/options/renderer getter is called.
            code='''
  var previousRows=new Arr58();
  foreach(var row in Json58.Parse(File.ReadAllText(@"PREVIOUS_MANIFEST")))previousRows.Add(new Obj58{["path"]=row["path"],["type"]=row["type"],["snapshot"]=row["snapshot"]});
  var prior=NativeSnapshot73.Compare(@"PREVIOUS_ROOT",previousRows);
  CreateOnly73.Text(@"PRIOR_RESULT",prior.ToString());
'''.replace('PREVIOUS_MANIFEST',str(OLD/'capture93b/NATIVE_BEFORE73.json')).replace('PREVIOUS_ROOT',str(OLD/'capture93b')).replace('PRIOR_RESULT',str(out/'PRIOR47_CURRENT94.json'))
            text=text.replace('  result.Log(',code+'  result.Log(',1)
        (out/(mode+'94.cs')).write_text(text,encoding='utf-8')
        bundle(base+[out/(mode+'94.cs')],out/('RUN_'+mode+'94.cs.txt'))
    relay=(OLD/'capture93b/relay93.py').read_text().replace("'Verify93B')","'Verify93B','Read94','Compile94','Capture94','Post94','Verify94')")
    (out/'relay94.py').write_text(relay,encoding='utf-8')
    (out/'GLOBAL_NAMES66.json').write_bytes((OLD/'capture93b/GLOBAL_NAMES66.json').read_bytes())
    graph=(OLD/'GraphSources93.cs').read_text()
    assert 'AddUnsafePass<Data>' in graph and 'SetRenderAttachment' not in graph
    assert 'ExecuteCommandBuffer' not in graph.replace('// Keep every owned RT and shadow texture declared; no nested ExecuteCommandBuffer.','')
    assert graph.count('builder.UseTexture(')==4 and 'AccessFlags.Write' in graph
    plan={'frames':4,'states':['original-open','production-metadata-open','production-metadata-full-Close','production-metadata-reopen'],'PlayLimit':1,'AssetsImports':0,'rendererRecreation':False,'productDefault':77,'graphSourceSHA256':hashlib.sha256(graph.encode()).hexdigest(),'ownedColourRTs':24,'ownedDepthRTs':4,'borrowedBuffersReleased':False,'graphProtocol':'UnsafePass native SetRenderTarget with explicit colour/depth writes and shadow/global texture reads; no native raster attachment array','failureRule':'Any graph/job/source frame error: normal exit, no repeat','preflightPrevious47Required':True}
    (HERE/'PLAN94.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(plan,indent=2))

if __name__=='__main__':make()
