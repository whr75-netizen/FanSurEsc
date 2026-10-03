"""One local invocation: fixed R10 analysis -> reconstruction -> technical checks."""
import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ENGINE = ROOT/'Tools/WorkLoop/work_loop.py'


def condition(stage, op):
    return {'op': op, 'args': [{'ref': f'{stage}.exit_code'}, {'literal': 0}]}


def start(source, output, levels=4):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file() or output.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Existing input and a fresh workspace output directory are required.')
    state_dir = ROOT/'LocalOnly/PerfectPixelUniform'/('redraw10-'+uuid.uuid4().hex)
    state_dir.mkdir(parents=True, exist_ok=False)
    code = [str(HERE/name) for name in ('redraw10.py','redraw_tones.py','redraw_checks.py',
                                      'redraw_cli.py','uniform.py','cleanup.py')]
    nodes = []
    files = {
        'prepare': ([], ['source.png','prepared.npz','analysis.json']),
        'render': (['prepared.npz','analysis.json'], ['native.png','maps.npz','line-mask.png',
                   'tone-map.png','band-dim.png','band-bright.png','receipt.json']),
        'validate': (['source.png','prepared.npz','analysis.json','native.png','maps.npz',
                     'line-mask.png','tone-map.png','band-dim.png','band-bright.png','receipt.json'],
                     ['validation.json']),
    }
    for phase, after in (('prepare','render'), ('render','validate'), ('validate','@complete')):
        reads, writes = files[phase]
        nodes.append({
            'id': phase, 'algorithm': 'command.run',
            'phase': 'validation' if phase == 'validate' else 'work',
            'inputs': {'stdin': {'literal': {'contract': 'R10: source lattice, observed RGB ramps; no authored-grid claim'}}},
            'parameters': {'argv': [sys.executable,'-B',str(HERE/'redraw10.py'),phase,
                '--source',str(source),'--output',str(output),'--levels',str(levels)],
                'cwd': str(ROOT), 'timeout': 60, 'code_files': code},
            'reads': ['file:'+source.as_posix()] + ['file:'+(output/name).as_posix() for name in reads],
            'writes': ['file:'+(output/name).as_posix() for name in writes],
            'edges': [{'when': condition(phase,'eq'), 'to': after},
                      {'when': condition(phase,'ne'), 'to': '@blocked'}],
        })
    graph = {'goal': 'R10 local line/region/ramp prototype; normalization certainty reported separately',
             'entry': 'prepare','max_steps': 3,
             'requirements': [{'id':'r10_technical','text':'Actual palette/coordinate/fixture contracts; not art approval',
                               'source':'REDRAW_DESIGN.md R10', 'predicate': condition('validate','eq')}],
             'nodes': nodes}
    (state_dir/'graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf-8')
    for command, extra in (('init',[str(state_dir/'graph.json')]), ('run',[])):
        run = subprocess.run([sys.executable,'-B',str(ENGINE),command,str(state_dir/'state.json'),*extra],
                             cwd=ROOT,capture_output=True,encoding='utf-8',shell=False)
        if run.returncode:
            raise ValueError(f'R10 WorkLoop {command}: {run.stdout} {run.stderr}')
        result = json.loads(run.stdout)
    report = json.loads((output/'receipt.json').read_text(encoding='utf-8')) if (output/'receipt.json').exists() else {}
    result.update(output=str(output), state=str(state_dir/'state.json'),
                  prototype_only=True, art_approved=False,
                  repeated_lattice_recovered=bool(report.get('grid_recovered')),
                  whole_normalization_certified=False)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--levels',type=int,choices=[3,4],default=4)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    result = start(args.source,args.output,args.levels)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['action'] == 'graph_complete' else 1)
