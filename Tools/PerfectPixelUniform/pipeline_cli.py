"""Bind existing pixel graphs to fresh local runs; keep production algorithms fixed."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUNS = ROOT / 'LocalOnly/PerfectPixelUniform/runs'
ENGINE = ROOT / 'Tools/WorkLoop/work_loop.py'
CURRENT = ROOT / 'docs/artifacts/building37/Parametric08'
ROUTES = {
    'wood': ('graph-v8.json', 'Parametric07-fixed',
             'Existing V7 geometry -> four-tone wood; no new geometry or Unity apply'),
    'structure': ('graph-v7-import-fix.json', 'Parametric06',
                  'V7 flat geometry -> existing V6 material; not combined with V8 wood'),
}
CODE = [
    'Tools/PerfectPixelUniform/cabinet_geometry06.py',
    'Tools/PerfectPixelUniform/cabinet_pipeline06.py',
    'Tools/PerfectPixelUniform/validate06.py',
    'Tools/PixelPipeline/common.py',
    'Tools/PerfectPixelUniform/pipeline_cli.py',
]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def run_dir(run_id):
    if not run_id or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', run_id):
        raise ValueError('run-id must be 1..64 lowercase letters/digits/hyphens')
    if run_id.split('-')[0] in {'con', 'prn', 'aux', 'nul', *{'com'+str(i) for i in range(1,10)}, *{'lpt'+str(i) for i in range(1,10)}}:
        raise ValueError('Reserved Windows run-id')
    path = (RUNS / run_id).resolve()
    if not path.is_relative_to(ROOT) or not path.is_relative_to((ROOT / 'LocalOnly').resolve()):
        raise ValueError('Run must stay in workspace LocalOnly')
    return path


def engine(command, directory, extra=()):
    process = subprocess.run(
        [sys.executable, '-B', str(ENGINE), command, str(directory/'state.json'), *extra],
        cwd=ROOT, capture_output=True, encoding='utf-8', shell=False)
    if process.returncode:
        raise ValueError(f'WorkLoop {command} failed: {process.stdout} {process.stderr}')
    return json.loads(process.stdout)


def plan(route, run_id, reason):
    if not reason or not reason.strip():
        raise ValueError('A concrete change reason is required')
    directory = run_dir(run_id)
    if directory.exists():
        raise ValueError('Existing run-id is preserved; inspect its status')
    template_name, previous_name, scope = ROUTES[route]
    template_path = HERE / template_name
    graph = read(template_path)
    output = directory / 'outputs'  # Do not create: production requires a fresh directory.
    original_outputs = set()
    for node in graph['nodes']:
        argv = node['parameters']['argv']
        original_outputs.add(argv[argv.index('--output')+1].rstrip('/'))
    if len(original_outputs) != 1 or len(graph['nodes']) != 3:
        raise ValueError('Expected one output root and three existing stages')
    original = original_outputs.pop()
    old_prefix = 'file:' + original + '/'
    new_prefix = 'file:' + output.as_posix() + '/'
    fixed_inputs = {}
    for node in graph['nodes']:
        params = node['parameters']
        params['argv'][0] = sys.executable
        params['argv'][params['argv'].index('--output')+1] = output.as_posix()
        params['cwd'] = str(ROOT)
        params['code_files'] = sorted({str((ROOT/p).resolve()) for p in params['code_files'] + CODE})
        for key in ('reads', 'writes'):
            node[key] = [new_prefix + value[len(old_prefix):] if value.startswith(old_prefix) else value
                         for value in node.get(key, [])]
        for value in node['reads']:
            if value.startswith('file:') and not value.startswith(new_prefix):
                path = Path(value[5:]); fixed_inputs[str(path)] = sha(path)
    previous_report = ROOT / 'docs/artifacts/building37' / previous_name / 'validation.json'
    report = read(previous_report)
    if report.get('passed') is not True:
        raise ValueError('Previous technical validation has not passed')
    fixed_inputs[str(previous_report)] = sha(previous_report)
    for name, digest in report['files_sha256'].items():
        path = Path(name)
        if sha(path) != digest:
            raise ValueError('Previous input changed: ' + name)
        fixed_inputs[str(path)] = digest
    # Include hidden prior-validation dependencies in every unit's read snapshot.
    for node in graph['nodes']:
        node['reads'] = sorted(set(node['reads']) | {'file:'+Path(p).as_posix() for p in fixed_inputs})
    directory.mkdir(parents=True, exist_ok=False)
    write(directory/'graph.json', graph)
    write(directory/'binding.json', {
        'route': route, 'reason': reason.strip(), 'scope': scope,
        'template': str(template_path), 'template_sha256': sha(template_path),
        'output': str(output), 'fixed_inputs_sha256': fixed_inputs,
        'unity_apply': False,
    })
    result = engine('init', directory, [str(directory/'graph.json')])
    if result.get('action') != 'ready':
        raise ValueError('Graph is not ready after initialization: ' + str(result))
    return {'action': 'planned', 'route': route, 'scope': scope,
            'run': str(directory), 'nodes': [n['id'] for n in graph['nodes']],
            'production_executed': False, 'output': str(output)}


def operate(command, run_id):
    directory = run_dir(run_id)
    binding = read(directory/'binding.json')
    if command == 'run':
        for name, digest in binding['fixed_inputs_sha256'].items():
            if sha(Path(name)) != digest:
                raise ValueError('Fixed input changed; production blocked: ' + name)
        before = engine('next', directory)
        if before['action'] != 'ready':
            result = before  # complete/paused/blocked/uncertain: never repeat production.
        else:
            result = engine('run', directory)
    else:
        result = engine('next' if command == 'status' else command, directory)
    result.update(run=str(directory), route=binding['route'], scope=binding['scope'], unity_apply=False)
    if result['action'] == 'graph_complete':
        state = read(directory/'state.json')
        report = read(Path(binding['output'])/'validation.json')
        if state.get('complete') is not True or report.get('passed') is not True:
            raise ValueError('Completion state and saved validation disagree')
        result['native_outputs'] = native_outputs(Path(binding['output']))
    return result


def native_outputs(output):
    paths = []
    for count in (2,3):
        path = output/f'pixels/native{count}.png'
        metadata = read(output/f'pixels/pixel{count}.json')
        digest = metadata.get('output_sha256')
        if digest is None:  # V7 metadata stores a path -> SHA map.
            matches = [value for name,value in metadata['outputs'].items()
                       if Path(name).resolve() == path.resolve()]
            if len(matches) != 1:
                raise ValueError('Missing unique native output digest: ' + str(path))
            digest = matches[0]
        if sha(path) != digest:
            raise ValueError('Saved native changed: ' + str(path))
        paths.append(str(path))
    return paths


def reuse():
    if read(CURRENT/'validation.json').get('passed') is not True:
        raise ValueError('Current saved technical validation has not passed')
    return {'action': 'reused', 'native_outputs': native_outputs(CURRENT),
            'production_executed': False, 'unity_apply': False,
            'scope': 'Saved V8 PNG hashes only; no renewed art or engine approval'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['reuse','plan','start','run','status','stop','resume'])
    parser.add_argument('--route', choices=ROUTES)
    parser.add_argument('--run-id')
    parser.add_argument('--reason')
    args = parser.parse_args()
    if args.command == 'reuse':
        result = reuse()
    elif args.command in {'plan','start'}:
        if not args.route:
            parser.error('--route is required for plan/start')
        result = plan(args.route, args.run_id, args.reason)
        if args.command == 'start':
            result = operate('run', args.run_id)
    else:
        result = operate(args.command, args.run_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    if result['action'] in {'blocked','uncertain_execution','error'}:
        return 1
    if args.command in {'run','start'} and result['action'] != 'graph_complete':
        return 1
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'action': 'error', 'message': str(error)}, ensure_ascii=False))
        raise SystemExit(2)
