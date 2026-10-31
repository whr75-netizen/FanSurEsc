from pathlib import Path
import difflib,hashlib,json
import numpy as np
from keyform51 import KeyForm51
R=Path(__file__).resolve().parent
B=json.loads((R/'KEYFORM_BUNDLE51.json').read_text(encoding='utf8'));K=KeyForm51(B)
checks=[]
def check(n,v):
    if not bool(v):raise AssertionError(n)
    checks.append(n)
for y in range(33):
    for x in range(33):
        q=K.reference_layer(K.key,'existing-open-reference',[x/32,y/32]);t=np.array(q['translation'])
        check('all cached cells share root translation',all(np.array_equal(np.array(a['xy'])-t,b['referenceXY'])for a,b in zip(q['cells'],B['cells'])))
        check('literal pigments/family kept',all(a['rgba8']==b['rgba8']and a['role']==b['role']and a['cellId']==b['cellId']for a,b in zip(q['cells'],B['cells'])))
        for e,base in zip(q['eyes'],B['eyes']):
            check('parent/iris curves use same transform as cells',np.allclose(np.array(e['parent'])-t,base['parent'],rtol=0,atol=1e-12)and np.allclose(np.array(e['iris'])-t,base['iris'],rtol=0,atol=1e-12))
            check('upper/lower paths share parent vertices and endpoints',e['upperLidPath'][0]==e['lowerLidPath'][0]and e['upperLidPath'][-1]==e['lowerLidPath'][-1])
for state in['blink50','blink100','unknownYaw']:
    try:K.reference_layer(K.key,state,[0,0])
    except ValueError:pass
    else:raise AssertionError('Unregistered state reused open pixels')
check('source bundle unchanged after placements',K.source==B)
native=[]
for name,morph in B['nativeClosingMorphs'].items():
    for eye in[1,2]:
        records=[K.native_lid_geometry(name,eye,w)for w in[0,50,100]]
        a,b,c=[np.array(q['nativeRestHeadPoints'])for q in records]
        check('native 50 geometry follows source morph, not invented key-form',np.max(abs(b-(a+c)*.5))<2e-7)
        check('closed geometry does not claim registered closed pixel form',not records[-1]['pixelKeyFormAvailable'])
        native.append(dict(source=name,eye=eye,changedRingVertices=int((np.linalg.norm(c-a,axis=1)>0).sum()),maxHeadDelta=float(np.max(np.linalg.norm(c-a,axis=1)))))
P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01')
shader=P/'EyeBoundaryRestore348/Shaders/EyeSkin348.shader';old=shader.read_text(encoding='utf8')
new=old.replace('Shader "EValidation/EyeSkin348"','Shader "EValidation/EyeSkin348_ControlEvidence51"',1)
needle='float4 uv:SV_Target3;};';replacement='float4 uv:SV_Target3;float4 control:SV_Target4;};'
check('actual S0 supplier has four original MRT fields',new.count(needle)==1)
new=new.replace(needle,replacement,1)
end='o.uv=float4(uv,primitiveID+1,_SupportKind348);return o;'
changed='o.uv=float4(uv,primitiveID+1,_SupportKind348);o.control=float4(v.e202Control.xy,0,alpha);return o;'
check('one actual skin control output connection',new.count(end)==1)
new=new.replace(end,changed,1)
(R/'EyeSkin348_control51.shader').write_text(new,encoding='utf8')
(R/'CONTROL_OUTPUT_ONLY.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='actual S0 supplier EyeSkin348',tofile='workspace-only EyeSkin348_ControlEvidence51')),encoding='utf8')
undo=new.replace('Shader "EValidation/EyeSkin348_ControlEvidence51"','Shader "EValidation/EyeSkin348"',1).replace(replacement,needle,1).replace(changed,end,1)
check('all original colour/alpha/depth/UV/role operations unchanged',undo==old)
result=dict(passed=len(checks),checks=checks,nativeMorphRingChanges=native,
    sourceShaderSHA256=hashlib.sha256(shader.read_bytes()).hexdigest(),newGPUCalls=0,productModified=False,newCommit=False,
    controlIsNotSemanticLidMask=True,closedPixelFormRegistered=False,candidateGPUCompiled=False)
(R/'BRIDGE_TESTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items()if k!='checks'},ensure_ascii=False,indent=2))
