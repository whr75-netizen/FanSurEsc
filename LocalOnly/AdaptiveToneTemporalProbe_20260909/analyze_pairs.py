"""Check paired actual camera captures; report measured output, not art quality."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent

def image(folder, name, dtype):
    return np.fromfile(folder / (name + '.bin'), dtype=dtype).reshape(768, 384, 4)

def group_rows(folder):
    groups = np.fromfile(folder/'groups.bin', dtype='<u4').reshape(160, 8)
    solutions = np.fromfile(folder/'solutions.bin', dtype='<f4').reshape(160, 3, 4)
    statuses = np.fromfile(folder/'status.bin', dtype='<u4')
    return [dict(key=int(g[0]), part=int(g[0] >> 16)-1, count=int(g[1]),
                 K=int(solutions[i, 0, 0]), rmse=float(solutions[i, 0, 1]),
                 status=int(statuses[i]))
            for i, g in enumerate(groups) if g[0]]

def main():
    report = ROOT/'paired_results.json'
    if report.exists():
        raise FileExistsError(report)
    pairs=[]
    for before in sorted(ROOT.glob('pair_*/*/before')):
        after = before.parent/'after'
        old=image(before,'output','<f2'); new=image(after,'output','<f2')
        meta=image(before,'cellMeta','u1'); skin=(meta[...,1]==4)&(old[...,3]>0)
        changed=np.any(old[...,:3]!=new[...,:3],axis=-1)
        old_groups=group_rows(before); new_groups=group_rows(after)
        sample=json.loads((before/'sample.json').read_text(encoding='utf-8-sig'))
        before_capture=json.loads((before/'capture.json').read_text(encoding='utf-8-sig'))
        after_capture=json.loads((after/'capture.json').read_text(encoding='utf-8-sig'))
        checks=dict(
            same_frame=before_capture['frame']==after_capture['frame'],
            same_camera=before_capture['cameraId']==after_capture['cameraId'],
            identical_input=all((before/(name+'.bin')).read_bytes()==(after/(name+'.bin')).read_bytes()
                for name in ('nativeColor','nativeMeta','nativeLighting','cellColor','cellMeta')),
            same_depth=np.array_equal(old[...,3],new[...,3]),
            other_parts_exact=not np.any(changed&~skin),
            gpu_global_zero=all(np.fromfile(p/'status.bin',dtype='<u4')[-1]==0 for p in (before,after)),
            groups_ready=all(g['status']&1 for g in old_groups+new_groups))
        def largest_skin(groups):
            return max((g for g in groups if g['part']==4),key=lambda g:g['count'])
        pairs.append(dict(path=str(before.parent.relative_to(ROOT)).replace('\\','/'),
                          mode=sample['mode'], index=sample['index'], phase=sample['phase'], scale=sample['scale'],
                          before=largest_skin(old_groups),after=largest_skin(new_groups),
                          before_skin_colors=len(np.unique(old[skin,:3],axis=0)),
                          after_skin_colors=len(np.unique(new[skin,:3],axis=0)),
                          skin_changed_seeds=int(np.count_nonzero(changed&skin)),checks=checks))
    if not pairs:
        raise ValueError('No paired captures')
    result=dict(pairs=pairs,passed=all(all(p['checks'].values()) for p in pairs),
                note='Before uses Oklab L, after uses E: RMSE units differ. Controlled poses, not continuous gameplay.')
    report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
