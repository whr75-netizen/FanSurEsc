from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'motion';D=H/'ties'
D.mkdir(exist_ok=False)
for mode in ['Compile','Capture','Post']:
 for run in [False,True]:
  p=O/(('RUN_'if run else'')+mode+'102'+('.cs.txt'if run else'.cs'));s=p.read_text(encoding='utf-8').replace(str(O),str(D))
  if mode in ['Compile','Capture']:
   point='   readyAllocated=Profiler.GetTotalAllocatedMemoryLong();'
   assert s.count(point)==1
   s=s.replace(point,'   if(motion82.Stage=="measured-phase"){if(!motion82.Advance())throw new InvalidOperationException("102 witness walk not reached");armedSerial=n.host.main.renderedSerial335;return;}\n'+point)
   s=s.replace('   if(motion82.Advance()){','   if(captured76>=1){BeginExit();return;}\n   if(motion82.Advance()){')
   point='JointBuffer102("canonical-decision",forward102.Source.Engine.Decisions);'
   assert s.count(point)==1
   s=s.replace(point,point+'JointBuffer102("canonical-layers",forward102.Source.Engine.Layers);JointBuffer102("canonical-visibility",forward102.Source.Engine.Visibility);AuxMesh("current-face102",e.sampleFace,h.motion.surface.outputs[1].transform.localToWorldMatrix,hf);\n  report["ties102Purpose"]="one actual first-walk input; exact unresolved cell part areas/depths, not repeated beauty tuning";report["headMatrix102"]=M(e.headMatrix);')
  (D/p.name).write_text(s,encoding='utf-8')
(D/'GLOBAL_NAMES66.json').write_bytes((O/'GLOBAL_NAMES66.json').read_bytes());(D/'relay102.py').write_bytes((O/'relay102.py').read_bytes());print('102 first-walk input-only witness: no phase readbacks, one frame, bounded layers/visibility/current face. No Unity calls.')
