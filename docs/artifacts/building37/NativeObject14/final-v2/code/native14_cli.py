"""Freeze and execute N14 production phases with the existing WorkLoop."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from native14 import ROOT,HERE,read,write,sha


def condition(node,operation):
    return {'op':operation,'args':[{'ref':node+'.exit_code'},{'literal':0}]}


def run(recipe,reference,output):
    recipe=Path(recipe).resolve();reference=Path(reference).resolve();output=Path(output).resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError('Use a fresh workspace output; existing results are preserved')
    if read(recipe)['reference_sha256']!=sha(reference):
        raise ValueError('Reference/recipe mismatch')
    code=[HERE/'native14.py',HERE/'native14_materials.py',Path(__file__).resolve()]
    state=output.parent/(output.name+'-workloop');state.mkdir(parents=True,exist_ok=False)
    phases=['geometry','material','raster','validate'];nodes=[];previous=[]
    artifacts={
        'geometry':['geometry/geometry.json']+[f'geometry/{stem}{n}.{ext}' for n in [2,3]
                    for stem,ext in [('buffers','npz'),('parts','json'),('parts','svg')]],
        'material':['material/palette.json','material/provenance.json','material/colors2.npz','material/colors3.npz'],
        'raster':[f'raster/{stem}{n}{suffix}' for n in [2,3] for stem,suffix in
                  [('cabinet-','.png'),('preview-','-x4.png'),('structural-ink-','.png'),('owners','.npz')]]+
                 ['native.png','preview-x4.png','preview-gray-x4.png','modular-preview-x4.png'],
        'validate':['validation.json','fixture-black-input.png']}
    # Real file resources permit WorkLoop observations to track changed inputs.
    for i,phase in enumerate(phases):
        nodes.append({'id':phase,'algorithm':'command.run','phase':'validation' if phase=='validate' else 'work',
            'inputs':{'stdin':{'literal':{'contract':'NATIVE14.md exact editable surface pixel production'}}},
            'parameters':{'argv':[sys.executable,'-B',str(HERE/'native14.py'),phase,
                                  '--recipe',str(recipe),'--reference',str(reference),'--output',str(output)],
                          'cwd':str(ROOT),'timeout':60,'code_files':[str(p) for p in code]+[str(recipe)]},
            'reads':['file:'+p.as_posix() for p in [recipe,reference]]+['file:'+(output/p).as_posix() for p in previous],
            'writes':['file:'+(output/p).as_posix() for p in artifacts[phase]+[phase+'-receipt.json']],
            'edges':[{'when':condition(phase,'eq'),'to':phases[i+1] if i+1<len(phases) else '@complete'},
                     {'when':condition(phase,'ne'),'to':'@blocked'}]})
        previous+=artifacts[phase]
    graph={'goal':'One complete editable cabinet object; technical conditions separated from art approval',
           'entry':'geometry','max_steps':4,
           'requirements':[{'id':'actual_native_object','text':'Source materials, editable module geometry, independent black lines and actual PNG',
                            'source':'NATIVE14.md; latest user request','predicate':condition('validate','eq')}],
           'nodes':nodes}
    write(state/'graph.json',graph);started=time.perf_counter();last={}
    for phase,extra in [('init',[str(state/'graph.json')]),('run',[])]:
        p=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),phase,str(state/'state.json'),*extra],
                         cwd=ROOT,capture_output=True,encoding='utf-8',shell=False)
        if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
        last=json.loads(p.stdout)
    if output.exists():
        package=output/'code';package.mkdir()
        for p in code+[recipe,HERE/'NATIVE14.md']:shutil.copyfile(p,package/p.name)
        for name in ['graph.json','state.json']:shutil.copyfile(state/name,output/('workloop-'+name))
        # Package retains its exact reference; file provenance does not certify visual fidelity.
        shutil.copyfile(reference,output/'appearance-reference.png')
        write(output/'execution.json',{'workloop_action':last['action'],'wall_seconds':time.perf_counter()-started,
              'reference_sha256':sha(reference),'code_sha256':{p.name:sha(p) for p in code+[recipe]},
              'artifact_sha256':{p.relative_to(output).as_posix():sha(p) for p in output.rglob('*') if p.is_file()},
              'art_approved':False,'original_grid_recovered':False,'runtime_lighting_implemented':False})
    return {'action':last['action'],'wall_seconds':time.perf_counter()-started,'output':str(output)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe',default=str(HERE/'native14_recipe.json'))
    parser.add_argument('--reference',default=str(ROOT/'docs/artifacts/building37/NativeObject14/appearance-reference.png'))
    parser.add_argument('--output',required=True)
    args=parser.parse_args();sys.stdout.reconfigure(encoding='utf-8')
    result=run(args.recipe,args.reference,args.output)
    print(json.dumps(result))
    if result['action']!='graph_complete':raise SystemExit(2)
