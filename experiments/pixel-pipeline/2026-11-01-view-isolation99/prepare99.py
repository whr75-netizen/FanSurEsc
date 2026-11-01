from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'live-underlay98/capture-c';OUT=HERE/'capture'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
def main():
    OUT.mkdir(exist_ok=False);base=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs'];deps=base+[ROOT/'uv-features64/GlobalJournal64.cs',ROOT/'uv-features64/CpuSourceCapture64.cs',ROOT/'eye-observer73/EyeReadback73.cs',ROOT/'eye-observer73/UnityEyeBuffer70.cs',ROOT/'eye-continuity77/NativeSource77.cs']+[HERE/n for n in ['HoldScope99.cs','GpuTiming98.cs','WholeEye96.cs','NonEyeUnderlay98.cs','NativeRetarget96.cs','GraphSources96.cs','LiveSurface96.cs','LiveGraph96.cs','LiveFinal96.cs','ViewB99.cs']]
    view=(HERE/'ViewB99.cs').read_text().replace('REGISTRATION99',str(ROOT/'native-feature89/REGISTRATION89.json'));(HERE/'ViewB99.cs').write_text(view,encoding='utf-8')
    for mode in ['Read','Compile','Capture','Post','Verify']:
        s=(OLD/(mode+'98C.cs')).read_text(encoding='utf-8').replace(str(OLD),str(OUT)).replace('"eye98c-"','"eye99-"').replace('STATE98C-','STATE99-').replace('TRACE98C-','TRACE99-').replace('CURRENT98.json','CURRENT99.json').replace('POST98.json','POST99.json').replace('VERIFY98.json','VERIFY99.json').replace('PRIOR47_CURRENT98.json','PRIOR47_CURRENT99.json')
        if mode in ['Compile','Capture']:
            s=s.replace('internal class CommandScript : IRunCommand','internal partial class CommandScript : IRunCommand').replace('MotionScope98 motion82','HoldScope99 motion82').replace('new MotionScope98(','new HoldScope99(')
            s=s.replace('final96=new LiveFinal96(n,retarget89,joint96,current91);','final96=new LiveFinal96(n,retarget89,joint96,current91);AddB99(n);')
            s=s.replace('timing98?.Dispose();final96?.Dispose();','CleanupViews99();timing98?.Dispose();final96?.Dispose();')
            s=s.replace('final96.PresentCurrent(probeROI);','final96.PresentCurrent(probeROI);TickViews99(n);')
            s=s.replace('    report["frameIndex"]=frameIndex;report["mainSerial"]=serial;','    CaptureB99(n,serial);\n    report["frameIndex"]=frameIndex;report["mainSerial"]=serial;')
            s=s.replace('Path.Combine(output,filename98),nativeFrame87,t98,','Path.Combine(output,filename98),group98.n.StartsWith("current-non-eye")?Frame(f,"viewA-physical-"+f.motion.camera.GetEntityId(),serial):group98.n.StartsWith("actual-world")?WorldFrame99(n,serial):nativeFrame87,t98,')
            s=s.replace('Bounded35-sample motion and evaluated Close observation budget','Bounded10-state actual existing two-view observation budget')
            assert 'CaptureB99(n,serial)'in s and 'TickViews99(n)'in s and 'internal partial class CommandScript'in s
        p=OUT/(mode+'99.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],OUT/('RUN_'+mode+'99.cs.txt'))
    (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes());relay=(OLD/'relay98.py').read_text().replace("'Verify98C','Import98C')","'Verify98C','Import98C','Read99','Compile99','Capture99','Post99','Verify99')");(OUT/'relay99.py').write_text(relay,encoding='utf-8');print('Prepared existing head/main actual URP source + per-owner cache/world isolation; no new camera/renderer or Asset changes; B final eye compose explicitly outside tested scope.')
if __name__=='__main__':main()
