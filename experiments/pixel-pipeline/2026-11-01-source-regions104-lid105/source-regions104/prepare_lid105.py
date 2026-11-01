"""Prepare three normal same-source states; no Unity execution or asset import."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;R=H.parent;OLD=R/'forward-eye102/captureH';D=R/'closed-support105'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle

def main():
    D.mkdir(exist_ok=False)
    base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',R/'live-underlay98/LiveSurface96.cs',R/'live-underlay98/WholeEye96.cs',R/'final-eye95/MotionScope95.cs',R/'forward-eye102/ForwardCanvas102.cs']
    for mode in ('Read','Compile','Capture','Post','Verify'):
        source=(OLD if mode in ('Compile','Capture','Post')else R/'forward-eye102/capture')/(mode+'102.cs')
        s=source.read_text(encoding='utf-8').replace(str(source.parent),str(D))
        if mode in ('Compile','Capture'):
            s=s.replace('Sequence102','MotionScope95')
            needle='   readyAllocated=Profiler.GetTotalAllocatedMemoryLong();'
            assert s.count(needle)==1
            s=s.replace(needle,'   if(motion82.StageIndex==1||motion82.StageIndex==2||motion82.StageIndex==4||motion82.StageIndex==6){if(!motion82.Advance()){BeginExit();return;}armedSerial=n.host.main.renderedSerial335;return;}\n'+needle)
            needle='JointBuffer102("canonical-decision",forward102.Source.Engine.Decisions);'
            assert s.count(needle)==1
            s=s.replace(needle,needle+'JointBuffer102("canonical-layers",forward102.Source.Engine.Layers);JointBuffer102("canonical-visibility",forward102.Source.Engine.Visibility);AuxMesh("current-face105",e.sampleFace,h.motion.surface.outputs[1].transform.localToWorldMatrix,hf);report["headMatrix105"]=M(e.headMatrix);report["purpose105"]="same canonical source lid coverage before/after Query/Select, source Close0/100/reopen; no size policy or shader change";')
        p=D/(mode+'102.cs');p.write_text(s,encoding='utf-8')
        bundle((deps if mode in ('Compile','Capture')else base)+[p],D/('RUN_'+mode+'102.cs.txt'))
    (D/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes())
    (D/'relay102.py').write_bytes((OLD/'relay102.py').read_bytes())
    protected=json.loads((R/'forward-eye102/PRESERVATION102.json').read_text(encoding='utf-8-sig'))
    (D/'PROTECTION_REFERENCE102.json').write_text(json.dumps(protected,indent=2))
    print('Prepared 3states open/Close100/reopen, full bounded canonical layers/visibility and same-source evaluated mesh. No Unity/Assets change.')
if __name__=='__main__':main()
