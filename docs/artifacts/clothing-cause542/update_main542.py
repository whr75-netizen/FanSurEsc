from pathlib import Path
import html,hashlib,json
O=Path(__file__).resolve().parent;M=Path('C:/Users/JG/Desktop/작업폴더/메인.html');b=M.read_bytes();assert b'id="elbow542Status"'not in b
anchor=b'<div style="display:grid;grid-template-columns:';start=b.index(b'<section id="current540"');at=b.index(anchor,start);u=lambda p:html.escape(p.as_uri(),quote=True)
note=f'''<aside id="elbow542Status" style="background:#fff0e8;border:2px solid #c45634;padding:10px;margin:10px 0"><b>542 정정 — 캐릭터 기준 왼쪽 팔꿈치 가시가 남아 있습니다.</b> Body3 겉옷/role10/왼팔part2로 Clothes 적용 부위입니다. 저장된540의64→65→66번에서 논리(201,73),(201,74)가1×2셀(실제2×4px) 밝은 돌출로 먼저 나온 뒤 외곽선색으로 바뀝니다. 선택마스크 자체가 돌출을 허용하며,65번에는 thin 예외로 선을 칠하지 않습니다. 경계밖쓰기0은 이 문제를 검사하지 못했습니다. 새 패치/새 전체촬영 없이 원인을 확인했으며 아직 수정 완료가 아닙니다. <a href="{u(O/'ELBOW_EVENT542_65_MARKED.png')}">전신＋확대64/65/66</a> · <a href="{u(O/'ELBOW_ALL542.webp')}">기존81프레임 왼팔 확대</a> · <a href="{u(O/'README542.md')}">실제 수치·원인·Body0 조사 보존</a></aside>
'''.encode();a=b[:at]+note+b[at:];assert a.replace(note,b'',1)==b;(O/'main542.html').write_bytes(a);(O/'MAIN542.json').write_text(json.dumps({'target':str(M),'before':hashlib.sha256(b).hexdigest(),'after':hashlib.sha256(a).hexdigest(),'onlyUnresolvedCaseAsideAdded':True},ensure_ascii=False,indent=2),encoding='utf8')
print('542 status aside prepared;540 full GIF/modes unchanged')
