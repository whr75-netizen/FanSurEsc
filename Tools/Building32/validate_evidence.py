"""Bounded evidence check: layout feasibility and isolated GPU alpha coverage only."""
import hashlib
import json
import re
import sys
from pathlib import Path

folder = Path('docs/artifacts/building32')
payload = json.load(sys.stdin)
probe_path = Path(payload['report'])
probe = probe_path.read_text(encoding='utf-8-sig')
layout = json.loads((folder / 'layout-report.json').read_text(encoding='utf-8'))
rows = {}
for name, expected, actual, missing, extra in re.findall(r'(diamond|full-rect): expected=(\d+), actual=(\d+), missing=(\d+), extra=(\d+)', probe):
    rows[name] = dict(zip(('expected','actual','missing','extra'), map(int,(expected,actual,missing,extra))))
errors = []
if layout['violations'] or layout['reachable_access_count'] != layout['use_area_count']:
    errors.append('layout_constraints_failed')
if set(rows) != {'diamond','full-rect'}:
    errors.append('missing_GPU_case')
else:
    if rows['diamond']['missing'] <= 0:
        errors.append('baseline_did_not_reproduce_alpha_loss')
    if rows['full-rect']['expected'] <= 0 or rows['full-rect']['missing'] or rows['full-rect']['extra']:
        errors.append('full_rect_does_not_preserve_exact_alpha')
if 'sceneDirtyBefore=False, sceneDirtyAfter=False' not in probe:
    errors.append('scene_preservation_not_observed')
result = {'scope':'unapplied plan and isolated single-floor alpha experiment',
          'layoutReachable':layout['reachable_access_count'], 'coverage':rows,
          'errors':errors, 'supported':not errors,
          'artApproved':False, 'buildingRenderingFixed':False, 'unityLayoutApplied':False,
          'probeSha256':hashlib.sha256(probe_path.read_bytes()).hexdigest(),
          'layoutPlanSha256':layout['plan_sha256'],
          'remaining':['tile joining/depth order','integer zoom and common lattice integration','new individual art','lighting design and actual play comparison']}
(folder/'experiment-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
sys.exit(1 if errors else 0)
