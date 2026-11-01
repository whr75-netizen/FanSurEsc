from pathlib import Path
import json,sys,hashlib
H=Path(__file__).resolve().parent;R=H.parent;D=H/'capture';OLD=R/'closed-support105/direct'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle

def plan():
    result={}
    for mode in ('Read','Compile','Capture','Post','Verify','Import'):
        if mode=='Read':p=R/'forward-eye102/capture/Read102.cs'
        elif mode=='Import':p=R/'forward-eye102/ImportHierarchy102.cs'
        else:p=OLD/(mode+'102.cs')
        s=p.read_text(encoding='utf-8')
        if mode=='Import':s=s.replace(str(R/'forward-eye102/captureH'),str(D)).replace('ForwardEye102.compute','ForwardEye106.compute').replace('IMPORT102','IMPORT106')
        else:s=s.replace(str(p.parent),str(D))
        if mode in ('Compile','Capture'):
            s=s.replace('ForwardCanvas102','ForwardCanvas106').replace('MotionScope95','Sequence106').replace('"eye102-"','"eye106-"')
            s=s.replace('STATE102-','STATE106-').replace('TRACE102-','TRACE106-')
            s=s.replace('91 current evaluated backing and same-ray normal/SH/light totals; product77 unchanged','106 current deformed source curve, same-input GPU102 comparison; product77 unchanged')
            old='   if(motion82.StageIndex==1||motion82.StageIndex==2||motion82.StageIndex==4||motion82.StageIndex==6){if(!motion82.Advance()){BeginExit();return;}armedSerial=n.host.main.renderedSerial335;return;}'
            assert s.count(old)==1
            s=s.replace(old,'   if(!motion82.CaptureThis){if(!motion82.Advance()){BeginExit();return;}armedSerial=n.host.main.renderedSerial335;return;}')
            a=s.index(' void JointBuffer102(');s=s[:a]+(H/'CaptureFragment106.cs').read_text(encoding='utf-8')+'\n}\n'
        result[str(D/(mode+'106.cs'))]=s
    print(json.dumps(result),flush=True)

def build():
    base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',R/'live-underlay98/LiveSurface96.cs',R/'live-underlay98/WholeEye96.cs',R/'live-underlay98/MotionScope97.cs',H/'SourceCurves106.cs',H/'ForwardCanvas106.cs',H/'MotionClose106.cs',H/'Sequence106.cs']
    for mode in ('Read','Compile','Capture','Post','Verify','Import'):
        bundle((deps if mode in ('Compile','Capture')else base)+[D/(mode+'106.cs')],D/('RUN_'+mode+'106.cs.txt'))
    (D/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
    s=(OLD/'relay102.py').read_text(encoding='utf-8');s=s.replace('assert mode in (',"assert mode in ('Read106','Compile106','Capture106','Post106','Verify106','Import106',")
    (D/'relay106.py').write_text(s,encoding='utf-8')
    baseline=(R/'forward-eye102/ForwardEye102.compute').read_bytes();assert hashlib.sha256(baseline).hexdigest()=='a42f360c33cfbcc1c44e7e0ceeebd4efad3ed678143419a00d63c0eb2463bded'
    shader='#pragma kernel ApplyCurve106\n'+baseline.decode('utf-8').replace('\r\n','\n')+'\n'+(H/'CurveSupport106.hlsl').read_text(encoding='utf-8')
    (H/'ForwardEye106.compute').write_bytes(shader.encode('utf-8'))
    print('106 external runner bundled. CPU current source segments -> live GPU geometry/sample decision. No Unity/Assets change.',flush=True)
if __name__=='__main__':{'plan':plan,'build':build}[sys.argv[1]]()
