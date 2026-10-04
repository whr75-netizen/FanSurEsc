"""N31 bounded graph; existing Unity editor is operated by one MCP writer."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'docs/artifacts/building39/light31/run01'
STATE = ROOT / 'LocalOnly/WorkLoop/light31-run01'
GATE = ROOT / 'Tools/Building38/light31_gate.py'

def known(node, field):
    return {'op': 'known', 'args': [{'ref': f'{node}.{field}'}]}

def handoff(ident, field, next_id, scope, reads, writes):
    return {'id': ident, 'algorithm': 'ai.work', 'phase': 'work',
        'inputs': {'output': {'literal': str(OUTPUT)}, 'contract': {'literal': 'BUILDING16 N31 R2'}},
        'parameters': {'scope': scope}, 'question': scope,
        'output_schema': {field: {'type': 'string'}}, 'reads': reads, 'writes': writes,
        'edges': [{'when': known(ident, field), 'to': next_id}]}

def invoke(op, *args):
    r = subprocess.run([sys.executable, '-B', str(ROOT/'Tools/WorkLoop/work_loop.py'), op,
        str(STATE/'state.json'), *args], cwd=ROOT, capture_output=True, encoding='utf-8',
        env={**os.environ, 'PYTHONUTF8':'1'}, shell=False)
    if r.returncode:
        raise RuntimeError(r.stderr or r.stdout)
    data = json.loads(r.stdout)
    print(json.dumps({k:v for k,v in data.items() if k in ('goal','steps','action','node','ticket','message')},ensure_ascii=False))
    return data

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) > 1 and sys.argv[1]=='--gate-recovery':
        old=json.loads((STATE/'state.json').read_text(encoding='utf-8'))
        gate=old['graph']['nodes'][-1]
        if old.get('active',{}).get('node')!='gate' or set(gate['inputs'])!={'contract'} or (OUTPUT/'validation31.json').exists():
            raise ValueError('This recovery applies only to the unlaunched command input-contract error.')
        # command.run rejected the unsupported input before subprocess.run.
        # Preserve that state and all real observations; execute only the gate.
        gate['inputs']={'stdin':{'literal':{'contract':'BUILDING16 N31 R2'}}}
        gate['reads']=['file:'+(OUTPUT/p).as_posix() for p in
            ('baseline-hashes.json','before/observation.json','after/observation.json','fixture/fixture.json')]
        graph={'goal':old['graph']['goal'],'entry':'gate','max_steps':1,
            'requirements':old['graph']['requirements'],'nodes':[gate]}
        prior=STATE;STATE=ROOT/'LocalOnly/WorkLoop/light31-gate-recovery02'
        if STATE.exists():raise ValueError('Recovery state already exists.')
        STATE.mkdir(parents=True)
        (STATE/'graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (OUTPUT/'graph-recovery.json').write_text(json.dumps({'priorState':str(prior),
            'cause':'command.run accepts stdin only; contract input rejected before process launch',
            'preservedWorkNodes':['baseline','loss','observe'],'recoveryState':str(STATE)},indent=2)+'\n',encoding='utf-8')
        invoke('init',str(STATE/'graph.json'));invoke('run')
    elif len(sys.argv) > 1 and sys.argv[1]=='--record':
        data=invoke('next')
        answer=STATE/(data['node']+'-answer.json')
        answer.write_text(json.dumps({'ticket':data['ticket'],'output':{sys.argv[2]:sys.argv[3]}},ensure_ascii=False)+'\n',encoding='utf-8')
        invoke('submit',str(answer))
    elif len(sys.argv) > 1:
        invoke('submit', sys.argv[1])
    else:
        if STATE.exists():
            raise ValueError('Existing graph is preserved; resume its ticket.')
        STATE.mkdir(parents=True)
        paths = [ROOT/'Assets/Scenes/GameMap1.unity']
        for folder in (ROOT/'Assets/Art').iterdir():
            if folder.is_dir() and folder.name.startswith(('NativeBuilding', 'NativeMaterial', 'PixelShopInterior34Aligned', 'PlannedPixelBuilding33Uniform')):
                paths.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in ('.png','.asset','.mat','.meta'))
        OUTPUT.mkdir(parents=True, exist_ok=True)
        hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        (OUTPUT/'baseline-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf-8')
        baseline = handoff('baseline','receipt','loss',
            'Record actual before camera/book caster on-off/night-day natural values; preserve source hashes.',
            ['file:'+p.as_posix() for p in paths], ['native31:baseline'])
        loss = handoff('loss','implementation','observe',
            'Implement only N31 native shadow-loss response and same-Light accumulation; preserve other shader paths.',
            ['native31:baseline'], ['native31:shader'])
        observe = handoff('observe','receipt','gate',
            'Single Unity MCP writer: actual float GPU fixture and same gameplay night/day/book/light controls; restore state.',
            ['native31:baseline','native31:shader'], ['native31:observation'])
        success = {'op':'eq','args':[{'ref':'gate.exit_code'},{'literal':0}]}
        gate = {'id':'gate','algorithm':'command.run','phase':'validation',
            'inputs':{'stdin':{'literal':{'contract':'BUILDING16 N31 R2'}}},
            'parameters':{'argv':[sys.executable,'-B',str(GATE),'--output',str(OUTPUT)],
                'cwd':str(ROOT),'timeout':60,'code_files':[str(GATE)]},
            'reads':['native31:baseline','native31:shader','native31:observation'],
            'writes':['native31:validation'],
            'edges':[{'when':success,'to':'@complete'},
                {'when':{'op':'ne','args':[{'ref':'gate.exit_code'},{'literal':0}]},'to':'@blocked'}]}
        graph={'goal':'Preserve actual occlusion in native readable night lighting',
            'entry':'baseline','max_steps':4,'nodes':[baseline,loss,observe,gate],
            'requirements':[{'id':'actual_shadow_loss','source':'BUILDING16 N31 R2',
                'text':'GPU response and actual book shadow, preserved sources/geometry/grid/light controls.',
                'predicate':success}]}
        (STATE/'graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        invoke('init',str(STATE/'graph.json'))
        invoke('run')
