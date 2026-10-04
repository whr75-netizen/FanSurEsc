"""Freeze N17 calculations and hand bounded Unity integration to the active writer."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from building16 import ROOT,HERE,read,write,sha

def condition(node,op):
    return {'op':op,'args':[{'ref':node+'.exit_code'},{'literal':0}]}

def run(output):
    output=Path(output).resolve();state=output.parent/(output.name+'-workloop')
    if output.exists() or state.exists() or not output.is_relative_to(ROOT):
        raise ValueError('Fresh workspace output required; previous runs stay preserved')
    phases=['geometry','materials','export','validate']; nodes=[]
    inputs=[ROOT/'Tools/Building37/input-contract.json',ROOT/'docs/artifacts/building38/placement-baseline.json',
        ROOT/'Tools/Building37/Source/sheet.png',ROOT/'docs/artifacts/building37/NativeObject14/appearance-reference.png',
        ROOT/'Tools/PerfectPixelUniform/native15_recipe.json',HERE/'shading17.json',
        ROOT/'Assets/Art/PixelShopInterior34/Source/floor-warm.png',ROOT/'docs/artifacts/building34/calibration.json']
    codes=[HERE/'building16.py',HERE/'geometry16.py',HERE/'floor17.py',HERE/'shade17.py',Path(__file__).resolve(),
        ROOT/'Tools/PerfectPixelUniform/native14_materials.py',ROOT/'Assets/Shaders/World/NativeShade17.hlsl']
    for index,phase in enumerate(phases):
        nodes.append({'id':phase,'algorithm':'command.run','phase':'validation' if phase=='validate' else 'work',
            'inputs':{'stdin':{'literal':{'contract':'BUILDING16.md canonical metric templates and immutable material caches'}}},
            'parameters':{'argv':[sys.executable,'-B',str(HERE/'building16.py'),phase,'--output',str(output)],
                'cwd':str(ROOT),'timeout':60,'code_files':[str(p) for p in codes]},
            'reads':['file:'+p.as_posix() for p in inputs]+([] if index==0 else ['native16:calculations']),
            'writes':['native16:calculations'],
            'edges':[{'when':condition(phase,'eq'),'to':phases[index+1] if index<3 else 'unity_probe',**({'feedback':True} if index==3 else {})},
                     {'when':condition(phase,'ne'),'to':'@blocked'}]})
    for ident,next_id,scope,receipt in [
        ('unity_probe','probe_gate','Import a new asset version; compare three GPU neutral fixture outputs with CPU native PNGs; production scene untouched','probe.json'),
        ('unity_bind','final_gate','Bind existing 26 objects, structures and floor after parity gate; set existing clock night default; observe moving stepped light and integer native cameras','play-observation.json')]:
        nodes.append({'id':ident,'algorithm':'ai.work','phase':'work',
            'inputs':{'contract':{'literal':'Tools/PerfectPixelUniform/BUILDING16.md'},'output':{'literal':str(output)}},
            'parameters':{'scope':scope},'question':scope+'. Use Unity MCP single writer and return the actual observation receipt path.',
            'output_schema':{'receiptFile':{'type':'string'}},
            'reads':['native16:calculations'],'writes':['unity:native16-integration','file:'+(output/receipt).as_posix()],
            'edges':[{'when':{'op':'known','args':[{'ref':ident+'.receiptFile'}]},'to':next_id}]})
        nodes.append({'id':next_id,'algorithm':'command.run','phase':'validation',
            'inputs':{'stdin':{'literal':{'receipt':receipt}}},
            'parameters':{'argv':[sys.executable,'-B',str(HERE/'unity_gate17.py'),str(output/receipt)],
                'cwd':str(ROOT),'timeout':30,'code_files':[str(HERE/'unity_gate17.py')]},
            'reads':['unity:native16-integration','file:'+(output/receipt).as_posix()], 'writes':[],
            'edges':[{'when':condition(next_id,'eq'),'to':'unity_bind' if ident=='unity_probe' else '@complete',**({'feedback':True} if ident=='unity_probe' else {})},
                     {'when':condition(next_id,'ne'),'to':'@blocked'}]})
    graph={'goal':'One existing base-scene test building: semantic native art and actual engine lighting',
        'entry':'geometry','max_steps':8,'requirements':[{'id':'building_native_runtime','source':'latest user request; BUILDING16.md',
        'text':'18 shared types,26 bound instances, preserved layout and actual pixel/depth/light observation',
        'predicate':condition('final_gate','eq')}],'nodes':nodes}
    state.mkdir(parents=True);write(state/'graph.json',graph)
    for action,extra in [('init',[str(state/'graph.json')]),('run',[])]:
        result=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),action,str(state/'state.json'),*extra],
            cwd=ROOT,capture_output=True,encoding='utf-8',shell=False)
        print(result.stdout)
        if result.returncode: raise RuntimeError(result.stderr)
    write(output/'input-hashes.json',{p.relative_to(ROOT).as_posix():sha(p) for p in inputs+codes})
    return state

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    sys.stdout.reconfigure(encoding='utf-8');run(a.output)
