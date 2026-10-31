from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from visibility55 import calculate,joint_visibility
R=Path(__file__).resolve().parent
def default(v):return v.tolist()if isinstance(v,np.ndarray)else v.item()
def run():
    fixture=json.loads((R/'cell-fixtures.json').read_text());records=[];checks=[]
    def check(n,v):
        if not v:raise AssertionError(n)
        checks.append(n)
    for case in fixture['cells']:
        r=calculate(case);records.append(r)
        check('fully open native-source LayerMode19',case['flags']['blinkWeight']==0 and case['flags']['layerMode19']and not case['flags']['useHairRegion502'])
        check('old any-front veto reproduced',r['oldAnyFront']and r['oldFrontSampleCounts']==case['old53Counts'])
        a=r['nativeAlpha'];depth=r['nativeDepth'];v=r['visibleAlpha']
        check('joint visibility bounded by original source alpha',np.all(v>=0)and np.all(v<=a))
        check('native visible with source skin separately bounded',r['perSampleAfterSourceSkinVisibleArea']<=r['sourceNativeAfterSkinArea'])
        check('positive area refutes blanket zero for this input',r['blanketZeroRefuted']and r['blanketZeroRefutedEvenWithOriginalSourceSkin'])
        check('same frozen diagnostic reproduced',abs(r['perSampleExternalVisibleArea']-case['firstDiagnosticArea'])<1e-12)
        none,_,_=joint_visibility(a,depth,{})
        check('no foreground preserves actual source alpha',np.array_equal(none,a))
        full=np.zeros((4,4,4),np.float32);full[...,0]=1;full[...,1]=12;full[...,3]=1
        blocked,_,_=joint_visibility(a,depth,{'synthetic-full-front':full})
        check('fully opaque nearer foreground really produces zero',not np.any(blocked))
    summary=dict(frames=[r['frame']for r in records],oldBlanketZero=[0.,0.],
        nativeFootprintVisible=[r['perSampleExternalVisibleArea']for r in records],
        withOriginalSourceSkin=[r['perSampleAfterSourceSkinVisibleArea']for r in records],
        refuted=[r['blanketZeroRefuted']for r in records],tests=len(checks),
        finalCellOwnerSolved=False,GPUReplay=False,productModified=False,newCapture=False,
        assumption='Recorded native S3 alpha/depth footprint retargeted upward1 logical cell without resampling; foreground sampled from recorded destination. This is a2D source-piece counterfactual, not a new3D pose.',
        decision='any(front) is not evidence of full invisibility here. Positive fractional area does not select an opaque pixel, approveA or solve whole-eye art.')
    (R/'RESULTS.json').write_text(json.dumps(dict(summary=summary,cells=records,checks=checks),ensure_ascii=False,indent=2,default=default),encoding='utf8')
    image=Image.new('RGB',(840,240),(25,29,36));draw=ImageDraw.Draw(image)
    for row,r in enumerate(records):
        draw.text((10,row*120+2),f'frame{r["frame"]}: SOURCE ALPHA / TRANSMITTANCE / VISIBLE / WITH SOURCE SKIN',fill='white')
        for col,key in enumerate(['nativeAlpha','destinationTransmittance','visibleAlpha','visibleAlphaWithOriginalSourceSkin']):
            im=Image.fromarray(np.rint(np.array(r[key])*255).astype(np.uint8),'L').convert('RGB').resize((80,80),Image.Resampling.NEAREST)
            image.paste(im,(10+col*205,row*120+25))
    image.save(R/'alpha-comparison.png')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
