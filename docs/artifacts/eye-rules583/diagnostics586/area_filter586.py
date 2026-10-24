"""Offline quadrature using the existing ray oracle and the actual GPU sampler.

The original 4x4 footprint is held fixed as quadrature density increases.
This is diagnostic code, not a production area engine. Triangle gradients are
computed from recorded projection and remain an explicitly approximate input.
"""
from pathlib import Path
import json, sys, time
import numpy as np

R = Path(__file__).parent
sys.path.insert(0, str(R.with_name('EyeArea585')))
from geometry_oracle585 import Frame, TEXTURES

CASES = [(2, 'OneCase2'), (5, 'OneCase5B'), (16, 'OneCase16')]


def prepare(token, n, offset=.5):
    root = R / token
    if root.exists():
        raise RuntimeError('Existing job must be inspected, never restarted')
    root.mkdir()
    groups, poses = {}, []
    start = time.perf_counter()
    for case, run in CASES:
        for frame in range(3):
            f = Frame(frame, R.with_name('EyeFollow584') / 'Runtime584' / run,
                      R.with_name('EyeArea585') / f'Runtime585/Geometry{case}')
            cells = f.possible_cells()
            pts = np.array([(x + (i + offset)/n, y + (j + offset)/n)
                            for x, y in cells for j in range(n) for i in range(n)])
            entries = []
            for x, y in cells:
                point_ids = np.flatnonzero((np.floor(pts[:, 0]) == x) &
                                           (np.floor(pts[:, 1]) == y))
                p = np.c_[pts[point_ids], np.ones(len(point_ids))]
                ix = np.flatnonzero(f.rendered &
                    (f.box[:, 0, 0] <= x+1) & (f.box[:, 1, 0] >= x) &
                    (f.box[:, 0, 1] <= y+1) & (f.box[:, 1, 1] >= y))
                bary = np.einsum('nd,mid->nmi', p, f.B[ix])
                inside=(bary >= -1e-7).all(axis=2)
                if n>4:
                    # A point contributes only if some front-facing same-eye
                    # reference triangle classifies it as upper lash. This
                    # ignores opacity, so it is a superset, never a visibility
                    # or alpha-derived pruning rule.
                    u=p @ f.uc[ix].T;v=p @ f.vc[ix].T
                    a,b=f.cfg['UpperLower348'][:2]
                    g=v-a-b*u*u;own=np.rint(p @ f.owner[ix].T)
                    can_ref=np.isin(f.s[ix],[0,1,2,3])&f.front[ix]
                    possible=np.any(inside&can_ref[None,:]&(own==2)&
                        (np.abs(u)<=1.08)&(g>=-.36)&(g<=.22),axis=1)
                    inside &= possible[:,None]
                row, col = np.nonzero(inside)
                tri = ix[col]
                uv = np.einsum('nd,ndk->nk', p[row], f.uv[tri])
                dep = np.sum(p[row] * f.depth[tri], axis=1)
                for k, t in enumerate(tri):
                    name = TEXTURES[f.mi[t]]['name']
                    a = groups.setdefault(name, [])
                    idx = len(a)
                    a.append([*uv[k], *(f.uv[t, 0]/4),
                              *(-f.uv[t, 1]/4), f.alpha[t], f.mode[t]])
                    entries.append((int(point_ids[row[k]]), int(t),
                                    float(dep[k]), int(f.mi[t]), idx))
            file = root / f'POSE_{case}_{frame}.npz'
            np.savez(file, points=pts, entries=np.array(entries))
            poses.append(dict(case=case, run=run, frame=frame,
                              cells=len(cells), points=len(pts), entries=len(entries),
                              file=str(file)))
            print(json.dumps(dict(prepared=[case, frame], points=len(pts),
                                  candidates=len(entries))), flush=True)
    manifest = []
    for name, rows in groups.items():
        p = root / f'INPUT{name}.bin'
        a = np.asarray(rows, '<f4')
        p.write_bytes(np.array([len(a)], '<i4').tobytes()+a.tobytes())
        manifest.append(dict(name=name, count=len(a), input=str(p),
                             output=str(root/f'OUTPUT{name}.bin')))
    (root/'GROUPS.tsv').write_text('name\tcount\tinput\toutput\n' + '\n'.join(
        '\t'.join(str(g[k]) for k in ['name','count','input','output'])
        for g in manifest)+'\n')
    (root/'JOB.json').write_text(json.dumps(dict(token=token, n=n, offset=offset,
        poses=poses, groups=manifest, prepareSeconds=time.perf_counter()-start,
        footprint='Original4x4 triangle UV derivatives held fixed; not measured hardware ddx.'), indent=2))
    (R/'CURRENT_AREA_JOB586.txt').write_text(token)


def consume(token):
    root = R/token
    job = json.loads((root/'JOB.json').read_text())
    if not (root/'COMPLETE.json').exists():
        raise RuntimeError('GPU probe completion required')
    arrays = {g['name']:np.frombuffer(Path(g['output']).read_bytes(), '<f4',
              offset=4).reshape(-1,4) for g in job['groups']}
    results = []
    for pose in job['poses']:
        f = Frame(pose['frame'], R.with_name('EyeFollow584')/'Runtime584'/pose['run'],
                  R.with_name('EyeArea585')/f"Runtime585/Geometry{pose['case']}")
        data = np.load(pose['file'])
        pts, entries = data['points'], data['entries']
        rows, tri = entries[:,0].astype(int), entries[:,1].astype(int)
        depths, mi, offsets = entries[:,2], entries[:,3].astype(int), entries[:,4].astype(int)
        alpha = np.empty((len(entries),3))
        for m in np.unique(mi):
            mask=mi==m
            alpha[mask] = arrays[TEXTURES[m]['name']][offsets[mask],:3]
        # Match the original MToon BLEND clip and source output discard. MASK
        # cutoff is already applied by the diagnostic sampler (all cutoffs .5).
        alpha[(f.mode[tri]==2)&(alpha[:,0]<6.103515625e-5),0]=0
        for ch in [1,2]:
            alpha[(f.mode[tri]==2)&(alpha[:,ch]<6.103515625e-5),ch]=0
        variants={}
        for ch,label in enumerate(['gpuGrad','gpuLevel0','gpuManualBilinear']):
            layers={}
            for s in [0,1,2,3,5,6]:
                ids=np.flatnonzero((f.s[tri]==s)&(alpha[:,ch]>1e-6))
                # Stable ascending triangle order and <= reproduce the oracle's
                # last-triangle tie convention. No overlap is double counted.
                ids=ids[np.argsort(tri[ids],kind='stable')]
                chosen=np.full(len(pts),-1,int);best=np.full(len(pts),np.inf)
                aa=np.zeros(len(pts))
                for k in ids:
                    row=rows[k]
                    if depths[k]<=best[row]:
                        best[row]=depths[k];chosen[row]=tri[k];aa[row]=alpha[k,ch]
                layers[s]=(chosen,best,aa)
            f.point_layer=lambda points,s:layers[s]
            weights=f.weights(pts)
            a=float(weights.sum()/(job['n']**2))
            variants[label]=dict(area=a,budget=int(np.floor(a+.5)),
                                 positivePoints=int(np.count_nonzero(weights)))
            if job['n']==4 and job['offset']==.5:
                # Independent nominal bilinear oracle already validated all
                # 20,016 old-grid upper-lash weights. Compare pointwise too.
                del f.point_layer
                expected=f.weights(pts)
                variants[label]['oldGridWeightMismatches']=int(np.count_nonzero(
                    np.abs(weights-expected)>2e-4))
                variants[label]['maxOldGridWeightError']=float(np.max(
                    np.abs(weights-expected)))
            else:
                del f.point_layer
        results.append(dict(case=pose['case'],frame=pose['frame'],variants=variants))
        print(json.dumps(results[-1]),flush=True)
    result=dict(token=token,n=job['n'],offset=job['offset'],records=results,
        inputScope='All ray-hit candidates, including fragments absent from old raster; original fixed footprint. Geometry derivatives approximate, hardware filtered alpha evaluated on original GPU/texture state.',
        gpu=json.loads((root/'COMPLETE.json').read_text()))
    (root/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2],int(sys.argv[3]),float(sys.argv[4]) if len(sys.argv)>4 else .5)
    elif sys.argv[1]=='consume':consume(sys.argv[2])
