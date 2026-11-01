from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'run82'
assert not list(OUT.glob('STATE82*'))and not (OUT/'CAPTURE_STARTED76.json').exists(),'Check prior outcome first'
# Prior source failed at the very first CreateNew: global81->82 replacement
# changed the directory name too. Preserve that source; no Play was entered.
src=(OUT/'Capture82.cs').read_text();bad=str(ROOT/'eye-motion82/run82');assert bad in src
src=src.replace(bad,str(OUT));(OUT/'Capture82Fixed.cs').write_bytes(src.encode())
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64';deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',OUT/'MotionScope82.cs']
bundle(deps+[OUT/'Capture82Fixed.cs'],OUT/'RUN_Capture82Fixed.cs.txt');r=(OUT/'relay76.py').read_text().replace("'Verify82')","'Verify82','Capture82Fixed')");(OUT/'relay76.py').write_bytes(r.encode())
assert str(OUT)in src and 'eye-motion82'not in src
print('Unique output path corrected; prior failed before any state/Play change')
