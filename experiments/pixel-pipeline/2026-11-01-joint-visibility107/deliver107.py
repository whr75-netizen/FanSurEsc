"""Review artifacts from actual107 captures. Explicitly rejected whole-cell rule."""
from pathlib import Path
import sys,json,hashlib,zipfile
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer,rgba,font
from analyse_capture68 import plane
from joint_reference107 import contributions
def card(e):
 p=Path(e['output']);a={k:plane(p/(k+'.plane'))[1]for k in ['C-EyeRGBA','F-EyeRGBA','F-FinalRGBA']};board=Image.new('RGB',(1120,360),'#20252c');d=ImageDraw.Draw(board)
 d.text((18,10),f"107 실제 GPU · 미채택 / frame {e['frame']} · {e['testStage82']}:{e['stageIndex82']}",font=font(21),fill='white');d.text((18,45),'원본 표본/가림 확인과 전체 셀 배정의 미술·형상 성공은 별개',font=font(18),fill='#f2bd91')
 for x,title,k in [(18,'106 · 기존 파츠 보호','C-EyeRGBA'),(385,'107 · 공동 가시성 + 곡선','F-EyeRGBA'),(752,'107 · 실제 머리 가림 후','F-FinalRGBA')]:
  d.text((x,81),title,font=font(17),fill='#c9d9e5');im=rgba(a[k]);board.paste(im,(x,108),im);zoom=min(20,340//im.width,190//im.height);board.paste(im.resize((im.width*zoom,im.height*zoom),Image.Resampling.NEAREST),(x,131),im.resize((im.width*zoom,im.height*zoom),Image.Resampling.NEAREST))
 return board
def main():
 s=load(sorted((H/'capture-final').glob('STATE107-*'))[-1]);assert s['PlayExited']and not s.get('error');es=s['sequencePackets'];out=H/'analysis-final/review'
 cards=[card(e)for e in es if e['frame']in [99,101,103,107,192]];im=Image.new('RGB',(1120,len(cards)*360),'#20252c')
 for i,c in enumerate(cards):im.paste(c,(0,i*360))
 im.save(out/'GPU107_KEY_STATES.png')
 for name,seq,duration in [('GPU107_CLOSE_REOPEN.webp',[e for e in es if e['testStage82']=='evaluated-blink106'],650),('GPU107_HAIR_ON_OFF.webp',[e for e in es if e['testStage82'].startswith('partial-hair-')],850)]:
  frames=[card(e)for e in seq];frames[0].save(out/name,save_all=True,append_images=frames[1:],duration=duration,loop=0,lossless=True)
 # Minimum counterexample from the actual same-source8x visibility data.
 e=next(e for e in es if e['frame']==103);p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');w,h=m['forward102']['denseSize'];v=np.zeros((4,h,w,4),np.float32);v[1:4]=buffer(p/'dense-three-part-visibility.f32').reshape(3,h,w,4);ls=np.zeros((4,5,h,w,4),np.float32)
 for part in [1,2]:ls[part,1]=np.flipud(plane(p/('D-part'+str(part)+'-meta.plane'))[1])
 ls[3,1]=np.flipud(plane(p/'D-lid-meta.plane')[1]);labels=np.zeros((8,8),int)
 for y in range(8):
  for x in range(8):
   lo,hi=contributions(ls,v,4*8+y,12*8+x);labels[y,x]=next((i+1 for i in range(4)if all(lo[i]>hi[q]for q in range(4)if q!=i)),0)
 board=Image.new('RGB',(1160,690),'#20252c');d=ImageDraw.Draw(board);d.text((20,12),'107 미채택 최소 반례 · frame103 / canonical(12,4)',font=font(25),fill='white');d.text((20,54),'같은 표본의 앞/뒤 판정이 맞아도 셀 전체의 올바른 소유권을 결정하지는 못함',font=font(20),fill='#f0c58d')
 colors={0:'#f2d05e',1:'#9e8bda',2:'#f4e9d5',3:'#835c45',4:'#555e69'}
 for y in range(8):
  for x in range(8):d.rectangle((20+x*40,104+y*40,58+x*40,142+y*40),fill=colors[labels[y,x]])
 d.text((20,440),'원본 가시성 우세 표본 · 범례용 색',font=font(18),fill='white');d.text((20,472),'홍채30 / 흰자27 / 안검2 / 바탕5',font=font(20),fill='#d0dbe8')
 d.text((390,112),'107: 곡선 위치에서 앞인 안검 표본 선택',font=font(21),fill='white');d.text((390,151),'→ 셀 전체를 안검색으로 출력',font=font(21),fill='#f1ae96')
 for xx,name in [(390,'C-EyeRGBA'),(770,'F-EyeRGBA')]:
  a=plane(p/(name+'.plane'))[1];im=rgba(a);z=20;board.paste(im.resize((im.width*z,im.height*z),Image.Resampling.NEAREST),(xx,210),im.resize((im.width*z,im.height*z),Image.Resampling.NEAREST))
 d.text((390,400),'106 실제 GPU',font=font(18),fill='white');d.text((770,400),'107 실제 GPU',font=font(18),fill='white')
 d.text((20,530),'남은 문제: 안검 곡선·홍채·흰자의 셀을 함께 재배치하는 전체 눈 목적함수가 없음.',font=font(20),fill='white');d.text((20,570),'무조건 보호 → 무조건 곡선으로 바꾸는 것도 해결이 아님. 제품77 유지.',font=font(20),fill='#f1bd9b');board.save(out/'MINIMUM_FAILURE107.png')
 # Complete final54 packets, and the two focused intermediate4x packets.
 items=[]
 with zipfile.ZipFile(H/'RAW107.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  previous=load(sorted((H/'capture-b').glob('STATE107-*'))[-1]);groups=[('final54',es),('intermediate4x-focus',[e for e in previous['sequencePackets']if e['frame']in [101,192]])]
  for group,entries in groups:
   for e in entries:
    p=Path(e['output'])
    for f in sorted(p.iterdir()):
     if f.suffix in ['.plane','.f32']or f.name in ['RAW_MANIFEST.json','RAW_COMPLETE76.marker','normal-query-geometry107.json','dense-query-geometry107.json']:
      rel=group+'/frame'+str(e['frame'])+'/'+f.name;z.write(f,rel);items.append({'file':rel,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 (H/'RAW107_INDEX.json').write_text(json.dumps(items,indent=2)+'\n',encoding='utf-8')
 page='''<!doctype html><meta charset="utf-8"><title>107 실제 공동 가시성 검증 · 미채택</title><style>body{background:#20252c;color:#e7edf4;max-width:1190px;margin:30px auto;font:17px/1.7 system-ui}img{max-width:100%;image-rendering:pixelated}a{color:#9dd3ff}td,th{padding:8px;border:1px solid #68717d}table{border-collapse:collapse}</style>
<h1>107 · 실제 GPU 공동 가시성 검증 — 전체 후보 미채택</h1><p>제품77 유지. 106의 홍채·흰자 무조건 보호를 제거하고, 곡선의 원본 표본 위치에서 세 파츠의 깊이/가시 기여를 함께 판정했습니다. 같은 프레임8× 표본에서 확인된 색소만 사용합니다. 6+2셀·최소 셀 수·포즈별 강제값·색 평균·최종×g는 없습니다.</p>
<p>최종1 Play에서 부분Close9, 열린 위상10/보행8/회전10, 닫힌 위상4/회전10, 부분Close의 실제 머리ON/OFF/복원3으로54상태를 캡처했습니다. 54연속 프레임 또는 실제 성능 영상이라는 뜻은 아닙니다. 정상 Present/history 경로이며 실제 GPU 선택 결과입니다.</p>
<table><tr><th>검사</th><th>결과</th></tr><tr><td>동등성/출처</td><td>7,959셀 CPU/GPU 불일치0, 1,350 plane 동일 source/frame/serial. 홍채·흰자 원본 팔레트 밖0.</td></tr><tr><td>표본화 손실</td><td>frame101 (14,3)/(7,4)의4×0표본→8×2/1개, frame192(3,9)0→1개. 실제 색소/깊이로 출력했으며 발명한 연결색이 아님.</td></tr><tr><td>측면 가림5셀</td><td>같은 프레임의 현재 삼각형/UV/행렬로157 ray 증거 재계산. 모두 앞쪽 얼굴과 불투명 alpha bound. depth 오차최대2.3352e−6, UV오차1.7892e−6.</td></tr><tr><td>머리 ON/OFF</td><td>OFF의 머리 표본0, 최종색=눈 합성색. ON복원 눈RGBA/owner 정확히 동일. 최종19픽셀 RGB8 차이는 변한 머리 입력RGB에서 왔으며 메타/owner는 같음.</td></tr><tr><td>위상/재개방</td><td>실측0~1px. 열린10/닫힌4 상태 각각shape ID1종 및RGB8 변화0. 재개방 RGBA/owner 원상태 동일. 전체 시간 안정성 보장 아님.</td></tr><tr><td>미통과</td><td>곡선 표본의 가시성은 전체 셀의 소유권을 유일하게 정하지 못함. 열린 홍채9→6, 부분Close50에서 한쪽 홍채0; 곡선·홍채·흰자의 전체 공동 재배치는 아직 없음. 일부 분절도 남음.</td></tr></table>
<h2>같은 입력 실제GPU106/107 · 원배율과 최근접 정수 확대</h2><img src="analysis-final/review/GPU107_KEY_STATES.png"><h2>핵심 반례</h2><img src="analysis-final/review/MINIMUM_FAILURE107.png"><h2>Close/reopen 상태 검토</h2><p>보기 시간을 늘린 상태별 미리보기이며 실제FPS/성능 영상은 아닙니다.</p><img src="analysis-final/review/GPU107_CLOSE_REOPEN.webp"><h2>실제 머리 메시 ON/OFF/복원</h2><img src="analysis-final/review/GPU107_HAIR_ON_OFF.webp">
<p>첫 실행은 HLSL bool 복합대입 컴파일 오류로0캡처 후 정상 종료했고, 이후 전9커널 IsSupported/group 검사를 추가했습니다. 중간4× 공동판정51상태는 확보했지만 머리관찰기 사전검사에서 종료했습니다. 최종은54상태/정상 종료입니다. 과거 오류9개는 Console에 남았지만 최종 실행의 신규 오류는0입니다. shader integer-divide 성능 경고1개가 있고 실제GPU 시간을 측정한 결과가 아닙니다.</p>
<p>마지막20:40:11UTC Edit/scene clean/dirty31 동일, 가능한 직렬화46개·입력 동일 객체22값/장치·옵션/time/pipeline/globals 복원. 임시 AssetImporter1개 unavailable. 보호32파일·기존 사용자30변경 유지, RT30→30. GetTotalAllocatedMemoryLong +35,825,685bytes(+34.17MiB), 물리WS/누수 확정값 아님. 신규C# Assets import·광범위 저장·CUA·삭제·초기화·강제종료·push는 없습니다.</p>
<p>새 Unity 자산은 격리 ForwardEye107.compute와.meta뿐입니다. 외부C# adapter/관찰기는 제품 기본77을 바꾸지 않습니다. native 안검 유한 팔레트·외곽선·얼굴/두피/볼 영역화는 미완이며 UV 임계값 탐색은 추가하지 않았습니다.</p>
<p><a href="analysis-final/RESULT107.json">실제 GPU 판정</a> · <a href="FOCUS107.json">셀별 source 기여·트레이드오프</a> · <a href="RAY_PROOF107.json">독립 ray 근거</a> · <a href="PRESERVATION107.json">복원/색차</a> · <a href="RAW107_INDEX.json">원시 자료 해시</a> · <a href="RAW107.zip">최종54+중간2 focus packet</a></p>'''
 (H/'INDEX.html').write_text(page,encoding='utf-8');print(json.dumps({'rawZipBytes':(H/'RAW107.zip').stat().st_size,'rawFiles':len(items),'actualFinalFrames':len(es)}))
if __name__=='__main__':main()
