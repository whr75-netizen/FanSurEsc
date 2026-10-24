"""Concrete geometric tradeoffs only; these are not renderer outputs or fixes."""
from pathlib import Path
import json,struct,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parent;PREV=ROOT.parent/'RegionContract572';CAP=ROOT.parent/'HairContract570/Full570'
E={'__file__':str(ROOT/'audit573.py')};exec((ROOT/'audit573.py').read_text().split('\nprior=')[0],E)
audit=json.loads((ROOT/'AUDIT573B.json').read_text());closed=[]
for row in audit['records']:
    frame=row['frame'];branches=E['env']['source_branches'](frame);packed=(PREV/f'Stored572/{frame:03}_LAYOUT.bin').read_bytes();_,_,x,y,w,h=struct.unpack_from('<6i',packed);mask=np.frombuffer(packed,'?',offset=24+4*w*h).reshape(h,w);outside=E['env']['exterior'](mask);seen=set()
    for r in row['nonOpenRecords']:
        if r['sourceType']!='cap>cap'or r['selectedNegativeArea']<=1e-12:continue
        b=branches[r['sourceBranch']];key=tuple(sorted(set(v for s in b['geometry']for v in s[6:8])))
        if key in seen:continue
        seen.add(key);hits=[c for c in r['selectedCells']if(c[0]-x,c[1]-y)in outside]
        closed.append({'frame':frame,'originalClosedBoundaryIDs':key,'postDesignArea':r['postDesignNegativeArea'],'selectedNegativeArea':r['selectedNegativeArea'],'selectedSourceCells':r['selectedCells'],'selectedCellsReachingExterior':hits,'state':'SOURCE_CLOSED_OUTPUT_OPEN'if hits else'SOURCE_CLOSED_OUTPUT_CLOSED'})
(ROOT/'CLOSED_SOURCE_VS_OUTPUT573.json').write_text(json.dumps(closed,indent=2)+'\n')

# One of the retained, non-subpixel pockets: no claim that filling every hole is valid.
frame=16;row=next(r for r in audit['records']if r['frame']==frame)
branch=next(r for r in row['nonOpenRecords']if r['sourceType']=='cap>cap'and r['postDesignNegativeArea']>1)
branches=E['env']['source_branches'](frame);b=branches[branch['sourceBranch']];pieces,_=E['original_pieces']({branch['sourceBranch']:b})
(x,y,w,h),nodes=E['atoms'](frame);packed=(PREV/f'Stored572/{frame:03}_LAYOUT.bin').read_bytes();mask=np.frombuffer(packed,'?',offset=24+4*w*h).reshape(h,w).copy();holearea=collections.defaultdict(float);negative=collections.defaultdict(float);polygons=[]
for z in nodes:
    lo,hi,l0,l1,r0,r1,*_=z;cell=z[8],z[9];polygon=[(l0,lo),(r0,lo),(r1,hi),(l1,hi)];negative[cell]+=E['polyarea'](polygon)
    for _,p in pieces.get(cell,[]):
        clipped=E['clip'](polygon,p);a=E['polyarea'](clipped)
        if a>1e-12:holearea[cell]+=a;polygons.append(clipped)
source_cells={p for p,a in holearea.items()if a>1e-12};pure={p for p in source_cells if negative[p]-holearea[p]<=1e-12 and not mask[p[1]-y,p[0]-x]}
assert pure
desired=set(pure);components=E['env']['parts'](desired)
if len(components)>1:
    # Witness illustration only: join the two diagonal pure pieces through the
    # source-hole corner with most actual coverage. This is not a runtime rule.
    assert len(components)==2
    bridges=set()
    for a in components[0]:
        for b in components[1]:
            if abs(a[0]-b[0])==abs(a[1]-b[1])==1:bridges.update([(a[0],b[1]),(b[0],a[1])])
    bridges&=source_cells;assert bridges
    desired.add(max(bridges,key=lambda p:(holearea[p],-p[0],-p[1])))
keep=mask.copy();fill=mask.copy()
for cx,cy in source_cells:keep[cy-y,cx-x]=True;fill[cy-y,cx-x]=True
for cx,cy in desired:
    keep[cy-y,cx-x]=False
    for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
        q=cx+dx,cy+dy
        if q not in desired:keep[q[1]-y,q[0]-x]=True
def holes(m):
    outer=E['env']['exterior'](m);return E['env']['parts']({(xx+x,yy+y)for yy in range(h)for xx in range(w)if not m[yy,xx]and(xx,yy)not in outer})
kh=holes(keep);fh=holes(fill);assert len(kh)==1
proof={'frame':frame,'originalClosedBranch':branch['sourceBranch'],'postDesignClosedArea':branch['postDesignNegativeArea'],'selectedNegativeArea':branch['selectedNegativeArea'],'sourceCells':sorted(source_cells),'pureSelectedHoleCells':sorted(pure),'KEEP':{'intent':'preserve one connected closed pixel pocket, grow a hair rim and redesign one source-supported bridge','desiredPixelHole':sorted(desired),'changedCells':[[int(xx+x),int(yy+y)]for yy,xx in np.argwhere(mask!=keep)],'addedHairCells':int(np.count_nonzero(keep&~mask)),'removedHairCells':int(np.count_nonzero(mask&~keep)),'closedPixelComponents':kh},'FILL':{'intent':'omit the closed pocket, integrate with the hair mass','changedCells':[[int(xx+x),int(yy+y)]for yy,xx in np.argwhere(mask!=fill)],'closedPixelComponents':fh},'kind':'explicit geometric layout illustrations, not evaluated by a new selector, not product patches, no new RGB/UV/depth render'}
(ROOT/'OPTIONS573.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

font=lambda n:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
im=Image.new('RGB',(1380,1050),'#eef3f7');draw=ImageDraw.Draw(im)
draw.text((22,14),'573 닫힌 틈과 머리 둘레의 충돌 — 두 형상 방향 / 새 렌더 아님',font=font(26),fill='#152a3a')
draw.text((22,56),f'Walk16 원형: cap 정리 뒤에도 닫힌 틈 {branch["postDesignNegativeArea"]:.6f}셀². 현재 픽셀 선택에서는 외부와 연결됩니다.',font=font(18),fill='#3c5262')
context=Image.open(CAP/'016_OFF.png').convert('RGB');cd=ImageDraw.Draw(context);params=json.loads((CAP/'016_OFF_PARAMS.json').read_text())
cx0=min(c[0]for c in source_cells);cy0=min(c[1]for c in source_cells);cx1=max(c[0]for c in source_cells)+1;cy1=max(c[1]for c in source_cells)+1
cd.rectangle((2*(cx0+params['offsetX'])-350,2*(cy0-params['offsetY'])-25,2*(cx1+params['offsetX'])-350,2*(cy1-params['offsetY'])-25),outline='#ec51a6',width=2)
im.paste(context,(22,125));draw.text((22,605),'전신 위치: 기존566 실제 캡처',font=font(16),fill='#3c5262');draw.text((22,634),'572/573의 새 최종색 결과 아님',font=font(15),fill='#7a345c')
cols,rows,step=11,12,31;zx=max(x,min(cx0-3,x+w-cols));zy=max(y,min(cy0-2,y+h-rows))
for col,(m,title,note)in enumerate([(keep,'A 닫힌 틈 KEEP','머리 둘레를 넓혀 빈 영역과 외부를 분리'),(fill,'B 닫힌 틈 FILL','빈 영역을 생략해 머리 덩어리로 통합')]):
    ox=285+540*col;oy=157;draw.text((ox,105),title,font=font(23),fill='#152a3a')
    for vv in range(rows):
        for uu in range(cols):
            cx,cy=zx+uu,zy+vv
            v=bool(m[cy-y,cx-x]);old=bool(mask[cy-y,cx-x]);colour='#303c4d'if v else'#ffffff'
            if v!=old:colour='#dc2d95'if v else'#10c5d5'
            xx,yy=ox+uu*step,oy+vv*step;draw.rectangle((xx,yy,xx+step-1,yy+step-1),fill=colour,outline='#b7c1cb')
    draw.text((ox,550),note,font=font(17),fill='#3c5262');draw.text((ox,582),f'현재572 마스크에서 변경 {np.count_nonzero(m!=mask)}셀',font=font(17),fill='#3c5262')
    draw.text((ox,614),'자홍=머리 추가 / 청록=빈 영역 재설계',font=font(15),fill='#7a345c')
draw.text((22,705),'단일 소유권의 실제 반례 (같은 저장16번, 다른 셀231,35)',font=font(23),fill='#152a3a')
witness=audit['firstWitnesses'][0]
draw.text((22,750),'외부 빈 영역0.890639 + 닫힌 틈0.017730 + 분리하는 머리0.091631이 한 셀에 함께 있습니다.',font=font(19),fill='#3c5262')
draw.text((22,790),'빈 셀 하나로 만들면 머리 띠를 생략하며 두 음의 영역을 병합합니다. 이름만 붙여 단일 소유권 통과로 세지 않았습니다.',font=font(17),fill='#3c5262')
draw.text((22,850),'남은 결정: 어떤 닫힌 틈을 정상 특징으로 KEEP하고, 어떤 틈을 덩어리에 통합할지의 공통 디자인 정책.',font=font(19),fill='#7a345c')
draw.text((22,889),'위는 효과를 보여주는 두 개념 배치이며, 유일한 최적해·새 알고리즘·정상 애니메이션 품질 통과가 아닙니다.',font=font(18),fill='#7a345c')
draw.text((22,945),'제품 미연결 / 소스·선택기·사용자설정 보존 / 실제 색·가림·FaceSkin·Walk 검증 미실행',font=font(18),fill='#152a3a')
im.save(ROOT/'OWNERSHIP_OPTIONS573.png');print(json.dumps({'sourceClosedUnitsOpened':len(closed),'witness':proof},ensure_ascii=False))
