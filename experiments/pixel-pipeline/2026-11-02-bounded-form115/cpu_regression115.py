"""Offline regression of frozen bindings and cached control flow. No shader compiler."""
from pathlib import Path
import copy, json, struct
import numpy as np
from cpu_tokens115 import VM

H = Path(__file__).resolve().parent

def validate(fixture, blobs):
    k, w, h = fixture['keyCount'], fixture['width'], fixture['height']
    assert 0 < k <= 32 and w > 0 and h > 0 and w * h <= 512, 'uniform bounds'
    strides = {'keys': 48, 'moments': 32, 'references': 32, 'frame': 16, 'points': 16, 'tags': 16, 'best': 48, 'candidates': 16}
    counts = {'keys': k, 'moments': w * h * k, 'references': k, 'frame': 64, 'points': 48, 'tags': w * h, 'best': 2, 'candidates': fixture['candidateCount']}
    for name, stride in strides.items(): assert len(blobs[name]) == stride * counts[name], ('stride/count', name)
    frame = np.frombuffer(blobs['frame'], '<u4').reshape(2, 32, 4)
    points = np.frombuffer(blobs['points'], '<u4').reshape(2, 24, 4)
    candidates = np.frombuffer(blobs['candidates'], '<u4').reshape(-1, 4)
    assert fixture['stages'][1]['groups'] == [len(candidates), 1, 1], 'reviewed slot0 only'
    for eye in range(2):
        n = int(frame[eye, 0, 0]); assert 0 <= n <= 24, 'point count bound'
        assert np.all(points[eye, :n, 0] < w * h), 'cell index bound'
    n = int(frame[0, 0, 0]); assert n == fixture['pointCount']
    assert np.all(candidates[:, :2] < (1 << n)), 'candidate bit outside current points'
    for name in ['keys', 'moments', 'references', 'best']:
        # best has integer metadata, so finite checks apply to its float score only.
        values = np.frombuffer(blobs[name], '<f4')
        if name == 'best': values = values.reshape(2, 12)[:, :4]
        assert np.isfinite(values).all(), ('nonfinite input', name)

def main():
    fixture = json.loads((H / 'FIXTURE115.json').read_text())
    packet = json.loads((H / 'CACHED_EVALUATE_DECODED115.json').read_text())
    blobs = {name: (H / info['file']).read_bytes() for name, info in fixture['files'].items()}
    tests = []
    validate(fixture, blobs); tests.append('Frozen binary stride/size, uniform, point/cell and mask ranges')
    wrapper = json.loads((H / 'CACHE_BINDING_BYTES115.json').read_text())
    following = {row['name']: row['nextEightUInt32'] for row in wrapper['rows']}
    expected_offsets = {'_CurveEyeIds106': 484, '_KeyCount113': 496, '_CellsSize113': 560}
    expected_slots = {'_Keys113': 0, '_CellTags113': 0, '_Frame113': 1, '_Points113': 2, '_CellKey115': 3, '_ReferenceKey115': 4, '_FormState115': 5, '_Candidates115': 6, '_Metrics115': 7}
    assert all(following[name][1] == offset for name, offset in expected_offsets.items())
    assert all(following[name][1] == slot for name, slot in expected_slots.items())
    tests.append('Cache wrapper bytes agree with interpreted constant offsets and SRV/UAV slots; not actual GPU binding contents')
    changes = [('zero width', {'width': 0}, None), ('key count33', {'keyCount': 33}, None)]
    for name, offset, value in [('point count25', 0, 25), ('cell144', 0, 144), ('mask beyond nine points', 0, 512)]:
        target = {'point count25': 'frame', 'cell144': 'points', 'mask beyond nine points': 'candidates'}[name]
        changed = dict(blobs); data = bytearray(changed[target]); struct.pack_into('<I', data, offset, value); changed[target] = data
        changes.append((name, {}, changed))
    changed = dict(blobs); changed['moments'] = changed['moments'][:-4]; changes.append(('short moment buffer', {}, changed))
    for name, edits, data in changes:
        candidate = dict(fixture, **edits)
        rejected = False
        try: validate(candidate, data or blobs)
        except AssertionError: rejected = True
        assert rejected, name
        tests.append('Reject ' + name)
    baseline = [VM(packet, fixture, tid).run() for tid in range(2)]
    reversed_blob = bytearray(blobs['candidates'][16:] + blobs['candidates'][:16])
    reversed_results = []
    for tid in range(2):
        vm = VM(packet, fixture, tid); vm.buffers[('u', 6)] = reversed_blob.copy()
        result = vm.run(); assert result['metricWords'] == baseline[1 - tid]['metricWords']
        reversed_results.append(result['steps'])
    tests.append('Candidate permutation changes output slots only; exact metric words preserved')
    vm = VM(packet, fixture, 0); vm.buffers[('u', 6)][:16] = bytes(16)
    empty = vm.run(); assert empty['info'] == [20, 0, 0, 0]
    keys = np.frombuffer(blobs['keys'], '<f4').reshape(-1, 12)
    refs = np.frombuffer(blobs['references'], '<f4').reshape(-1, 8)
    available = [int(((keys[:, 2] == 2) & (keys[:, 3] == part) & (refs[:, 4] > 0)).sum()) for part in [1, 4]]
    missing = [n * (n - 1) // 2 for n in available]
    assert [empty['metricFloats'][2], empty['metricFloats'][8]] == missing
    tests.append('Observed0: missing pairs equal n*(n-1)/2; absent relative geometry remains invalid')
    vm = VM(packet, fixture, 0); vm.buffers[('u', 4)] = bytearray(len(blobs['references']))
    empty_source = vm.run(); assert empty_source['info'] == [20, 0, 0, 0]
    assert all(v == 0 for v in empty_source['metricFloats'])
    tests.append('Available0: pair arithmetic has no unsigned-underflow loop; relative dimensions remain absent')
    # Strict budget makes a VM control-flow regression fail locally rather than run indefinitely.
    vm = VM(packet, fixture, 0)
    try: vm.run(budget=100)
    except AssertionError as error: assert 'budget exhausted' in str(error)
    else: raise AssertionError('Budget guard did not stop execution')
    tests.append('CPU interpreter hard step budget stops incomplete interpretation')
    report = {'passed': len(tests), 'tests': tests, 'GPUOrUnityOrCompilerInvocations': 0,
              'baselineSteps': [r['steps'] for r in baseline], 'reversedSteps': reversed_results,
              'activeSourceKeysByPart': available, 'emptyCandidateMissingPairs': missing,
              'sourceOfBounds': 'Reviewed115 capacity32keys/24points; microfixture slot0 two candidates; not a GPU-content attestation',
              'productionApplied': False, 'rootCauseConfirmed': False}
    (H / 'CPU_REGRESSION115.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))

if __name__ == '__main__': main()
