from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'capture';OUT=HERE/'motion'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
def main():
    OUT.mkdir(exist_ok=False);base=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs'];deps=base+[ROOT/'uv-features64/GlobalJournal64.cs',ROOT/'uv-features64/CpuSourceCapture64.cs',ROOT/'eye-observer73/EyeReadback73.cs',ROOT/'eye-observer73/UnityEyeBuffer70.cs',ROOT/'eye-continuity77/NativeSource77.cs',HERE/'MotionScope97.cs',HERE/'WholeEye96.cs',HERE/'NativeRetarget96.cs',HERE/'GraphSources96.cs',HERE/'LiveSurface96.cs',HERE/'LiveGraph96.cs',HERE/'LiveFinal96.cs']
    for mode in ['Read','Compile','Capture','Post','Verify']:
        s=(OLD/(mode+'96.cs')).read_text().replace(str(OLD),str(OUT)).replace('eye96-','eye97-').replace('STATE96-','STATE97-').replace('TRACE96-','TRACE97-').replace('CURRENT96.json','CURRENT97.json').replace('POST96.json','POST97.json').replace('VERIFY96.json','VERIFY97.json').replace('PRIOR47_CURRENT96.json','PRIOR47_CURRENT97.json').replace('MotionScope95','MotionScope97')
        if mode in ['Compile','Capture']:
            s=s.replace('if(!motion82.Ready(n.host.main.renderedSerial335))','final96.PresentCurrent(probeROI);\n   if(!motion82.Ready(n.host.main.renderedSerial335))')
            s=s.replace('for(int ch95=0;ch95<5;ch95++)','for(int ch95=0;retarget89.controlFields!=null&&ch95<5;ch95++)').replace('for(int field91=0;field91<current91.fields[group91].Length;field91++)','for(int field91=0;current91.fields[group91]!=null&&field91<current91.fields[group91].Length;field91++)')
            s=s.replace('["productOutputChanged"]=false','["productOutputChanged"]=false,["finalPresentations"]=final96.Presentations,["sourceGraphFrames"]=engine96.Frames,["sourceDiagnostics"]=false')
            s=s.replace('Bounded24-frame observation budget','Bounded28-sample motion observation budget')
        p=OUT/(mode+'97.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],OUT/('RUN_'+mode+'97.cs.txt'))
    (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes());relay=(ROOT/'final-eye95/capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','Read97','Compile97','Capture97','Post97','Verify97')");(OUT/'relay97.py').write_text(relay,encoding='utf-8');print('Prepared28 measured-phase/walk/turn snapshots; final composition executes on every new observed rendered serial. No execution yet.')
if __name__=='__main__':main()
