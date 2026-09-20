"""Small D22 graph: exported material, scene integration, actual capture, numeric verdict."""
import json,sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'Tools/WorkLoop'))
import work_loop as w
OUT=ROOT/'LocalOnly/PixelUnityProbe22';STATE=OUT/'work-state.json'
def ref(s):return {'ref':s}
def lit(x):return {'literal':x}
def eq(s,x):return {'op':'eq','args':[ref(s),lit(x)]}
def edge(target,when):return {'to':target,'when':when}
def file(s):return 'file:'+str(ROOT/s)
def invoke(args):
    previous=sys.argv;sys.argv=['work_loop.py',*args]
    try:result=w.main()
    finally:sys.argv=previous
    print(json.dumps(result,ensure_ascii=False))

def create():
    nodes=[]
    def command(id,script,args,following,phase='work'):
        nodes.append({'id':id,'algorithm':'command.run','phase':phase,'inputs':{},
            'reads':[file('LocalOnly/PixelUnityProbe22'),file(script)],'writes':[],
            'parameters':{'argv':[sys.executable,'-B',str(ROOT/script),*args],'cwd':str(ROOT),'timeout':60,'code_files':[str(ROOT/script)]},
            'edges':[edge(following,eq(id+'.exit_code',0)),edge('@blocked',{'op':'ne','args':[ref(id+'.exit_code'),lit(0)]})]})
    command('export','Tools/PixelUnityProbe/prepare.py',['--output',str(OUT/'input')],'place')
    nodes[0]['writes']=[file('LocalOnly/PixelUnityProbe22/input')]
    for id,scope,question,following in [
        ('place','D22 material/geometry only; existing GameMap1 objects and lights preserved',
         'Compile the desk shader/editor helper, run PixelDeskLightingProbe.Build through Unity MCP, read actual build.json and shader errors. The 3D material must use grain only, not final PNG.', 'capture'),
        ('capture','D22 controlled Play Mode camera/light observation; restore temporary state',
         'Use the actual base PlayerCamera to run BeginCapture. Wait for capture.json, inspect Console and restore Play Mode. Do not declare pixel or lighting success yourself.', 'analyze')]:
        nodes.append({'id':id,'algorithm':'ai.work','phase':'work','inputs':{},'parameters':{'scope':scope},'question':question,
            'reads':[file('LocalOnly/PixelUnityProbe22/input')],
            'writes':[file('Assets/Tests/PixelDeskLighting22'),file('Assets/Scenes/GameMap1.unity'),file('LocalOnly/PixelUnityProbe22'),'unity:base-scene'],
            'output_schema':{'evidence':{'type':'string'}},'edges':[edge(following,{'op':'known','args':[ref(id+'.evidence')]})]})
    command('analyze','Tools/PixelUnityProbe/analyze.py',[],'verdict','validation')
    nodes[-1]['writes']=[file('LocalOnly/PixelUnityProbe22/analysis.json'),file('LocalOnly/PixelUnityProbe22/comparison.png')]
    nodes.append({'id':'verdict','algorithm':'json.select','phase':'validation','inputs':{'document':ref('analyze.stdout')},
        'parameters':{'path':['accepted']},'edges':[edge('@complete',eq('verdict.value',True)),edge('@blocked',eq('verdict.value',False))]})
    graph={'goal':'Compare baked image and actual 3D lighting in Unity base, and measure fixed-view pixel preservation.',
        'entry':'export','max_steps':12,'nodes':nodes,'requirements':[{'id':'R1','text':'Actual Unity pixel/lighting measurements pass',
        'source':'user D22 request and Tools/PixelUnityProbe/README.md','predicate':eq('verdict.value',True)}]}
    OUT.mkdir(parents=True,exist_ok=True);w.save(OUT/'work-graph.json',graph)
    invoke(['init',str(STATE),str(OUT/'work-graph.json')]);invoke(['run',str(STATE)])

def trial(name):
    if not name.isalnum():raise ValueError('Simple trial name required')
    graph=json.loads((OUT/'work-graph.json').read_text(encoding='utf-8-sig'))
    graph['entry']='capture';graph['nodes']=[n for n in graph['nodes'] if n['id'] in ('capture','analyze','verdict')]
    graph['goal']+=' Corrected trial after recorded light-response failure; preserve original captures and verdict.'
    capture=graph['nodes'][0]
    capture['question']=f'Run actual GameMap1 PlayerCamera BeginCaptureTrial("{name}"); restore Play Mode and submit capture.json. Previous failed evidence remains immutable.'
    for n in graph['nodes']:
        if n['id']=='analyze':
            n['parameters']['argv'].append(name)
            n['writes']=[file(f'LocalOnly/PixelUnityProbe22/{name}/analysis.json'),file(f'LocalOnly/PixelUnityProbe22/{name}/comparison.png')]
    path=OUT/(name+'-graph.json');state=OUT/(name+'-state.json')
    if path.exists() or state.exists():raise FileExistsError(name)
    w.save(path,graph);invoke(['init',str(state),str(path)]);invoke(['run',str(state)])

if __name__=='__main__':
    if sys.argv[1]=='start':create()
    elif sys.argv[1]=='trial':trial(sys.argv[2])
    elif sys.argv[1]=='submit':
        if len(sys.argv)>3:STATE=OUT/(sys.argv[3]+'-state.json')
        state=w.load_state(STATE);answer={'ticket':state['pending']['ticket'],'output':{'evidence':sys.argv[2]}}
        path=OUT/(STATE.stem+'-answer-'+state['cursor']+'.json');w.save(path,answer);invoke(['submit',str(STATE),str(path)])
