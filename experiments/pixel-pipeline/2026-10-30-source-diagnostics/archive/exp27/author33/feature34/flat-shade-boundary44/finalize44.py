"""Verify/export existing candidate without new curve search or rendering."""
from pathlib import Path
import sys, json, hashlib, base64, subprocess, collections, re
import numpy as np
from PIL import Image, ImageDraw
O=Path(__file__).resolve().parent;R=O.parent
sys.path.insert(0,str(R))
import candidate as c
from diagnose44 import INPUT,load,sha,dump,components
from curves44 import boundary_image

data=load(INPUT/'INPUT.json');binding=load(O/'SOURCE_BINDING.json');result=load(O/'RESULTS.json');paths=load(O/'CURVES.json')
layers=np.load(O/'LAYERS.npz');mask=layers['mask'];g=layers['g'];q=layers['Q'];after=layers['correctedQ']
original=np.frombuffer(base64.b64decode(data['originalRGBA']),np.uint8).reshape(80,64,4)
outside=~np.repeat(np.repeat(mask,2,0),2,1)
checks=[]
def check(name,value):
 assert value,name
 checks.append({'name':name,'pass':True})

check('source/input/palette/geometry packet binding unchanged',sha(INPUT/'INPUT.json')==binding['inputSHA256'] and sha(INPUT/'PALETTE_DISTINCT.json')==binding['paletteSHA256'] and sha(R/'ribbon-path/GEOMETRY_PACKETS.json')==binding['packetsSHA256'])
expected_q=np.sum(g[...,None]>=data['thresholds'],-1);expected_q[~mask]=-1
check('all original Q values preserved separately and exactly equal count(g>=threshold)',np.array_equal(q,expected_q))
check('all source g samples preserved exactly',all(g.flat[i]==cell['g'] for i,cell in enumerate(data['cells']) if cell))
before=np.asarray(Image.open(O/'before-RGB-1x.png').convert('RGBA'));corrected=np.asarray(Image.open(O/'corrected-RGB-1x.png').convert('RGBA'))
check('before image exactly reproduces upstream flat-distinct diagnostic',np.array_equal(before,np.asarray(Image.open(INPUT/'flat-distinct-1x.png').convert('RGBA'))))
check('outside hair mask and all alpha unchanged',np.array_equal(corrected[outside],original[outside]) and np.array_equal(corrected[...,3],original[...,3]))
P=np.array(result['paletteRGB8'],np.uint8)
for y,x in np.argwhere(mask):
 block=corrected[y*2:y*2+2,x*2:x*2+2,:3]
 assert np.all(block==P[after[y,x]])
check('every final 2x2 cell exactly equals P[correctedQ], no RGB averages or extra colours',True)
check('changed-cell log is complete',set(np.flatnonzero(q!=after))==set(p['index']for p in result['changes']))
check('all changed cells have same-chart measured native stage/visible witness',all(p['sourceWitnesses'] and all(w['chart']==p['sourceChart'] and w['Q']==p['afterQ'] for w in p['sourceWitnesses'])for p in result['changes']))
check('all source witnesses stay within the declared spatial correction corridor',all(w['distanceOutsideCell']<=2**-.5+1e-10 for p in result['changes']for w in p['sourceWitnesses']))
check('changed-cell g interval errors reported, not hidden as primary-Q correctness',all(p['addedGIntervalDistance']>=0 for p in result['changes']))
for name in ['before','corrected']:
 a=Image.open(O/f'{name}-RGB-1x.png').convert('RGBA');b=Image.open(O/f'{name}-RGB-8x.png').convert('RGBA')
 check(name+' exact nearest 8x RGBA',a.resize(b.size,Image.Resampling.NEAREST).tobytes()==b.tobytes())
 boundary_image(q if name=='before'else after,mask).save(O/f'{name}-boundary.png')
boundary_image(after,mask,paths).save(O/'curve-reference-overlay.png')
oldcc,newcc=components(q,mask),components(after,mask)
olds={(a['Q'],tuple(a['cells'][0]))for a in oldcc if a['size']==1};news={(a['Q'],tuple(a['cells'][0]))for a in newcc if a['size']==1}
check('no new standalone cells introduced by final candidate',not(news-olds))
check('all six original singleton locations retained, not silently called noise',olds<=news and len(olds)==6)
check('reverse scan proof from original candidate run',result['reverseScanExact'])
bad=load(O/'unconstrained-failure-RESULTS.json')
check('failure counterexample retained and final excludes its thin-connection cut',bad['afterSingletons']==7 and all(p['index']!=937 for p in result['changes']))

# Reuse the existing palette implementation. Spacing is a colour-only parameter.
node=Path('C:/Program Files/nodejs/node.exe')
js='''const fs=require('fs'),p=process.argv[1],M=require(p+'/palette_math.cjs'),P=JSON.parse(fs.readFileSync(p+'/PALETTE_DISTINCT.json','utf8'));console.log(JSON.stringify([0,.5,1,1.5].map(m=>({m,P:[0,1,2,3].map(k=>M.paletteValue(P,23,k,m).rgb)}))));'''
spacing=json.loads(subprocess.check_output([str(node),'-e',js,str(INPUT)],text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
for s in spacing:
 a=original.copy();pal=np.array(s['P'],np.uint8)
 for y,x in np.argwhere(mask):a[y*2:y*2+2,x*2:x*2+2,:3]=pal[after[y,x]]
 check(f'spacing {s["m"]}: fixed Q/Qprime/source maps; every pixel in that supplied palette',all(tuple(a[y*2,x*2,:3]) in set(map(tuple,pal))for y,x in np.argwhere(mask)))
 s['outputHairRGBCount']=len(np.unique(a[::2,::2,:3][mask],axis=0))
dump('SPACING_INDEPENDENCE.json',{'palettes':spacing,'QSHA256':hashlib.sha256(q.tobytes()).hexdigest(),'correctedQSHA256':hashlib.sha256(after.tobytes()).hexdigest(),'noRegionRecalculationFromPalette':True})

# Small fixed examples test shared-face complement and thin connection rejection,
# without treating synthetic success as actual motion or native visibility proof.
from feature_curves import winding
old=np.array([[1,0],[1,2]],float);new=np.array([[1,0],[2,0],[2,2],[1,2]],float)
Y,X=np.indices((2,3));points=np.c_[X.ravel()+.5,Y.ravel()+.5];delta=winding(new,points)-winding(old,points)
a=(points[:,0]<1).astype(int)+delta;b=1-(points[:,0]<1).astype(int)-delta
check('shared path updates two faces oppositely with no gap/overlap in fixed example',np.all(a+b==1)and np.all((a>=0)&(a<=1))and np.all((b>=0)&(b<=1)))
old_triangle=np.array([[0,0],[2,0],[2,2]],float)
check('reversing an oriented path reverses winding, no hidden RGB operation',np.array_equal(winding(old_triangle,points),-winding(old_triangle[::-1],points)))

hashes=load(R/'eye-cache42/VERIFIED.json')['productInputSHA256']
check('eleven tracked product/template inputs unchanged',all(sha(p)==h for p,h in hashes.items()))
dump('VERIFIED.json',{'passed':len(checks),'checks':checks,'newUnityCalls':0,'newCaptures':0,'productEdits':0,'DesktopWrites':0,'temporalVerification':False})

# Show actual output raster separately from smooth guide overlays.
for name in ['before','corrected']:
 im=Image.open(O/f'{name}-labels-8x.png').convert('RGBA');draw=ImageDraw.Draw(im)
 for x,y in [s['cell']for s in load(O/'SINGLETON_CAUSES.json')]:
  draw.rectangle((x*16,y*16,(x+1)*16-1,(y+1)*16-1),outline=(255,70,70,255),width=2)
 for p in result['changes']:
  x,y=p['xy'];draw.rectangle((x*16,y*16,(x+1)*16-1,(y+1)*16-1),outline=(20,255,160,255),width=3)
 im.save(O/f'{name}-marked.png')
 # Literal six-cell case ROI plus the changed boundary; nearest crop only.
 if result['changes']:
  x,y=result['changes'][0]['xy'];src=Image.open(O/f'{name}-RGB-1x.png').convert('RGBA');roi=src.crop(((x-3)*2,(y-3)*2,(x+4)*2,(y+4)*2));roi.resize((224,224),Image.Resampling.NEAREST).save(O/f'{name}-ROI.png')

table=[]
for s in load(O/'SINGLETON_CAUSES.json'):
 prev=s['priorCentreSampling'];d=s['diagnosis'];table.append(f'| {s["cell"]} | {s["Q"]} / {s["g"]:.8f} | {prev["sourceCentreQ"]}→{prev["selectedQ"]} | {d["actualVisibilityEdges"]} | {s["sameChartFineQCounts"]} |')
accepted=[p for p in paths if p['accepted']]
report=f'''# 단색 명암 경계 후보 — 전체 정돈 미완

결론: 실제 Q 영역 마스크의 공유 경계부터 cubic 근사와 격자 재배치를 구현했고, 원래 팔레트로 출력했다. 최종 무회귀 후보는 **{result['correctedCells']}셀 변경, 11→{result['afterQRegions']}영역, 단독6→{result['afterSingletons']}셀**이다. 전체가 깨끗해졌다는 결과가 아니다. 9개 공유 경로 중 {len(accepted)}개만 실제 셀 변경까지 통과했다. `CURVES.json`, `LAYERS.npz`, `VERIFIED.json`이 대응 근거다.

## 6개 단독 셀의 원인

모든 g는 원본 측정 pool에서 확인됐고 Q 산술은 정확하다. 단색이므로 텍스처 색이나 RGB 팔레트가 이 Q 분단을 만든 것이 아니다. 현재 선택 packet의 실제 투영점 간 geometry를 다시 계산한 102개 Q 경계 중 같은 front chart39, 깊이 연속 owner교환5, 실제 앞뒤 가림55, 투영 빈틈3이다. 이 hair-only 분석이 face/body의 숨은 가림까지 증명하지는 않는다.

| 논리 좌표 | Q / 실제 g | 원래 중심→선택 Q | 인접 실제 가림/빈틈 변 | 같은 chart 내부 native Q 지원 |
|---|---|---|---:|---|
{chr(10).join(table)}

(7,29)는 표면 선택으로 g .06597649/Q3→.02827420/Q2가 되었다. 그 결과 예전 2셀 Q3 영역의 (7,30)도 단독이 된다. (7,30) 자체 g/Q는 바뀌지 않았다. 두 위치는 표본 선택의 분절 기여를 구체적으로 확인한 사례다. 다른 네 단독은 선택 이전에도 존재했다. 모두 '임계값 오류'나 '지워야 할 잡음'으로 분류하지 않았다. `SINGLETON_CAUSES.json`에는 각 셀의 이웃/실제 가림/표본/지원값이 있다.

## 실제 알고리즘과 확인한 실패

색이나 명암을 평균하지 않는다. Q의 두 라벨 사이 경계를 한 번만 만들고 두 면이 반대 방향으로 공동 사용한다. 마스크/접합 끝점은 고정한다. 깊이가 연속인 경우만 실제 g 교차점으로 guide를 잡고, 가림 변에서는 g를 섞지 않는다. coarse 격자의 계단 코너를 모두 원래 특징으로 고정하지 않았다. guide 근사→별도 4연결 격자 재배치→반대 winding에 의한 양쪽 라벨 채움→같은 P[Q'] 출력이다.

처음 곡선 재근사만 한 대조는 출력 변화0이었다. coarse 입력인데 native 간격의 작은 허용 오차로 계단까지 따라갔고, 연속 곡선을 셀 중심에서 판정하는 것만으로는 기존 raster를 바꾸지 못했다. 이 대조는 `fit-only-control-RESULTS.json`에 보존했다.

다음 무제약 곡선 raster는 (9,29)를 Q1→Q2로 바꿔 (8,29)의 유효 Q1 셀을 새로 고립시켰다. 단독6→7, 영역11→12의 **실패**다. 곡선 접선 오차가 줄었어도 채택하지 않았다. 원본/native g 지지가 있는 얇은 연결을 끊는 제안은 거부했다. 모든 기존 component/구멍을 무조건 동결하는 규칙은 넣지 않았다. 실패 PNG와 수치는 `unconstrained-failure-*`로 보존했다.

## 남긴 실제 변경

{json.dumps(result['changes'],ensure_ascii=False,indent=2)}

이 변경 경로의 고정 reference arclength 접선 오차는 {accepted[0]['fixedArclengthTangent']['before'] if accepted else None}→{accepted[0].get('constrainedMetrics',{}).get('tangent') if accepted else None}다. 위치/라벨/원래g 오차도 함께 기록했고, 둘레 감소만을 성공 기준으로 쓰지 않았다. original Q와 g는 불변이며 Q'는 별도다.

긴 Q2/Q3 경로는 처음에 source 지지를 '기존 셀 내부'에서만 찾는 제약에 막혔다. 그러나 (18,14)의 같은 chart110002에서 셀 바깥0.500577칸에 실제 Q3/g=.05981928 표본이 있고 그 사이 가림이 없음을 확인했다. 움직일 경계를 기존 coarse 칸으로 동결한 것이 과도했다. 선언한 같은 공간 보정 범위 안에서 실제 동일 표면의 지지를 쓰도록 고쳐 긴 경로의4셀 재배치를 검사했다. 다른 표면/색을 평균하거나 임계값을 바꾼 것이 아니다. 모든 witness 거리/가림/원래g 대비 오차를 공개했다.

그 밖의 6경로는 이번 공간 오차 범위에서 셀을 바꾸지 않았다. 한 경로는 source-constrained 격자 접합이 모호하여 제외했고, 얇은 연결을 끊던 경로도 제외했다. 즉 완성된 전두부 정돈이나 6개 섬 제거 결과가 아니며, 단색에서도 실제 표면 가림·선택점·명암 분포가 남는 병목이다. 원래6셀 모두를 잡음이라고 증명하지 않았다.

## 보존·검증·한계

원래 source/g/Q/geometry/P/카메라/2×2와 마스크 밖 RGBA를 보존했다. 모든 final hair RGB는 P[Q']에 정확히 속한다. 간격 m=0/.5/1/1.5는 기존 palette API로 색만 바꾸며 Q/Q'/곡선은 고정했다. 역순 제안과 출력이 같고 실제 PNG를 검수했다. 11개 추적 제품/템플릿 hash 변화0. Unity 호출·추가 캡처·Desktop/31/34/제품 변경0이며 현재 Editor/dirty를 새로 조회하지 않았다. 실제 움직임은 미검증이다.

이 후보를 더 강하게 만든다고 임의 오차나 면적 목표를 높이지 않았다. 남은 얇은 명암과 가림을 어느 정도 단순화할지의 판단 없이 기존 측정 g 특징을 일괄 삭제한 결과로 보고하지 않는다. 그래도 영역 보정 자체가 불가능하다는 뜻은 아니다. 이번 구현/반례/실제 변경은 명시적으로 분리된, 제한된 정지 프레임 결과다.
'''
(O/'REPORT_KO.md').write_text(report,encoding='utf8')
tr=''.join(f'<tr><td>{p["id"]}</td><td>{p["pair"]}</td><td>{len(p["raw"])-1}</td><td>{p["reason"]}</td></tr>'for p in paths)
page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>단색 명암 공유 경계44</title><style>body{{background:#1b2028;color:#eee;font:16px/1.7 system-ui;max-width:1600px;margin:auto;padding:28px}}a{{color:#9ecaff}}.warning{{background:#50362b;padding:15px}}.grid{{display:flex;flex-wrap:wrap;gap:20px}}article{{min-width:240px;max-width:510px}}img{{image-rendering:pixelated;max-width:100%}}.normal{{width:64px;height:80px}}table{{border-collapse:collapse}}td,th{{border:1px solid #667;padding:8px}}</style><h1>단색 명암 영역·공유 곡선 보정 후보</h1><p class="warning">전체 정돈 미완 · 최종 {result['correctedCells']}셀 변경 · 11영역/단독6셀 유지. 곡선 guide를 그린 것과 실제 raster 변경을 구분합니다. 제품 미적용, 실제 시간 안정성 미검증.</p><p><a href="REPORT_KO.md">원인·알고리즘·실패·한계</a> · <a href="CONTRACT_KO.md">계약</a> · <a href="SINGLETON_CAUSES.json">6셀 원인 수치</a> · <a href="EDGE_VISIBILITY.json">102변의 실제 가림 근거</a> · <a href="CURVES.json">공유곡선·결정·변경</a> · <a href="VERIFIED.json">검증</a> · <a href="SPACING_INDEPENDENCE.json">색 간격 독립</a></p><h2>같은 팔레트의 실제 최종 RGB</h2><div class="grid"><article><h3>원래 분류</h3><img class="normal" src="before-RGB-1x.png"><img src="before-RGB-8x.png"></article><article><h3>회귀 없는 제한 후보</h3><img class="normal" src="corrected-RGB-1x.png"><img src="corrected-RGB-8x.png"></article></div><h2>실제 출력 라벨·경계</h2><p>빨간 테두리=기존 단독6셀. 초록=실제 바뀐 셀. 회색은 명암 label 표시이며 실제 헤어색이 아닙니다.</p><div class="grid"><article><h3>Q</h3><img src="before-marked.png"></article><article><h3>Q'와 실제 경계</h3><img src="corrected-marked.png"></article></div><div class="grid"><article><h3>변경 부위 전</h3><img src="before-ROI.png"></article><article><h3>변경 부위 후</h3><img src="corrected-ROI.png"></article></div><h2>실패 반례를 숨기지 않음</h2><p>(9,29)의 연결을 끊어 새 단독 셀을 만든 후보: 11→12영역, 단독6→7. 아래는 미채택입니다.</p><img src="unconstrained-failure-corrected-labels-8x.png"><h2>곡선 참조선 — 실제 픽셀 경계와 구별</h2><p>초록은 채택한 경로, 푸른 선은 미적용 guide입니다. 이 선이 부드럽다고 최종 raster가 정돈됐다는 뜻은 아닙니다.</p><img src="curve-reference-overlay.png"><table><tr><th>경로</th><th>공유 Q</th><th>원래 변 수</th><th>판정</th></tr>{tr}</table><p>원본/Unity/제품/31/34/Desktop은 변경하지 않았습니다.</p></html>'''
(O/'INDEX.html').write_text(page,encoding='utf8')
missing=[s for s in re.findall(r'(?:href|src)="([^"]+)"',page)if ':'not in s and not(O/s).exists()]
assert not missing,missing
dump('MANIFEST.json',{'files':{p.name:sha(p)for p in O.iterdir()if p.is_file()and p.name!='MANIFEST.json'},'missingLinks':missing,'UnityCalls':0,'productEdits':0,'DesktopWrites':0})
print(json.dumps({'checks':len(checks),'candidateChanges':result['correctedCells'],'regions':result['afterQRegions'],'singletons':result['afterSingletons'],'missingLinks':missing,'output':str(O/'INDEX.html')}))
