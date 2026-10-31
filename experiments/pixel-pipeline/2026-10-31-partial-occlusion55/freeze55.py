"""Extract exactly the already captured source/destination cells. No Unity."""
from pathlib import Path
import hashlib,json
import numpy as np
from replay55 import run
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';E=R.parent/'joint-eye53'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
metas=load(B/'fixtures/frames.json');z=np.load(B/'fixtures/replay-inputs.npz')
glyph=load(E/'INPUT_GLYPHS53.json')['glyphs']['upper-lid'][0]
enum=load(E/'JOINT_ENUMERATION53.json');old=next(t for t in enum['trials']if t['shifts']=={'iris':[0,0],'sclera':[0,0],'upper-lid':[0,-1]})
cells=[]
for frame,expected in[(100,0.013491877078195103),(101,0.10666229018534068)]:
    m=metas[frame-96];d={k.split('_',1)[1]:z[k]for k in z.files if k.startswith(f'f{frame-96:02}_')and not k.endswith('_GPU')}
    xy=np.array(glyph['xy']);target=xy+[0,-1]
    def take(key,p):
        x,y=p-[m['x'],m['y']];return d[key][y*4:(y+1)*4,x*4:(x+1)*4].tolist()
    # Counts are from the prior53 fixture/branch, not chosen to match a new rule.
    veto=next(r['veto']for r in old['externalBlocks']if r['frame']==frame)
    counts={key:next((int(v.split(': ')[-1].split('/')[0])for v in veto if key in v),0)for key in['S4META','S5META','S6META']}
    cells.append(dict(frame=frame,sourceId=m['sourceId'],eye=1,sourceXY=xy.tolist(),targetXY=target.tolist(),
        flags={k:m[k]for k in['blinkWeight','layerMode19','useHairRegion502','useLashRegion583']},
        S3META=take('S3META',xy),S3POINT=take('S3POINT',xy),S0META=take('S0META',xy),S0POINT=take('S0POINT',xy),
        destinationExternal={key:take(key,target)for key in['S4META','S5META','S6META']},
        representativeDepth53=load(E/'INPUT_GLYPHS53.json')['sourceDepths'][str(frame)][glyph['id']],
        old53Counts=counts,firstDiagnosticArea=expected))
(R/'cell-fixtures.json').write_text(json.dumps(dict(cells=cells,rawSourceSHA256=sha(B/'fixtures/replay-inputs.npz'),
    frameMetadataSHA256=sha(B/'fixtures/frames.json'),prior53SHA256=sha(E/'JOINT_ENUMERATION53.json'),
    sourceScope='two captured4x4 source/target cells; no colour/backing/new frame'),indent=2),encoding='utf8')
run()
