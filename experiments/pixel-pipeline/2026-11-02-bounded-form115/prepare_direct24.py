"""Prepare an unimported three-site113 shader candidate. Never compiles it."""
from pathlib import Path
import difflib, hashlib, json, re
from direct_support24 import H, P

def sha(data): return hashlib.sha256(data).hexdigest()

def main():
    original = (P / 'ForwardEye113.compute').read_text(encoding='utf-8')
    assert 'EvaluateForm115' not in original and 'Down115' not in original
    assert '.b.z' not in original and '.tail.z' not in original, 'Reserved fields must be unused in the source being patched'
    replacements = [
        ('return a.tail.x<b.tail.x;', 'if(asfloat(a.tail.z)!=asfloat(b.tail.z))return asfloat(a.tail.z)>asfloat(b.tail.z);return a.tail.x<b.tail.x;'),
        ('float cost=0;bool valid=true;', 'float cost=0,directMass24=0;bool valid=true;'),
        ('cost+=K113-mass.x-mass.z-(part==0?mass.x:mass.z);', 'cost+=K113-mass.x-mass.z-(part==0?mass.x:mass.z);directMass24+=part==0?mass.x:mass.z;'),
        ('outValue.b=uint4(asuint(cost),valid?1:0,0,0);', 'outValue.b=uint4(asuint(cost),valid?1:0,asuint(directMass24),0);'),
        ('r.tail=uint4(countbits(active.z&~(a.a.z|b.a.z)),1,0,0);', 'r.tail=uint4(countbits(active.z&~(a.a.z|b.a.z)),1,asuint(asfloat(a.b.z)+asfloat(b.b.z)),0);')
    ]
    changed = original
    for before, after in replacements:
        assert changed.count(before) == 1, before
        changed = changed.replace(before, after)
    # Both the old error and original source-key fallback are deliberately
    # retained. Direct matched mass is inserted before that fallback.
    assert 'cost+=K113-mass.x-mass.z-' in changed
    assert 'EvaluateForm115' not in changed and 'Pareto115' not in changed and 'Stat115' not in changed
    assert re.findall(r'#pragma kernel (\w+)', changed) == re.findall(r'#pragma kernel (\w+)', original)
    (H / 'ForwardEye113_Direct24.compute').write_bytes(changed.encode('utf-8'))
    patch = ''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True), fromfile='a/ForwardEye113.compute', tofile='b/ForwardEye113_Direct24.compute'))
    (H / 'DirectSupport24.patch').write_text(patch, encoding='utf-8')
    touched = [name for name in ['Less113', 'BuildSubsets113', 'Enumerate113']]
    report = {'base': str(P / 'ForwardEye113.compute'), 'baseSHA256': sha((P / 'ForwardEye113.compute').read_bytes()),
              'baseNormalizedLFSHA256': sha(original.encode()), 'candidateSHA256': sha((H / 'ForwardEye113_Direct24.compute').read_bytes()),
              'functionsChanged': touched, 'extraKernels': 0, 'extraBuffers': 0, 'layoutStrideChanges': 0,
              'Subset113_b_z': 'bit pattern of float32 direct matching mass, not rounded uint mass',
              'Group113_tail_z': 'bit pattern of float32 sum of selected I/W matching mass',
              'tieOrder': ['four existing primary scores', 'maximum direct matched mass', 'minimum existing missing source keys', 'consensus of all remaining ties'],
              'EvaluateOrPareto115InCandidate': False, 'intervalBitHelpers115InCandidate': False,
              'existing113PrivateArraysElsewhereRetained': True, 'compiledDXBCZeroScratchClaim': False,
              'compiled': False, 'AssetsImported': False, 'runtimeApplied': False, 'GPUExecuted': False,
              'remainingIntegration': 'Geometry24 transport/ring/curve changes are CPU-tested separately, not silently merged into this shader. Full113 driver still needs a separately reviewed candidate-only path without baseline duplication or synchronous readback.'}
    (H / 'DIRECT_PATCH24.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__': main()
