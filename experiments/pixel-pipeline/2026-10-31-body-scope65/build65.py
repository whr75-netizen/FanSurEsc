"""Prepare an unapplied, working-copy-anchored patch. No writes to Assets or Unity calls."""
from pathlib import Path
import difflib, hashlib, json, subprocess

HERE = Path(__file__).resolve().parent
REPO = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
FILES = [
    'Assets/EUnityValidation01/ClothRegion524/Runtime/ClothRegion524.cs',
    'Assets/EUnityValidation01/MinimalRestore335/Runtime/Full319View335.cs',
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def replace_once(s, old, new):
    assert s.count(old) == 1, repr(old[:120])
    return s.replace(old, new, 1)

def prepare():
    manifest = {'status': 'UNAPPLIED_REVIEW_PATCH', 'files': []}
    patches = []
    for rel in FILES:
        raw = (REPO / rel).read_bytes()
        original = raw.decode('utf-8-sig').replace('\r\n', '\n')
        candidate = original
        if rel == FILES[0]:
            start = candidate.index('    static Mesh scopeMesh551;')
            end = candidate.index('    static bool[] Scope551(', start)
            owner = (HERE / 'BodyScopeOwner65.fragment.cs').read_text(encoding='utf-8')
            candidate = candidate[:start] + owner + '\n' + candidate[end:]
            candidate = replace_once(candidate,
                '        if(scopeMesh551==mesh&&scopeHead551==head&&included551!=null)return included551;',
                '        var owner=ScopeOwner551(f);\n'
                '        if(owner.Mesh==mesh&&owner.Head==head&&owner.Included!=null){selectedScope551=owner;return owner.Included;}')
            candidate = replace_once(candidate,
                '        var ix=mesh.GetIndices(0);included551=new bool[ix.Length/3];var data=new float[included551.Length];ScopeIncluded551=0;',
                '        var ix=mesh.GetIndices(0);var included=new bool[ix.Length/3];var data=new float[included.Length];int count=0;')
            candidate = replace_once(candidate,
                '        for(int pr=0;pr<included551.Length;pr++)if(included551[pr]=!vertex[ix[3*pr]]&&!vertex[ix[3*pr+1]]&&!vertex[ix[3*pr+2]]){data[pr]=1;ScopeIncluded551++;}',
                '        for(int pr=0;pr<included.Length;pr++)if(included[pr]=!vertex[ix[3*pr]]&&!vertex[ix[3*pr+1]]&&!vertex[ix[3*pr+2]]){data[pr]=1;count++;}')
            candidate = replace_once(candidate,
                '        scopeBuffer551?.Release();scopeBuffer551=new ComputeBuffer(data.Length,sizeof(float));scopeBuffer551.SetData(data);scopeMesh551=mesh;scopeHead551=head;return included551;',
                '        owner.Commit(mesh,head,included,data,count);selectedScope551=owner;return owner.Included;')
            candidate = replace_once(candidate,
                'cmd.SetGlobalBuffer("_BodyScope551",ScopeBuffer551());',
                '// 65: motion.materials are runtime-owned clones (MotionView331.Initialise).\n'
                '        // Bind before the existing probe draws; never overwrite an unknown global.\n'
                '        var buffer=ScopeBuffer551(f);\n'
                '        foreach(var material in f.motion.materials)if(material)material.SetBuffer("_BodyScope551",buffer);')
            candidate = candidate.replace('ScopeBuffer551());', 'ScopeBuffer551(f));')
            candidate = replace_once(candidate,
                'cmd.SetComputeIntParam(shader,"_BodyCount553",included551?.Length??1);',
                'cmd.SetComputeIntParam(shader,"_BodyCount553",ScopeOwner551(f).Included?.Length??1);')
            candidate = replace_once(candidate,
                'scopeBuffer551?.Release();scopeBuffer551=null;scopeMesh551=null;scopeHead551=null;included551=null;ScopeIncluded551=0;',
                'ReleaseAllScopes551();')
        else:
            candidate = replace_once(candidate,
                '  if(Active==this)Active=null;if(!ready)return;',
                '  ClothRegion524.ReleaseScope551(this); // also runs after incomplete Initialise / cancelled capture\n'
                '  if(Active==this)Active=null;if(!ready)return;')
        assert candidate != original
        before = HERE / 'before' / rel
        after = HERE / 'candidate' / rel
        before.parent.mkdir(parents=True, exist_ok=True)
        after.parent.mkdir(parents=True, exist_ok=True)
        before.write_bytes(raw)
        after.write_text(candidate, encoding='utf-8', newline='\n')
        manifest['files'].append({'path': rel, 'working_copy_sha256': sha(raw),
                                  'candidate_sha256': sha(after.read_bytes()),
                                  'before_bytes': len(raw), 'candidate_bytes': after.stat().st_size})
        patches.extend(difflib.unified_diff(original.splitlines(True), candidate.splitlines(True),
                                           fromfile='a/' + rel, tofile='b/' + rel))
    (HERE / 'body-scope65.patch').write_text(''.join(patches), encoding='utf-8', newline='\n')
    (HERE / 'PATCH_MANIFEST65.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    index = []
    for rel in FILES:
        text = (HERE/'candidate'/rel).read_text(encoding='utf-8')
        for number, line in enumerate(text.splitlines(), 1):
            names = ('class BodyScopeResources551', 'ComputeBuffer Upload(', 'ComputeBuffer Buffer(',
                     'void Commit(', 'void Dispose(', 'BodyScopeResources551 ScopeOwner551(',
                     'ComputeBuffer ScopeBuffer551(', 'void ReleaseScope551(', 'void ReleaseAllScopes551(',
                     'bool[] Scope551(', 'void BeginProbe(', 'void Bind(', 'void BindLines553(',
                     'void Release()', 'void OnDisable(')
            matches = [name for name in names if name in line]
            if matches:
                index.append({'path': 'candidate/'+rel, 'line': number, 'functions': matches})
    (HERE/'FUNCTION_INDEX65.json').write_text(json.dumps(index, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'prepared': len(FILES), 'applied': False, 'patch_bytes': (HERE/'body-scope65.patch').stat().st_size}))

if __name__ == '__main__':
    prepare()
