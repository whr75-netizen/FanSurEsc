"""Selective create-only archive and local commit, unrelated user files excluded."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,zipfile
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
BASE='f32078ee3d1eb38c4c154bab69385f0dcfa5ca1d';REL='experiments/pixel-pipeline/2026-11-01-whole-eye95';DEST=REPO/REL;DOC='docs/ai/PIXEL_ALBEDO_20261030.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a,binary=False):return subprocess.check_output(['git','-C',str(REPO),*a],**({}if binary else{'text':True,'encoding':'utf-8'}))
def protected():
    p=json.loads((REPO/'experiments/pixel-pipeline/2026-11-01-graph-context94/PRESERVATION94.json').read_text())['protected32']
    assert all(sha(REPO/f)==h for f,h in p.items());return p
def copy(p,d):d.parent.mkdir(exist_ok=True,parents=True);assert not d.exists();shutil.copy2(p,d)
def archive():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();p=protected();assert len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30;assert not DEST.exists()
    summary=json.loads((HERE/'SUMMARY95.json').read_text());assert summary['nativeExact']==47 and not summary['publicDifferences']and not summary['newConsoleErrors'];DEST.mkdir()
    keep={'SUMMARY95.json','FINAL_VALIDATION95.json','INDEX.html','RESULT95-source-cache-audit.json','CELL_PROVENANCE95-source-cache-audit.json','VISIBILITY_PROOF95-source-cache-audit.json','ALPHA_SOURCE95B.json','ALPHA_SOURCE_SKIN95.json','ALPHA_REQUEST95.json','ALPHA_REQUEST_SKIN_FOCUS95.json','QUERIES_OWNED95.json','QUERY_SUMMARY95.json','QUERY_SKIN_FOCUS_SUMMARY95.json','RESULT95.json','RESULT95-joint.json','RESULT95-owned-eye.json','RESULT95-owned-fragment.json','GPU_VALIDATION95.json','FINAL_SEQUENCE95-source-cache-audit.gif','FINAL_STRIP95-source-cache-audit.png','GPU_CLOSED95-native1x.png'}
    for x in HERE.iterdir():
        if x.is_file()and(x.name in keep or x.suffix in ['.py','.cs']or x.name.startswith('GPU_FINAL')and x.suffix=='.png'):copy(x,DEST/x.name)
    copy(HERE.parent/'apply-capture66/analyse_capture68.py',DEST/'reader68.py')
    for x in (HERE/'candidate-source-cache-audit').iterdir():
        if x.is_file():copy(x,DEST/'candidate-source-cache-audit'/x.name)
    # Exclude large native-before JSON snapshots (including UnityConnect native
    # internals), broad unused skin queries, and intermediate console payloads.
    for folder in ['capture','capture-scale-correct','alpha','alpha-bounded','alpha-skin-focus','gpu-closed','gpu-final','post-final']:
        for x in (HERE/folder).iterdir():
            if not x.is_file()or x.name.startswith('native-before-')or '_CONSOLE_'in x.name:continue
            if x.suffix=='.cs' or x.name.startswith('RUN_')or x.name=='relay95.py' or (x.suffix=='.json'and(x.name.startswith(('STATE95','CURRENT95','POST95','VERIFY95','NATIVE95','NATIVE_BEFORE','PRIOR47','FINAL_GPU','FinalGPU','ReadAlpha','Post95Final'))or x.name in ['GLOBAL_NAMES66.json','CAPTURE_STARTED76.json'])):copy(x,DEST/folder/x.name)
    with zipfile.ZipFile(DEST/'RAW95.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for e in json.loads((HERE/'capture-scale-correct/STATE95B-0018-finished.json').read_text())['sequencePackets']:
            q=Path(e['output']);assert(q/'RAW_COMPLETE76.marker').read_text()==sha(q/'RAW_MANIFEST.json')
            for x in q.iterdir():
                assert x.is_file();z.write(x,f'frame-{e["frame"]}/'+x.name)
    report=json.loads((HERE/'gpu-final/FINAL_GPU95_FINAL.json').read_text())
    with zipfile.ZipFile(DEST/'GPU95.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for x in Path(report['output']).iterdir():
            if x.is_file():z.write(x,x.name)
    (DEST/'.gitattributes').write_text('* -text\n')
    (DEST/'PRESERVATION95.json').write_text(json.dumps({'baselineCommit':BASE,'protected32':p,'userModified30Preserved':True,'product':77,'AssetsChanged':0,'uncommittedProductIntegration':False,'push':False},indent=2)+'\n')
    (DEST/'REPRODUCTION.md').write_text('''# Read-only reproduction\n\nRun `python -B test_archive95.py` with NumPy installed. This checks saved source markers/770 plane headers, all21 actual GPU fields, finite tables, protected native pixels and recorded restoration without extraction or Unity.\n\n`solve95.py` and preparation scripts retain original task-relative dependencies and original capture output paths. They are source navigation records, not a portable fresh-capture launcher. The bundled `RUN_*.cs.txt` files are the exact external compilations used. Do not automatically execute them: their existing output paths are create-only and their capture modes enter Play.\n\nFinal active experimental output is `candidate-source-cache-audit`; `gpu-final` is the21-field replay with source primitive in owner.w. `gpu-closed` was an intermediate numerical replay before correcting owner.w; it is NOT final semantic validation. First capture95 failed scale-reference matching and produced0packets, then95B corrected BakeMesh(true). The original source-cache packet computation completed but JSON provenance export failed on NumPy int64. Audit fixed scalar serialization; every frozen output array is byte-equivalent. The candidate did not change for that export fix.\n\n`RESULT95*.json` ablations retain failed all-protection, double-occlusion and whole-cell backing conditions. Source-rest affine registration and original support are inherited from89; algorithm dependencies remain in the existing source workspace/prior archives. Product77 remains active. Cold exact part ties, live C#/HLSL joint selection and full motion aesthetic validation remain unresolved.\n''',encoding='utf-8')
    files=[{'path':x.relative_to(DEST).as_posix(),'SHA256':sha(x),'bytes':x.stat().st_size}for x in sorted(DEST.rglob('*'))if x.is_file()];(DEST/'ARTIFACTS95.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    doc=REPO/DOC;before=doc.read_bytes();assert b'## Eye95 'not in before
    with doc.open('ab')as f:f.write((HERE/'HANDOFF_APPEND95.txt').read_bytes())
    (HERE/'HANDOFF_BEFORE95.sha256').write_text(hashlib.sha256(before).hexdigest()+'\n')
    print(json.dumps({'archive':str(DEST),'files':len(files)+1,'rawZipBytes':(DEST/'RAW95.zip').stat().st_size,'gpuZipBytes':(DEST/'GPU95.zip').stat().st_size,'protected32Matched':True,'AssetsChanges':0},indent=2))
def commit():
    assert git('rev-parse','HEAD').strip()==BASE and not git('diff','--cached','--name-only').strip();p=protected();m=json.loads((DEST/'ARTIFACTS95.json').read_text())['files'];assert all(sha(DEST/r['path'])==r['SHA256']for r in m)
    git('add','--',REL,DOC);expected={REL+'/'+r['path']for r in m}|{REL+'/ARTIFACTS95.json',DOC};staged=set(git('diff','--cached','--name-only','-z').strip('\x00').split('\x00'));assert staged==expected
    for r in m:assert hashlib.sha256(git('show',':'+REL+'/'+r['path'],binary=True)).hexdigest()==r['SHA256']
    assert git('diff','--cached','--numstat','--',DOC).strip().split('\t')[1]=='0';git('diff','--cached','--check','--',DOC)
    print(git('commit','-m','Validate whole-eye source ownership and evaluated blink composition in isolation'))
    assert not git('diff','--cached','--name-only').strip()and len(git('status','--porcelain=v1','--untracked-files=no').splitlines())==30;protected()
    r={'commit':git('rev-parse','HEAD').strip(),'files':len(staged),'archive':REL,'userModified30Preserved':True,'protected32Matched':True,'product':77,'push':False};(HERE/'COMMIT95.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':{'archive':archive,'commit':commit}[sys.argv[1]]()
