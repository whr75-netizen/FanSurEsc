from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'unsafe93-review';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'native-feature89/NativeRetarget89.cs',HERE/'GraphSources93.cs',HERE/'MotionScope91.cs']
# No executable capture is generated in this review folder.
source=(HERE/'capture93b/Compile93B.cs').read_text().replace('93B normal default-renderer path compiled; no Play','93 UnsafePass candidate compiled only; GPU execution blocked pending renderer job safety');(OUT/'CompileUnsafe93.cs').write_text(source,encoding='utf-8');bundle(deps+[OUT/'CompileUnsafe93.cs'],OUT/'RUN_CompileUnsafe93.cs.txt');relay=(HERE/'capture93b/relay93.py').read_text().replace("'Verify93B')","'Verify93B','CompileUnsafe93')");(OUT/'relay93.py').write_text(relay,encoding='utf-8');print('Compile-only candidate, no runnable Play request prepared.')
