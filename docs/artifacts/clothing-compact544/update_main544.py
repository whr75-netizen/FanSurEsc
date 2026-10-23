from pathlib import Path
import json,hashlib,html
O=Path(__file__).resolve().parent;M=Path('C:/Users/JG/Desktop/작업폴더/메인.html');b=M.read_bytes();s=b.decode('utf8');assert 'id="performance544"'not in s
j=json.loads((O/'PERFORMANCE544.json').read_text());assert j['adoptedForExplicitMode']and j['actualWalkPoses']==81
u=lambda p:html.escape(p.as_uri(),quote=True)
table=''
for label,key in [('선택기','selectionMs'),('옷 경계 전체','boundaryTotalMs'),('core RenderFrame','renderMs')]:
 a=j['timingMs']['REFERENCE'][key];c=j['timingMs']['COMPACT'][key];table+=f'<tr><td>{label}</td><td>{a["median"]:.2f} / {a["p95"]:.2f}</td><td>{c["median"]:.2f} / {c["p95"]:.2f}</td></tr>'
panel=f'''<aside id="performance544" style="background:#e7f3ec;border:1px solid #42805c;padding:10px;margin:10px 0">
<b>544 동등 최적화 통과 — 실제 Walk81포즈의 마스크·소유권·UV·최종 색·월드 출력 차이0.</b>
<table style="border-collapse:collapse;margin:8px 0" border="1" cellpadding="5"><thead><tr><th>ms: 중앙값 / 상위95%</th><th>543 참조</th><th>544 최적화</th></tr></thead><tbody>{table}</tbody></table>
<p>같은 실행·동일 포즈·해상도·워밍업에서 짝지은 측정입니다. 선택 목적식은 그대로 두고 라벨이 수학적으로 확정된 셀을 그래프에서 제외했습니다. 기하·색·깊이·시간 필터 변경은 없습니다. 추가 검증 readback·PNG·저장은 계측 밖이며 core에는 기존 런타임 readback이 포함되어 게임 FPS가 아닙니다. 이전540의42.48ms와 직접 최적화율을 계산하지 않았습니다.</p>
<p>프레임 할당 바이트는 <b>미측정</b>: 현재 Mono API가1MB 양성대조에도0을 반환했습니다. 이를 할당0으로 부르지 않습니다. 전체 실시간 성능·Body0/손·내부명암·회색 원인은 여전히 미완료이며 기본 자동 활성화는 OFF입니다.</p>
<p><a href="{u(O/'README544.md')}">변경·비교조건·한계</a> · <a href="{u(O/'PERFORMANCE544.json')}">81포즈 출력/성능 수치</a> · <a href="{u(O/'ACTUAL_COMPARE544.png')}">새544 동일시각65포즈 전후</a></p>
</aside>
'''
s=s.replace('최신543 — 왼쪽 팔꿈치 영역 선택 수정','최신 기록543·544 — 팔꿈치 영역 수정·동등 최적화',1).replace('EValidation/Boundary540/Experimental543 Shape only','EValidation/Boundary540/Clothes543 (validated spans)',1).replace('비용은 최적화 전 수치이며 캡처시간을 게임 FPS로 해석하지 않습니다.','아래 성능표는 동일 실행의 최적화 전후 수치이며 게임 FPS로 해석하지 않습니다.',1)
at=s.index('</figure>',s.index('id="current543"'))+len('</figure>');s=s[:at]+panel+s[at:]
s=s.replace('WebP81프레임 1350ms. GIF는10ms 시간단위로 근사합니다.','영상은 최적화 전543의 전신 기능 비교입니다.544 동등 출력 검증에 따라 재사용하며 새544 촬영으로 표시하지 않습니다. WebP81프레임1350ms, GIF는10ms 시간단위 근사입니다.',1)
a=s.encode('utf8');(O/'main544.html').write_bytes(a);(O/'PERFORMANCE_SECTION544.html').write_text(panel,encoding='utf8');(O/'MAIN544.json').write_text(json.dumps({'target':str(M),'before':hashlib.sha256(b).hexdigest(),'after':hashlib.sha256(a).hexdigest(),'previousPageAndVideosPreserved':True},ensure_ascii=False,indent=2));print('Prepared544 performance panel and validated menu link;543 full GIF preserved')
P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game');base={p:hashlib.sha256((P/p).read_bytes()).hexdigest()for p in ['docs/ai/CURRENT_STATE.md','unity_development_progress.md']};(O/'DOC_BASE544.json').write_text(json.dumps(base,indent=2));q=(P/'docs/ai/CURRENT_STATE.md').read_text(encoding='utf8');q=q.replace('아래 §252 | 348활성;543옷선택수정81포즈·제품OFF','아래 §253 | 348활성;543/544옷경계81포즈·제품OFF',1);assert len(q.encode('utf8'))<=12288;(O/'CURRENT_STATE544.md').write_text(q,encoding='utf8')
