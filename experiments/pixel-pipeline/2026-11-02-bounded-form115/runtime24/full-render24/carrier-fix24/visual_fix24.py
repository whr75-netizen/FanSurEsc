"""Actual old/new renders and owner masks; no CPU render labelled as GPU."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;R=H.parent;sys.path.insert(0,str(R));from report_full24 import read,plane
review=read(H/'VALIDATED_FIX24.json');phase=read(H/'PHASE_EXPOSURE24.json')
font=lambda n:ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',n)
board=Image.new('RGB',(1400,1360),'#18202a');d=ImageDraw.Draw(board)
def text(x,y,s,n=19,c='#e8eef5'):d.text((x,y),s,font=font(n),fill=c)
def owner_image(packet):
 o=plane(packet/'F-FinalOwner.plane')[1];a=np.zeros((*o.shape[:2],3),np.uint8);a[:]=[26,32,42]
 for role,c in [(2,(60,150,235)),(5,(245,245,235)),(7,(165,90,45)),(4,(225,170,140)),(12,(60,50,70)),(13,(65,50,80)),(14,(70,55,80))]:a[o[:,:,0]==role]=c
 a[o[:,:,3]==-116]=[255,220,20]
 a[o[:,:,3]==-117]=[220,70,80]
 return Image.fromarray(np.flipud(a)).resize((o.shape[1]*16,o.shape[0]*16),Image.Resampling.NEAREST)
def packet(root,frame):
 s=read(next(root.glob('STATE113-*-finished.json')));row=next(x for x in s['sequencePackets']if x['frame']==frame);return Path(row['output'])
def paste(im,x,y):
 if isinstance(im,Path):im=Image.open(im)
 bg=Image.new('RGBA',im.size,'black');bg.alpha_composite(im.convert('RGBA'));board.paste(bg.convert('RGB'),(x,y))
text(20,12,'안검 carrier 수정 · 실제 GPU 40프레임 재검증',28)
text(20,58,'안와 테두리의 깊이 범위로 실제 안검 깊이를 버리던 조건 한 곳만 수정했습니다.',20)
text(20,96,'미확정 carrier 0셀 / 실제 외부 가림 유지 / 눈 팔레트 밖 RGB8 0 / 제품77 기본값 유지',19)
text(20,142,'이전 실제 RGB');text(320,142,'수정 실제 RGB');text(620,142,'이전 owner');text(920,142,'수정 owner')
for j,(oldRoot,newRoot,frame,label)in enumerate([(R/'sequence24',H/'close',105,'Close75 · 공유 피부 차단 유지'),(R/'motion24',H/'motion',134,'회전 · 안검1셀 복구'),(R/'motion24',H/'motion',135,'회전 · 안검2셀 복구'),(R/'motion24',H/'motion',136,'회전 · 안검1셀 복구')]):
 y=178+j*178;text(20,y,f'{label} | frame {frame}',18)
 i=next(i for i,r in enumerate(read(newRoot/'RESULT_FULL24.json')['frames'])if r['frame']==frame)
 paste(oldRoot/'results'/f'{i:02d}-candidate-eye.png',20,y+29);paste(newRoot/'results'/f'{i:02d}-candidate-eye.png',320,y+29)
 paste(owner_image(packet(oldRoot,frame)),620,y+29);paste(owner_image(packet(newRoot,frame)),920,y+29)
text(20,905,'owner 표시: 파랑=홍채 / 흰색=흰자 / 갈색=안검 / 노랑=미확정 / 빨강=확정 피부 차단',18)
text(20,944,'별도 Play의 피부·머리 조명 입력 차이가 있어 전체 RGB 차이를 수정 효과로 세지 않았습니다.',18,'#ffcc88')
text(20,981,'동일 현재 입력의 이전 조건 CPU 검산 ↔ 실제 수정 GPU를 비교: 가시 안검 복구 7건, 얼굴·머리 강제 통과 0.',18)
text(20,1032,'남은 반례 · 수치/우선순위 튜닝으로 숨기지 않음',24,'#ffcc88')
text(20,1073,'Close75: 원본 안검은 보이나, 배정 목적지는 양안 blink 공유 피부 9삼각형 뒤에 놓입니다.',19)
text(20,1110,'현재 단안 소유권 규칙은 이 공유 피부를 면제하지 않습니다. 눈·공유 바탕의 변형 운반 규칙이 필요합니다.',18)
text(20,1162,'위상: 메쉬 변형 ≤ 4.77e-7 world, 카메라 기저 변화 0. 원형은 유지되나 최종 흰자 5위치가 변합니다.',18)
text(20,1199,'예: 0→0.125px 이동에서 눈 목적지가 1px 이동하고, 머리 가림 면적은 12/16→0/16으로 바뀝니다.',18)
text(20,1243,'눈의 정수 배치와 머리의 물리 4×4 격자에 공통 이동/가림 기준이 아직 없습니다.',19,'#ffcc88')
text(20,1290,'색 평균·고정 셀 수·모든 피부 무시를 추가하지 않았습니다. 전체 얼굴 UV·외곽선·시간 안정성은 미완입니다.',18)
board.save(H/'GPU_CARRIER_FIX24.png')
#Short actual turn sequence with the final native-size whole frame and nearest
#eye crop. Durations are presentation timing, not measured capture/GPU speed.
frames=[];s=read(next((H/'motion').glob('STATE113-*-finished.json')))
for i in range(18,28):
 p=s['sequencePackets'][i];a=Image.new('RGB',(1000,465),'#18202a');dd=ImageDraw.Draw(a)
 dd.text((15,7),f'실제 GPU 회전 frame{p["frame"]} / serial{p["serial"]} · 관측 순서, 표시 180ms',font=font(20),fill='white')
 im=Image.open(H/'motion/results'/f'{i:02d}-candidate.png').convert('RGB');a.paste(im,(15,45))
 eye=Image.open(H/'motion/results'/f'{i:02d}-candidate-eye.png').convert('RGB');a.paste(eye,(15,325))
 dd.text((520,95),'수정 후보 · 제품77 기본값 유지',font=font(20),fill='white')
 dd.text((520,135),'미확정 carrier: 0',font=font(20),fill='white')
 dd.text((520,175),'실제 피부·머리 가림 유지',font=font(20),fill='white');frames.append(a)
frames[0].save(H/'GPU_CARRIER_FIX_TURN24.webp',save_all=True,append_images=frames[1:],duration=180,loop=0,lossless=True,method=4)
print(H/'GPU_CARRIER_FIX24.png')
