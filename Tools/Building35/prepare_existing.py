"""Compile measured source annotations into explicit plane inputs; not image generation."""
import json
from pathlib import Path
from project_faces import project

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/artifacts/building35'
items=[json.loads((OUT/'rear-shelf-landmarks-proposal.json').read_text(encoding='utf-8-sig'))]
items+=json.loads((OUT/'additional-fixture-landmarks-proposal.json').read_text(encoding='utf-8-sig'))['assets'][:2]
for a in items:
    v=a['shared_vertices']
    spec={'id':a['asset_id'],'source':a['source']['native_path'],'ppu':127,'preserve_outline':True,'ground_from_source_outline':True,
          'faces':[{'id':f['id'],'source_xy':[[n-.5 for n in v[k]['source']] for k in f['vertices']],
                    'xyz':[v[k]['target_xyz'] for k in f['vertices']]} for f in a['faces']],
          'limitations':a.get('limits',a.get('source_regions_not_on_three_planes',[]))}
    if a['asset_id']=='rear_shelf':
        spec['faces'][1]['holdout']=[{'id':l['id'],'points':l['source_endpoints'],'target_slope':-.5} for l in a['source_holdout_segments']]
    project(spec,OUT/'projected-grounded'/a['asset_id'])
