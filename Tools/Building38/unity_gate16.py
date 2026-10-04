"""Final gate reads actual Unity observations and GPU captures, not art approval."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

path=Path(sys.argv[1]).resolve();j=json.loads(path.read_text(encoding='utf-8'))
fail=[]
if j.get('phase')=='probe':
    a=np.asarray(Image.open(path.parent/j['beforeFile']).convert('RGBA'))
    b=np.asarray(Image.open(path.parent/j['afterFile']).convert('RGBA'))
    count=int(np.count_nonzero(np.any(a!=b,axis=-1)))
    if count<100: fail.append('Engine illumination changed too few pixels')
    if not j.get('sameMaterialMaps') or not j.get('sameRenderer'): fail.append('Immutable input or renderer changed')
    if j.get('shaderErrorCount')!=0: fail.append('Shader compiler errors')
    print(json.dumps({'gpu_changed_pixels':count,'failures':fail}))
else:
    if not j.get('isPlayMode'):fail.append('Actual gameplay observation required')
    if j.get('boundInstanceCount')!=26 or j.get('sharedObjectTypes')!=18:fail.append('Interior binding count')
    if j.get('unmatchedSources'):fail.append('Unmatched source instances')
    if abs(j.get('cameraPitch',0)-30)>.01 or abs(j.get('cameraYaw',0)-350)>.01:fail.append('Gameplay view changed')
    if not j.get('samePlayer') or not j.get('sameCamera'):fail.append('Gameplay identity changed')
    if j.get('insideCount',0)<1 or j.get('hiddenRoofCount',0)<1:fail.append('Roof cutaway observation')
    if j.get('shaderErrorCount')!=0:fail.append('Shader compiler errors')
    a=np.asarray(Image.open(path.parent/j['lightOnFile']).convert('RGBA'))
    b=np.asarray(Image.open(path.parent/j['lightOffFile']).convert('RGBA'))
    changed=int(np.count_nonzero(np.any(a!=b,axis=-1)))
    if changed<100:fail.append('Actual interior local-light reaction absent')
    print(json.dumps({'changed_pixels':changed,'failures':fail}))
if fail:raise SystemExit(2)
