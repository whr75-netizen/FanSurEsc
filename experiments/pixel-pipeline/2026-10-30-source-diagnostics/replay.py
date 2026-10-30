"""Relocatable replay of original definitions, with bounded frozen fixtures.

Only function/class AST nodes are loaded. Absolute-path assignments, original
imports, archive CLI main functions, file writes and capture calls never run.
NumPy is required; Pillow and Unity are not used by this entry point.
"""
from pathlib import Path
import ast, base64, collections, dataclasses, hashlib, json, math, os, sys, types
import numpy as np

R = Path(__file__).resolve().parent
F = R/'archive/exp27/author33/feature34'
load = lambda p: json.loads(Path(p).read_text(encoding='utf-8-sig'))
checks = []

def guard(event, args):
    if event!='open' or not isinstance(args[0],(str,bytes,os.PathLike)): return
    p=Path(os.fsdecode(args[0])).resolve()
    if not (p.is_relative_to(R) or p.is_relative_to(Path(sys.base_prefix).resolve())):
        raise PermissionError('Replay attempted external file read: '+str(p))
    mode=args[1]
    if isinstance(mode,str) and any(c in mode for c in 'wax+'):
        raise PermissionError('Replay must not write files: '+str(p))

sys.addaudithook(guard)

def check(name, value):
    assert bool(value), name
    checks.append(name)

def reject(name, fn):
    try: fn()
    except ValueError: checks.append(name)
    else: raise AssertionError(name)

def defs(path, name, initial=None):
    m = types.ModuleType(name); sys.modules[name] = m
    m.__dict__.update({'np':np,'Path':Path,'json':json,'math':math,'hashlib':hashlib,
        'collections':collections,'dataclass':dataclasses.dataclass,'__file__':str(path)})
    m.__dict__.update(initial or {})
    tree = ast.parse(path.read_text(encoding='utf-8'))
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]),str(path),'exec'),m.__dict__)
    return m

eye = defs(F/'eye_cache42.py','replay_eye')
template=load(F/'eye-cache42/TEMPLATE_FEATURE_GRAPH.json')
canonical=template['features']
check('eye42 actual source graph contains four iris cells per eye',all(len(canonical[str(e)]['iris']['cellIds'])==4 for e in [1,2]))
cache=eye.SourceFeatureCache42('bound',canonical)
v=cache.membership('bound',1,1,[True,True],[1,0],[False,True])
check('eye42 intrinsic source identity survives normalized subtype',v['featureId']=='eye1:iris' and v['intrinsicMask'].tolist()==[True,True])
check('eye42 visibility cannot erase canonical membership',v['visibleMask'].tolist()==[False,True])
reject('eye42 rejects stale source binding',lambda:cache.membership('stale',1,1,[True],[0],[True]))
reject('eye42 rejects unbound hair role',lambda:cache.membership('bound',1,11,[True],[0],[True]))
selected,budget=eye.iris_allocated([9,7,7,0],[0,0,0,0],[(0,0),(1,0),(0,1),(1,1)])
check('eye42 saved area-threshold counterexample remains reproducible',budget==1 and len(selected)==1)

joint=defs(F/'eye-cache42/joint-placement43/joint43.py','replay_joint')
provenance=load(F/'eye-cache42/joint-placement43/CELL_AND_COLOUR_PROVENANCE.json')
cells=[joint.Cell(c['cellId'],c['eye'],c['role'],tuple(c['referenceXY']),tuple(c['rgba8']))for c in provenance['cells']]
check('joint43 actual template fixture has 20 literal-colour cells',len(cells)==20 and all(sum(c.eye==e and c.role==1 for c in cells)==4 for e in [1,2]))
register=load(F/'eye-cache42/joint-placement43/REGISTRATIONS.json')
packets=load(R/'fixtures/eye-source-packets.json')
expected=load(F/'eye-cache42/joint-placement43/RESULTS.json')
by_pose={p['pose']:p for p in packets}
for reg, exp in zip(register,expected):
    p=by_pose[reg['pose']];roi=p['roi'];bounds=(roi['x']-5,roi['y']-4,roi['width']+12,roi['height']+10)
    rows={int(e):[{k:(np.array(v)if k in ['xy','weight','uv']else v)for k,v in row.items()}for row in rr]for e,rr in p['eyes'].items()}
    adapter=joint.JointPlacement(reg['fingerprint'],reg['stateToken'],cells,reg['referenceAnchor'],reg['jointAnchor'])
    shape_sets={1:set(),2:set()};pairs=set();joint_pairs=set();disconnected=0;worst=0
    for y in range(65):
        for x in range(65):
            phase=np.array([x/64,y/64]);current={e:joint.allocator(rows[e],phase,bounds)[0]for e in [1,2]}
            for e in [1,2]:shape_sets[e].add(joint.shape_key(current[e]))
            pairs.add(joint.pair_key(current))
            disconnected+=any(joint.component_count(current[e])>1 for e in [1,2])
            placed,translation,delta=adapter.place(reg['fingerprint'],reg['stateToken'],phase)
            assert all(r['xy']==(np.array(c.xy)+translation).tolist() and r['rgba8']==list(c.rgba)for c,r in zip(cells,placed))
            joint_pairs.add(joint.pair_key({e:[r['xy']for r in placed if r['eye']==e and r['role']==1]for e in [1,2]}))
            worst=max(worst,float(np.max(np.abs(translation-delta))))
    name=reg['pose']
    check(name+': old allocator shape count replays from source packets',len(pairs)==exp['oldPairShapes'] and all(len(shape_sets[e])==exp['oldPerEyeShapes'][str(e)]for e in [1,2]))
    check(name+': old disconnected states exactly replay',disconnected==exp['oldDisconnectedStates'])
    check(name+': joint shape/colour and half-cell translation bound',len(joint_pairs)==1 and worst<=.5)
    reject(name+': missing state cannot reuse open-eye entry',lambda:adapter.place(reg['fingerprint'],'unregistered'))
    reject(name+': stale model cannot reuse placement',lambda:adapter.place('stale',reg['stateToken']))

# Frozen one-cell geometry, not a copy of the user's full mesh.
s=load(R/'fixtures/selection935.json');G=types.SimpleNamespace(**{k:np.array(s[k])for k in ['p','inv','z','chart','valid']})
selection=defs(F/'flat-shade-boundary44/selection935/audit935.py','replay_select',{'THRESHOLDS':s['thresholds']})
evidence=load(F/'flat-shade-boundary44/selection935/EVIDENCE.json');old=evidence['oldCentre'];target=evidence['coverageRepresentative']
for case in evidence['integrationCases']:
    scale=case['scale'];owner,_=selection.cell_raster(G,scale)
    packet,details=selection.select(owner,scale,(.5,.5),s['pool'],old['chart'])
    check('selection935 '+str(scale)+': original CPU area and representative reproduced',packet==target and details['coverageCounts']=={int(k):v for k,v in case['details']['coverageCounts'].items()})
    reverse,_=selection.cell_raster(G,scale,reverse=True)
    check('selection935 '+str(scale)+': reverse triangle traversal unchanged',np.array_equal(owner,reverse))
for case in evidence['fixedFootprintOffsets']:
    offset=case['offset'];owner,_=selection.cell_raster(G,16,offset)
    chosen,_=selection.select(owner,16,offset,s['pool'],old['chart'])
    check('selection935 fixed quadrature '+str(offset),chosen==case['packet'])
for seed in range(8):
    pool=list(s['pool']);np.random.default_rng(seed).shuffle(pool);owner,_=selection.cell_raster(G,16)
    check('selection935 candidate order '+str(seed),selection.select(owner,16,(.5,.5),pool,old['chart'])[0]==target)

curve_core=defs(F.parent/'feature_curves.py','replay_curve_core')
c=defs(F/'candidate.py','replay_candidate',{'fit':curve_core.fit,'sample_curves':curve_core.sample_curves,'winding':curve_core.winding})
flat=load(R/'archive/exp30/flat-albedo-control/INPUT.json')
b=defs(F/'flat-shade-boundary44/curves44.py','replay_boundary',{'c':c,'DATA':flat,'FIT_BOUND':math.sqrt(.5),'SPATIAL_BOUND':math.sqrt(.5),'fit':curve_core.fit,'sample_curves':curve_core.sample_curves,'winding':curve_core.winding})
layers=np.load(F/'flat-shade-boundary44/LAYERS.npz');mask=layers['mask'];q=layers['Q'];g=layers['g'];corrected=layers['correctedQ']
fixture=load(R/'fixtures/boundary44.json');paths=b.edge_graph(q,mask,fixture['visibility'])
check('boundary44 frozen g maps to exact primary Q',np.array_equal(q[mask],np.sum(g[...,None]>=flat['thresholds'],-1)[mask]))
check('boundary44 graph partitions 102 edges into nine shared paths',len(paths)==9 and sorted(i for p in paths for i in p['edgeIndices'])==list(range(102)))
for p, exp in zip(paths,fixture['paths']):
    check('boundary44 path '+str(p['id'])+': guide/source-visibility split preserved',np.allclose(p['guide'],exp['guide'],rtol=0,atol=1e-12)and p['actualVisibilityEdges']==exp['actualVisibilityEdges'])
    fitted,cubics,metric=b.fit_path(p)
    check('boundary44 path '+str(p['id'])+': original fit replays',np.allclose(np.array(cubics),exp['cubics'],rtol=0,atol=1e-9))
    if fitted is not None:
        check('boundary44 path '+str(p['id'])+': grid traversal replays',np.array_equal(b.grid_path(fitted),exp['raster']))
diag=defs(F/'flat-shade-boundary44/diagnose44.py','replay_diag',{'c':c})
before=diag.components(q,mask);after=diag.components(corrected,mask)
result=load(F/'flat-shade-boundary44/RESULTS.json')
check('boundary44 retained component/singleton limitations',len(before)==result['beforeQRegions']==11 and len(after)==result['afterQRegions']==11 and sum(r['size']==1 for r in before)==sum(r['size']==1 for r in after)==6)
check('boundary44 corrected cell log matches frozen labels',sorted(np.flatnonzero((q!=corrected)&mask).tolist())==sorted(r['index']for r in result['changes']))
print(json.dumps({'suite':'portable eye/geometry/boundary replay','passed':len(checks),'cases':checks,'externalFileReads':0,'productChanges':0,'Python':sys.version.split()[0],'NumPy':np.__version__},indent=2))
