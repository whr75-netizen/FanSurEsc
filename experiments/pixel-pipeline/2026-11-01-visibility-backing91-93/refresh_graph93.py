from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'capture93'
assert not(OUT/'Capture93_REQUEST.json').exists(),'Do not change an executing observer'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'native-feature89/NativeRetarget89.cs',HERE/'GraphSources93.cs',HERE/'MotionScope91.cs']
bundle(deps+[OUT/'Capture93.cs'],OUT/'RUN_Capture93.cs.txt');bundle(deps+[OUT/'Compile93.cs'],OUT/'RUN_CompileFinal93.cs.txt');p=OUT/'relay93.py';relay=p.read_text().replace("'Verify93')","'Verify93','CompileFinal93')");p.write_text(relay,encoding='utf-8');print('Final bundle has4 distinct per-group materials; no shared mutable material across graph passes.')
