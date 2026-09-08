"""Export only committed pixel-tool history; optionally push to verified private GitHub.

No checkout/reset of the game worktree, source writes, force pushes, or credentials
in files/stdout. fast-export/import use an exact byte pipe, not shell text encoding.
"""
import argparse
import json
from pathlib import Path
import subprocess

REPOSITORY = 'whr75-netizen/pixel-normalization-lab'
REMOTE = 'https://github.com/' + REPOSITORY + '.git'
PATHS = ['LocalOnly/PerfectPixelPalette_20260906',
         'LocalOnly/ChibiPixelReview_20260908_Bright']


def run(args, cwd, **kwargs):
    return subprocess.run(args, cwd=cwd, check=True, **kwargs)


def output(args, cwd):
    return run(args, cwd, capture_output=True, text=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--push', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if Path(output(['git', 'rev-parse', '--show-toplevel'], root)).resolve() != root:
        raise RuntimeError('Run this exporter from its original game-repository location.')
    mirror = root / 'LocalOnly' / 'PixelNormalizationGitBackup'
    if not mirror.resolve().is_relative_to((root / 'LocalOnly').resolve()):
        raise RuntimeError('Backup directory escaped LocalOnly.')
    if args.push:
        repo = json.loads(output(['gh', 'repo', 'view', REPOSITORY,
                                  '--json', 'nameWithOwner,isPrivate'], root))
        if repo.get('nameWithOwner') != REPOSITORY or repo.get('isPrivate') is not True:
            raise RuntimeError('Refusing upload: exact destination must be private.')
    if mirror.exists():
        if output(['git', 'rev-parse', '--is-bare-repository'], mirror) != 'true':
            raise RuntimeError('Existing backup target is not a bare repository.')
    else:
        run(['git', 'init', '--bare', str(mirror)], root)
    branch = output(['git', 'symbolic-ref', 'HEAD'], root)
    # A branch at current HEAD would include all game ancestors. Path-filtered
    # fast-export prunes unrelated commits and all unrelated file contents.
    export = subprocess.Popen(['git', 'fast-export', '--reencode=yes',
        '--refspec=' + branch + ':refs/heads/main', 'HEAD', '--', *PATHS],
        cwd=root, stdout=subprocess.PIPE)
    try:
        imported = subprocess.run(['git', 'fast-import', '--quiet'], cwd=mirror,
                                  stdin=export.stdout)
    finally:
        export.stdout.close()
    if export.wait() != 0 or imported.returncode != 0:
        raise RuntimeError('History export/import failed; nothing pushed.')
    files = output(['git', 'ls-tree', '-r', '--name-only', 'main'], mirror).splitlines()
    if not files or any(not any(p.startswith(prefix + '/') for prefix in PATHS) for p in files):
        raise RuntimeError('Export contains paths outside the pixel tools.')
    head = output(['git', 'rev-parse', 'main'], mirror)
    if args.push:
        run(['git', 'push', REMOTE, 'refs/heads/main:refs/heads/main'], mirror)
        remote_head = output(['git', 'ls-remote', REMOTE, 'refs/heads/main'], mirror).split()[0]
        if remote_head != head:
            raise RuntimeError('Remote head verification failed.')
    print(json.dumps({'private_repository': REPOSITORY, 'filtered_head': head,
        'source_head': output(['git', 'rev-parse', 'HEAD'], root), 'files': len(files),
        'commits': int(output(['git', 'rev-list', '--count', 'main'], mirror)),
        'pushed_and_verified': args.push}, ensure_ascii=False))


if __name__ == '__main__':
    main()
