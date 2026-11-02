from pathlib import Path
import sys
H=Path(__file__).resolve().parent;R=H.parent
suffix=sys.argv[1]if len(sys.argv)>1 else''
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle
deps=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs',R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',R/'joint-lid107/NativeDense107.cs',H/'NativeCarrier113.cs',H/'NativeCarrier115.cs',R/'joint-lid107/LiveSurface107.cs',R/'aperture-runtime111/WholeEye111.cs',R/'joint-lid107/HairDrawScope107.cs',R/'argon23-runtime113/SourcePigmentStream113.cs',H/'RegionDriver113.cs',H/'RegionDriver115.cs',H/'Forward115.cs',R/'live-curve106/MotionClose106.cs',R/'joint-lid107/HoldMorph107.cs',R/'aperture-runtime111/Sequence111.cs']
s=(H/'Capture115.cs').read_text(encoding='utf8')
old='public void Execute(ExecutionResult result)\n {'
assert old in s
c=s.replace(old,'public void Execute(ExecutionResult result){result.Log("115 external complete sources compile only; no Play");}\n void Prepared115(ExecutionResult result)\n {',1)
compileSource=H/('Compile115'+suffix+'.cs');compileRun=H/('RUN_Compile115'+suffix+'.cs.txt');assert not compileRun.exists(),'Executed sources are immutable'
compileSource.write_text(c,encoding='utf8')
bundle(deps+[compileSource],compileRun)
assert not(H/'Capture115_REQUEST.json').exists(),'Do not overwrite a dispatched capture bundle'
bundle(deps+[H/'Capture115.cs'],H/'RUN_Capture115.cs.txt')
(H/'GLOBAL_NAMES66.json').write_bytes((R/'argon23-runtime113/GLOBAL_NAMES66.json').read_bytes())
print('Complete external115 sources bundled; no Unity call')
