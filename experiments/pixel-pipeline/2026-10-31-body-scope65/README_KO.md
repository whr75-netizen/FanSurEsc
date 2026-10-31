# `_BodyScope551` 소유권65 — 검토용 패치, 제품 미적용

대상 기준은 commit `b0312165aa7b331415f6f06394808ff5f69c3538` 이후의 **현재 수정 작업본**이다. 두 대상 Assets 파일 모두 이미 기존 수정이 있으므로 HEAD로 덮어쓰지 않는다. `PATCH_MANIFEST65.json`의 작업본 SHA와 맞는 경우에만 이 패치를 검토한다. 패치 적용·import·Unity 접근·Play·렌더는 이번에 하지 않았다.

## 확인한 원인과 사용 경로

| 지점 | 현재 코드의 책임 / 문제 |
|---|---|
| `ClothRegion524.ScopeBuffer551:38` | 읽기처럼 보이는 함수가 1-float fallback을 생성·업로드한다. flag가 꺼져 있어도 raster/compute에서 호출됨 |
| `Scope551:39–52` | 원본 body0의 skin weight/Head 하위 bone 영향으로 primitive별 포함 bool/float를 만든다. old buffer를 먼저 Release하고 새 GPU 업로드를 하며 CPU cache도 먼저 갱신하므로 실패 시 이전 CPU/GPU 쌍이 보장되지 않음 |
| `FullFeature367.Probe:11 → ClothRegion524.BeginProbe:134` | `_BodyScope551`의 유일한 Assets literal **전역** buffer setter. 공개 getter가 없어 기존 binding의 정확한 snapshot/restore가 불가능 |
| `MotionView331.Initialise:32–37` | 원본 재질에서 `new Material(src)`로 probe 재질을 만들고 `materials`에 보관. `OnDisable`에서 이 임시 재질들을 DestroyImmediate함. 원본 asset 재질이 아님 |
| `VisibilityMotion331/Probe331.shader:126,132` | raster consumer. enabled/part 조건 또는 `buffer[primitiveID]>.5`로 body0를 제한 |
| `FullFeature367`의 Prepare/Resolve → `ClothRegion524.Bind:135` | 이미 `SetComputeBufferParam(shader,kernel,...)` 사용. global일 필요 없음 |
| OwnerLines → `BindLines553:137–140` | 같은 buffer를 `_BodySource553`라는 kernel-local 별칭으로 사용. count도 해당 renderer의 mask 길이에 맞아야 함 |
| `ClothSurface525`의 두 `InScope551` 호출 | CPU triangle 영역 필터. 포함 판정 자체는 그대로 유지해야 함 |
| `HeadLocal367.OnDisable:48 → ClothRegion524.Release:142` | 기존 전체 해제 경로. `Full319View335.OnDisable`에는 scope 해제가 없어 standalone/부분 초기화의 수명 보장이 약함 |

전체 검색 범위/파일 SHA/정확한 행은 `SOURCE_AUDIT65.json`에 기록했다. 후보 함수의 정확한 경로·행은 `FUNCTION_INDEX65.json`이다. DLL·동적 이름·reflection까지 모든 외부 writer가 없다고 증명한 것은 아니다. HeadRegion/HairBoundary의 별도 shader에는 이 buffer의 literal 소비가 없고 Probe331의 UsePass 참조도 검색되지 않았다. 다른 Shader global은 이 패치 범위가 아니며 이전60의 손실된 백업을 복원하지 않는다.

## 실제 패치: 두 파일, shader/기본값 변경 없음

`body-scope65.patch`와 `candidate/Assets/...`는 **아직 적용하지 않은 후보**이다. `before/`는 이번 작업 시작 시점의 두 작업본 bytes다.

1. `ClothRegion524.cs:BodyScopeResources551.Upload/Buffer/Commit/Dispose`
   - `Full319View335`별로 직접 생성한 buffer만 소유한다. static dictionary는 소유자 조회만 하며 다른 buffer를 가져오지 않는다.
   - fallback은 첫 사용에만 생성. 실제 mask는 candidate 생성·SetData가 성공한 뒤 CPU mask/mesh/head/count와 함께 교체한다. 업로드 실패 시 candidate만 해제하고 이전 쌍은 유지한다.
   - `ReleaseScope551`는 한 renderer만, 기존 `Release`는 전체 adapter 종료 때 모든 scope를 해제한다. 같은 종료를 반복해도 중복 Release하지 않는다.
2. `ClothRegion524.cs:BeginProbe/Bind/BindLines553`
   - `BeginProbe`의 global buffer 명령 한 개를 제거하고 그 renderer의 `motion.materials` 임시 재질에 `Material.SetBuffer`로 연결한다. Probe draw 직전의 기존 진입점을 그대로 쓴다.
   - compute는 기존 kernel-local 경로를 유지하며 같은 renderer의 owner를 참조한다. 수치 flag·primitive 포함 판정·정점 skin weight 식·clothing 선택·팔레트는 바꾸지 않는다.
   - 기존 global buffer를 읽거나 덮거나 null로 치환하지 않는다. 가짜 복원도 없다.
3. `Full319View335.cs:OnDisable`
   - 기존 `!ready` 조기 return보다 앞에서 `ReleaseScope551(this)`를 호출한다. 부분 초기화/취소 뒤에도 이 owner가 해제될 수 있도록 한다. 기존 사용자 자산의 저장/dirty 해제 코드는 추가하지 않는다.

기존 CPU clothing adapter의 `current/selectedScope` 상태는 여전히 단일 현재 준비 대상을 가리킨다. 이 패치는 전체 clothing 알고리즘을 여러 독립 모델의 동시 실행용으로 재설계하지 않는다. GPU buffer와 kernel count의 renderer별 출처만 분리한다. 일반 raster에서 임시 재질당 한 SetBuffer 호출이 추가되며 buffer 생성은 매 프레임 하지 않는다. 교체 때 일시적으로 이전+candidate 두 buffer가 존재한다. 실제 비용은 측정하지 않았다.

## 실행한 검증

실행: `python -B build65.py`, `python -B audit65.py`, `python -B validate65.py`. Python 표준 라이브러리만 사용한다. 검증기는 설치된 .NET Framework `csc.exe`로 **실제 후보의 owner fragment와 BeginProbe 본문을 추출해서** CPU fake API와 함께 컴파일·실행한다. Unity assembly나 native GPU 검증이 아니다.

- C# 격리 수명 13사례: 중복 초기화/fallback 재사용, 두 renderer 분리, 정상 교체, 생성 실패, 업로드 실패, 첫 업로드 실패 후 재시도, 빈/불일치 mask, 취소 finally, ready 전 실패의 cleanup, 반복 종료/재진입, 다른 owner 선택 보존, 실제 BeginProbe의 local binding, 외부 buffer 비해제.
- fake 생성20/해제20, double Release 0. 실패 주입에서 이전 buffer/CPU mask/mesh/head 참조가 유지됨. 이는 물리 GPU 메모리 측정이 아니다.
- 소스 불변식5개: 포함 판정 식 유지, 전역 buffer setter 0, compute/lines local binding, ready 전 해제 hook, 두 파일 범위. 대상 Assets SHA 변경0.
- 현재 수정 작업본에 `git apply --check` 성공. **apply는 하지 않음.** `COMPILE65.txt`, `LIFECYCLE65.txt`, `VALIDATION65.json`에 실제 결과 기록.

전체 Unity C# 컴파일 실패/domain reload 중 `OnDisable` 호출·native GPU in-flight 수명·material buffer override의 실제 shader 동작은 오프라인 fake로 검증할 수 없다. 실제 renderer와 이미지의 동등성도 미검증이다. 컴파일 실패를 정적 테스트로 해결했다고 쓰지 않는다.

## 다음 실제 연결에 필요한 범위

이 두 파일을 **함께** 기존 변경 위에 적용·import하는 단계와 컴파일/제한 렌더 검증이 남았다. 짧은 Play 캡처 승인은 도착했지만65는 계속 오프라인 준비 범위이며, 미저장 상태/import 안전성이 미확인이라 실행하지 않는다. import 전 현재 Editor/dirty 내용을 다시 확인·보존해야 한다. 이전에 존재한 전역 binding을 null로 지우거나 임의값으로 복원하지 않는다. 새 경로에서는 해당 binding을 아예 변경하지 않아야 한다. 숫자/texture global은 기존64 journal의 별도 백업·복원 계약 대상이다.

현재 컴파일된 `FullFeature367.Probe`는 기존 `ClothRegion524.BeginProbe`를 정적으로 호출한다. Assets 밖 command runner에 새 helper를 로드하는 것만으로 이 호출이 교체되지는 않는다. 이 패치의 정상 활성화에는 C# import/재컴파일이 필요하다. Enter Play Mode의 `DisableDomainReload`는 **Play 진입** 때의 reload 옵션이며 script import reload를 막는 장치가 아니다. 현재 조건인 미저장 내용 보존·domain reload 회피를 만족한 채 두 기존 C# 메서드를 안전하게 교체할 경로는 확인하지 못했다. 이를 private reflection/hotpatch/assembly 교체로 우회하지 않는다. 관련 공식 근거: [Asset Database refresh와 script hot reload](https://docs.unity3d.com/6000.0/Documentation/Manual/AssetDatabaseRefreshing.html). 기존24/30 dirty 수를 현재 Editor 상태라고 가정하지 않았고, 새로운 조회도 하지 않았다.

실제 검증 시: scope off/on 동일 입력에서 기존 buffer float 값·CPU mask·출력 비교, main/head별 local binding 확인, 종료/재진입과 새 Console 오류·소유 buffer 수명 확인이 필요하다. native GPU 결과가 나오기 전에는 실행 안전성 전체 또는 실제 미술 결과가 해결됐다고 판정하지 않는다.

근거 API: [Unity Material.SetBuffer](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Material.SetBuffer.html), [Shader.SetGlobalBuffer](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Shader.SetGlobalBuffer.html). global fallback과 material-local override의 구분에 사용했으며 GPU 실행 증거로 대신하지 않는다.
