from pathlib import Path
import sys
H=Path(__file__).resolve().parent;R=H.parent;O=H/'capture';D=H/'motion'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle
D.mkdir(exist_ok=False)
base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',R/'live-underlay98/LiveSurface96.cs',R/'live-underlay98/WholeEye96.cs',R/'live-underlay98/MotionScope97.cs',H/'ForwardCanvas102.cs']
for mode in ['Compile','Capture','Post']:
 s=(O/(mode+'102.cs')).read_text(encoding='utf-8').replace(str(O),str(D)).replace('Sequence102 motion82','MotionScope97 motion82').replace('new Sequence102(n,output)','new MotionScope97(n,output)').replace('Bounded9-state forward eye/actual evaluated Close budget','Bounded28-state actual relative phase/walk/turn forward eye budget')
 p=D/(mode+'102.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],D/('RUN_'+mode+'102.cs.txt'))
(D/'GLOBAL_NAMES66.json').write_bytes((O/'GLOBAL_NAMES66.json').read_bytes());(D/'relay102.py').write_bytes((O/'relay102.py').read_bytes());print('102 actual phase10/walk8/turn10 prepared; existing verified normal gameplay input scope; no InputSettings replacement')
