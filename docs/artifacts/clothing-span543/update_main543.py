from pathlib import Path
import html,json,hashlib
O=Path(__file__).resolve().parent;M=Path('C:/Users/JG/Desktop/작업폴더/메인.html');b=M.read_bytes();assert b'id="current543"'not in b
result=json.loads((O/'FULL_RESULT543.json').read_text());media=json.loads((O/'MEDIA543.json').read_text());verdict=json.loads((O/'VERDICT543.json').read_text());assert verdict['reviewCompleted']
u=lambda p:html.escape(p.as_uri(),quote=True)
section=f'''<section id="current543" style="background:#f5f7fb;border-bottom:4px solid #316a73;padding:16px;max-width:1320px;color:#20252c">
<h1 style="margin:0 0 8px">최신543 — 왼쪽 팔꿈치 영역 선택 수정</h1>
<p><b>{html.escape(verdict['headline'])}</b> 같은 실행의 제품 OFF / 기존540 Clothes / 543 형상 후보입니다. 실제 Walk81포즈·243렌더, 모든 프레임을 원래 시간순서로 보존했습니다. 아래540 영상은 이전 결과이며 새 수정으로 표시하지 않습니다.</p>
<p>선택 마스크가 가시 두 셀을 허용했고, 별도의 thin 예외가 밝게 남긴 것이 원인이었습니다. 선색은 마스크와 다릅니다. 넓은 원형 내부가 확인된 선행 경계 구간을 하나의 선택 단위로 묶었습니다. 선 명도만 바꾼 실험은 가시가 남아 철회했고 원래 셰이더를 복원했습니다.</p>
<p>적용: <b>겉옷·하의·신발 공통 경로</b>. 기본 자동 활성화는 OFF입니다. Unity 메뉴 <code>EValidation/Boundary540/Experimental543 Shape only</code>로 실행할 수 있고 기존 Clothes/Off도 유지합니다. Body0의 상의·스타킹·피부·손, 얼굴·눈·헤어는 확장하지 않았습니다.</p>
<p>{html.escape(verdict['limits'])} 비용은 최적화 전 수치이며 캡처시간을 게임 FPS로 해석하지 않습니다. 얼굴 회색은 이번 미재현이며 원인 해결 표기가 아닙니다.</p>
<figure style="margin:0"><img id="proof543" src="{u(O/'FULL_WALK543.webp')}" style="max-width:100%;image-rendering:pixelated" alt="같은 실제 걷기 제품 OFF 기존540 형상543 전신 비교"><figcaption>좌: 제품 OFF / 중: 기존540 Clothes / 우:543 형상 후보. 논리480×272→실제960×544, 전신을 유지한 정수 좌표 자르기, 보간 축소 없음. WebP81프레임 {media['webp']['durationMs']}ms. GIF는10ms 시간단위로 근사합니다.</figcaption></figure>
<p><a href="{u(O/'FULL_WALK543.gif')}">전신 GIF ({media['gif']['bytes']:,}byte)</a> · <a href="{u(O/'LATEST543.png')}">65번 전신 정지 비교</a> · <a href="{u(O/'ELBOW543_65.png')}">형상/명도 독립 실험 확대</a> · <a href="{u(O/'CONSISTENCY543.md')}">실제 함수·수식·일관성 판정</a> · <a href="{u(O/'FULL_RESULT543.json')}">81포즈 검증 수치</a></p>
<p>전달 상태: 로컬 페이지·파일 제공. 이전 Library403 접근 제한은 재시도하거나 우회하지 않았습니다.</p>
</section>
'''.encode('utf8')
at=b.index(b'<section id="current540"');a=b[:at]+section+b[at:];assert a.replace(section,b'',1)==b
(O/'main543.html').write_bytes(a);(O/'MAIN543.json').write_text(json.dumps({'target':str(M),'before':hashlib.sha256(b).hexdigest(),'after':hashlib.sha256(a).hexdigest(),'oldPagePreserved':True},ensure_ascii=False,indent=2));(O/'SECTION543.html').write_bytes(section);print('Prepared latest543 section; prior page bytes preserved')
