from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'boundary-input69')); from prepare73 import bundle
B=ROOT/'apply-capture66'; O=ROOT/'eye-observer73'; U=ROOT/'uv-features64'
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',HERE/'NativeRetarget95.cs',HERE/'GraphSources95.cs',HERE/'MotionScope95.cs']
for mode in ['Compile95','Capture95']:bundle(deps+[HERE/'capture'/(mode+'.cs')],HERE/'capture'/('RUN_'+mode+'.cs.txt'))
print('Rebundled complete external compiler inputs; no Unity invocation.')
