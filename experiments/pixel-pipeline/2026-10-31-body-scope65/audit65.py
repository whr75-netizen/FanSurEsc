"""Record the bounded Assets source search. This never connects to Unity."""
from pathlib import Path
import hashlib, json

HERE = Path(__file__).resolve().parent
REPO = Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
TOKENS = ('_BodyScope551', '_BodySource553', 'ClothRegion524.BeginProbe(',
          'ClothRegion524.Bind(', 'ClothRegion524.BindLines553(',
          'ClothRegion524.Release()', 'ClothRegion524.InScope551(')

def run():
    hits, files, scanned = [], {}, 0
    for p in (REPO/'Assets').rglob('*'):
        if p.suffix not in ('.cs', '.shader', '.compute', '.hlsl'):
            continue
        raw = p.read_bytes()
        text = raw.decode('utf-8-sig', errors='replace')
        scanned += 1
        rel = p.relative_to(REPO).as_posix()
        found = False
        for number, line in enumerate(text.splitlines(), 1):
            tokens = [t for t in TOKENS if t in line]
            if tokens:
                found = True
                hits.append({'path': rel, 'line': number, 'tokens': tokens,
                             'source': line.strip()[:1200]})
        if found:
            files[rel] = hashlib.sha256(raw).hexdigest()
    literal_writers = [h for h in hits if 'SetGlobalBuffer("_BodyScope551"' in h['source']]
    assert len(literal_writers) == 1
    owner_paths = [
        'Assets/EUnityValidation01/VisibilityMotion331/Runtime/MotionView331.cs',
        'Assets/EUnityValidation01/MinimalRestore335/Runtime/Full319View335.cs',
    ]
    owner_traces = []
    for rel in owner_paths:
        raw = (REPO/rel).read_bytes()
        files[rel] = hashlib.sha256(raw).hexdigest()
        for number, line in enumerate(raw.decode('utf-8-sig').splitlines(), 1):
            if any(t in line for t in ('new Material(src)', 'materials=mats.ToArray()', 'void OnDisable(', 'foreach(var m in materials)')):
                owner_traces.append({'path':rel, 'line':number, 'source':line.strip()[:1300]})
    result = {'kind': 'SOURCE_ONLY', 'scanned_assets_sources': scanned,
              'global_literal_writer_count': 1, 'global_literal_writers': literal_writers,
              'hits': hits, 'owner_traces':owner_traces, 'files_sha256': files,
              'limits': ['Does not inspect compiled plugins or runtime reflection/dynamic property-name construction.',
                         'Editor/Order21Prepare.compute is a diagnostic copy; product kernels are Prepare333/OwnerLines333.',
                         'No runtime state, Shader globals, GPU buffers or native objects were queried.']}
    (HERE/'SOURCE_AUDIT65.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'scanned': scanned, 'matching_files': len(files), 'hits': len(hits), 'global_literal_writers': 1}))

if __name__ == '__main__':
    run()
