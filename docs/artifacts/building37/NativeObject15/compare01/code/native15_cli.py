"""Freeze and execute N15 actual production phases with the existing WorkLoop."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import time
from native15 import ROOT, HERE, items, read, write, sha


def condition(node, operation):
    return {'op':operation, 'args':[{'ref':node+'.exit_code'}, {'literal':0}]}


def run(recipe, reference, output):
    recipe = Path(recipe).resolve(); reference = Path(reference).resolve()
    output = Path(output).resolve(); settings = read(recipe)
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Use a fresh workspace output; preserve previous results')
    if settings['reference_sha256'] != sha(reference):
        raise ValueError('Reference/recipe mismatch')
    code = [HERE/'native15.py', HERE/'native15_geometry.py', HERE/'native14_materials.py',
            HERE/'native15_validation.py', Path(__file__).resolve(),
            ROOT/'Tools/PixelPipeline/common.py']
    state = output.parent/(output.name+'-workloop'); state.mkdir(parents=True, exist_ok=False)
    phases = ['geometry','material','shade','raster','validate']
    cases = items(settings)
    artifacts = {
        'geometry':[f'geometry/{m}/{stem}{n}.{ext}' for m,n in cases
                    for stem,ext in [('buffers','npz'),('geometry','json'),('model','obj')]],
        'material':['material/palette.json','material/provenance.json']+
                   [f'material/{m}/materials{n}.npz' for m,n in cases],
        'shade':[f'shade/{m}/{stem}{n}.{ext}' for m,n in cases
                 for stem,ext in [('shade','npz'),('shadow-','png')]],
        'raster':[f'raster/{m}/{stem}{n}{suffix}' for m,n in cases for stem,suffix in
                  [('cabinet-','.png'),('owners','.npz'),('policies','.json'),
                   ('edge-roles-','.png'),('preview-','-x4.png')]]+
                 [f'{m}-{stem}.png' for m in settings['modes'] for stem in ['native','preview-x4']]+
                 ['comparison-x4.png'],
        'validate':['validation.json']}
    nodes = []; previous = []
    for i,phase in enumerate(phases):
        nodes.append({'id':phase,'algorithm':'command.run',
            'phase':'validation' if phase == 'validate' else 'work',
            'inputs':{'stdin':{'literal':{'contract':'NATIVE15.md finite solid and semantic edge roles'}}},
            'parameters':{'argv':[sys.executable,'-B',str(HERE/'native15.py'),phase,
                '--recipe',str(recipe),'--reference',str(reference),'--output',str(output)],
                'cwd':str(ROOT),'timeout':60,'code_files':[str(p) for p in code]+[str(recipe)]},
            'reads':['file:'+p.as_posix() for p in [recipe, reference]]+
                    ['file:'+(output/p).as_posix() for p in previous],
            'writes':['file:'+(output/p).as_posix() for p in artifacts[phase]+[phase+'-receipt.json']],
            'edges':[{'when':condition(phase,'eq'),'to':phases[i+1] if i+1 < len(phases) else '@complete'},
                     {'when':condition(phase,'ne'),'to':'@blocked'}]})
        previous += artifacts[phase]
    graph = {'goal':'Native cabinet: genuine geometric coverage, observed material, discrete normal lighting and semantic edges',
             'entry':'geometry','max_steps':5,
             'requirements':[{'id':'actual_native_object','source':'NATIVE15.md; latest user correction',
                'text':'Actual A/B PNG, preserved source, editable geometry, no expanded coverage, colored creases and actual solid shadows',
                'predicate':condition('validate','eq')}], 'nodes':nodes}
    write(state/'graph.json',graph); started = time.perf_counter(); last = {}
    for action,extra in [('init',[str(state/'graph.json')]),('run',[])]:
        completed = subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),
            action,str(state/'state.json'),*extra],cwd=ROOT,capture_output=True,encoding='utf-8',shell=False)
        if completed.returncode: raise RuntimeError(completed.stdout+'\n'+completed.stderr)
        last = __import__('json').loads(completed.stdout)
    if output.exists():
        package = output/'code'; package.mkdir()
        for p in code+[recipe,HERE/'NATIVE15.md']:
            shutil.copyfile(p,package/p.name)
        for name in ['graph.json','state.json']:
            shutil.copyfile(state/name,output/('workloop-'+name))
        shutil.copyfile(reference,output/'appearance-reference.png')
        write(output/'execution.json',{'workloop_action':last['action'],
            'wall_seconds':time.perf_counter()-started,'reference_sha256':sha(reference),
            'code_sha256':{p.name:sha(p) for p in code+[recipe]},
            'artifact_sha256':{p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()},
            'art_approved':False,'original_grid_recovered':False,'runtime_lighting_implemented':False,
            'comparison':'planar analytic visible quads without volume shadow; finite solids with real shadow rays'})
    return {'action':last['action'],'wall_seconds':time.perf_counter()-started,'output':str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe', default=str(HERE/'native15_recipe.json'))
    parser.add_argument('--reference', default=str(ROOT/'docs/artifacts/building37/NativeObject14/appearance-reference.png'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args(); sys.stdout.reconfigure(encoding='utf-8')
    result = run(args.recipe,args.reference,args.output)
    print(__import__('json').dumps(result))
    if result['action'] != 'graph_complete': raise SystemExit(2)
