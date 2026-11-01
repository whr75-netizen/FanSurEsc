from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
s=(REPO/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeSurface348.shader').read_text();s=s.replace('Shader "EValidation/EyeSurface348"','Shader "EValidation/ProductionTrace92"',1)
# Source name can differ from its filename. Replace only its leading declaration.
first=s.splitlines()[0];s=s.replace(first,'Shader "EValidation/ProductionTrace92"',1)
s=s.replace('float4 _ClipShift333,','#include "Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ProbeLight91.hlsl"\nfloat4 _ClipShift333,',1)
s=s.replace('O333 o;o.shade=0;','O333 o;o.shade=0;float4 normal92=0,sh92=0,totals92=0;')
s=s.replace('ContinuousSurfaceLight335(v,material)','ProbeLight91(v,material,f.facing,normal92,sh92,totals92)')
end='o.uv=float4(uv,primitiveID+1,_SupportKind348);return o;'
assert end in s;s=s.replace(end,'o.uv=float4(uv,primitiveID+1,_SupportKind348);if(_SupportKind348==3){o.restPosition=normal92;o.uv=sh92;o.shade=float4(o.shade.x,totals92.x,totals92.y,totals92.z);}return o;')
path=HERE/'shaders91/ProductionTrace92.shader'
assert not path.exists()
print('*** Begin Patch\n*** Add File: '+path.relative_to(Path.cwd()).as_posix()+'\n'+''.join('+'+line+'\n'for line in s.splitlines())+'*** End Patch')
