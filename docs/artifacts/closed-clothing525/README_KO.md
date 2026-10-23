# 525: MASK 입력·연속 표면 공급 국소 확인, 성능 실패로 미채택

2026-10-23. 525는 작업 기록 번호다. 기본 OFF이며 전신 공통 경계 구현/전체 가시 해결/픽셀아트 시간 품질 통과가 아니다. 524 실패 증거와 da3f5fd를 보존한다.

## 실제 결과

동일 실행의 실제 Walk33/34/35 OFF/ON 3쌍을 모두 보존했다. phase .412502527/.425002575/.437502623, 자세·카메라·조명·시간 일치. 34번 소매 논리셀(198,85)의 source packet primitive724/depth13.90072155를 허용하지 않는 독립 디자인 경계는 유지된다. 해당 셀 면적 .4428685, 선택 false. 최종 0/1/0 가시는 0/0/0으로 바뀌었다. 1논리셀은 명목상2×2화면픽셀이다. 그 외 모든 가시 원인이 같다는 뜻은 아니다.

기존 공급 누락3/3/2셀은 0/0/0이다. 실제 불투명 표면이 있는 빈 셀2/1/1개는 원래 UV·법선·접선·깊이·primitive를 공급했다. source primitive/UV/depth와 GPU centre packet, 최종 clothing owner가 모두 일치했다. 나머지4관측셀은 MASK를 고려한 영역에서 제외됐다. 예: 33번(227,94)의 fitted area는 .822754→.0485211로 변경되어 제외됐다. 이것은 단일 UV 조사로 한 셀을 지운 결과가 아니라 원본 UV alpha 경계의 투영→곡선→영역 선택 결과다.

선택 영역 미채움0, 최종 영역 밖 clothing0, 마지막 gate 위반0. 이는 제한된3쌍의 버퍼 계약 검증이며 실제 시간 품질 전체 합격이 아니다. 기존 중심점 raster mask를 복사하거나 고정 좌표/프레임을 예외 처리하지 않았다.

## 두 책임과 실제 비용

OpacityRegion525는 원본 텍스처 texel중심 alpha를 고정 대각선 선형 필드로 나타내고 material cutoff/.alpha/UV ST를 포함한 등고선을 원본 UV삼각형과 교차한다. barycentric anchor/동일 rest위치+skin weight 공유변을 사용한다. 원본 기하 투영으로 갱신한 뒤 기존 vector union→RDP .1875논리셀→면적/둘레 joint 선택→공통C를 사용한다. GPU bilinear alpha의 곡선과 선형 texel 경계가 수학적으로 같다고 주장하지 않는다.

정적 전처리711.07ms, 전체 texture contour28,382선분, 삼각형 경계12,931조각/7,742anchor다. 실제 포즈 source 경계2602/2583/2581점이 최종 fit38/46/44점이 되었다. steady geometry1751.69/1748.68ms로 **실시간 채택 불가**다. 이 텍스처 해상도 경계 확장 경로는 더 최적화·확장하지 않았다. 새 정확면적 엔진/시간 선택기/SS를 추가하지 않았다.

ClothSurface525는 기존 두 렌더 사이의 빈 선택 셀에만 실제 가시 옷 표면점을 연결한다. 원본 삼각형과 셀의 교차/가까운 점을 쓰고, 같은 source ray의 실제 모든 actor triangle UV alpha/cull/depth를 비교한다. 불확실한 alpha는 통과하지 않는다. source 위치의 소유권과 명암을 설계 셀로 옮기며 첫 렌더에서 다른 부위가 차지한 셀은 공급 대상에서 제외한다. 기존 Probe502/Legacy502 shader와 기존 attachment를 재사용한다. 새RT0/새renderpass0/RGB복사층0. CPU packet build24.31/16.43/13.75ms. Editor RenderFrame OFF/ON은616.49/2783.96,744.63/2091.91,269.64/2056.10ms이며 Player FPS나 GPU 단독 비용이 아니다. 별도 head212ms와 혼합하지 않는다.

GPU RAW는 실제 sourceUV의 원본 texture 선형RGB와 반정밀도/texture format 반올림 범위에서 대응한다. 이후 기존 profile 명암 및 외곽선/cream palette가 최종 RGB를 만든다. 예:33(199,89) RAW(.94385,.83984,.76807), Prepare(.67957,.60469,.55301), 최종(.12744,.06848,.04817). 주변 화면 RGB를 복사한 값이 아니다.

## 회귀와 남은 범위

실제 전신3포즈의 옷·소매/손/다리·머리·비율을 비교했다. body33(225,67)은 source packet/Prepare RGB가 그대로인 채, 공통 외곽선 이웃관계 변화로 OwnerLines reason/outer가0/0→1/1이 되어 기존 .55 외곽선 계수가 적용됐다. 원본색이나 얼굴 재질 입력 오염이 아니다. 전체 애니메이션에서 이 디자인 변경을 채택할지는 미검증이다.

얼굴의 실제 가시4/5/8셀 RGB 변경0. faceRAW/META/Prepare/base 및 material/shader/texture/RT/culling/renderer/MPB/합성 상태는 OFF/ON과 시작/종료 전후 같다. 회색은 이번3포즈에서 미재현이며 반복 회색 문제 해결 표기 금지다.

성능 gate 실패 때문에 전체 Walk는 실행하지 않았다. 추가 패치/촬영 루프를 시작하지 않았다. 기본 OFF와 초기 Edit를 직접 확인했고, 입력/Animator Idle speed1 loc0/자동시계/capture0/후크/배경실행을 복원했다. GameMap1 dirty false, compiling/updating false. 사용자 QualitySettings/TimeManager 수정은 해시로 보존한다.

기존 활성44d13c0, OFF인 곡선511/source-ray513, 종료한 전역arcDP 확장, 내부색head11+body1, headpacket약212ms는 별도다. 전체 공통 boundary-first 목표의 현재 검증 범위는 옷만이며 머리 실험을 전신 완료로 보지 않는다.

## 증거와 전달

REVIEW525.json, ADJACENT_ANALYSIS525.json, COLOUR_INPUT525.json, IMPLEMENTATION_CONTRACT_KO.md 및 정상속도 모든3프레임 WebP/검수GIF/전신PNG. WebP17/16/17ms, GIF250ms이며35→33은 짧은 구간 재시작이다. 전체Walk GIF가 아니다. 원 float/PNG/face상태/packet/비용 자료는 C:/Users/JG/Documents/Codex/2026-10-07/task/Current472/Cloth525/Adjacent 에 보존한다. Library403은 우회·재시도하지 않아 로컬 전달만 완료했다.

초기 진단 동적컴파일은 Mesh 이름/SortedSet 참조 오류로 미실행이었다. 정식 Unity 컴파일 후 세 저장 포즈 폐합은 확인됐다. Edit alpha readback에서 기존 Destroy helper 경고가 발생한 최초 조회는 부분 실행으로 기록했으며, 새525 alpha 읽기는 Edit에서 DestroyImmediate/RT원상복구를 사용한다. 후속 실제Play3쌍은 CAPTURED 및 직접 복원 확인됐다. stale PID24412 ENOENT 요청은 미실행, 현재 PID22792 공식 연결로 복구했다.
