"""Data figures only. Stored GPU77 is actual; solver panels are labelled
false-colour diagnostics, NOT a new rendered character or final palette.
"""
import json,gzip
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from stored110 import H,P108,source_packet,plane

COL=np.array([[24,32,43],[60,202,233],[252,236,191],[191,124,252],[248,78,139]],np.uint8)
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
def read(p):return json.loads(p.read_text(encoding='utf8'))
def rgb(a):
    c=np.clip(a,0,1);return np.rint(np.where(c<=.0031308,c*12.92,1.055*c**(1/2.4)-.055)*255).astype(np.uint8)
def consensus(frame,root):
    info=[read(root/f'frame{frame}-eye{owner}-result.json')for owner in [1,2]];w=max(q['metadata']['canonicalSize'][0]for q in info);h=max(q['metadata']['canonicalSize'][1]for q in info);pic=np.zeros((h,w),int)
    for owner in [1,2]:
        q=info[owner-1];ix=q.get('selectedIndicesWithinEnumeratedOptima',[])
        for j,(y,x)in enumerate(q['cells']):
            values={q['solutions'][i][j]for i in ix}
            if not values:continue
            value=next(iter(values))if len(values)==1 else 4
            if pic[y,x]not in [0,value]and value:pic[y,x]=4
            elif value:pic[y,x]=value
    return Image.fromarray(COL[pic]),info
def main():
    rows=read(P108/'INPUT108.json');states=[(99,'열림'),(103,'부분 Close50 / 최소 반례'),(107,'완전 Close100'),(125,'동일 포즈 / 위상0.5'),(192,'완전 Close / 측면'),(207,'머리 OFF / 부분 Close25')]
    board=Image.new('RGB',(1400,1320),'#101923');d=ImageDraw.Draw(board);d.text((24,16),'110 — 공동 배치 / 외부 가림 순서 검증 · 제품 미적용',font=font(26),fill='white');d.text((24,59),'왼쪽만 실제 저장 GPU77. 나머지는 라벨 진단색: 홍채=청록, 흰자=크림, 안검=보라, 여러 해=분홍.',font=font(18),fill='#b8d8e9');d.text((24,88),'최종 RGB·유한 안검 팔레트·화면 미관·시간 안정성의 성공 그림이 아닙니다. 잘린 64해는 조건부 표본입니다.',font=font(17),fill='#ffbf92')
    for x,label in [(24,'GPU77 머리'),(180,'GPU77 눈 16×8 / ×10'),(400,'머리 가림으로 배치 제한 (기각)'),(690,'머리 가림과 분리한 배치 (가림 전)'),(1000,'동률·가림·남은 문제')]:d.text((x,130),label,font=font(15),fill='white')
    for i,(frame,title)in enumerate(states):
        y=173+i*185;row=next(v for v in rows if v['name']=='actual107-frame'+str(frame));p=source_packet(row);m=read(p/'RAW_MANIFEST.json');head=np.flipud(plane(p/'H-product77-final.plane')[1]);head=Image.fromarray(rgb(head[:,:,:3]));head.save(H/f'frame{frame}-actual77-head.png');board.paste(head.resize((120,144),Image.Resampling.NEAREST),(24,y+24));roi=m['grid102']['eyeTopLeftROI'];hx,hy,hw,hh=m['grid102']['headROI'];ox=roi[0]-hx;oy=roi[1]-(272-hy-hh);eye=head.crop((ox,oy,ox+roi[2],oy+roi[3]));eye.save(H/f'frame{frame}-actual77-eye.png');board.paste(eye.resize((160,80),Image.Resampling.NEAREST),(180,y+40));board.paste(eye,(180,y+136));d.text((24,y),f'F{frame} {title}',font=font(16),fill='#d5e6f3')
        summaries=[]
        for x,root in [(400,H),(690,H/'separated')]:
            pic,info=consensus(frame,root);board.paste(pic.resize((pic.width*10,pic.height*10),Image.Resampling.NEAREST),(x,y+31));summaries.append(info)
            a=' / '.join(f"눈{q['owner']}: {len(q.get('selectedIndicesWithinEnumeratedOptima',[]))}해"+(' 전체열거'if q.get('enumerationComplete')else ' 일부')for q in info);d.text((x,y+148),a,font=font(13),fill='#aac9df')
        info=summaries[1]
        for j,q in enumerate(info):
            ix=q.get('selectedIndicesWithinEnumeratedOptima',[]);counts={part:sorted({q['solutions'][v].count(part)for v in ix})for part in [1,2,3]};d.text((1000,y+30+j*48),f"eye{q['owner']} I/W/L: {counts[1]}/{counts[2]}/{counts[3]}",font=font(14),fill='#c9deeb')
        note='홍채1셀도 허용됨 → 목적함수 미완'if frame in [99,125,207]else '후보끼리의 양립 불가·다중해를 보존'if frame==103 else '홍채/흰자 재생성 0 · 안검은 별도 노출'if frame==107 else '배치 3셀은 남되, 실제 표본은 모두 가림'if frame==192 else ''
        d.text((1000,y+137),note,font=font(14),fill='#ffb0a4')
    board.save(H/'JOINT_RESOLVER110.png')
    # Exact conceptual source-cache counterexample; positions/IDs shown, RGB
    # is a legend only. Identity histograms cannot encode relative positions.
    im=Image.new('RGB',(1100,380),'#111b27');dd=ImageDraw.Draw(im);dd.text((24,20),'Source-ID 분포가 같아도 특징 모양은 다릅니다',font=font(25),fill='white');dd.text((24,60),'A와 B를 한 셀에 함께 저장한 캐시와, 원형처럼 이웃한 두 셀에 배치한 캐시는 히스토그램이 같습니다.',font=font(17),fill='#bcdaed')
    for origin,label,squares in [((40,120),'원형 source bank',[(0,'A'),(1,'B')]),((390,120),'분포만 보존: 두 ID가 한 셀',[(0,'A+B')]),((760,120),'상대 좌표까지 보존',[(0,'A'),(1,'B')])]:
        x,y=origin;dd.text((x,y-30),label,font=font(18),fill='white')
        for offset,text in squares:dd.rectangle((x+offset*80,y,x+offset*80+70,y+70),fill='#2e9ebb',outline='white');dd.text((x+offset*80+12,y+20),text,font=font(21),fill='white')
    dd.text((24,260),'수정: source ID별 상대 위치 오차·누락된 source 쌍을 별도 Pareto 차원으로 기록. 가중 합이나 색 평균 없음.',font=font(17),fill='#d5e9ec');dd.text((24,300),'이 기준만으로 최초 프레임의 모든 디자인 동률 또는 64해 밖의 해를 결정했다고 주장하지 않습니다.',font=font(17),fill='#ffbc9e');im.save(H/'SOURCE_ID_IS_NOT_SHAPE110.png')
    print(json.dumps({'figures':['JOINT_RESOLVER110.png','SOURCE_ID_IS_NOT_SHAPE110.png'],'actualHeadAndEyeROIs':12,'nearestScale':[3,10],'newRender':False}))
if __name__=='__main__':main()
