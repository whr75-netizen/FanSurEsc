"""Freeze bounded, offline diagnostics; source files are never modified."""
from pathlib import Path
import argparse, ast, base64, collections, dataclasses, hashlib, json, math
import os, shutil, struct, sys, types
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--exp27', type=Path, required=True)
ap.add_argument('--exp30', type=Path, required=True)
ap.add_argument('--output', type=Path, required=True)
ap.add_argument('--resume-preparation', action='store_true')
args = ap.parse_args()
E27, E30, OUT = args.exp27.resolve(), args.exp30.resolve(), args.output.resolve()
assert not OUT.exists() or args.resume_preparation, 'Use a new dated snapshot directory; never overwrite'
OUT.mkdir(parents=True, exist_ok=args.resume_preparation)
F = E27 / 'author33/feature34'
origins, external = {}, {}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))

def alias(p):
    p = Path(p).resolve()
    for name, root in [('EXP27', E27), ('EXP30', E30)]:
        if p.is_relative_to(root): return name + '/' + p.relative_to(root).as_posix()
    model_root=Path.home()/'Desktop/작업폴더'
    product_root=Path.home()/'Documents/work/Fantasy Survival Escape Game'
    if p.is_relative_to(model_root): return 'MODEL/' + p.relative_to(model_root).as_posix()
    if p.is_relative_to(product_root): return 'PRODUCT/' + p.relative_to(product_root).as_posix()
    raise ValueError('Unregistered provenance root: '+str(p))

def record(p):
    p = Path(p)
    return {'source': alias(p), 'sha256': sha(p), 'bytes': p.stat().st_size}

def copy(p, dest):
    p = Path(p); d = OUT / dest
    assert p.is_file(), p
    d.parent.mkdir(parents=True, exist_ok=True)
    if d.exists(): assert args.resume_preparation and sha(d)==sha(p), 'Changed prepared copy: ' + str(d)
    else: shutil.copyfile(p, d)
    assert sha(d) == sha(p)
    origins[d.relative_to(OUT).as_posix()] = {**record(p), 'mode': 'byte-exact copy'}

def fixture(name, data, sources, rule):
    d = OUT / 'fixtures' / name
    d.parent.mkdir(parents=True, exist_ok=True)
    payload=json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    if d.exists(): assert args.resume_preparation and d.read_bytes()==payload, 'Changed prepared fixture: ' + str(d)
    else: d.write_bytes(payload)
    origins[d.relative_to(OUT).as_posix()] = {'mode': 'derived bounded fixture',
        'rule': rule, 'sources': [record(p) for p in sources]}

def omit(p, purpose):
    p = Path(p)
    if p.is_file(): external[alias(p)] = {**record(p), 'neededFor': purpose, 'included': False}

groups = {
 'palette-v3': ['SHARED_NATIVE_PALETTE.json','SHARED_EXISTING16_ABLATION.json','NATIVE_COVERAGE_FIT.json','SOURCE_FAMILY_INPUT.json','API_VERIFIED.json','NATIVE_VERIFIED.json','PIXEL_EVIDENCE.json','SUMMARY.json','REPORT_KO.md','CONTRACT_DIFF.md'],
 'palette-v4-feature': ['CONSTRAINED_16.json','CONSTRAINED_32.json','CONSTRAINED_64.json','PALETTE_16.json','PALETTE_32.json','PALETTE_64.json','NINE_NATIVE_AUDIT.json','AUDIT_DECISIONS.json','FEATURE_CERTIFICATES.json','CONTRACT.md','REPORT_KO.md','VERIFIED.json','API_VERIFIED.json','BUDGET_SUMMARY.json'],
 'flat-albedo-control': ['INPUT.json','PALETTE_LEGACY.json','PALETTE_DISTINCT.json','CONSTANT_SOURCE.json','VERIFIED.json','API_VERIFIED.json','PIXEL_VERIFIED.json','CURRENT_PIPELINE_AUDIT.json','SHADE_FRAGMENTATION.json','SUMMARY.json','REPORT_KO.md']}
excluded_code = {'publish.py','complete_publish.py','finalize.py','package.py'}
for name, contracts in groups.items():
    d = E30 / name
    for p in sorted(d.iterdir()):
        if p.is_file() and ((p.suffix in {'.py','.cjs','.mjs','.js'} and p.name not in excluded_code) or p.name in contracts):
            copy(p, 'archive/exp30/' + name + '/' + p.name)
copy(E30/'colour-family/pngio.py', 'archive/exp30/colour-family/pngio.py')
copy(E30/'cdp.mjs', 'archive/exp30/cdp.mjs')
copy(E30/'palette-v2/PATTERN_REFERENCE_PALETTE.json', 'archive/exp30/palette-v2/PATTERN_REFERENCE_PALETTE.json')

folders = {
 'eye-cache42': ['CACHE_BINDING.json','TEMPLATE_FEATURE_GRAPH.json','SYNTHETIC_SELECTOR_COUNTEREXAMPLES.json','STORED_FRAME_EVIDENCE.json','VERIFIED.json','CONTRACT_DIFF.json','REPORT_KO.md','VISUAL_REVIEW_KO.md'],
 'eye-cache42/joint-placement43': ['CELL_AND_COLOUR_PROVENANCE.json','REGISTRATIONS.json','RESULTS.json','PHASE_FAILURES.json','STATE_TESTS.json','TESTS.json','OUTPUT_VERIFIED.json','CONTRACT_KO.md','REPORT_KO.md','VISUAL_REVIEW_KO.md'],
 'flat-shade-boundary44': ['FROZEN_INPUT.npz','LAYERS.npz','RESULTS.json','CONTRACT_KO.md','REPORT_KO.md','VISUAL_REVIEW_KO.md','VERIFIED.json','SPACING_INDEPENDENCE.json','fit-only-control-RESULTS.json','strict-cell-control-RESULTS.json','unconstrained-failure-RESULTS.json'],
 'flat-shade-boundary44/selection935': ['EVIDENCE.json','REPORT_KO.md','VERIFIED.json']}
for folder, contracts in folders.items():
    for p in sorted((F/folder).iterdir()):
        if p.is_file() and (p.suffix=='.py' or p.name in contracts):
            copy(p, 'archive/exp27/author33/feature34/' + folder + '/' + p.name)
for name in ['eye_cache42.py','document_eye_cache42.py','finalize_eye_cache42.py','candidate.py','geometry_edges.py','coverage35.py']:
    copy(F/name, 'archive/exp27/author33/feature34/' + name)
copy(F.parent/'feature_curves.py', 'archive/exp27/author33/feature_curves.py')

evidence = [
 (E30/'flat-albedo-control', ['pattern-distinct-1x.png','flat-distinct-1x.png','flat-unlit-1x.png']),
 (E30/'palette-v4-feature', ['preserve-v3-1x.png','preserve-64-protected-1x.png']),
 (F/'eye-cache42', ['neutral-saved-final-1x.png','SYNTHETIC_COUNTEREXAMPLES.png']),
 (F/'eye-cache42/joint-placement43', ['neutral-template-colour-1x.png']),
 (F/'flat-shade-boundary44', ['before-RGB-1x.png','corrected-RGB-1x.png','curve-reference-overlay.png']),
 (F/'flat-shade-boundary44/selection935', ['coverage-replay.png'])]
for folder, names in evidence:
    for name in names:
        copy(folder/name, 'evidence/' + folder.name + '/' + name)

results = load(E30/'flat-albedo-control/RESULTS.json')
expected = {}
for name, row in results['outputs'].items():
    expected[name] = {'pixelsSHA256': hashlib.sha256(bytes(row['pixels'])).hexdigest(),
        'hairRGBUnique': len({tuple(c['rgb']) for c in row['rows'] if c}),
        'references': [c['sourceReferenceId'] if c else None for c in row['rows']]}
fixture('flat-expected.json', expected, [E30/'flat-albedo-control/RESULTS.json'], 'All eight saved branch pixel SHA256 and source-reference IDs; no full generated result JSON')

def defs(path, name, initial=None):
    m = types.ModuleType(name); sys.modules[name] = m
    m.__dict__.update({'np':np,'Path':Path,'json':json,'math':math,'hashlib':hashlib,
       'collections':collections,'dataclass':dataclasses.dataclass,'struct':struct, '__file__':str(path)})
    m.__dict__.update(initial or {})
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    body = [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'), m.__dict__)
    return m

# Bounded eye packets, rather than full frame buffers or Unity texture assets.
import gzip
eye = defs(F/'eye_cache42.py','freeze_eye',{'gzip':gzip})
joint = defs(F/'eye-cache42/joint-placement43/joint43.py','freeze_joint',{'classify':eye.classify})
register = load(F/'eye-cache42/joint-placement43/REGISTRATIONS.json')
packets = []
deps = [F/'eye_cache42.py',F/'eye-cache42/joint-placement43/joint43.py']
for reg in register:
    frame = E27/'final-validation'/reg['pose']; params=load(frame/'params.json')
    b = eye.buffers(frame/'buffers.gz'); rows, projected = joint.source_packets(b,params)
    assert sha(frame/'buffers.gz')==reg['sourceBuffersSHA256']
    assert sha(frame/'params.json')==reg['sourceParamsSHA256']
    packets.append({'pose':reg['pose'],'roi':params['roi'], 'projected':projected,
       'eyes':{str(e):[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in row.items()}for row in values]for e,values in rows.items()}})
    deps += [frame/'params.json',frame/'buffers.gz']
    omit(frame/'buffers.gz','rebuild original saved eye source packets from full frame')
fixture('eye-source-packets.json', packets, deps, 'Original source_packets() result for S1/S2/S3 at five stored poses; no full source RGBA buffers, template texture, or animation copied')

# Exact visible triangles affecting ONE cell, sufficient for selection935's CPU quadrature.
geometry = defs(F/'geometry_edges.py','freeze_geometry',{'R':F,'O':F/'geometry-export','c':types.SimpleNamespace(R=F)})
G = geometry.Geometry()
indices = np.flatnonzero(G.valid & np.all(G.p.max(axis=1)>=[7,29],axis=1) & np.all(G.p.min(axis=1)<=[8,30],axis=1))
pool_path = F/'coverage-v3/PACKET_POOL.json'; pool=load(pool_path)
subset = [r for r in pool if r['chart'] in set(G.chart[indices].tolist()) and np.max(np.abs(np.array(r['point'])-[7.5,29.5]))<=.751]
single = {'p':G.p[indices].tolist(),'inv':G.inv[indices].tolist(),'z':G.z[indices].tolist(),'chart':G.chart[indices].tolist(),
   'valid':G.valid[indices].tolist(),'originalTriangleIndices':indices.tolist(),'pool':subset,
   'thresholds':load(E30/'flat-albedo-control/INPUT.json')['thresholds']}
geo_deps = [F/'geometry-export/EVALUATED.npz',F/'SOURCE_TOPOLOGY.npz',F/'source-export/CAPTURE.json',pool_path]
fixture('selection935.json', single, geo_deps, 'Retain only projected triangle integration arrays intersecting fixed cell [7,8]x[29,30] and candidates within original .751 selection radius; source positions/depth/chart unmodified')
for p in geo_deps: omit(p,'full mesh/frame geometry reconstruction or all-cell representative selection')

visibility_path=F/'flat-shade-boundary44/EDGE_VISIBILITY.json'; curves_path=F/'flat-shade-boundary44/CURVES.json'
edge_keys=['a','b','indices','Q','g','protectedActualVisibility','selectedPoints']
curve_keys=['id','pair','edgeIndices','closed','sourceInterpolatedEdges','actualVisibilityEdges','raw','guide','cubics','fitMetric','raster','accepted','reason']
fixture('boundary44.json', {'visibility':[{k:r[k]for k in edge_keys}for r in load(visibility_path)],
 'paths':[{k:r[k]for k in curve_keys if k in r}for r in load(curves_path)]}, [visibility_path,curves_path],
 '102 frozen edge witnesses and nine guide/control-point/raster contracts; dense fitted polylines and full mesh visibility output omitted')
for name in ['prelight-source.json','frame-source-data.json']:
    omit(F/'source-export/bundle'/name,'re-extract or rebind original material/UV/native colour provenance')
for name in ['source480-6.bin','source960-6.bin','light480-3.bin','light960-3.bin']:
    omit(F/'source-export'/name,'redo raw GPU buffer/hash validation; no new Unity capture')
omit(Path.home()/'Desktop/작업폴더/AvatarSample_A.vrm','original model export, native texture palette refitting; not redistributed')
for p in (E30/'model-source').glob('image-*.png'):
    omit(p,'native texture medoid/palette fitting and texel source verification; omitted original texture')
for name in ['GEOMETRY_PACKETS.json','PALETTE_V2_BINDING.json']:
    omit(F/'ribbon-path'/name,'rebuild original flat-albedo and palette binding inputs')
for reg in register:
    omit(E27/'final-validation'/reg['pose']/'params.json','re-extract eye packets from original buffers')
for d in [E30/'palette-v3',E30/'palette-v4-feature',E30/'flat-albedo-control']:
    for p in d.iterdir():
        if p.is_file() and p.stat().st_size>500000: omit(p,'full historical diagnostics/HTML or refitting; portable replay uses bounded fixtures')
aliases={
 'EXP27':'%USERPROFILE%/Documents/Codex/2026-10-27/task-2/render-fix21',
 'EXP30':'%USERPROFILE%/Documents/Codex/2026-10-30/task',
 'PRODUCT':'%USERPROFILE%/Documents/work/Fantasy Survival Escape Game',
 'MODEL':'%USERPROFILE%/Desktop/작업폴더'}
OUT.joinpath('SOURCE_MANIFEST.json').write_text(json.dumps({'kind':'offline research snapshot; not product integration', 'sourceAliases':aliases,'files':origins},indent=2,ensure_ascii=False),encoding='utf-8')
OUT.joinpath('EXTERNAL_INPUTS.json').write_text(json.dumps({'fullRawAssetReproduction':False,'sourceAliases':aliases,'excluded':list(external.values())},indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'files':len(origins),'bytes':sum(p.stat().st_size for p in OUT.rglob('*')if p.is_file()),'eyeFixtureBytes':(OUT/'fixtures/eye-source-packets.json').stat().st_size,'cellTriangles':len(indices),'cellCandidatePackets':len(subset)},ensure_ascii=False))
