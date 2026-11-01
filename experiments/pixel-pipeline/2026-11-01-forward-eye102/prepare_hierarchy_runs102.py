from pathlib import Path
H=Path(__file__).resolve().parent
for old,new in [('capture','captureH'),('motion','motionH')]:
 O=H/old;D=H/new;D.mkdir(exist_ok=False)
 for mode in ['Compile','Capture','Post']:
  for run in [False,True]:
   name=('RUN_'if run else'')+mode+'102'+('.cs.txt'if run else'.cs');s=(O/name).read_text(encoding='utf-8').replace(str(O),str(D))
   if mode in ['Compile','Capture']:
    s=s.replace('report["noExperimental98or99"]=true;','report["noExperimental98or99"]=true;report["forwardComputeSHA102"]=SHA("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye102.compute");report["selectionHierarchy102"]="eye union vs canvas, then child coverage, unique source depth only for exact part ties";')
    if old=='motion':
     point='JointBuffer102("canonical-decision",forward102.Source.Engine.Decisions);';assert s.count(point)==1;s=s.replace(point,point+'JointBuffer102("canonical-layers",forward102.Source.Engine.Layers);JointBuffer102("canonical-visibility",forward102.Source.Engine.Visibility);')
   (D/name).write_text(s,encoding='utf-8')
 (D/'GLOBAL_NAMES66.json').write_bytes((O/'GLOBAL_NAMES66.json').read_bytes());(D/'relay102.py').write_bytes((O/'relay102.py').read_bytes())
O=H/'Import102.cs';s=O.read_text(encoding='utf-8').replace(str(H/'capture'),str(H/'captureH'));(H/'ImportHierarchy102.cs').write_text(s,encoding='utf-8')
import sys
sys.path.insert(0,str(H.parent/'boundary-input69'));from prepare73 import bundle
bundle([H.parent/'apply-capture66/Json58Linear66.cs',H.parent/'eye-observer73/CreateOnly73.cs',H/'ImportHierarchy102.cs'],H/'captureH/RUN_Import102.cs.txt')
print('102 hierarchy-only reruns prepared; 9actualClose +28normalMotion; motion carries bounded frozen GPU source for CPU equivalence')
