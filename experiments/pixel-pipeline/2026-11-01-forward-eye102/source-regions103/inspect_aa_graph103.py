from pathlib import Path
import sys,json,numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'uv-features64'));from uv_features64 import edge_components
rows=[]
for part in [3,6]:
 p=H/f'part{part}';z=np.load(p/'aa-transition.npz');groups,_=edge_components(z['x'],z['y']);top=sorted(groups,key=lambda g:-g['edges'])[:8];source=np.array(Image.open(p/'source.png').convert('RGBA'));source[z['x']|z['y']]=[25,255,80,255];Image.fromarray(source).save(p/'aa-edges-on-source.png');rows.append({'part':part,'edgeComponents':len(groups),'openComponents':sum(g['endpoints']>0 for g in groups),'closedNonBranching':sum(g['closedNonBranching']for g in groups),'top':top,'conclusion':'detected source edge samples do not yet form a shared closed region boundary; no gap filling inferred'})
(H/'AA_GRAPH103.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows,ensure_ascii=False))
