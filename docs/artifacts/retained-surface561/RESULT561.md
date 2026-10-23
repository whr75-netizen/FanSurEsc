# 561: 표면 유지/뒤 표면 공급의 최소 합성 후보

**48/50 목표는 실제 통과, 다음47 정상 접합에서 새 구멍으로 중단·미채택·철회.** 전체루프/후속손변형/시간필터/새엔진 없음. 제품코드는547/544/550/551/553그대로다.

## 구현한 최소 계약

원래Opacity525의primitive 기원/원위치+스킨가중치 seam weld를 보존했다. 같은 앞면 연결영역의 연속 불투명 면적을 만들되 557A처럼 영역마다 Fit/cut하지 않았다. 기존 공통 디자인영역/이웃field에서 각 표면의 유지−생략 비용 `1-2*min(Afit,Adomain)+B(Ncommon)`을 계산했다. 유지된 표면의 OR가 재질coverage다. 이것은 전역 공동최적해를 증명한 선택기가 아닌 조건부 상태 후보다.

GPU에 primitive→domain, domain bounds/offset, 셀별 유지상태를 전달했다. Probe331은 관리범위의 생략된 앞 삼각형만 제외하여 뒤 유지표면이 실제 깊이테스트에 남도록 했다. Prepare333의 centre/native 선택과 Resolve도 같은 상태를 소비하고, 기존ClothSurface525 공급 요청/Visible도 생략된 관리표면을 건너뛴다. 기존quads/UV/명암 경로 재사용, 새RT·RGB donor·깊이bias·얼굴강제우선 없음. Body0 머리피부는 기존551scope밖으로 유지했다. CPUtop-left480×272/셰이더bottom-left 변환은 한 번만 한다.

## 같은 실행의 실제3쌍

48,50을 먼저 검사하고 통과 후47을 검사했다. 각pause된 실제Walk포즈에서 좌=기존553, 우=561, phase동일. 연속걷기 영상/전체루프 통과가 아니다.

|fixture|기존|561|판정|
|---|---|---|---|
|48(209,110)|Afit .581633568, 최종primitive7920/depth14.006278|손영역 .3332099/뒤다리 .2712673 모두생략, coverage/최종0|목표가시 제거|
|50(231,87)|Afit .999505579, 앞primitive8549/depth14.2904835|앞영역 .217875376생략/뒤영역 .9313095유지. 첫centre→마지막centre→prepared→최종 모두뒤primitive7122/depth14.3010979. UV(.613725007,.947355211)|뒤표면 보존·대체공급 표현 작동|
|47(209,105)|Afit .575037062, coverage true, primitive7823/depth14.0008383|동일Afit이지만 표면OR coverage false, 최종0. 사방이채워진새구멍1|정상접합 실패, 즉시중단|

primitive 표는0기준이다. 저장meta의1기준 값은각7921/8550/7123/7824.50새깊이는논리중심ray에서의GPU표본이다.559의UV재투영ray 뒤깊이14.301152876과 동일ray/비트동일이라 혼용하지 않는다.

47의 최초 손실은 공급/후단 가림 전의 표면선택OR이며 원래 면적 입력 자체가 줄어든 것은 아니다. primitive7823은domain27로 분류됐지만 이번 캡처는 실패셀의 모든 domain면적/경계항을 저장하지 않아 각 기여자별 세부비용까지 확정하지 않았다. 다른깊이층을 표면별로 표현할 수 있다는 것과 현재 조건부 유지규칙이 정상접합을 보존한다는 것은 별개다. 새수치/분리규칙을 반복추가하지 않았다.

실행은FIRST_FAILURE/pairs3에서종료.49/35/36/41 및 전체루프는 **미실행**. 실행한3포즈의기존Face4/5meta차이0은 전체얼굴보호/회색원인해결/눈검증이 아니다. 목표 두셀만 통과해 제품채택하지 않았다. [수치](FIRST_RESULT561.json)·[전신/확대](PROOF561.png)·[철회코드](TRIAL561.patch).

## 운영·비용

표면domain53~60/상태범위7105~7412셀. 후보 Build18.97~23.61ms는3포즈진단관측이며 최적화/워밍업/GC/PlayerFPS측정아님. OFF파일의BuildMs/domain수는 이전ON의잔존진단필드이므로 OFF비용으로사용하지 않는다. packet Unsupported0. 입력/Animator/clock복원true, 직접컴파일완료·cleanEdit·모든시험OFF. 기존5파일diff0, 새helper/HLSL/meta제거. 사용자Quality/Time보존, Library403미시도. 원자료는workspace Current472/Retained561/Compare561에만 보존했고 대량버퍼복제 없음.
