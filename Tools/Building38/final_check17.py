"""Validator-only reopen: preserve native caches and actual Unity observations."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from floor_repair17 import compare_fixture, sha

ROOT=Path(__file__).resolve().parents[2]
GATE='Tools/Building38/unity_gate17.py'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def check(source,output):
    repair=read(output/'validator-repair.json');frozen=read(source/'input-hashes.json')
    changed=[name for name,value in frozen.items() if sha(ROOT/name)!=value]
    if changed != [GATE] or repair['before_sha256']!=frozen[GATE] or repair['after_sha256']!=sha(ROOT/GATE):
        raise ValueError('Only the documented float32 validator correction may change')
    cpu=read(source/'cpu-validation.json')
    if not cpu['success'] or cpu['other_cache_regeneration_count']!=0:
        raise ValueError('Floor-only CPU evidence failed')
    previous=ROOT/'docs/artifacts/building39/run02'
    comparisons=[compare_fixture(previous/name/'preview.png',previous/name/'gpu-fixture.png',name)
                 for name in ['empty_counter','stock_shelf']]
    comparisons.append(compare_fixture(source/'floor_surface/preview.png',source/'floor_surface/gpu-fixture.png','floor_surface'))
    receipt=read(source/'play-observation.json')
    if receipt.get('phase')!='play' or receipt.get('floorContrastRetention')!=1 or not all(receipt['restoration'].values()):
        raise ValueError('Final actual grain/clock/background observations required')
    result=subprocess.run([sys.executable,'-B',str(ROOT/GATE),str(source/'play-observation.json')],
                          cwd=ROOT,text=True,encoding='utf-8',capture_output=True,shell=False)
    print(result.stdout)
    if result.returncode:raise ValueError(result.stderr or 'Actual Play requirements failed')
    write(output/'validation.json',{'success':True,'comparisons':comparisons,
          'validator_only_reopen':repair,'source_receipt':str(source/'play-observation.json'),
          'production_regeneration_count':0})
    print(json.dumps({'success':True,'comparisons':comparisons}))

def start(source,output):
    if output.exists() or not output.is_relative_to(ROOT):raise ValueError('Fresh workspace validation output required')
    output.mkdir(parents=True);frozen=read(source/'input-hashes.json')
    write(output/'validator-repair.json',{'file':GATE,'before_sha256':frozen[GATE],'after_sha256':sha(ROOT/GATE),
          'reason':'Observed 0.99999994px was inside integer tolerance but rejected by an exact >=1 lower bound; apply existing .001px tolerance consistently. Raw Unity receipt unchanged.'})
    argv=[sys.executable,'-B',str(Path(__file__).resolve()),'check','--source',str(source),'--output',str(output)]
    predicate={'op':'eq','args':[{'ref':'final.exit_code'},{'literal':0}]}
    graph={'goal':'Accept actual N17 production and corrected floor observations after validator-only float32 repair',
           'entry':'final','max_steps':1,'requirements':[{'id':'actual_native_night','source':'BUILDING16.md N17 actual receipts',
           'text':'Actual GPU parity, shared grid, night, moving light, same Player/Camera and restored test controls','predicate':predicate}],
           'nodes':[{'id':'final','algorithm':'command.run','phase':'validation',
           'inputs':{'stdin':{'literal':{'production_repeated':False}}},
           'parameters':{'argv':argv,'cwd':str(ROOT),'timeout':30,'code_files':[str(Path(__file__).resolve()),str(ROOT/GATE)]},
           'reads':['file:'+str(source/'play-observation.json'),'file:'+str(source/'input-hashes.json'),'file:'+str(output/'validator-repair.json')],
           'writes':['file:'+str(output/'validation.json')],
           'edges':[{'when':predicate,'to':'@complete'},
                    {'when':{'op':'ne','args':[{'ref':'final.exit_code'},{'literal':0}]},'to':'@blocked'}]}]}
    write(output/'graph.json',graph)
    for action,extra in [('init',[str(output/'graph.json')]),('run',[])]:
        result=subprocess.run([sys.executable,'-B',str(ROOT/'Tools/WorkLoop/work_loop.py'),action,str(output/'state.json'),*extra],cwd=ROOT,text=True,capture_output=True,encoding='utf-8',shell=False)
        print(result.stdout)
        if result.returncode:raise ValueError(result.stderr)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['start','check']);p.add_argument('--source',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    sys.stdout.reconfigure(encoding='utf-8');{'start':start,'check':check}[a.action](Path(a.source).resolve(),Path(a.output).resolve())
