"""N32 fixed four-stage graph; one Unity/production writer supplies actual captures."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT/'docs/artifacts/building39/book32'
STATE = ROOT/'LocalOnly/WorkLoop/book32-run01'
GATE = ROOT/'Tools/Building38/book32_gate.py'
OWNER = ROOT/'Assets/Scripts/WorldLighting/SteppedLocalLight.cs'


def invoke(op, *args):
    result = subprocess.run([sys.executable, '-B', str(ROOT/'Tools/WorkLoop/work_loop.py'), op,
        str(STATE/'state.json'), *args], cwd=ROOT, capture_output=True, encoding='utf-8',
        env={**os.environ, 'PYTHONUTF8': '1'}, shell=False)
    if result.returncode:
        raise RuntimeError(result.stderr or result.stdout)
    value = json.loads(result.stdout)
    print(json.dumps({k:v for k,v in value.items() if k in ('goal','steps','action','node','ticket','message')}, ensure_ascii=False))
    return value


def command(ident, experiment, next_id):
    passed = {'op':'eq', 'args':[{'ref': ident+'.exit_code'}, {'literal':0}]}
    argv = [sys.executable, '-B', str(GATE), '--output', str(OUTPUT)]
    if experiment:
        argv.append('--experiment-only')
    return {'id':ident, 'algorithm':'command.run', 'phase':'work' if experiment else 'validation',
        'inputs':{'stdin':{'literal':{'contract':'BUILDING16 N32 R3', 'minimumCells':8, 'minimumDeltaYByte':8}}},
        'parameters':{'argv':argv, 'cwd':str(ROOT), 'timeout':60, 'code_files':[str(GATE)]},
        'reads':['file:'+(OUTPUT/'baseline-hashes.json').as_posix(), 'native32:experiment']+
            ([] if experiment else ['native32:owner', 'native32:final']),
        'writes':['native32:'+ident],
        'edges':[{'when':passed, 'to':next_id},
            {'when':{'op':'ne', 'args':[{'ref':ident+'.exit_code'}, {'literal':0}]}, 'to':'@blocked'}]}


def handoff(ident, field, next_id, scope, reads, writes):
    return {'id':ident, 'algorithm':'ai.work', 'phase':'work',
        'inputs':{'output':{'literal':str(OUTPUT)}, 'contract':{'literal':'BUILDING16 N32 R3'}},
        'parameters':{'scope':scope}, 'question':scope,
        'output_schema':{field:{'type':'string'}}, 'reads':reads, 'writes':writes,
        'edges':[{'when':{'op':'known', 'args':[{'ref':ident+'.'+field}]}, 'to':next_id}]}


def initialize():
    if STATE.exists() or (OUTPUT/'baseline-hashes.json').exists():
        raise ValueError('Existing N32 state and hashes are immutable; resume its pending ticket.')
    if not (OUTPUT/'experiment01/context.json').is_file():
        raise ValueError('Actual baseline/policy experiment must be captured before graph init and owner edits.')
    paths = [ROOT/'Assets/Scenes/GameMap1.unity']
    for folder in (ROOT/'Assets/Art').iterdir():
        if folder.is_dir() and folder.name.startswith(('NativeBuilding','NativeMaterial','PixelShopInterior34Aligned','PlannedPixelBuilding33Uniform')):
            paths.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in ('.png','.asset','.mat','.meta'))
    paths.extend(p for p in (ROOT/'Assets/Shaders/World').rglob('*') if p.is_file())
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUTPUT/'baseline-hashes.json').write_text(json.dumps(hashes, indent=2)+'\n', encoding='utf-8')
    STATE.mkdir(parents=True)
    baseline = command('baseline', True, 'owner')
    owner = handoff('owner', 'implementation', 'observe',
        'Single production writer: change only existing RoomLamp SynchronizeRoomDirectLight range to max(Radius,2*maximum world distance to assigned room corners); preserve moving/local path, lamps color/intensity, geometry, art, shader, camera.',
        ['native32:baseline', 'file:'+OWNER.as_posix()], ['native32:owner', 'file:'+OWNER.as_posix()])
    observe = handoff('observe', 'receipt', 'gate',
        'Single Unity writer: actual same gameplay camera/time final brown target caster ON/OFF and lamp/moving controls into book32/final01; restore actual player/camera/control state. No geometry, source, shader, pixel or scene edits.',
        ['native32:experiment', 'native32:owner'], ['native32:final'])
    gate = command('gate', False, '@complete')
    success = {'op':'eq','args':[{'ref':'gate.exit_code'}, {'literal':0}]}
    graph = {'goal':'Actual brown-object readable shadow on the visible counter top', 'entry':'baseline', 'max_steps':4,
        'nodes':[baseline, owner, observe, gate], 'requirements':[{'id':'actual_brown_receiver_shadow',
            'text':'Actual ray receiving native cells, connected>=8, luminance decrease>=8byte; original art/geometry/grid/camera/control preserved.',
            'source':'BUILDING16 N32 R3', 'predicate':success}]}
    (STATE/'graph.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    invoke('init', str(STATE/'graph.json'))
    invoke('run')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) == 1:
        initialize()
    elif sys.argv[1] == '--init-prepared':
        # The original init rejected phase validation -> work before making state.
        # Preserve that uninitialized graph and original hashes; launch no work twice.
        if (STATE/'state.json').exists() or (STATE/'graph.invalid-init.json').exists():
            raise ValueError('This recovery is restricted to the first rejected graph init.')
        graph = json.loads((STATE/'graph.json').read_text(encoding='utf-8'))
        baseline = graph['nodes'][0]
        if baseline['id'] != 'baseline' or baseline['algorithm'] != 'command.run' or baseline['phase'] != 'validation':
            raise ValueError('Unexpected pre-init cause; no automatic recovery.')
        (STATE/'graph.invalid-init.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        baseline['phase'] = 'work'
        (STATE/'graph.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        invoke('init', str(STATE/'graph.json')); invoke('run')
    elif sys.argv[1] == '--record':
        current = invoke('next')
        answer = STATE/(current['node']+'-answer.json')
        answer.write_text(json.dumps({'ticket':current['ticket'], 'output':{sys.argv[2]:sys.argv[3]}}, ensure_ascii=False)+'\n', encoding='utf-8')
        invoke('submit', str(answer))
    elif sys.argv[1] in ('--next','--resume'):
        invoke('next' if sys.argv[1] == '--next' else 'run')
    else:
        invoke('submit', sys.argv[1])
