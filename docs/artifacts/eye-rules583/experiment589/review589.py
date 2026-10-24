from pathlib import Path
from fractions import Fraction as Q
import sys,json,hashlib
import numpy as np
R=Path(__file__).parent
sys.path.insert(0,str(R.with_name('EyeArea585')))
from geometry_oracle585 import Frame
j=json.loads((R/'REAL_INPUT589.json').read_text())
f=Frame(0,R.with_name('EyeFollow584')/'Runtime584/OneCase2',R.with_name('EyeArea585')/'Runtime585/Geometry2')
x,y=j['selectedTile'];checks=[]
for q in j['oldGridChecks']:
    index=q['sample'];shader_index=(3-index//4)*4+index%4
    q=dict(q,shaderSample=shader_index)
    depth_errors=[]
    for role,layer,prim in [('reference',q['referenceLayer'],q['referencePrimitive']),('support',q['supportLayer'],q['supportPrimitive'])]:
        original=next(z for z in f.samples if int(z['cellX'])==x and int(z['cellY'])==y and int(z['k'])==shader_index and int(z['support'])==int(layer))
        q[role+'MatchesSavedGPUPrimitive']=round(float(original['primitive']))==prim
        q[role+'SavedGPUAlpha']=float(original['alpha'])
        assert q[role+'MatchesSavedGPUPrimitive'] and float(original['pointValid'])>.5 and round(float(original['eye']))==2
        tri=next(t for t,z in enumerate(f.tr)if f.s[t]==int(layer)and f.prim[t]==prim)
        pt=np.array([x+(index%4+.5)/4,y+(index//4+.5)/4,1])
        depth_errors.append(abs(float(pt@f.depth[tri])-float(original['depth'])))
    q['maxSavedGPUDepthError']=max(depth_errors);checks.append(q)
summary=dict(status=j['status'],selectedTile=j['selectedTile'],referenceSupportPairs=len(j['referenceSupportMapping']),
    referenceSupportLayerPairs=sorted(set((v['referenceLayer'],v['supportLayer'])for v in j['referenceSupportMapping'])),
    limits='Actual certified subset only exercises S0 reference/S0 support. Real S3 fallback remains alpha-uncertain; not falsely counted as passed.',
    coreLower=float(Q(j['core']['lower'])),coreUpper=float(Q(j['core']['upper'])),unknownAreaUpper=float(Q(j['unknownAreaUpper'])),
    nominalTotalLower=float(Q(j['totalLower'])),nominalTotalUpper=float(Q(j['totalUpper'])),
    nominalTotalWidth=float(Q(j['totalUpper'])-Q(j['totalLower'])),coreSeconds=j['core']['seconds'],
    totalSecondsIncludingInputLoad=j['secondsIncludingInputLoad'],providerClipCalls=j['providerClipCalls'],providerDepthPairs=j['providerDepthPairs'],
    savedGPUChecks=checks,savedGPUPointCount=len(checks),maxSavedGPUDepthError=max(q['maxSavedGPUDepthError']for q in checks),
    actualGPUContinuousAreaCertified=False,productConnected=False)
(R/'REVIEW589.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items()if k!='savedGPUChecks'},indent=2))
