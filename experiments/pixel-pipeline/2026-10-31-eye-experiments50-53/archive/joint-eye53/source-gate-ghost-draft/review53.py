"""Readability/source-error audit and second feasible output; offline only."""
from pathlib import Path
import copy,json
import numpy as np
from PIL import Image,ImageDraw
from joint53 import connected_components
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def default(v):return v.tolist()if isinstance(v,np.ndarray)else v.item()
def dump(n,d):(R/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=default),encoding='utf8')
inp=load(R/'INPUT_GLYPHS53.json');result=load(R/'JOINT_ENUMERATION53.json');rows0=[r for g in inp['glyphs'].values()for r in g]
feasible=[r for r in result['trials']if r['feasible']];feasible.sort(key=lambda r:(r['movementPerPart'],r['curveError']))
assert len(feasible)==2
metas={r['frame']:r for r in load(B/'fixtures/frames.json')};z=np.load(B/'fixtures/replay-inputs.npz')
records=[];output=[]
original_box=(np.ptp([r['xy']for r in rows0],axis=0)+1).tolist()
original_iris=np.mean([r['xy']for r in rows0 if r['part']=='iris'],axis=0)
for index,trial in enumerate(feasible):
    label='B'if index==0 else'C';rows=[]
    for src in rows0:
        r=copy.deepcopy(src);r['xy']=(np.array(r['xy'])+trial['shifts'][r['part']]).tolist();rows.append(r)
    iris=np.mean([r['xy']for r in rows if r['part']=='iris'],axis=0)
    box=(np.ptp([r['xy']for r in rows],axis=0)+1).tolist()
    measure=dict(candidate=label,shifts=trial['shifts'],perPartSquaredMovement=trial['movementPerPart'],
        sourceRegionCurveErrorSquared=trial['curveError'],relativePartCentroidErrorSquared=trial['relativeCentreError'],
        originalBoundsCells=original_box,outputBoundsCells=box,heightScale=box[1]/original_box[1],
        irisShiftVsUnmodifiedOtherEye=(iris-original_iris).tolist(),
        irisComponents=len(connected_components([r['xy']for r in rows if r['part']=='iris'])),
        wholeComponents=len(connected_components([r['xy']for r in rows])),
        singleNativeLidCellCannotProveCurveFit=True,paletteChanged=False,
        opticalReadability='NOT automatically passed; source geometry, component and colour checks are insufficient for art approval')
    for frame in[100,101]:
        m=metas[frame];base=Image.open(B/f'fixtures/actual-{frame}.png').convert('RGBA');im=base.copy();draw=ImageDraw.Draw(im)
        visibility=inp['sourceVisibility'][str(frame)];emitted=[]
        for r in rows:
            if not visibility[r['id']]:continue
            x,y=(r['xy'][0]-m['x'])*2,(r['xy'][1]-m['y'])*2
            draw.rectangle((x,y,x+1,y+1),fill=tuple(r['rgba8']));emitted.append(r)
        im.save(R/f'frame{frame}-candidate{label}-1x.png')
        im.resize((im.width*12,im.height*12),Image.Resampling.NEAREST).save(R/f'frame{frame}-candidate{label}-12x.png')
        if label=='B':assert np.array_equal(np.asarray(im),np.asarray(Image.open(R/f'frame{frame}-joint-safe-1x.png')))
        # Only these direct per-token source colours are assigned. The untouched
        # scene is not claimed to be inside the eye palette.
        assert all(tuple(np.asarray(im)[(r['xy'][1]-m['y'])*2,(r['xy'][0]-m['x'])*2])==tuple(r['rgba8'])for r in emitted)
        output.append(dict(candidate=label,frame=frame,visibleTokens=len(emitted),
            rgba8=sorted({tuple(r['rgba8'])for r in emitted})))
    records.append(measure)
orig_points=np.array(inp['sourcePaths']['upper-lid']['points'])
dump('READABILITY_AND_SOURCE_ERROR53.json',dict(candidates=records,
    sourceUpperCurveSpan=np.ptp(orig_points,axis=0),sourceUpperCurveLength=float(np.linalg.norm(np.diff(orig_points,axis=0),axis=1).sum()),
    limitation='One observed native output pixel is an evidenced part token, not a complete authored lid stroke. No claim of reconstructed upper/lower-eye art curve.',
    objectiveMeaning='Movement is normalized per part; region/curve distances use source geometry; centroid error is relative part-layout change. These do not constitute a validated human aesthetic function.'))
dump('OUTPUT_PALETTE53.json',dict(outputs=output,unlitColourClaim=False,RGBMultiplyUsed=False))
# Six rows, two frames: actual / iris-first / lid-first / rejectedA / B / C.
plate=Image.new('RGBA',(64,96))
for col,frame in enumerate([100,101]):
    names=[f'frame{frame}-actual-1x.png',f'frame{frame}-iris-priority-1x.png',f'frame{frame}-lid-priority-1x.png',
        f'frame{frame}-logical-only-A-rejected-1x.png',f'frame{frame}-candidateB-1x.png',f'frame{frame}-candidateC-1x.png']
    for row,name in enumerate(names):plate.alpha_composite(Image.open(R/name).convert('RGBA'),(col*32,row*16))
plate.save(R/'review-comparison-1x.png');plate.resize((768,1152),Image.Resampling.NEAREST).save(R/'review-comparison-12x.png')
print(json.dumps(dict(feasibleCandidates=records,sourceUpperCurveSpan=np.ptp(orig_points,axis=0)),default=default,indent=2))
