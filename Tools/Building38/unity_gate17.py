"""Only actual matching GPU pixels and gameplay observations pass N17."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

def integer_native_scale(value):
    # Unity float32 reports one native screen pixel as 0.99999994.
    # Apply the same .001px tolerance to the minimum and integer distance.
    return np.isfinite(value) and value >= 1-.001 and abs(value-round(value)) <= .001

path=Path(sys.argv[1]).resolve(); j=json.loads(path.read_text(encoding='utf-8')); failures=[]
if j.get('phase')=='probe':
    comparisons=[]
    for ident in ['empty_counter','stock_shelf','floor_surface']:
        a=np.asarray(Image.open(path.parent/ident/'preview.png').convert('RGBA')).astype(int)
        b=np.asarray(Image.open(path.parent/ident/'gpu-fixture.png').convert('RGBA')).astype(int)
        if a.shape!=b.shape: failures.append(ident+': domain mismatch'); continue
        mask=a[...,3]>127; mismatch=int(np.count_nonzero(mask!=(b[...,3]>127)))
        error=int(np.max(np.abs(a[mask,:3]-b[mask,:3]))) if np.any(mask) else 0
        comparisons.append({'asset':ident,'coverage_mismatch':mismatch,'max_rgb_error':error})
        if mismatch or error>2: failures.append(ident+': GPU parity')
    print(json.dumps({'comparisons':comparisons,'failures':failures}))
else:
    required={'isPlayMode':True,'samePlayer':True,'sameCamera':True,'boundInstanceCount':26,'sharedObjectTypes':18,'nativeSurfaceCount':44,'shaderErrorCount':0}
    failures += [k for k,v in required.items() if j.get(k)!=v]
    if abs(j.get('cameraPitch',0)-30)>.01 or abs(j.get('cameraYaw',0)-350)>.01:failures.append('camera orientation')
    for k in ['sourcePixelsOnScreen','floorPixelsOnScreen','scenePixelsOnScreen']:
        value=j.get(k,0)
        if not integer_native_scale(value):failures.append(k)
    if abs(j.get('floorPixelsOnScreen',0)-j.get('sourcePixelsOnScreen',1))>.001:failures.append('floor/object spacing')
    if not j.get('nightDefault') or j.get('insideCount',0)<1 or j.get('hiddenRoofCount',0)<1:failures.append('night/cutaway')
    motion=j.get('motionPositions',[])
    if len(motion)<6 or max(p[0] for p in motion)<2.5 or min(p[0] for p in motion)>-2.5:failures.append('actual left/right motion')
    files=j.get('motionFiles',[])
    if len(files)<6:failures.append('motion captures')
    else:
        a=np.asarray(Image.open(path.parent/files[1]).convert('RGB')); b=np.asarray(Image.open(path.parent/files[5]).convert('RGB'))
        changed=int(np.count_nonzero(np.any(a!=b,axis=-1)))
        if changed<100:failures.append('moving light surface reaction')
        print(json.dumps({'motion_changed_pixels':changed}))
    print(json.dumps({'failures':failures}))
if failures:raise SystemExit(2)
