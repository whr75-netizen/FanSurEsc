# 549–550: 손 표본 원인과 헤어 동일시선 가림 수정

2026-10-23. 547 옷 경계/544 최적화 유지. 550은 기본 OFF인 헤어 가림 후보이며 손/헤어 범위화 전체 완료가 아니다.

## 손 — 실제 원인 확정, 제품 변경 없음

실제 Walk32/33/34의 오른손 (207,111), owner8/Body0 primitive7997(source7998)을 조회했다. RightHand/RightLittleProximal 가중치의 **새끼손가락 기부**이며 끝이라고 가정하지 않는다. 1논리셀은 화면2×2픽셀이다.

33번 삼각형의 중심 (207.5,111.5) barycentric=(.332899474,.197204454,.469896072); 32·34는 중심이 모든 앞면 Body0 삼각형 밖이다. 알파255/cutoff.5, GPU depth14.01174545/UV(.356779695,.933251381). source raster→Prepare→최종에서 같은 표본이 유지된다. contour Map은0이며 기존 contour 추가는 owner11 소매만 대상으로 한다. 두 번의 작은 조회에서 centre0/5/6 버퍼는 전체 ROI 바이트 동일이다. 첫 JSON 기하 직렬화 누락은 보존하고 별도 binary 조회로만 보충했다.

기존540 Body0 시험에서는 같은 셀의 설계 면적 .447389096, 선택OFF였다. 이는 새547 기반 Body0 전체 검증 통과를 뜻하지 않는다. 정상 손끝 보존 및 아래 얼굴 소유권 범위가 남아 새 손 전용 제거 규칙을 만들지 않았다.

## 얼굴 — 가림 오류 가설 정정

35/36 (217,49),41 (218,49)의 native Body0 donor primitive9626뿐 아니라 **같은 head source ray**의 앞면 primitive9648까지 조회했다. alpha1, Head100% 가중치다. Body 깊이(main좌표)13.693165/13.692049/13.689439는 Face13.865363/13.864371/13.862361보다 앞이다. 목적 셀 중심에는 몸 표면이 없으나 donor·head source ray에는 존재한다.

따라서 시선 불일치만 고치면 이 얼굴 소유권 변화가 사라진다는 가설은 기각했다. Body0 material 범위를 곧 몸/손 의미 범위로 볼 수 없다. 머리 피부까지 독립 영역 확장 대상에 포함하는 소유권 범위를 먼저 분리해야 하며, 얼굴 항상 우선/깊이 바이어스 수정은 하지 않았다. Body0는 계속 미채택이다.

## 헤어 — 두 셀의 다른 원인과 최소 수정

실제 Walk23/24/25에서 (216,48~49)의 틈을 재현했다. 511·491은 OFF. 두 셀 모두24번 head source와 Prepare에 hair가 있으며 최초 피부 전환은 JoinBare다.

- 위 (216,48): hair source5282의 head depth13.69875908. main depthOffset .003168838을 더하면13.70192792. 기존 destination Body depth13.70149994+.0001에 비교하여 잘못 거부했다. 같은 head ray의 실제 Body primitive9639 depth13.70082756(GPU13.70083141)는 hair보다 뒤다.
- 아래 (216,49): hair source807 depth13.91694260, 같은 ray Body primitive9619 depth13.71138234(GPU13.71138096). 실제 몸 앞가림이므로 유지해야 한다.

`HeadLocal367.UseCentreBodyRay550`은 기존 head centreMeta[1] 패스의 torso 필터를 풀어 **모든 Body submesh/part** 깊이를 그린다. 기존 출력/카메라/알파/cull을 재사용하며 새 RT·패스·dilation·시간필터가 없다. JoinBare는 원래 centre hair와 현재 body의 비교에만 이 동일 ray 깊이를 사용한다. 511/491 대체 패킷이 활성화되면550을 사용하지 않는다. Face/eyes/world depth는 이번 변경 범위가 아니다. head의 centreMeta[1]은 기존 head 경로에서 OwnerLines를 실행하지 않아 기존 소비자가 없었으며 main torso 입력은 유지한다.

## 실제 검증

연속3쌍 후 전체 Walk81쌍을 각각 한 번 수행했다. 양쪽 모두547 Clothes 경로(bits14); 왼쪽550 OFF/오른쪽550 ON이다. Body0와 헤어 영역 실험은 OFF, skyHour3.1476202 고정, 동일 포즈/카메라/빛이다.

- 전체81쌍: source head 입력 전부 동일, alpha변경0, 17포즈22표본 Body8→Hair14. 같은 ray 규칙 불일치0.
- 기존 face/eye 및 동일 소유자의 비헤어 색 차이0. 같은 소유자의 헤어 float 최대7.45e-9 차이는 별도 기록하며 비트동일이라고 하지 않는다.
- 정상 아래 셀 가림 유지. 정상 손/소매/다른 파츠에 영역 처리 추가 없음. 전체 픽셀 출몰 해결 판정은 하지 않는다.
- GIF81프레임/1350ms/2,909,861bytes, WebP lossless81프레임/1350ms/1,428,726bytes. 전신·시간순서·모든 프레임 보존, 배경만 공통 crop, 보간 축소 없음. GIF는 공통256팔레트, 무디더; WebP가 무손실 기준이다.
- 자동 입력/Animator/시계 복원true 및 직접 Edit/clean/후보OFF 확인. Console 기존 진단2건 동일/새0. Quality/Time 설정과547 소스 SHA 불변.

새 성능 측정은 하지 않았다. 기존 패스/RT 재사용이라는 구조 사실을 실시간 비용 통과로 바꾸지 않는다. 544 최적화와 별도 패킷/내부 명암 문제를 보존한다.

## 실행 문제와 남은 작업

import 호출은 domain reload 중 timeout 후 재import 없이 컴파일 확인. 첫 긴 비교 시작은 산출물 없음/Play 정상/captureDelta0/기존훅1 확인 후 미사용 기하 코드를 뺀 짧은 실행기로1회 진행했다. System.Reflection 조회는 Unity 도구가 거절하여 우회하지 않고 공개 상태 API만 사용했다. 전체루프는 중복 실행하지 않았다.

남은 작업: Body0의 머리 피부와 몸/손 영역 소유권 분리, 정상 손끝 포함 실제 비교; 정상 앞가림과 원본 기하의 미세 틈을 구분한 헤어 양·음 영역 디자인; 내부 명암 및 성능. 그라데이션 자료는 GRADIENT_REFERENCE549.md의 참고만 유지한다. Library403 재시도 없음, 산출물은 로컬이다.

근거: ACTUAL_HAND_CAUSE549.json, FACE_SAME_RAY549.json, ACTUAL_HAIR_CAUSE549.json, HAIR_SAME_RAY549.json, COMPARE_RESULT550.json, FULL_RESULT550.json, MEDIA550.json, RESTORED_LOOP550.json, CONSOLE_DELTA550.json.
