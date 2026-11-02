"""Read-only source call-closure/binding/dispatch audit. No Unity or compiler."""
from pathlib import Path
import hashlib, json, re, sys
from direct_support24 import H, P, sibling

R = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
BANNED = ['EvaluateForm115', 'Pareto115', 'BoundRun115', 'Probe115', 'Forward115', 'ForwardEye115', 'RegionDriver115', 'Down115', 'Up115']
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def text(path): return path.read_text(encoding='utf-8-sig')
def strip_usings(source): return re.sub(r'(?m)^using [^;\n]+;\r?\n?', '', source)

def functions(source):
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', lambda m: ''.join('\n' if c=='\n' else ' ' for c in m[0]), source, flags=re.S)
    out = {}
    for match in re.finditer(r'\b[A-Za-z_]\w*\s+(\w+)\s*\([^;{}]*\)\s*\{', clean):
        name = match[1]
        if name in ['if', 'for', 'while', 'switch']: continue
        start = clean.index('{', match.start()); depth = 1; at = start + 1
        while depth:
            depth += (clean[at] == '{') - (clean[at] == '}'); at += 1
        assert name not in out, name
        out[name] = {'body': clean[start+1:at-1], 'source': clean[match.start():at], 'line': source.count('\n',0,match.start())+1}
    return out

def closure(name, funcs):
    todo = [name]; found = set()
    while todo:
        name = todo.pop()
        if name in found: continue
        found.add(name)
        todo.extend(n for n in re.findall(r'\b(\w+)\s*\(', funcs[name]['body']) if n in funcs and n not in found)
    return sorted(found)

DETAIL = {
 'PackPart': ('12 dispatches:4 parts ×3 engines; ceil(w/8),ceil(h/8)', 'Native dimensions72×32, dense/carrier144×64;20 float4 planes/engine', 'Constant5 fields; per-thread O(1)'),
 'Refit': ('3 engines × each recorded BVH level; ceil(levelCount/64)', 'Nodes59083, depth15 in actual113; boxes2×nodes; indices checked by original constructor', 'One node/thread per level; full topology unchanged'),
 'Query': ('3 dispatches; total82944 logical query rays', 'Same triangles29542/vertices20459/materials15/BVH59083 in saved inputs', 'while(sp>0), stack32; no explicit visit-budget check. Acyclic-tree proof only; worst59083 node visits/ray'),
 'Select': ('3 dispatches; each ceil((w/4)/8),ceil((h/4)/8)', 'Same input layers/visibility, canonical outputs n/16', '16 sub-samples,3 parts; private weight48/L4/U4 arrays retained'),
 'CarrierQueries113': ('1 dispatch:ceil(144×64×4/64)=576 groups', 'Read20 layer planes; write4×9216 query records', 'O(1)/query; original8x carrier coordinate contract remains'),
 'PrepareCells113': ('3×1 groups ×64 threads;144 in-bounds cells', 'Cells512×7×16, tags512×16, source144×64, keys20, curves846', '64 samples/cell; SourceKey scan≤32; curve loops≤1024. Source limits unchanged'),
 'GatherEye113': ('2×1×1, numthreads1', 'Frame64×16, points48×16, grid≤512; same caches', 'RawConnected seen16; up to32 active scope calls ×512 passes ×512 cells, plus24-point adjacency'),
 'BuildSubsets113': ('64×4×1, numthreads64 =16384 nominal threads', 'Subsets16384×32; head np≤24/ni,nw≤12/ni+nw≤21; b.z now direct float bits', 'Per valid subset≤24 point scans +8×24×24 connectivity checks. New≤24 scalar mass additions/subset'),
 'Enumerate113': ('32768×2×1, numthreads64 =4194304 nominal threads', 'Groups65536×48; subset indices<16384; same guard/buffer sizes', '64-thread shared reduction,6 barrier rounds; one direct-sum add/valid pair; comparator adds scalar tie check'),
 'Reduce113': ('2×1×1, numthreads64', 'Read32768 groups/eye; best2×48; tail.z now direct float bits', '512 serial group merges/thread +6 shared reduction rounds. Body unchanged but Less113 closure changes'),
 'Write113': ('3×1 groups ×64 threads;144 in-bounds cells', 'Read cells/frame/points/best; four144×16 outputs for current grid', '≤24 point lookups/cell; closure unchanged; valid first-write diagnostic entry'),
 'ComposeForward102': ('Twice for original102 and legacy106 controls;ceil(ROI/8)', 'Same canvas/hair and four ROI RTs', '16 fine samples and legacy select; control-only work not required in new first probe'),
 'ApplyCurve106': ('1 control dispatch:ceil(18/8),ceil(8/8)', 'Original legacy106 debug output/curves', 'Curve loop and source sampling unchanged; control-only work not needed in first probe'),
 'ComposeRegion113': ('1 dispatch:ceil(ROI/8)', 'Same four region output RTs; exposure1024×16', '16 carrier/hair samples; private depth16/known16 retained. New transport and ring policy NOT integrated'),
 'ComposeWhole113': ('1 extra capture dispatch:60×34 groups ×64 threads', '480×272 float4 RT; candidate tile/current product77 colour', 'O(1)/pixel; capture helper then synchronous plane readbacks'),
 'ResolveCurve107': ('Not called in successful113 Draw (literal ApplyCurve106 selected)', 'Unchanged declarations', 'Dead on audited path, but retained shader entrypoint'),
 'PackWorld98': ('Not called by Forward113 path; method exists in WholeEye107', 'Unchanged world-underlay resources', 'Dead on audited path; no claim physically absent from asset'),
 'Compose': ('Not called by Forward113 path; method exists in WholeEye107', 'Unchanged legacy composition resources', 'Dead on audited path; no claim physically absent from asset')
}

def main():
    old_path = P/'ForwardEye113.compute'; new_path = H/'ForwardEye113_Direct24.compute'
    old, new = text(old_path), text(new_path); a,b=functions(old),functions(new)
    assert set(a)==set(b)
    changed = [n for n in a if a[n]['source'] != b[n]['source']]
    assert sorted(changed)==['BuildSubsets113','Enumerate113','Less113'], changed
    kernels=re.findall(r'#pragma kernel (\w+)',old)
    assert kernels==re.findall(r'#pragma kernel (\w+)',new) and not any(x in new for x in BANNED)
    resources={}
    for declaration in re.finditer(r'((?:RW)?(?:StructuredBuffer|Texture2D)<[^>]+>)\s+([^;]+);',old):
        for name in re.findall(r'(_\w+)',declaration[2]):resources[name]=declaration[1]
    rows=[]
    for kernel in kernels:
        ca,cb=closure(kernel,a),closure(kernel,b);sa='\n'.join(a[n]['source']for n in ca);sb='\n'.join(b[n]['source']for n in cb)
        ra=sorted(n for n in resources if re.search(r'\b'+re.escape(n)+r'\b',sa));rb=sorted(n for n in resources if re.search(r'\b'+re.escape(n)+r'\b',sb));assert ra==rb
        array_sites=[{'function':n,'name':m[1],'count':int(m[2])}for n in cb for m in re.finditer(r'\b(?:float\d?|int\d?|uint\d?|bool\d?)\s+(\w+)\s*\[(\d+)\]',b[n]['body'])]
        threads=re.search(r'\[numthreads\(([^)]+)\)\]\s*void\s+'+kernel+r'\b',new)[1]
        dispatch,memory,bound=DETAIL[kernel]
        rows.append({'kernel':kernel,'threads':threads,'line':b[kernel]['line'],'bodyChanged':a[kernel]['source']!=b[kernel]['source'],
                     'closureChanged':sa!=sb,'closure':cb,'sameResourceNamesAndTypes':True,'resources':{n:resources[n]for n in rb},
                     'sourceLocalArrays':array_sites,'dispatch113AndUnconnectedCandidate':dispatch,'memoryRange':memory,'loopBoundAndDelta':bound})
    run=P/'attempt5/RUN_Capture113e.cs.txt'
    if not run.exists():run=P/'RUN_Capture113e.cs.txt'
    bundle=text(run); request_path=P/'attempt5/Capture113e_REQUEST.json'
    if request_path.exists():assert sha(run)==json.loads(text(request_path))['sourceSHA256']
    # Frozen successful command is the authoritative host, not a newly rebundled copy.
    assert not any(x in bundle for x in BANNED)
    dependencies=[('argon23-runtime113','Forward113.cs'),('argon23-runtime113','RegionDriver113.cs'),('argon23-runtime113','NativeCarrier113.cs'),
                  ('argon23-runtime113','SourcePigmentStream113.cs'),('aperture-runtime111','WholeEye111.cs'),('joint-lid107','LiveSurface107.cs'),
                  ('layer-zero101','LayerZero101.cs'),('live-underlay98','NativeRetarget96.cs')]
    dep_rows=[]
    for folder,name in dependencies:
        if folder=='argon23-runtime113':path=P/name
        else:
            path=H.parent/folder/name
            if not path.exists():
                matches=list((R/'experiments/pixel-pipeline').glob('*/'+name));assert len(matches)==1,(name,matches);path=matches[0]
        body=strip_usings(text(path))
        typename={'WholeEye111.cs':'WholeEye107','SourcePigmentStream113.cs':'SourcePigment113'}.get(name,Path(name).stem)
        match=re.search(r'\bclass\s+'+typename+r'\b',bundle);assert match,typename
        dep_rows.append({'path':str(path),'SHA256':sha(path),'bodyInSuccessfulBundle':body in bundle,'bundledClass':typename,'bundleLine':bundle.count('\n',0,match.start())+1})
    assert all(r['bodyInSuccessfulBundle']for r in dep_rows),dep_rows
    scans=[];hits=[];total=0
    for root in [R/'Assets/EUnityValidation01',R/'Assets/Scripts']:
        for path in root.rglob('*.cs'):
            data=path.read_bytes();total+=len(data);scans.append(str(path.relative_to(R)))
            found=[word for word in BANNED if word.encode()in data]
            if found:hits.append({'file':str(path.relative_to(R)),'names':found})
    assert not hits
    serialized_hits=[];serialized_skipped=[];serialized_files=0;serialized_bytes=0
    dangerous_guid=b'fe1e7dae18456b94c99d1169e94d2c67'
    for root in [R/'Assets/EUnityValidation01',R/'Assets/Settings',R/'Assets/Scenes']:
        for path in root.rglob('*'):
            if path.suffix not in ['.asset','.prefab','.unity'] or not path.is_file():continue
            size=path.stat().st_size
            if size>16*1024*1024 or serialized_bytes+size>128*1024*1024:
                serialized_skipped.append(str(path.relative_to(R)));continue
            data=path.read_bytes();serialized_files+=1;serialized_bytes+=len(data)
            if dangerous_guid in data.lower() or b'ForwardEye115' in data:
                serialized_hits.append(str(path.relative_to(R)))
    report={'schema':'candidate24/static-host-gate/v1','GPUOrUnityOrCompilerInvocations':0,'oldShaderSHA256':sha(old_path),'candidateShaderSHA256':sha(new_path),
            'successfulCommand':{'path':str(run),'SHA256':sha(run),'bytes':run.stat().st_size,'forbiddenReferences':[],'keyDependencies':dep_rows},
            'productCSharpScan':{'roots':['Assets/EUnityValidation01','Assets/Scripts'],'files':len(scans),'bytes':total,'forbiddenReferences':hits,'notScanned':'Other package/native/reflection/dynamically loaded session code; current Editor state not queried'},
            'serializedAssetScan':{'files':serialized_files,'bytes':serialized_bytes,'dangerous115References':serialized_hits,'skipped':serialized_skipped,'scope':'EUnityValidation01/Settings/Scenes .asset/.prefab/.unity; not all package/native/session state'},
            'currentCandidateHostExists':False,'candidateShaderInAssets':False,
            'currentHardcodedShaderLoads':{'file':'Forward113.cs','line':21,'count':3,'path':'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye113.compute'},
            'cloneOwnership':{'file':'WholeEye111.cs','line':26,'cloneInput':'Explicit original passed from Forward113, not a hardcoded115 asset','perViewOwned':True,'disposeLine':69},
            'callbacks':{'Capture113.cs:64':'EditorApplication.update+=Tick (Play lifecycle/capture)','Forward113.cs:21':'LayerZero101.AfterCanvas=Record','Forward113.cs:48':'Unhooks own AfterCanvas, disposes own region/three engines/native/targets','Capture113.cs:107':'EditorApplication.update-=Tick'},
            'hazardsInHistoricalRunner':['It enters Play and installs observers; do not replay it for the first compute test.','Whole engine still Query stack32/Select arrays; GatherEye113 still seen16; ComposeRegion113 still depth16/known16.','GraphicsBuffer.GetData and CpuSourceCapture64 synchronous plane readback are present; strip height bounds bytes, not GPU waiting time.','Full3-engine BVH/region enumeration and legacy102/106 control paths remain; no automatic full renderer reuse.'],
            'mechanicallyExcludedNow':'115 evaluator/interval code absent from candidate source and frozen113 host. Not an end-to-end loaded candidate attestation: no candidate host/binding exists yet.',
            'changedFunctionBodies':changed,'changedKernelClosures':[r['kernel']for r in rows if r['closureChanged']],
            'geometryImplementation':'Transport/ring/midpoint are CPU checks and uncompiled helper source only. No changes in RegionDriver113 scalar12mm, CarrierQueries1138x or ComposeRegion113 missing-carrier logic.',
            'matrix':rows}
    (H/'HOST_ROUTE24.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# 113 → Direct24 정적 커널 비교','', '소스/호출 폐쇄만 비교했다. 후보 host 없음, Assets/import/컴파일/GPU0. 현행 C#을 실행하면 원래113 shader가 로드된다.','',
           '| 커널 | 코드·호출 폐쇄 변화 | 기존/예정 dispatch | 메모리·반복 한계 |','|---|---|---|---|']
    for row in rows:
        delta='본문 및 폐쇄 변경'if row['bodyChanged']else'본문 동일, Less113 폐쇄 변경'if row['closureChanged']else'동일'
        lines.append('| '+row['kernel']+' | '+delta+'; 바인딩 이름·형 동일 | '+row['dispatch113AndUnconnectedCandidate']+' | '+row['memoryRange']+'; '+row['loopBoundAndDelta']+' |')
    lines.extend(['','115 Evaluate/Pareto/interval 기능은 후보에 없다. 113의 나머지 배열/큰 반복은 남아 있으므로 전체 shader가 zero-scratch이거나 현재 GPU가 안전하다는 뜻은 아니다.',
                  '', '관측된113 전체 GPU dispatch/자원은 제품77·URP/world 자체 작업을 포함한 전체 시스템 상한이 아니다. Stage별 작은 검증은 아래 NEXT_GPU_PREFIX24.json 계획이며 아직 host도 작성·실행하지 않았다.'])
    (H/'HOST_KERNELS24.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'successful113BundleHas115':False,'candidateHostExists':False,'changedFunctions':changed,'changedKernelClosures':report['changedKernelClosures'],
                      'kernelsCompared':len(rows),'productCsScanned':len(scans),'localArrayKernels':[r['kernel']for r in rows if r['sourceLocalArrays']]}))

if __name__=='__main__':main()
