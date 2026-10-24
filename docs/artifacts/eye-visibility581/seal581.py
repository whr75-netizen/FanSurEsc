from pathlib import Path
import csv,json,hashlib
R=Path(__file__).parent;P=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game')
def J(n):return json.loads((R/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=J('ANALYSIS581.json');trial=J('APERTURE581.json');lash=J('LASH_EXACT_ANALYSIS581.json')
irisRows=J('SUBPIXEL_REPLAY581.json');lashRows=J('LASH_EXACT_SUBPIXEL_REPLAY581.json')
assert all(f['allWinnerReplayMatchesGPU'] for f in base['frames']+lash['frames'])
assert all(z[k]==0 for f in base['frames']+lash['frames'] for z in f['savedInputs'].values() for k in ['EYE_INTRINSIC_differentCells','EYE_VISIBLE_differentCells'])
assert all(f['rawSourceSupportSameOFFON']for f in base['frames']+lash['frames'])
def get(rows,frame,x,y,side='ON'):return next(z for z in rows if z['originalFrame']==frame and z['x']==x and z['y']==y and z['side']==side)
critical=get(irisRows,17,224,53)
sample1=next(z for z in critical['samples']if z['k']==1)
sample12=next(z for z in critical['samples']if z['k']==12)
raw=list(csv.DictReader((R/'Runtime581/Samples17To19/000_ON_SUBPIXELS581.tsv').open(),delimiter='\t'))
raw1=[z for z in raw if z['cellX']=='224'and z['cellY']=='53'and z['k']=='1'and int(z['support'])in[0,1,2]]
def short(z):return {k:z[k]for k in ['originalFrame','x','y','side','visibleCounts','intrinsicCounts','replayedWinner','replayedFinalVisible','gpuVisible','lateOcclusion']}
sourcePaths=['Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeFeature348.compute','Assets/EUnityValidation01/EyeBoundaryRestore348/Runtime/EyeFeature348.cs','Assets/EUnityValidation01/HeadLocal367/Runtime/EyeRenderer367.cs','Assets/EUnityValidation01/HeadRegion502/Runtime/HeadRegion502.cs','Assets/EUnityValidation01/HeadRegion502/Shaders/LegacyProvider580.shader']
sources={n:{'sha256':sha(P/n),'bytes':(P/n).stat().st_size}for n in sourcePaths}
body=[]
for f in [34,35,36]:
 rows=[get(lashRows,f,x,52)for x in [219,220]]
 body.append({'originalFrame':f,'cells':[short(z)for z in rows],'visibleLashSupportAcrossTheseCells':sum(z['visibleCounts'][5]for z in rows),'lashSamples':[{'x':z['x'],**s}for z in rows for s in z['samples']if s['label']==5]})
assert [z['visibleLashSupportAcrossTheseCells']for z in body]==[4,4,5]
record={'record':581,'productSourceChanged':False,'preservedSourceFix580':'c216d3ebdc4922730dceb74500e8c9ff46fdb2f0','preservedHEAD':'807e783be9dbeb537ccf2af78000d13e2a259bc9','iris':{'observation':'Stable eye2 iris visible logical-cell count 1,0,1 in original ON17..19. Native0,0,1.','firstSelectionChange':'EyeFeature348.compute Evaluate/Classify then Choose, before final Merge. Not a colour-provider regression.','cells':[short(get(irisRows,f,x,53,s))for f in [17,18,19]for x in [223,224]for s in ['OFF','ON']],'skinSupportedIrisSample':sample1,'rawSameRaySurfaces':raw1,'nativeHairBlocksFifthCandidateSupportAtK12':sample12,'interpretation':'Source support is first valid skin/sclera/iris/eyeline, not frontmost eye-aperture ownership. Stylized Classify labels skin as iris. This plus different native/selected-hair occlusion changes 4 versus5 support, and per-cell Choose loses a moving subpixel feature. Physical hair occlusion also exists at adjacent cell223,53; do not remove that valid layer or call all changes one cause.'},'lash':{'observation':'Stable eye2 upperLash visible-cell count1,0,1 in original OFF and ON34..36.','firstSelectionChange':'Choose per-cell total>=4 and iris>=5 priority, not late hair/brow/body occlusion.','cases':body,'scope':'Exact stored-angle/phase replay. Complete saved intrinsic/visible ROI agrees with original all3frames/bothmodes. This is a causal pose replay, not a new continuous rotation quality pass.'},'offlineApertureTrial':{'applied':False,'definition':'Front-to-back same-ray alpha/transmittance of source sclera, skin, iris. Eye contribution blocked by nearer opaque skin; only feat1..4 weights multiplied.','targetCountsBefore':'ON cell224,53 at17:iris5,sclera3','targetCountsAfter':'ON cell224,53 at17:iris4,sclera2,Choose0; OFF also changes sclera1 to fallback0.','decision':'Not adopted. It clips the already designed independent V11 eye aperture to raw mesh surfaces and changes sclera too. No normal-view/style-regression evidence supports that contract change. This does not fix lash per-cell allocation. No product patch or threshold/history change made.'},'validation':{'irisWinnerReplayMatched':24,'lashWinnerReplayMatched':108,'originalIntrinsicAndVisibleRoiDifferenceCells':0,'sourceSupportsOFFONBitEqual':[0,1,2,3,5,6],'candidateRawHairSupport4':'Intentionally not rendered when HeadRegion502.Ready; use selected HairMETA in replay.','irisRunStatus':base['captureStatus'],'irisCompletePairFiles':3,'irisThirdPair':'Files saved before diagnostic Euler-step precision guard failed; not a formally CAPTURED3 run.','nearbyLashRun':'Lash34To36:nominal151deg instead of original150.856033deg; retained as nearby diagnostic and excluded from exact replay claims.','exactLashRunStatus':lash['captureStatus'],'productCompileRequired':False,'newWholeLoopCaptured':False,'newProductFixValidated':False},'sources':sources,'separateUnresolved':['Body internal-line palette3 samples from580','Player/runtime performance and allocations','General eye feature temporal/design quality outside investigated events'],'nextContract':'Keep normalized model-bound design curves, real occlusion, source pigment and whole-cell ownership in one representation. Per-cell Choose lacks inter-cell feature allocation. A raw-mesh aperture clamp or scalar threshold change is not established as a sufficient preserving fix.'}
(R/'CAUSE581.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
text='''# 581 홍채·속눈썹 출몰 원인 확인

580 얼굴 색 공급 수정(c216d3e)은 보존했다. 이번에는 제품 소스를 바꾸지 않았다. 원인 판정은 완료했지만 눈의 시간 품질 수정·전체 회전 합격은 아니다.

## 홍채 17~19

실제 580 회전의 눈 ID 2에서 후보 홍채 셀 수가 1→0→1이다. head(224,53)의 가시 홍채 지지가 5→4로 줄어 `Choose`의 5개 조건을 넘나든다. 17번의 k1은 피부 표면을 `Classify`가 홍채로 분류한 표본이다. 같은 시선에서 피부 깊이 13.7255764, 홍채 13.7275229(알파 0.0164492261), 흰자 13.7326155이므로 불투명 피부가 앞에 있다. 지원 표면은 깊이순 눈 개구부가 아니라 첫 유효 skin/sclera/iris/eyeline이다.

17번 k12는 원본 머리 깊이 13.6870002747이 눈 평면 13.7188501358보다 앞이다. 원본 경로는 이를 가리고 후보는 선택된 머리 셀을 사용하므로 이 표본을 지원한다. 따라서 원본 홍채4, 후보5가 된다. 인접 head(223,53)는 원래 머리 면적 .9925816→.7614231→.4844282에 따른 머리 셀 선택1→1→0도 개입한다. 실제 가림을 제거해서는 안 된다. 전체 사건을 색 오류나 단일 물리 가림으로 설명할 수 없다.

같은 입력을 재계산한 24개 관측 셀의 최종 feature가 GPU와 모두 일치했다. 원본 영상 대비 저장 intrinsic/visible ROI는 두 모드·세 포즈 모두 차이0이다. 진단 실행은 세 쌍 파일 저장 뒤 세 번째 회전 오차 검사에서 실패했다(약 .0001도 허용 폭의 float 문제). status는 FAILED/poses2를 그대로 보존했고 CAPTURED3으로 세지 않는다.

## 속눈썹 34~36

눈 ID 2에서 원본과 후보 모두 1→0→1이다. 실제 기록 각도는 150.856033,152.350616,153.846115도이다. 초기 명목각151도 조회는 약 .14도 달라 정확 재현에서 제외하고, 실제 각도로 다시 동결 포즈를 조회했다. 이 조회는 실제 회전 품질 시험을 대신하지 않는다.

| 프레임 | head(219,52) | head(220,52) | 두 셀 가시 속눈썹 지지 합 |
|---|---|---|---|
| 34 | 홍채7,속눈썹1 → 홍채 | 흰자2,속눈썹3 → 약한 선 | 4 |
| 35 | 홍채5,흰자1,속눈썹2 → 홍채 | 흰자1,속눈썹2 → 없음 | 4 |
| 36 | 홍채4,흰자1,속눈썹3 → 약한 선 | 속눈썹2 → 없음 | 5 |

표본은 피부 support0이며 가시 weight1이고 머리/눈썹/몸 앞가림이 없다. 합계4가 유지돼도 3+1이 2+2로 분산되면 셀별 선택은 선을 전부 버린다. `Choose`의 total>=4, iris>=5 우선순위, weakUpperLash>=3 조건에서 최초 소실한다. 후단 합성이 선을 지운 사건이 아니다. 108개 관측 셀의 계산이 GPU와 일치했고 원본 영상 intrinsic/visible 전체 저장 ROI도 두 모드·세 포즈 모두 차이0이다.

## 적용하지 않은 대조와 남은 계약

기존 source 흰자/피부/홍채를 깊이순 알파 합성해 개구부 지지로 쓰는 오프라인 대조를 한 번 수행했다. 17번 후보 홍채5→4, 흰자3→2가 되어 feature0으로 바뀌고 원본 흰자도 없어졌다. 원본 표면으로 독립적인 V11 디자인 눈 영역을 제한하는 변화이므로 제품에 적용하지 않았다. 기존 `referenceSocketMetres`와 style 정규화는 원본 눈 표면의 정확 복사를 의미하지 않는다. 속눈썹 분산 손실도 이 대조로 해결되지 않는다.

현재 부족한 것은 추가 RGB 필터가 아니라 정규화된 디자인 곡선·실제 가림·픽셀 feature 배정을 같은 계약으로 연결하는 선택이다. 기존 `Choose`는 이웃 셀로 나뉜 동일 특징의 지원을 공유하지 않는다. 5/4/3 상수 변경이나 이전 프레임 고정만으로 공통 보존 규칙이 성립했다고 주장하지 않는다. 다음 수정은 이 계약을 기존 선택기 안에서 다루고 홍채·속눈썹과 정상 세 방향 눈 크기를 함께 비교해야 한다. 이번 기록에 새 선택기를 구현한 것은 아니다.

## 실제 코드와 좌표

- `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeFeature348.compute`: `Classify`, `Choose`, `Evaluate`의 support→occlusion→histogram→winner→late composition→`Merge`.
- `Assets/EUnityValidation01/EyeBoundaryRestore348/Runtime/EyeFeature348.cs`: 모델 폐경계 바인딩과 rest-head 축, V11 style 크기, 4×4 지원 렌더 ROI.
- `Assets/EUnityValidation01/HeadLocal367/Runtime/EyeRenderer367.cs`: Samples(550), Candidate(551). HeadRegion 준비 시 raw hair S4를 생략하고 선택 HairMETA를 사용한다.
- head 좌표는 480×272 논리 격자, 한 셀의 4×4 표본이다. 출력960×544에서 한 셀은2×2 화면 픽셀이다. main 위치는 저장 PARAMS의 offsetX/offsetY로 변환한다. 좌표·프레임은 관측 위치이며 제품 분기가 아니다.

제품 소스580/547/544와 사용자 설정은 보존했다. 내부선 팔레트3건, 일반 실행 성능/할당량, 미검증 눈 시간 품질은 별도 미해결이다. 새 전체 루프·성능 변경·P 접근·Library403 재시도는 하지 않았다. 원본 PNG와 작은 원인 표본은 작업 폴더에만 보존하고 Git에 대량 복제하지 않는다. 도구/권한 차단은 없다.
'''
(R/'RESULT581.md').write_text(text,encoding='utf-8')
(R/'CHECKPOINT581.md').write_text('''# 581 재개 지점

580 수정 보존, 제품 소스 변경 없음. CAUSE581/RESULT581을 먼저 읽는다. iris17~19 원인: 피부도 정규화 홍채 support로 집계 + 실제/선택 머리 가림 차이 + Choose5/4 경계. lash34~36 원인: 가시 속눈썹 지지 합4가 셀3+1→2+2로 분산되어 Choose가 전부 생략. 실제 기록각 동결 조회로 원본 눈 ROI 차이0, 재계산24+108셀 전부 일치.

개구부 alpha 대조는 오프라인만 수행했고 원본 흰자도 줄어 제품 미적용. 임계값·색·히스토리 변경 금지. 다음은 정규화된 디자인 곡선과 실제 가림을 보존하며 이웃 셀 feature 배정을 기존 선택기 안에서 일관되게 만드는 최소 계약이다. 새 전체 루프 전에 홍채/속눈썹 및 정상 세 방향 반례가 필요하다. Body 내부선3건·성능은 별도.

Runtime581/Samples17To19는3쌍 파일 완료 뒤 float step guard FAILED/poses2. Runtime581/Lash34To36는 명목각 .14도 차이의 인접 진단이므로 exact 근거 제외. Runtime581/LashExact34To36는 실제 기록각·phase 재현3쌍 CAPTURED. 이들은 기존 실제 회전의 인과 조회이며 새 실제 회전 품질 합격이 아니다. 반복 캡처하지 않는다.
''',encoding='utf-8')
(R/'CENTRAL_GRAPH_UPDATE581.proposal.json').write_text(json.dumps({'record':581,'originalCentralGraphWritten':False,'productSourceChanged':False,'nodes':[{'id':'eye-iris-17-19','state':'CAUSE_CONFIRMED_NOT_FIXED','input':'580 original turn +581 matched support query','code':'EyeFeature348.Evaluate/Classify/Choose','proof':'CAUSE581.json iris','output':'skin-labelled iris support and 4/5 per-cell visibility transition'},{'id':'eye-lash-34-36','state':'CAUSE_CONFIRMED_NOT_FIXED','input':'580 actual recorded angles +581 exact pose query','code':'EyeFeature348.Choose','proof':'CAUSE581.json lash','output':'same total4 visible lash supports redistributed3+1 to2+2; all pixels discarded'},{'id':'eye-preserving-common-selection','state':'NOT_IMPLEMENTED','input':'Existing normalized model-bound feature curves + same-ray real occlusion','invariants':['No RGB/history/coordinate exceptions','Preserve designed eye size and true foreground occlusion'],'next':'bounded spatial allocation contract before product edit, then adjacent real rotation +80/170/260 regression'}]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sourceChanged':False,'irisReplay':24,'lashReplay':108,'exactRoiDifference':0,'lashSupport':[z['visibleLashSupportAcrossTheseCells']for z in body],'output':'CAUSE581.json / RESULT581.md / CHECKPOINT581.md'},ensure_ascii=False))
