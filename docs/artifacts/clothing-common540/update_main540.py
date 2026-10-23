from pathlib import Path
import json,hashlib,html,sys
O=Path(__file__).resolve().parent;M=Path('C:/Users/JG/Desktop/작업폴더/메인.html');phase=sys.argv[1]
full=phase=='full';tag='FULL540'if full else'ADJACENT540';result=json.loads((O/f'{tag}_RESULT.json').read_text());n=result['poses'];u=lambda p:html.escape(p.as_uri(),quote=True)
mb=M.read_bytes();ident=b'<section id="current540"'if b'<section id="current540"'in mb else b'<section id="current539"';a=mb.index(ident);b=mb.index(b'</section>',a)+10
size=result['media']['CLOTH']['size'];width,height=size
headline='전체 Walk81쌍: 경계·채움 통과 / 실시간 채택 보류'if full else'19포즈 검증 완료·전체 Walk 검사 중'
extra='<p><b>전체81쌍:</b> 경계밖·빈칸·패킷실패0, 얼굴·눈변화0. 34/43 가시 제거·44 유지·50 파임 방지. 옷 경계 CPU단계 중앙값 합계42.48ms로 실시간 기본채택은 보류합니다. 내부선·명암 전환은 별도 미해결이며 픽셀튐 전체해결이 아닙니다. 추가 루프끝 floatRGB1셀은 기존입력차가선생략부위에드러난것이고 실제화면RGBA8차이0·경계반전없음으로 구분했습니다. 이번 전체영상 skyHour17.86330, 이전19포즈7.22407로 실행간 배경/광원은 다릅니다.</p>'if full else''
scope='0~80 전체81프레임'if full else'33~51 연속19프레임'
new=f'''<section id="current540" style="background:#f5f7fb;border-bottom:4px solid #56739b;padding:16px;max-width:1320px;color:#20252c">
<h1 style="margin:0 0 8px">최신540 전신 비교 — 제품 OFF / 공통 옷 경계 ON</h1>
<p><b>{headline}.</b> 겉옷·하의·신발이 같은 경계→영역→채움 코드를 사용합니다. 기존348은 유지하며 기본 자동 활성화는 하지 않았습니다.</p>
{extra}
<div style="display:grid;grid-template-columns:{width*2}px 370px;gap:18px;align-items:start"><div>
<p>왼쪽 현재 제품 OFF · 오른쪽 공통 옷3부위 ON · 새 실제 Walk {scope} · 같은 실행/포즈/빛</p>
<img id="proof540" src="{u(O/f'{tag}_CLOTH.webp')}" width="{width*2}" height="{height*2}" style="display:block;image-rendering:pixelated" alt="최신540 실제 전신 Walk 제품OFF와 공통 옷ON 비교">
<p><a href="{u(O/f'{tag}_CLOTH.gif')}">최신 GIF {result['media']['CLOTH']['gifBytes']:,}B</a> · <a href="{u(O/f'{tag}_RESULT.json')}">실제 검증/비용</a></p>
<p>원래60Hz 시간 간격·모든 {n}프레임 보존·보간0. GIF는10ms 단위, 무손실WebP는16/17ms 간격. {'전체 루프 끝→처음 검토는 결과 기록을 참조하세요.'if full else'짧은 발췌의 반복은 전체 루프 연결 검증이 아닙니다.'}</p>
</div><div><h3>적용과 미채택을 구분합니다</h3>
<p><b>실행 메뉴:</b> Unity → EValidation → Boundary540 → Clothes / Off. Body0 모드는 별도 시험이며 아래 회귀가 있습니다.</p>
<table style="font-size:14px"><tr><td>겉옷</td><td>Body3·role10</td></tr><tr><td>하의 / 신발</td><td>Body1·role8 / Body2·role9</td></tr><tr><td>상의·스타킹·피부·손</td><td>Body0·role7, 공유재질. 옷만 선택 분리한 상태가 아닙니다.</td></tr><tr><td>얼굴·눈 / 헤어</td><td>직접 알고리즘 변경 없음</td></tr></table>
<p><b>539 겉옷 국소수정 커밋14d4b6c:</b> 임의 RDP 부분 chord 대신 전체 outward-return 면적≤1논리셀²을 함께 생략.43 가시 제거·44 정상계단 유지·50 파임 방지, 정상 얇은 끝8저장사례 유지. 논문전체 재현/해상도최적공식 적용은 아닙니다.</p>
<p style="color:#8b1e18"><b>Body0 시험 미채택:</b> 33~51의19포즈에서35/36/41 얼굴 경계1셀의 소유권이Body0로 변경됐습니다. 손을 포함한 전체Body0 시험이며 얼굴 회색 원인 해결 증거가 아닙니다.</p>
<p><a href="{u(O/'ADJACENT540_BODY.webp')}">Body0 포함 실제19포즈 비교</a> · <a href="{u(O/'OTHER_ADJACENT_WITHFACE540.json')}">소유권/중간버퍼 근거</a></p>
<button onclick="document.getElementById('still540').src='{u(O/f'{tag}_CLOTH_043.png')}'">43번 전후</button> <button onclick="document.getElementById('still540').src='{u(O/f'{tag}_CLOTH_050.png')}'">50번 전후</button>
<img id="still540" src="{u(O/f'{tag}_CLOTH_050.png')}" width="{width}" height="{height}" style="display:block;image-rendering:pixelated;margin-top:8px" alt="최신540 전신 정지 전후">
<p style="font-size:13px">RenderFrame은 기존 core GPU동기readback을 포함하고 별도PNG저장·분석은 제외한 호출시간이며 PlayerFPS가 아닙니다. 얼굴 회색 미재현·내부 명암/가림 잔여·성능은 별도 미해결입니다. Library403 재시도 없이 로컬 전달입니다.</p>
<a href="{u(Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game/docs/artifacts/clothing-full533/FULL_WALK533.gif'))}">과거533 전체 영상 — 현재 수정 결과 아님</a>
</div></div></section>'''.encode()
ma=mb[:a]+new+mb[b:];assert ma[:a]==mb[:a]and ma[a+len(new):]==mb[b:]
(O/f'main.{phase}540.html').write_bytes(ma);(O/f'MAIN_{phase.upper()}540.json').write_text(json.dumps({'target':str(M),'before':hashlib.sha256(mb).hexdigest(),'after':hashlib.sha256(ma).hexdigest(),'onlyCurrentSectionChanged':True,'capture':tag},ensure_ascii=False,indent=2),encoding='utf8')
print('prepared main',phase,n)
