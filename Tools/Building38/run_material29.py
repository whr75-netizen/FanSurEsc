"""Freeze N29 material calculation, bounded Unity handoff and observation gate."""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/artifacts/building39/material29/run01'
STATE=ROOT/'LocalOnly/WorkLoop/material29'
SCRIPT=ROOT/'Tools/Building38/material29.py'

def condition(node,op):return {'op':op,'args':[{'ref':node+'.exit_code'},{'literal':0}]}

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-maps',action='store_true')
    parser.add_argument('--integration-version',type=int,default=2);args=parser.parse_args()
    if args.reuse_maps:
        if args.integration_version<2:raise ValueError('Integration version must be >=2')
        STATE=ROOT/('LocalOnly/WorkLoop/material29-integration'+str(args.integration_version).zfill(2))
        if not (OUTPUT/'calculation.json').is_file():raise ValueError('Prior calculation required')
    if STATE.exists() or (OUTPUT.exists() and not args.reuse_maps):raise ValueError('Existing run preserved; resume state instead')
    STATE.mkdir(parents=True)
    source=[ROOT/'Assets/Art/NativeBuilding41MaterialRepair/empty_counter.png',
      ROOT/'docs/artifacts/building39/run02/empty_counter/geometry.npz',
      ROOT/'docs/artifacts/building39/run02/empty_counter/normal.f32',
      ROOT/'docs/artifacts/building39/run02/empty_counter/geometry.json',
      ROOT/'Assets/Art/NativeBuilding39/palette.png']
    codes=[SCRIPT,Path(__file__).resolve(),ROOT/'Assets/Shaders/World/NativePaletteSurface16.shader',
      ROOT/'Assets/Editor/NativeMaterial29Observation.cs']
    nodes=[]
    for ident,phase,next_id in [('material','verify' if args.reuse_maps else 'generate','unity'),('gate','gate','@complete')]:
        nodes.append({'id':ident,'algorithm':'command.run','phase':'work' if ident=='material' else 'validation',
          'inputs':{'stdin':{'literal':{'contract':'BUILDING16 N29 R2'}}},
          'parameters':{'argv':[sys.executable,'-B',str(SCRIPT),phase,'--output',str(OUTPUT)],
            'cwd':str(ROOT),'timeout':60,'code_files':[str(p) for p in codes]},
          'reads':['file:'+p.as_posix() for p in source]+([] if ident=='material' else ['native29:maps','unity:native29']),
          'writes':['native29:maps'] if ident=='material' else ['native29:validation'],
          'edges':[{'when':condition(ident,'eq'),'to':next_id},{'when':condition(ident,'ne'),'to':'@blocked'}]})
    nodes.append({'id':'unity','algorithm':'ai.work','phase':'work',
      'inputs':{'output':{'literal':str(OUTPUT)},'contract':{'literal':'Tools/PerfectPixelUniform/BUILDING16.md N29'}},
      'parameters':{'scope':'Import versioned maps/material; same actual camera before/after, normal response fixture; bind only checkout and save clean. Preserve original assets, geometry, lighting and pixel grid.'},
      'question':'Perform authorized bounded Unity integration with one MCP writer; return actual observation path and continue to gate.',
      'output_schema':{'receiptFile':{'type':'string'}},'reads':['native29:maps'],'writes':['unity:native29'],
      'edges':[{'when':{'op':'known','args':[{'ref':'unity.receiptFile'}]},'to':'gate'}]})
    graph={'goal':'One checkout cabinet: material clusters and live-light handle microrelief',
      'entry':'material','max_steps':3,'requirements':[{'id':'native_material_detail','source':'Latest user request; BUILDING16 N29',
        'text':'Canonical cluster/normal calculations, preserved source/geometry and actual 2px Play comparison; art approval is not automated.',
        'predicate':condition('gate','eq')}],'nodes':nodes}
    (STATE/'graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for phase,extra in [('init',[str(STATE/'graph.json')]),('run',[])]:
        r=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),phase,str(STATE/'state.json'),*extra],
          cwd=ROOT,capture_output=True,encoding='utf-8',shell=False,env={**os.environ,'PYTHONUTF8':'1'})
        (STATE/(phase+'.json')).write_text(r.stdout,encoding='utf-8');print(r.stdout)
        if r.returncode:raise RuntimeError(r.stderr)
