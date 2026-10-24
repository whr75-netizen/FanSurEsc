"""Explicit design illustrations, not final rendered RGB or product patches."""
from pathlib import Path
import json,struct,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parent;PREV=ROOT.parent/'RegionContract571';CAP=ROOT.parent/'HairContract570/Full570'
env={'__file__':str(ROOT/'review572.py')};exec((ROOT/'review572.py').read_text().split('\nrows=[]')[0],env)
review=json.loads((ROOT/'REVIEW572.json').read_text());gates=json.loads((PREV/'GATES571.json').read_text())
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
canvas=Image.new('RGB',(1320,1450),'#eef2f7');draw=ImageDraw.Draw(canvas)
draw.text((22,12),'572 영역 디자인 대조 — 기존 전신 위 변경 표시 / 확대는 형상 마스크만',font=font(24),fill='#122638')
draw.text((22,52),'새 Unity 렌더가 아닙니다. 자홍=머리 추가, 청록=머리 생략. 새 색·가림·눈 결과는 미검증입니다.',font=font(18),fill='#643250')
def layout(frame):
    b=(ROOT/f'Stored572/{frame:03}_LAYOUT.bin').read_bytes();_,_,x,y,w,h=struct.unpack_from('<6i',b);a=np.frombuffer(b,'<f4',offset=24,count=w*h).reshape(h,w);m=np.frombuffer(b,'?',offset=24+4*w*h).reshape(h,w)
    mx,my,old=env['env']['mask'](CAP/f'{frame:03}_OFF_MASK.bin');old=old[y-my:y-my+h,x-mx:x-mx+w]
    return x,y,w,h,a,m,old
def energy(m,a):
    score=float(np.where(m,1-a,a).astype('float64').sum())
    for dx,dy,factor in[(1,0,.58578644),(0,1,.58578644),(1,1,.29289322),(-1,1,.29289322)]:
        if dx<0:u,v=m[:-1,1:],m[1:,:-1]
        elif dx and dy:u,v=m[:-1,:-1],m[1:,1:]
        elif dy:u,v=m[:-1],m[1:]
        else:u,v=m[:,:-1],m[:,1:]
        score+=float(np.float32(np.float32(.14)*np.float32(factor)))*int((u!=v).sum())
    return score
records=[]
for index,gate in enumerate(gates):
    frame=gate['frame'];x,y,w,h,a,prototype,old=layout(frame);rec=next(r for r in review if r['frame']==frame);branches=env['source_branches'](frame)
    ids=gate['sourceNegativeAtCorner'][0];left=(ids['leftBoundary'][0]<<32)|ids['leftBoundary'][1];right=(ids['rightBoundary'][0]<<32)|ids['rightBoundary'][1]
    candidates=[d for d in rec['allAxisDecisionRecords']if d['axis']=='y'and left in d['positiveLeftBoundary']and right in d['positiveRightBoundary']and d['fillLo']<=gate['sharedCorner'][1]<=d['fillHi']]
    assert len(candidates)==1;decision=candidates[0]
    footprint=env['local_cells'](branches[decision['sourceBranch']]['geometry'],decision['fillLo'],decision['fillHi'])
    fill=old.copy()
    for xx,yy in footprint:
        if x<=xx<x+w and y<=yy<y+h and prototype[yy-y,xx-x]:fill[yy-y,xx-x]=True
    options=[]
    for corner in gate['positiveCorners']:
        xx,yy=corner['head'];m=old.copy();m[yy-y,xx-x]=False;options.append((energy(m,a),xx,yy,m))
    _,xx,yy,keep=min(options,key=lambda z:(z[0],z[1],z[2]))
    params=json.loads((CAP/f'{frame:03}_OFF_PARAMS.json').read_text());source=Image.open(CAP/f'{frame:03}_OFF.png').convert('RGB')
    top=100+index*670
    for col,(mask,title,note)in enumerate([(fill,'A: 좁은 막힌 끝 생략 / 넓은 입구 유지','1논리픽셀 폭까지의 국소 FILL 부분만 표시'),(keep,'B: 원래 가는 틈 유지 / 인접 머리 1셀 생략','두 개 KEEP 배치 중 기존 공간비용이 낮은 예')]):
        px=22+650*col;draw.text((px,top),f'Walk {frame}  {title}',font=font(20),fill='#122638');draw.text((px,top+32),note,font=font(16),fill='#465c6a')
        overlay=source.copy();d=ImageDraw.Draw(overlay)
        changed=np.argwhere(mask!=old)
        for v,u in changed:
            hx,hy=int(u+x),int(v+y);sx=2*(hx+params['offsetX'])-350;sy=2*(hy-params['offsetY'])-25
            colour='#db2e96'if mask[v,u]else'#12c8d7';d.rectangle((sx,sy,sx+1,sy+1),fill=colour)
        draw.rectangle((px,top+66,px+230,top+536),outline='#8293a5');canvas.paste(overlay,(px,top+66))
        cx,cy=gate['sharedCorner'];zx,zy=cx-5,cy-6;step=28
        for v in range(11):
            for u in range(10):
                hx,hy=zx+u,zy+v;selected=bool(mask[hy-y,hx-x]);colour='#30394a'if selected else'#ffffff'
                if selected!=bool(old[hy-y,hx-x]):colour='#db2e96'if selected else'#12c8d7'
                x1,y1=px+250+u*step,top+95+v*step;draw.rectangle((x1,y1,x1+step-1,y1+step-1),fill=colour,outline='#b7c1cb')
        draw.text((px+250,top+414),'형상만 확대 · 원색/명암 합성 아님',font=font(16),fill='#465c6a')
        draw.text((px+250,top+445),f'이 틈만 비교, 다른 영역은 기준566',font=font(15),fill='#465c6a')
        draw.text((px+250,top+474),f'표시 변경 {len(changed)}셀',font=font(16),fill='#465c6a')
    records.append({'frame':frame,'sourceBranch':decision['sourceBranch'],'fillRange':[decision['fillLo'],decision['fillHi']],'KEEPExampleRemovedCorner':[xx,yy],'illustration':'local geometry alternatives over the same existing baseline566 image; no new RGB or occlusion render; other regions remain baseline','pitch':1.0})
draw.text((22,1420),'이 그림은 선택 가능한 형상 대가를 보여줍니다. 실제 최종 품질·가림·애니메이션 통과 증거가 아닙니다.',font=font(17),fill='#643250')
canvas.save(ROOT/'DESIGN_OPTIONS572.png');(ROOT/'DESIGN_OPTIONS572.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('DESIGN_OPTIONS572.png', (ROOT/'DESIGN_OPTIONS572.png').stat().st_size)
