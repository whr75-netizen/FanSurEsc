"""Reuse corrected runtime candidate for existing28-frame motion regression."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'gate-alpha';RUN=G/'motion-run'
sys.path.insert(0,str(H));from prepare_support import replace
sys.path.insert(0,str(H.parent));from prepare_live import compile_cs
def main():
 global G,RUN
 native='--native-proof'in sys.argv
 if native:G=H/'native-proof';RUN=G/'motion-run'
 if '--surface'in sys.argv:G=H/'surface27';RUN=G/'motion-run'
 seed=G/('typed-run'if native else'phase-run')
 assert not(RUN/'PHASE_REQUEST.json').exists()and not(RUN/'CAPTURE_STARTED76.json').exists()
 state=json.loads((seed/'STATE113-0012-finished.json').read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError')
 RUN.mkdir(exist_ok=True)
 s=(seed/'RUN_Capture25.cs.txt').read_text().replace(str(seed),str(RUN))
 s=replace(s,'MotionClose106 motion82;','MotionScope97 motion82;');s=replace(s,'motion82=new MotionClose106(n,output);','motion82=new MotionScope97(n,output);')
 s=replace(s,'if(captured76>=4)','if(captured76>=28)').replace('boundedTwoPhaseFrames25','boundedMotion28Frames26')
 source=RUN/'RUN_Capture25.cs.txt';source.write_text(s,encoding='utf-8',newline='\n');compile_cs(source)
 (RUN/'GLOBAL_NAMES66.json').write_bytes((seed/'GLOBAL_NAMES66.json').read_bytes())
 relay=(G/'relay.py').read_text();relay=replace(relay,"assert mode in ['import','phase']","assert mode in ['phase']")
 relay=replace(relay,"root=H if mode=='import'else H/'phase-run'","root=H/'motion-run'")
 relay=replace(relay,"contract=load(H/'LIVE_PREPARED.json')","contract=load(H/'MOTION_PREPARED.json')")
 relay=relay.replace('Four evaluated Open Close75 Close100 reopen states then normal exit and restore','Existing28 measured-phase walk turn frames then normal exit and restore')
 (G/'relay_motion.py').write_text(relay,encoding='utf-8',newline='\n')
 d={'captureSourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'CSharpCPUCompiled':True,'framesBound':28,
  'producerFramesBound':64,'existingMotionScope97Reused':True,'shaderChanged':False,'newImport':False,'GPUOrUnityExecuted':False}
 (G/'MOTION_PREPARED.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');print(json.dumps(d))
if __name__=='__main__':main()
