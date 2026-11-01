"""Compare exact same source. Diagnostic labels are NOT output palette colours."""
from pathlib import Path
import json,sys
from collections import deque
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from graph_regions104 import boundary
from run_graph104 import debug
H=Path(__file__).resolve().parent;S=H.parent/'source-regions103'
sys.path.insert(0,str(H.parent/'uv-features64'));from uv_features64 import lab

def cc_check(labels,mask):
    h,w=mask.shape;done=np.zeros(mask.shape,bool);components={}
    for y,x in np.argwhere(mask):
        if done[y,x]or labels[y,x]<0:continue
        label=int(labels[y,x]);components[label]=components.get(label,0)+1
        stack=[(int(y),int(x))];done[y,x]=True
        while stack:
            yy,xx=stack.pop()
            for a,b in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
                if 0<=a<h and 0<=b<w and mask[a,b]and not done[a,b]and labels[a,b]==label:
                    done[a,b]=True;stack.append((a,b))
    return {'labels':len(components),'disconnectedRegionIds':[k for k,n in components.items()if n!=1]}

def exact_source_mode(rgb,labels,mask):
    # Modal SOURCE texel is used only as a counterfactual diagnostic of the
    # invalid 'one region -> one flat anchor' assumption. Never sent to GPU.
    out=np.zeros_like(rgb);colours=[]
    for k in np.unique(labels[mask]):
        if k<0:continue
        select=mask&(labels==k);values,counts=np.unique(rgb[select],axis=0,return_counts=True)
        colour=values[np.argmax(counts)];out[select]=colour;colours.append(colour.tolist())
    return out,colours

def main():
    rows=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22)
    board=Image.new('RGB',(2160,1430),'#20252c');draw=ImageDraw.Draw(board)
    draw.text((20,12),'104 · 원본 UV 분할 비교 — 게임 최종 렌더가 아닙니다',font=font,fill='white')
    titles=['원본 재질·UV 색','103 affine 경계 / 실패','104 graph FH / 과분절','104 h-minima + geodesic']
    for i,title in enumerate(titles):draw.text((20+i*540,60),title,font=font,fill='white')
    for part in (3,6):
        d=np.load(S/f'part{part}/hierarchy.npz');mask=d['mask'];rgb=d['rgba'][...,:3]
        old=d['coarse'];fh=np.load(H/f'part{part}/graph-labels.npz')['labels']
        geo=np.load(H/f'part{part}/geodesic-labels.npz')['labels'];base,_=exact_source_mode(rgb,geo,mask)
        baseRGBA=np.zeros_like(d['rgba']);baseRGBA[mask,:3]=base[mask];baseRGBA[...,3]=d['rgba'][...,3]
        Image.fromarray(baseRGBA).save(H/f'part{part}/ONE_ANCHOR_COUNTEREXAMPLE_NOT_ADOPTED.png')
        checks={name:cc_check(labels,mask)for name,labels in [('103',old),('FH',fh),('geodesic',geo)]}
        row={'part':part,'connectivity':checks,'oneAnchorPaletteAdopted':False,'weakRidgesNotSemanticTruth':True}
        # Independent, visible cheek-stroke counterexample selected from a
        # source ROI after visual inspection, NOT a seed/constraint of either
        # tested segmentation. Locate the strongest opposed three-texel ridge.
        if part==3:
            roi=np.zeros_like(mask);roi[620:710,310:425]=True
            colour=lab(rgb);best=None
            for y,x in np.argwhere(mask&roi):
                for dy,dx in ((0,2),(2,0)):
                    a=(int(y-dy),int(x-dx));b=(int(y+dy),int(x+dx))
                    if not mask[a]or not mask[b]:continue
                    # This is an exact native RGB8 diagnostic, not the old
                    # +/-half-code latent-image confidence gate. The native
                    # authored codes must not be declared meaningless noise.
                    residual=float(np.linalg.norm(rgb[y,x].astype(float)-(rgb[a].astype(float)+rgb[b].astype(float))*.5))
                    if best is None or residual>best[0]:best=(residual,int(y),int(x),a,b)
            if best:
                residual,y,x,a,b=best;points=[(y,x),a,b]
                row['thinCheekStrokeProbe']={'sourceROIOnlyDiagnostic':[310,620,115,90],
                    'sourceRGB8ResidualNorm':residual,'old64ThinRidge':bool(d['thinX'][y,x]or d['thinY'][y,x]),'samples':[{'cropXY':[xx,yy],'RGB8':rgb[yy,xx].tolist(),
                    'coarse103':int(old[yy,xx]),'FH':int(fh[yy,xx]),'geodesic':int(geo[yy,xx]),
                    'hypotheticalFlatAnchorRGB8':base[yy,xx].tolist()}for yy,xx in points],
                    'sameGeodesicRegion':len({int(geo[yy,xx])for yy,xx in points})==1,
                    'finding':'A flat anchor for this parent would erase an observed thin source stroke. Keep child/source evidence; do not adopt flat P.'}
            l=lab(rgb);k=int(geo[760,461]);where=np.argwhere(mask&(geo==k));values=l[mask&(geo==k),0]
            row['skinRegionExtrema']=[{'cropXY':[int(where[j,1]),int(where[j,0])],
              'RGB8':rgb[tuple(where[j])].tolist(),'L':float(values[j])}for j in (int(np.argmin(values)),int(np.argmax(values)))]
            images=[Image.fromarray(d['rgba']),Image.fromarray(debug(old,mask)),Image.fromarray(debug(fh,mask)),Image.fromarray(debug(geo,mask))]
            for i,im in enumerate(images):
                # The source UV overview is explicitly reduced for this board;
                # native source PNGs and native diagnostic labels are retained.
                im=im.resize((508,505),Image.Resampling.NEAREST);board.paste(im,(20+i*540,110),im)
            crops=[(250,440,760,590),(280,610,440,720),(420,735,610,795)]
            for j,box in enumerate(crops):
                yy=660+j*220
                draw.text((20,yy-30),'native UV crop '+str(box)+' · nearest 확대',font=font,fill='#f4c880')
                for i,labels in enumerate([None,old,fh,geo]):
                    im=Image.fromarray(d['rgba']if labels is None else debug(labels,mask)).crop(box)
                    scale=min(3,510//im.width,170//im.height);im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
                    board.paste(im,(20+i*540,yy),im)
        rows.append(row)
    draw.text((20,1360),'미채택: 단순 영역 수 감소는 합격이 아닙니다. 얇은 무늬/AA/연속 음영의 하위 계층은 미해결입니다.',font=font,fill='#f4c880')
    board.save(H/'SOURCE_REGION_COMPARE104.png')
    (H/'REVIEW104.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
