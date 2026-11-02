from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

H=Path(__file__).resolve().parent
O=H/'results'
result=json.loads((H/'RESULT113.json').read_text(encoding='utf8'))
font_path=r'C:\Windows\Fonts\malgun.ttf'
def font(size): return ImageFont.truetype(font_path,size)
im=Image.new('RGB',(1510,1510),'#171b24');d=ImageDraw.Draw(im)
def txt(x,y,s,size=21,fill='#eef2fa'): d.text((x,y),s,font=font(size),fill=fill)
def paste(p,x,y,box=None,scale=1):
    a=Image.open(p).convert('RGBA')
    if box: a=a.crop(box)
    if scale!=1:a=a.resize((a.width*scale,a.height*scale),Image.Resampling.NEAREST)
    bg=Image.new('RGBA',a.size,'black');bg.alpha_composite(a);im.paste(bg.convert('RGB'),(x,y))
txt(24,15,'113 | 실제 Unity GPU 전체 캐릭터 비교 — 격리 통합, 제품 기본값 유지',29)
txt(24,57,'동일 렌더 프레임: product77 바탕 / 현재 원본 기하 + 공동 셀 배정 + 가림 + 팔레트 직접 대입',18)
txt(24,92,'기존 product77 · 480 × 272 원배율',21)
txt(528,92,'격리 GPU113 · 480 × 272 원배율',21)
paste(O/'00-control.png',24,127);paste(O/'00-candidate.png',528,127)
txt(1040,128,'실제 캡처 범위',23)
for n,s in enumerate(['12개 GPU 렌더 상태','열림 → Close → 재개방','Close75 머리 ON / OFF','추가 CPU 배치 재생 없음','눈 ROI 밖 원시 값 동일','셀 수 6+2 강제 없음']):txt(1040,171+n*31,s,19)
txt(24,419,'전체 캐릭터 최근접 3배 (동일 위치 crop)',23)
txt(24,455,'기존 product77',20);txt(282,455,'격리 GPU113',20)
crop=(184,25,266,189)
paste(O/'00-control.png',24,491,crop,3);paste(O/'00-candidate.png',282,491,crop,3)
txt(567,419,'눈 ROI 최근접 16배 | 왼쪽 기존 / 오른쪽 GPU113',23)
stages=[(0,'열림 · frame99'),(2,'Close50 · frame103'),(4,'완전 Close · frame107'),(8,'재개방 · frame115'),(9,'Close75 / 머리 ON · frame122'),(10,'Close75 / 머리 OFF · frame125')]
for n,(idx,label) in enumerate(stages):
    y=462+n*158;txt(567,y,label,18)
    r=result['frames'][idx]['pixelRectBottomLeft'];x,by,w,h=r
    box=(x,272-by-h,x+w,272-by)
    paste(O/f'{idx:02d}-control.png',567,y+26,box,16)
    paste(O/f'{idx:02d}-candidate.png',843,y+26,box,16)
txt(24,1020,'확인된 결과',23)
for n,s in enumerate(['12장 모두 frame/source/serial 일치','눈 ROI 밖 전체 RGBA 원시 값 동일','홍채·흰자·안검의 유한 색 조회 위반 0','Play 정상 종료 / 완료 marker 검증']):txt(24,1060+n*32,s,18)
txt(24,1205,'남은 실패 · 완성 주장 아님',23,'#ffcc88')
for n,s in enumerate(['Close50: 동일 최적해 2개 → 일부 셀 미확정','native 지지 표면 부족: 상태별 1~5셀','머리 가림 경계: 상태별 최대 2셀 미확정','완전 Close: 색소 표본 없는 안검 1셀','전체 얼굴 UV·외곽선·연속 움직임 미완']):txt(24,1247+n*32,s,18,'#ffdcad')
txt(567,1434,'113은 현재 프레임 GPU 배정/합성 결과입니다. 미확정은 바탕으로 표시됩니다.',17,'#ffdcad')
txt(567,1464,'확대는 nearest만 사용했습니다. 상태별 캡처를 실제 연속 보행 검증으로 세지 않습니다.',16)
path=H/'GPU_RUNTIME113_WHOLE_CHARACTER.png';im.save(path)
print(path)
