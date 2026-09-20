"""Validate that this experiment produced evidence, not that it achieved 99%."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2] / 'LocalOnly' / 'DeskReference20'
required = ['reference.png', 'desk.blend', 'render.png', 'comparison.png',
            'spec.json', 'geometry_check.json', 'metrics.json', 'prompt.txt']
for filename in required:
    assert (root / filename).is_file() and (root / filename).stat().st_size > 0, filename
geometry = json.loads((root / 'geometry_check.json').read_text())
assert geometry['invariants_passed'], geometry
metrics = json.loads((root / 'metrics.json').read_text())
assert metrics['comparison_size'] == [1536, 1024]
assert metrics['denominator'] == 'foreground_union_alpha_ge_128'
for key in ['silhouette_iou', 'rgb_within_8_fraction', 'exact_rgb_fraction']:
    assert 0 <= metrics[key] <= 1
computed = metrics['silhouette_iou'] >= .99 and metrics['rgb_within_8_fraction'] >= .99
assert computed == metrics['achieved_99_operational_threshold']
print(json.dumps({'experiment_evidence_complete': True, 'achieved_99': computed,
                  'metrics': metrics}, ensure_ascii=False))
