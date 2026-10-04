"""N30 fixed graph: features -> surface -> observe -> GPU gate -> save -> gate."""
import json
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'docs/artifacts/building39/material30/run01'
STATE=ROOT/'LocalOnly/WorkLoop/material30-plan02'
SCRIPT=ROOT/'Tools/Building38/material30.py'

def success(node,op='eq'):return {'op':op,'args':[{'ref':node+'.exit_code'},{'literal':0}]}
def command(ident,argv,next_id,reads,writes,validation=False):
    codes=[SCRIPT,Path(__file__).resolve(),ROOT/'Tools/Building38/material29.py',
        ROOT/'Tools/Building38/material30_finish.py',ROOT/'Assets/Shaders/World/NativePaletteSurface16.shader',
        ROOT/'Assets/Editor/NativeMaterial30Observation.cs']
    return {'id':ident,'algorithm':'command.run','phase':'validation' if validation else 'work',
        'inputs':{'stdin':{'literal':{'contract':'BUILDING16 N30 R2'}}},
        'parameters':{'argv':[sys.executable,'-B',*argv],'cwd':str(ROOT),'timeout':60,
            'code_files':[str(p) for p in codes]},'reads':reads,'writes':writes,
        'edges':[{'when':success(ident),'to':next_id,**({'feedback':True} if validation and next_id!='@complete' else {})},
            {'when':success(ident,'ne'),'to':'@blocked'}]}
def handoff(ident,key,next_id,scope,reads,writes):
    return {'id':ident,'algorithm':'ai.work','phase':'work',
        'inputs':{'output':{'literal':str(OUTPUT)},'contract':{'literal':'BUILDING16 N30 R2'}},
        'parameters':{'scope':scope},'question':scope+' Return the actual receipt path and continue; this is not a user question.',
        'output_schema':{key:{'type':'string'}},'reads':reads,'writes':writes,
        'edges':[{'when':{'op':'known','args':[{'ref':ident+'.'+key}]},'to':next_id}]}

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--reuse-maps',action='store_true');args=parser.parse_args()
    if args.reuse_maps:STATE=ROOT/'LocalOnly/WorkLoop/material30-integration03'
    if STATE.exists() or (OUTPUT.exists() and not args.reuse_maps):raise ValueError('Previous state and output are preserved')
    STATE.mkdir(parents=True)
    inputs=[ROOT/'Assets/Art/NativeBuilding41MaterialRepair/empty_counter.png',
        ROOT/'Assets/Art/NativeBuilding39/palette.png',
        ROOT/'docs/artifacts/building39/run02/empty_counter/geometry.npz',
        ROOT/'docs/artifacts/building39/run02/empty_counter/geometry.json',
        ROOT/'docs/artifacts/building39/run02/empty_counter/normal.f32',
        ROOT/'docs/artifacts/building39/material29/run01/normal.f32',
        ROOT/'LocalOnly/Material30/before-shader/legacy-readable-native.png',
        ROOT/'LocalOnly/Material30/before-shader/legacy-albedo-native.png']
    reads=['file:'+p.as_posix() for p in inputs]
    nodes=[command('features',[str(SCRIPT),'features','--output',str(OUTPUT)],'surface',reads,['native30:features']),
        command('surface',[str(SCRIPT),'verify' if args.reuse_maps else 'generate','--output',str(OUTPUT)],'observe',reads+([] if args.reuse_maps else ['native30:features']),['native30:maps']),
        handoff('observe','receiptFile','gpu','Single Unity MCP writer: Prepare fresh version, enter existing GameMap1 Play Mode, Observe same actual camera/native scale, restore state and exit Play. Do not save/bind production before GPU gate.',
            ['native30:maps'],['unity:native30-observation']),
        command('gpu',[str(ROOT/'Tools/Building38/material30_finish.py')],'save',
            ['native30:maps','unity:native30-observation'],['native30:gpu-validation'],True),
        handoff('save','finalFile','gate','After actual GPU gate passed, BindAndSave one checkout material reference in existing GameMap1, preserving original assets, scene geometry and lighting.',
            ['native30:gpu-validation'],['unity:native30-save']),
        command('gate',[str(SCRIPT),'gate','--output',str(OUTPUT)],'@complete',
            ['native30:maps','native30:gpu-validation','unity:native30-save'],['native30:final-validation'],True)]
    if args.reuse_maps:nodes=nodes[1:]
    graph={'goal':'One cabinet: cause-specific material detail replacing broad paint blobs',
        'entry':'surface' if args.reuse_maps else 'features','max_steps':len(nodes),'requirements':[{'id':'cause_specific_detail',
            'source':'Latest user correction; BUILDING16 N30 R2',
            'text':'Separate causal masks/height/roughness, preserved sources/geometry/grid; actual GPU/camera evidence. Art acceptance is not an automated predicate.',
            'predicate':success('gate')}],'nodes':nodes}
    (STATE/'graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for phase,extra in [('init',[str(STATE/'graph.json')]),('run',[])]:
        r=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),phase,str(STATE/'state.json'),*extra],
            cwd=ROOT,capture_output=True,encoding='utf-8',shell=False,env={**os.environ,'PYTHONUTF8':'1'})
        (STATE/(phase+'.json')).write_text(r.stdout,encoding='utf-8');print(r.stdout)
        if r.returncode:raise RuntimeError(r.stderr)
