"""Actual GPU images, nearest enlargement, labelled limitations."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;Q=H/'sequence24';O=Q/'results'
r=json.loads((Q/'RESULT_FULL24.json').read_text());assert r['completedRuntimeGPUFrames']==12 and r['PlayExited']
im=Image.new('RGB',(1500,1470),'#18202a');d=ImageDraw.Draw(im)
def text(x,y,s,n=19,c='#e8eef5'):d.text((x,y),s,font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',n),fill=c)
def paste(file,x,y,crop=None,scale=1):
 a=Image.open(file).convert('RGBA')
 if crop:a=a.crop(crop)
 if scale!=1:a=a.resize((a.width*scale,a.height*scale),Image.Resampling.NEAREST)
 bg=Image.new('RGBA',a.size,'black');bg.alpha_composite(a);im.paste(bg.convert('RGB'),(x,y))
text(20,12,'Argon2.4 | 실제 Unity GPU 전체 렌더 · 제품77 기본값 유지',28)
text(20,55,'113 기반 공동 배정 + 16개 목적지 깊이 + 안와 정규화 + 원본 곡선 중점 복구',19)
text(20,91,'기존 제품77 · 480 × 272 원배율');text(520,91,'격리 runtime24 후보 · 동일 프레임')
paste(O/'00-control.png',20,123);paste(O/'00-candidate.png',520,123)
text(1040,122,'실제 검증',23)
for j,t in enumerate(['12개 Close / 재개방 / 머리 상태','실제 source·frame·serial 대응','모든 배정에서 최적해 1개','눈 파트 팔레트 밖 RGB8: 0','Play 정상 종료 · 44개 내용 동일','입력 객체·값·장치·옵션 복원']):text(1040,161+31*j,t,17)
text(20,418,'캐릭터 최근접 3배');text(20,451,'제품77');text(290,451,'후보 runtime24')
crop=(182,24,267,190)
paste(O/'00-control.png',20,484,crop,3);paste(O/'00-candidate.png',290,484,crop,3)
text(590,418,'눈 ROI 최근접 16배 · 제품77 / 후보')
for j,(i,label)in enumerate([(0,'열림'),(2,'Close50'),(4,'완전 Close'),(8,'재개방'),(9,'Close75 머리 ON'),(10,'Close75 머리 OFF')]):
 y=455+j*157;text(590,y,label,17)
 paste(O/f'{i:02d}-control-eye.png',590,y+27);paste(O/f'{i:02d}-candidate-eye.png',875,y+27)
text(20,1020,'남은 문제 · 채택/미관 완성 판정 아님',22,'#ffcc83')
for j,t in enumerate(['Close75: 목적지 지지 표면 부족 1셀','실제 차단 표면(-117)과 미확정(-116) 분리','머리 ON/OFF 전 원형 역할·색 RGB8 동일','얼굴 UV 영역화 · 외곽선 · 전체 팔레트 미완','별도 실제 움직임 28프레임 완료','회전 지지 표면 최대2셀·최종 노출 변동 남음']):text(20,1063+j*33,t,18,'#ffdcad')
text(590,1430,'실제 GPU 버퍼의 전체/최근접 확대입니다. 제품 기본 경로로 채택하지 않았습니다.',16,'#ffdcad')
im.save(H/'GPU_RUNTIME24_WHOLE_CHARACTER.png')
print(H/'GPU_RUNTIME24_WHOLE_CHARACTER.png')
