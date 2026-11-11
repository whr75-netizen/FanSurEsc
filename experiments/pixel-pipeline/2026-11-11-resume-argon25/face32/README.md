# 초기 Q/Qprime 계약 및 callback 수명 검토32

기준 `cea8f19a`. **Unity/relay/GPU/Play/import/재시작0, Assets 수정0, 두 패치 미적용**입니다. 제품77과 후보31은 그대로입니다. 중간에 CPU 실행 서버 연결이 끊겨 두 읽기 명령이 프로세스 생성 전에 실패했으나 이후 복구되어 CPU 검증·파일 보존을 마쳤습니다. Unity 연결이나 현재 Editor 상태를 조회한 것은 아닙니다.

## Q가 같아지는 정확한 조건

기존 `RestoreStyle335.ShadeBoundary`는 원본 분류 버퍼를 읽어 proposal mask를 쓰고, 그다음 `ApplyShadeBoundary`가 분류 X를 갱신합니다. 같은 입력의 한 셀에서:

`Qprime = proposal` iff `apply && ShadeRole(meta) && abs(Q0-proposal)>=0.01`; 나머지는 `Qprime=Q0`입니다. 연속 명암 Y·깊이 Z·alpha는 이 적용 단계가 바꾸지 않습니다. 곡률 보정이 꺼졌거나 유효 변경 제안이 없으면 Q가 같지만, proposal과 적용 결과는 별도 단계입니다. 명암 색 효과가 꺼지면 RGB가 같아도 Q 라벨은 달라질 수 있습니다.

31의 native 초기 Q와 기존 Qprime을 비교하려면 먼저 **초기 Q 생산자 자체**의 shader/pass/keyword, 원본 mesh·normal·material/alpha·region clip, 투영·격자·샘플, 조명/SH·모드·단계 수가 대응해야 합니다. 같은 함수 이름이나 화면 크기만으로 이 조건을 충족하지 않습니다.

`QPrime32.cjs::reviewQ32`는 현재 HLSL의 float32 유한 입력 CPU oracle입니다. 동일 입력의 폭1 돌출 반례에서 Q0=0, proposal=Qprime=1을 재현했습니다. 반면 ROI+1로 자르면 거리2의 지지 표본이 없어져 proposal=0이 됩니다. **stride1의 Qprime 한 셀에는 halo2, 4이웃 경계 조회까지는 halo3**이 필요합니다. 일반식은 `2*ShadeStride + queryRadius`이며 native stride2/논리 이웃 간격2라면 native halo6입니다. 초기 Q의 경계 조회에는 기존 halo1이면 됩니다. 31을 Qprime으로 이름만 바꿔 쓰면 안 됩니다.

## 확인된 생산자 스키마 불일치

`FullFeature367.LegacySignals` → `HeadRegion502.Draw(kind4)`는 Ready/current이고 renderer1/2이면 `Legacy502.shader`로 바꿉니다. 이 shader는 `classifier=(binary shadow, role+1, depth, alpha)`를 씁니다. 후단 `ShadeBoundary`는 **Y를 연속 명암**으로 읽습니다. 지원 role3·7~14에서는 Y>=4, 이진 라벨의 중간값은[0,1], 허용 반경은<=0.1이므로 불확실성 조건에 들어갈 수 없습니다. 해당 분기에서는 Qprime이 안 바뀌는 것을 올바른 공간 보정의 증거로 삼을 수 없습니다.

동일 Q 버퍼 안에서도 renderer0/fallback은335, renderer1/2의 해당 분기는502가 될 수 있어, 생산자 종류는 전역 한 개로 추정하지 않습니다. **현재 살아 있는 Editor에서 이 분기가 활성인지 확인하지 않았습니다.** 검사한 saved27 frame99에는 Q0/proposal/Qprime 분류 plane과502 분기 flag가 없어 실제 변화 셀 수를 계산하지 못했습니다.

`prepare_qreview32.py` → `UNAPPLIED_Legacy502_32.patch`는335의 기존 layered fragment를 그대로 재사용하되 `Region502Vertex/Clip`을 보존합니다. classifier X/Y와 layered shade 채널을335 계약에 맞추고 cluster keyword도 현재335와 맞춥니다. 새 수학·색 보정·영역 휴리스틱이 아닙니다. shader variant와 실제 RGB/가시성 동등성은 **미검증**입니다. 검토 shader 파일을 별도 Asset으로 그대로 import하는 패치가 아닙니다.

## MRT와 수명 검토에서 수정한 부분

- 기존335/502 및 파생 QMeta31은 `Blend One Zero`, `ZWrite On`, `AlphaToMask Off`입니다. 이 소스에서 framebuffer blend가 metadata를 평균한다는 가설은 지지되지 않습니다. 실제5-MRT 포맷 지원/variant/raster·조명 동등성은 아직 별도 검증입니다. QMeta31의 owner는 상수0이고 normal/UV membership도 빠져 있어 기존 Qprime의 `ShadeNeighbour` 입력을 대신할 수 없습니다.
- 31의 end readback은 **생산자까지만** 덮습니다. 이후 관찰기 readback에도 수명 보호가 필요합니다. `ConsumerReads32`와 `UNAPPLIED_ConsumerLifetime32.patch`를 준비했습니다. producer와 모든 consumer가 끝나야 해제하며, 한 번에<=262144B 한 strip만 허용합니다. 잘못된 owner ticket·pending/error·byte mismatch·불명 enqueue에서는 해제/재제출하지 않습니다.
- 검토 variant는 raw RT 공개를 없애고 bounded readback API를 통하도록 했습니다. callback 안에서 데이터를 작은 managed byte[]로 복사하고, 사용자 callback이 끝난 **후** lease를 완료합니다. 파일/복사 실패는 결과를 무효화하되 이미 증명된 GPU 완료는 안전한 drain에 사용할 수 있습니다. byte 수는 픽셀 예산 검사 뒤 곱해 정수 overflow를 차단합니다.
- `ReadbackPreflight32`는 Render/LoadStore/ReadPixels 지원 및 정확한 비-MSAA·비-sRGB·비-dynamic-scale RGBAFloat target을 사전 검사하는 코드입니다. **실행하지 않았습니다.** readback 결과 수명이 짧으므로 borrowed NativeArray/request를 외부로 넘기지 않습니다. [Unity 공식 request 수명 설명](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rendering.AsyncGPUReadbackRequest.html)
- `EditorExitRequest32`는 callback에서 종료를 큐에 넣기만 하고, 생성 스레드의 명시 observer pump에서 한 번 실행합니다. CPU worker-thread 반례를 검사했습니다. 실제 생성/펌프가 Editor main thread에 놓이는지와 native Exit/복원 동작은 실행 검증이 남습니다.

## 검증 결과와 다음 단계

`verify_qreview32.py`: Q 시나리오37개, 모든 이진 ring256패턴(기대 돌출16개), legacy 스키마 범위108경우, 소비자 수명30검사 통과. D4 검사는 이진 합성 경계의 회전/반사이며 실제 머리 움직임 검증이 아닙니다. UV membership은 주어진 ID 입력으로 취급했고 실제 texture sampling을 검증하지 않았습니다. `prepare_qreview32.py`: 검토 C# metadata 참조 컴파일 및 정적12검사 통과. shader GPU compile/import/dispatch는 없습니다. 증거는 `CPU_Q32.json`, `CPU_CONSUMER32.json`, `CPU_REVIEW32.json`, `SOURCE_AUDIT32.json`입니다.

두 미적용 patch는 `git apply --check --unidiff-zero` dry-run을 통과했습니다(`PATCH_CHECK32.json`). 실제 적용하지 않았습니다. 전체 검토 shader/빌드 DLL은 중복 저장하지 않고 생성 스크립트·원본 SHA·최소 patch로 재현합니다. 이 dry-run과 C# 참조 컴파일은 실제 shader variant 컴파일 성공을 뜻하지 않습니다.

안전 정지는 유지합니다. 다음 허용된 실행 단계에서 먼저 최신 공개 상태/기존 보존 기준·미완료 owner0·옵션/domain 조건을 확인해야 합니다. 검토 패치와 observer의 journal/생성·펌프 위치를 연결한 뒤 실제 shader variant/MRT를 확인하고, 최소 한 프레임의 bounded producer+consumer 완료/정상 종료/복원부터 검증하는 순서입니다. 기존 URP private job이나 과거 reset 원인까지 안전해졌다는 뜻이 아닙니다. 오류/불명 결과면 추가 제출 없이 정지합니다.

Qprime 비교의 최소 자료는 **동일 sourceId/view/frame**의 생산자 shader·분기·keyword·모드, 원본 Q0(ShadeBoundary 전), proposal, Qprime(Apply 후), 실제 meta role/owner/depth·normal·필요 UV membership과 정규화/단계 수/world-pixel 설정입니다. 논리 halo3 또는 이에 대응하는 native 범위가 필요합니다. shader/geometry가 다른31 초기 Q는 별도 출처로 유지합니다. 이 자료를 지금 캡처하지 않았습니다. 전체 얼굴 영역화·유한 팔레트·외곽선·미관·시간 안정성도 이번 결과로 완료되지 않았습니다.
