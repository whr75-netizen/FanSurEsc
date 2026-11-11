"""Correct only the historical source material tag; no shader change/import."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'surface27'
sys.path.insert(0,str(H));from prepare_surface27 import bind_pigment_material27
from prepare_support import replace
sys.path.insert(0,str(H.parent));from prepare_live import compile_cs
def main():
 motion='--motion'in sys.argv;seed=G/('pigment-run'if motion else'phase-run');run=G/('pigment-motion'if motion else'pigment-run')
 assert not(run/'PHASE_REQUEST.json').exists();run.mkdir(exist_ok=True)
 state=json.loads((seed/'STATE113-0012-finished.json').read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError')
 host=(seed/'RUN_Capture25.cs.txt').read_text().replace(str(seed),str(run))
 if motion:
  host=replace(host,'MotionClose106 motion82;','MotionScope97 motion82;');host=replace(host,'motion82=new MotionClose106(n,output);','motion82=new MotionScope97(n,output);');host=replace(host,'if(captured76>=4)','if(captured76>=28)')
 else:host=bind_pigment_material27(host)
 source=run/'RUN_Capture25.cs.txt';source.write_text(host,encoding='utf-8',newline='\n');compile_cs(source)
 (run/'GLOBAL_NAMES66.json').write_bytes((seed/'GLOBAL_NAMES66.json').read_bytes())
 metadata='PIGMENT_MOTION_PREPARED.json'if motion else'PIGMENT_PREPARED.json'
 relay=(G/'relay.py').read_text().replace("assert mode in ['import','phase']","assert mode in ['phase']")
 relay=replace(relay,"root=H if mode=='import'else H/'phase-run'","root=H/"+repr(run.name));relay=replace(relay,"contract=load(H/'LIVE_PREPARED.json')","contract=load(H/"+repr(metadata)+")")
 rp=G/('relay_pigment_motion.py'if motion else'relay_pigment.py');rp.write_text(relay,encoding='utf-8',newline='\n')
 result={'captureSourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'CPUCompiled':True,'framesBound':28 if motion else 4,'shaderChanged':False,'newImport':False,'newGPUBuffer':False,'proofTag':'existing semantic part3 / native submesh6 / renderer1; actual material obtained from current triangle map, not hardcoded RGB/material name','GPUExecuted':False}
 (G/metadata).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
