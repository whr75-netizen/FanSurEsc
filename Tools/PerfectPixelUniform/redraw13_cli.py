"""Fixed WorkLoop recipe for the first source cabinet's R13 reconstruction."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from redraw13 import ROOT, SOURCE_SHA, digest, write

HERE=Path(__file__).resolve().parent


def condition(stage,op):
    return {'op':op,'args':[{'ref':stage+'.exit_code'},{'literal':0}]}


def start(source,output):
    source=Path(source).resolve();output=Path(output).resolve()
    if not source.is_file() or not output.is_relative_to(ROOT) or digest(source)!=SOURCE_SHA:
        raise ValueError('Unchanged reference sheet and a fresh workspace output are required')
    code=[str(HERE/name) for name in ('redraw13.py','redraw_geometry13.py','redraw_detail13.py','redraw13_cli.py')]
    hashes={Path(p).name:digest(p) for p in code}
    if output.exists():
        record=read_execution(output)
        if record.get('code_sha256')!=hashes or record.get('source_sha256')!=SOURCE_SHA or record.get('workloop_action')!='graph_complete':
            raise ValueError('Existing result has different inputs/code or is incomplete; preserve it and use a fresh output.')
        files=record.get('artifact_sha256',{})
        if not files or any(not (output/name).is_file() or digest(output/name)!=sha for name,sha in files.items()):
            raise ValueError('Cached artifact changed; do not overwrite or re-generate silently.')
        return {'action':'graph_complete','output':str(output),'cached':True,'generation_calls':0,'art_approved':False}
    # This runner has one recipe owner. File inspections cannot replace any
    # geometry, detail or raster computation, and failure stops dependent work.
    state_dir=output.parent/(output.name+'-workloop')
    state_dir.mkdir(parents=True,exist_ok=False)
    phases=['geometry','detail','raster','validate'];nodes=[]
    artifacts={
        'geometry':['source-cabinet.png','geometry.json','geometry.npz','geometry-overlay.png','geometry-receipt.json'],
        'detail':['detail.json','detail.npz','detail-receipt.json'],
        'raster':['native.png','preview-x4.png','preview-x8.png','structure-mask.png','raster.npz','comparison.png','raster-receipt.json'],
        'validate':['validation.json','validate-receipt.json']}
    preceding=[]
    for i,phase in enumerate(phases):
        after=phases[i+1] if i+1<len(phases) else '@complete'
        nodes.append({'id':phase,'algorithm':'command.run','phase':'validation' if phase=='validate' else 'work',
            'inputs':{'stdin':{'literal':{'contract':'REDRAW13.md: real-source structural/detail reconstruction'}}},
            'parameters':{'argv':[sys.executable,'-B',str(HERE/'redraw13.py'),phase,'--source',str(source),'--output',str(output)],
                'cwd':str(ROOT),'timeout':60,'code_files':code},
            'reads':['file:'+source.as_posix()]+['file:'+(output/name).as_posix() for name in preceding],
            'writes':['file:'+(output/name).as_posix() for name in artifacts[phase]],
            'edges':[{'when':condition(phase,'eq'),'to':after},{'when':condition(phase,'ne'),'to':'@blocked'}]})
        preceding+=artifacts[phase]
    graph={'goal':'One source cabinet reconstructed on a common authored pixel grid; no automatic art approval',
        'entry':'geometry','max_steps':4,
        'requirements':[{'id':'r13_technical','text':'Actual source features, geometry and finite native raster',
                         'source':'REDRAW13.md','predicate':condition('validate','eq')}],'nodes':nodes}
    write(state_dir/'graph.json',graph)
    started=time.perf_counter();last={}
    for phase,extra in [('init',[str(state_dir/'graph.json')]),('run',[])]:
        run=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),phase,
                            str(state_dir/'state.json'),*extra],cwd=ROOT,capture_output=True,encoding='utf-8',shell=False)
        if run.returncode:raise RuntimeError(run.stdout+'\n'+run.stderr)
        last=json.loads(run.stdout)
    duration=time.perf_counter()-started
    # Source and code provenance travel with the deliverable, not just LocalOnly.
    if output.exists():
        package=output/'code';package.mkdir()
        for path in code:shutil.copyfile(path,package/Path(path).name)
        for name in ['graph.json','state.json']:shutil.copyfile(state_dir/name,output/('workloop-'+name))
        artifact_hashes={p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()}
        write(output/'execution.json',{'code_sha256':hashes,'source_sha256':SOURCE_SHA,
            'artifact_sha256':artifact_hashes,
            'workloop_action':last['action'],'wall_seconds':duration,'generation_calls':0,
            'alpha_policy':'0/255 geometry coverage','original_grid_recovered':False,
            'art_approved':False,'output':str(output),'state':str(state_dir/'state.json')})
    return {'action':last['action'],'output':str(output),'wall_seconds':duration,'art_approved':False}


def read_execution(output):
    path=output/'execution.json'
    if not path.is_file():raise ValueError('Existing output lacks a completion receipt.')
    return json.loads(path.read_text(encoding='utf-8'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default=str(ROOT/'docs/artifacts/building37/Redraw10/source.png'))
    parser.add_argument('--output')
    args=parser.parse_args();sys.stdout.reconfigure(encoding='utf-8')
    if not args.output:
        version=''.join(digest(HERE/name) for name in ['redraw13.py','redraw_geometry13.py','redraw_detail13.py','redraw13_cli.py'])
        import hashlib
        key=hashlib.sha256((SOURCE_SHA+version).encode()).hexdigest()[:16]
        args.output=str(ROOT/'LocalOnly/PerfectPixelUniform'/('R13-'+key))
    result=start(args.source,args.output);print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['action']=='graph_complete' else 1)
