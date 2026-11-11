"""Selectively preserve the public lifecycle audit; never calls Unity or the GPU."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

H = Path(__file__).resolve().parent
R = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
P = 'experiments/pixel-pipeline/2026-11-11-resume-argon25'
BASE = 'b2cd7b1da7b8a4df596418a80e1431ba9b1227ae'
ROOTS = ['PublicResources51.cs.txt', 'public_resources51.py', 'public_resource_details51.py',
         'tool_inventory51.py', 'audit_supported51.py', 'archive_support51.py', 'relay33.py']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=R, text=True, encoding='utf-8').strip()


def save(path, data):
    path.write_text(json.dumps(data, indent=2), encoding='utf-8', newline='\n')


def main():
    assert git('rev-parse', 'HEAD') == BASE
    assert not git('diff', '--cached', '--name-only')
    user = json.loads((H / 'RESUME_STATUS.json').read_text())['userTrackedFiles']
    assert len(user) == 30 and all(sha(R / p) == s for p, s in user.items())
    result = json.loads((H / 'face51/SUPPORTED_LIFECYCLE51.json').read_text())
    assert result['newGPUOperationsThisAudit'] == 0 and not result['ownedResourcesReleased']
    assert result['backup47FilesExactHash'] and not result['reflectionRecoveryRetried']
    files = ROOTS + [p.relative_to(H).as_posix() for p in (H / 'face51').rglob('*')
                     if p.is_file() and 'build' not in p.parts
                     and p.name not in ['SCHEMA.json', 'ARCHIVE51.json', 'COMMIT51.json', 'COMMIT_BODY51.txt']]
    files = sorted(set(files))
    rows = [{'path': p, 'bytes': (H / p).stat().st_size, 'SHA256': sha(H / p)} for p in files]
    save(H / 'face51/ARCHIVE51.json', {'baselineCommit': BASE, 'files': rows,
                                   'liveResourceRetentionNotResolved': True,
                                   'user30Equal': True, 'product77Changed': False})
    if '--publish' in sys.argv:
        for row in rows + [{'path': 'face51/ARCHIVE51.json', 'SHA256': sha(H / 'face51/ARCHIVE51.json')}]:
            source, target = H / row['path'], R / P / row['path']
            if target.exists() and sha(target) != row['SHA256']:
                assert row['path'] == 'relay33.py'
                old = subprocess.check_output(['git', 'show', BASE + ':' + P + '/relay33.py'], cwd=R)
                assert target.read_bytes().replace(b'\r\n', b'\n') == old.replace(b'\r\n', b'\n')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            assert sha(target) == row['SHA256']
        doc = R / 'docs/ai/PIXEL_ALBEDO_20261030.md'
        assert not git('diff', '--name-only', '--', str(doc))
        original = doc.read_bytes()
        addition = (H / 'face51/HANDOFF_APPEND51.md').read_bytes()
        assert addition not in original
        doc.write_bytes(original + addition)
        assert all(sha(R / p) == s for p, s in user.items())
    print(json.dumps({'files': len(rows) + 1, 'bytes': sum(r['bytes'] for r in rows),
                      'published': '--publish' in sys.argv, 'GPUCalls': 0,
                      'resourcesReleased': False, 'user30Equal': True}))
    if '--commit' in sys.argv:
        assert '--publish' in sys.argv
        names = [P + '/' + row['path'] for row in rows] + [P + '/face51/ARCHIVE51.json', 'docs/ai/PIXEL_ALBEDO_20261030.md']
        assert len(set(names)) == len(names) and not set(names).intersection(user)
        git('add', '--', *names)
        assert set(git('diff', '--cached', '--name-only').splitlines()) == set(names)
        # Keep executed-source CRLF bytes intact; still reject real trailing spaces.
        subprocess.run(['git', '-c', 'core.whitespace=trailing-space,space-before-tab,cr-at-eol',
                        'diff', '--cached', '--check'], cwd=R, check=True)
        body = H / 'face51/COMMIT_BODY51.txt'
        body.write_text('Audit official public resource lifetime and preserve retained diagnostic state\n\n'
                        'Record 45 still-created diagnostic RTs, named materials, the public updater target and seven supported MCP tools. '
                        'Verify 47 native snapshot hashes and distinguish installed Undo helpers from asynchronous owner completion. '
                        'Do not retry rejected reflection, release pending resources, run GPU work or modify product77.\n', encoding='utf-8')
        git('commit', '--file', str(body))
        assert not git('diff', '--cached', '--name-only')
        assert all(sha(R / p) == s for p, s in user.items())
        save(H / 'face51/COMMIT51.json', {'commit': git('rev-parse', 'HEAD'), 'selectedFiles': len(names),
                                        'user30Equal': True, 'product77Changed': False,
                                        'resourcesReleased': False, 'GPUCalls': 0, 'push': False})
        print((H / 'face51/COMMIT51.json').read_text())


if __name__ == '__main__':
    main()
