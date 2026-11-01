from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=HERE/'capture';OUT=HERE/'capture-b'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
def main():
    OUT.mkdir(exist_ok=False)
    base=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[ROOT/'uv-features64/GlobalJournal64.cs',ROOT/'uv-features64/CpuSourceCapture64.cs',ROOT/'eye-observer73/EyeReadback73.cs',ROOT/'eye-observer73/UnityEyeBuffer70.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'final-eye95/MotionScope95.cs']+[HERE/n for n in ['MotionScope97.cs','MotionScope98.cs','GpuTiming98.cs','WholeEye96.cs','NonEyeUnderlay98.cs','NativeRetarget96.cs','GraphSources96.cs','LiveSurface96.cs','LiveGraph96.cs','LiveFinal96.cs']]
    for mode in ['Read','Compile','Capture','Post','Verify','Import']:
        s=(OLD/(mode+'98.cs')).read_text(encoding='utf-8').replace(str(OLD),str(OUT)).replace('eye98-','eye98b-').replace('STATE98-','STATE98B-').replace('TRACE98-','TRACE98B-')
        p=OUT/(mode+'98B.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],OUT/('RUN_'+mode+'98B.cs.txt'))
    (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'GLOBAL_NAMES66.json').read_bytes());relay=(OLD/'relay98.py').read_text().replace("'Import98')","'Import98','Read98B','Compile98B','Capture98B','Post98B','Verify98B','Import98B')");(OUT/'relay98.py').write_text(relay,encoding='utf-8')
    print('Prepared98B35-state comparison with only fallback ordering changed; no Unity execution.')
if __name__=='__main__':main()
