"""Offline compilation/test of exact patch owner + binding with CPU fakes. No Unity."""
from pathlib import Path
import hashlib, json, re, subprocess, sys

HERE = Path(__file__).resolve().parent
REPO = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
CSC = Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe')
CLOTH = 'Assets/EUnityValidation01/ClothRegion524/Runtime/ClothRegion524.cs'
FULL = 'Assets/EUnityValidation01/MinimalRestore335/Runtime/Full319View335.cs'

def method(text, signature):
    start = text.index(signature)
    begin = text.index('{', start)
    depth = 1
    for i in range(begin + 1, len(text)):
        depth += (text[i] == '{') - (text[i] == '}')
        if depth == 0:
            return text[start:i+1]
    raise AssertionError('method not closed')

def run():
    candidate = (HERE/'candidate'/CLOTH).read_text(encoding='utf-8')
    before = (HERE/'before'/CLOTH).read_text(encoding='utf-8-sig')
    fragment = (HERE/'BodyScopeOwner65.fragment.cs').read_text(encoding='utf-8')
    assert fragment.rstrip() in candidate
    probe = method(candidate, 'public static void BeginProbe(')
    assert 'SetGlobalBuffer' not in candidate
    assert 'SetBuffer("_BodyScope551",buffer)' in probe
    assert 'ScopeBuffer551()' not in candidate
    assert candidate.count('"_BodyScope551",ScopeBuffer551(f)') == 1
    assert candidate.count('"_BodySource553",ScopeBuffer551(f)') == 1
    full = (HERE/'candidate'/FULL).read_text(encoding='utf-8')
    disable = method(full, 'void OnDisable(')
    assert disable.index('ClothRegion524.ReleaseScope551(this)') < disable.index('if(!ready)return')
    # Exact original eligibility expression: only staging variables/atomic commit differ.
    predicate = '!vertex[ix[3*pr]]&&!vertex[ix[3*pr+1]]&&!vertex[ix[3*pr+2]]'
    assert before.count(predicate) == candidate.count(predicate) == 1
    source_test = [
        ('eligibility unchanged', True), ('no global buffer writer', True),
        ('compute and lines kernel-local', True), ('cleanup before ready guard', True),
        ('two-file patch only', len(json.loads((HERE/'PATCH_MANIFEST65.json').read_text())['files']) == 2),
    ]
    output = HERE/'.run'
    output.mkdir(exist_ok=True)
    harness = (HERE/'Harness65.cs').read_text(encoding='utf-8')
    harness = harness.replace('// CANDIDATE_OWNER', fragment)
    harness = harness.replace('// CANDIDATE_BEGIN_PROBE', probe)
    src = output/'Extracted65.cs'
    src.write_text(harness, encoding='utf-8')
    exe = output/'Ownership65.exe'
    c = subprocess.run([str(CSC), '/nologo', '/warnaserror+', '/out:'+str(exe), str(src)], capture_output=True, text=True)
    (HERE/'COMPILE65.txt').write_text(c.stdout+c.stderr, encoding='utf-8')
    assert c.returncode == 0, c.stdout+c.stderr
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    (HERE/'LIFECYCLE65.txt').write_text(r.stdout+r.stderr, encoding='utf-8')
    assert r.returncode == 0, r.stdout+r.stderr
    m = re.search(r'CASES (\d+) CREATED (\d+) RELEASED (\d+)', r.stdout)
    assert m and m[2] == m[3]
    manifest = json.loads((HERE/'PATCH_MANIFEST65.json').read_text(encoding='utf-8'))
    current_same = []
    for entry in manifest['files']:
        actual = hashlib.sha256((REPO/entry['path']).read_bytes()).hexdigest()
        assert actual == entry['working_copy_sha256'], 'current Assets changed since snapshot'
        current_same.append(entry['path'])
    result = {'status': 'OFFLINE_TESTED_UNAPPLIED', 'source_invariants': source_test,
              'cpu_fake_lifecycle_cases': int(m[1]), 'fake_allocations': int(m[2]),
              'fake_releases': int(m[3]), 'current_asset_files_sha_unchanged': current_same,
              'compiled': 'exact candidate owner fragment + exact BeginProbe + CPU fakes',
              'not_compiled': 'full Unity assemblies, renderer, shaders',
              'unity_calls': 0, 'gpu_dispatches': 0, 'patch_applied': False,
              'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest()}
    (HERE/'VALIDATION65.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    run()
