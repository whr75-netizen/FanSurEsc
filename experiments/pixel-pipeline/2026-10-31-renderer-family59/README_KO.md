# Renderer family59 — 구성 연결 완료, 실제 프레임 대기

Play 범위 추가 점검: dirty 24개는 Shader 23개와 EditorBuildSettings 1개다. 사전 SaveAssets는 Play의 필수 조건이 아니며 이번에는 저장하지 않는다. 다만 직렬화 해시만으로 Shader의 모든 native 상태를 백업·복구할 수 있다고 주장하지 않는다. import/refresh/compile 없이 현재 객체와 내용을 유지하고 전후 비교해야 한다. `PersistentGameplayShell.ResetStaticState`와 `GameStartRequest.ResetStaticState`, `EditorDirectPlayStorageIsolation.ResetForPlaySession`은 SubsystemRegistration으로 진입 상태를 초기화한다. `CurrentSurface330`, `Full319View335`, `HeadLocal367`은 등록한 콜백의 해제 경로가 있으며 `HeadLocal367.OnDisable`은 ClothRegion524.Release를 호출한다. 그러나 DisableDomainReload는 그 밖의 static/비직렬화 상태를 자동 복구하지 않는다. 따라서 pipeline/시간/Shader global 및 실제 진입 후 변경 상태를 별도 비교·복원해야 하고, 설정 한 항목만 바꾸면 안전하다고 단정하지 않는다. 기존 PreviewScene 실행 경로는 확인되지 않았다. 실제 초기화는 Application.isPlaying, Camera.main, Player/CharacterController와 world render serial을 요구하므로 PreviewScene에 prefab만 생성해서 동일 renderer라고 볼 수 없다. 최소안은 scene reload를 유지한 정상 Play 1회이며, 설정 변경과 Play는 아직 미실행이다.

현재 열린 GameMap1은 Edit/clean이며 **live NativePlayer395가 0개**다. 정상 진입은 `GameplayShellBootstrap.Awake`가 직렬화된 `shellPrefab`을 Instantiate하는 것이다. 그 실제 참조가 `PersistentGameplayShell.prefab`이고, 내부 nested `ValidatedPresentation399.prefab`에 E399가 있다. 원본 prefab을 Instantiate하거나 초기화하지 않고 asset 참조만 읽었다.

## 확인한 연결

- `ReadRenderer59.cs`: 현재 bootstrap의 SerializedObject 참조 → 실제 구성된 NativePlayer395 → host/main/motion/surface → 3개 source SkinnedMeshRenderer/15개 material slot을 추적했다. Material 이름이나 두 시험 primitive 선택을 사용하지 않았다.
- `map_sources59.py`: 현재 메쉬의 **전체 UV/indices**를 실제 texture가 참조하는 VRM 컨테이너의 primitive와 대조한다. 세 메쉬/15개 slot 모두 유일하게 일치하고 material factor도 정확 일치했다. UV의 Unity V 반전과 triangle winding 차이를 명시하며 추정 이름 매칭은 없다.
- `RendererFamily59.cs`: 검증된 source slot을 실제 renderer 배열에 다시 연결하고 UV/indices 해시를 확인한다. `TryReadSourcePoint`는 유효한 draw/primitive/effective shader UV에서 실제 readable texture만 읽는다. 없거나 지원되지 않는 입력은 `false/reason`이며 임의 RGB를 채우지 않는다. `_MainTex/_Color`의 현재 MToon source 계약이 없는 shader는 거부한다. 조명 g나 palette RGB 합성은 이 helper의 역할이 아니다.
- `CheckConfiguredSources59.cs`: 15개 실제 draw에서 8개씩 CPU point를 읽고 `PackDrawDescriptors`로 **240바이트**를 만들었다. 실제 texture의 120개 RGBA가 원본 embedded PNG와 120/120 일치했다. 이 결과는 유한 point 검사이고 full-image 동등성/가시 셀 검증이 아니다.
- descriptor는 draw별 uint4 `[familyOrdinal+1, rendererOrdinal, subMesh, triangleCount]`다. 원본 model/primitive/material/image/UV convention과 경로·GUID는 SOURCE_REGISTRY59.json에 남는다. 이는 **draw→source 표**이며 실제 화면의 pixel-family RT가 아니다.

Getter 전후 dirty 24개 내용/identity·관련 파일·씬 clean/37root·Edit/domain 변경 0. prefab 로딩/UV getter/CPU point 읽기만 수행했다. 원본 메쉬 Bake/재설정/업로드, 재질 변경, Play, renderer 초기화, GPU dispatch, C# import, SaveAssets, CUA, 앱 종료는 하지 않았다. source helper 검사 구간 Unity allocated +412,592 bytes, reserved 0, mono +45,936,640 bytes이며 물리 RAM/누수 판정이 아니다. 앞선 prefab 참조 로딩의 allocated +95,611,633 bytes는 별도 구간이고 cache 소유자까지 확정하지 않았다.

## 현재 중단 경계와 필요한 다음 동작

현재 `EditorSettings.enterPlayModeOptionsEnabled=false`, options `None`, playModeStartScene 없음이다. 그냥 Play하면 domain+scene reload를 거친다. 59 지시의 **domain reload 회피/필요한 일시 모드 변경 직전 중지** 조건 때문에 Play를 실행하지 않았다. Edit에서 prefab을 활성 Instantiate하면 ExecuteAlways 초기화·renderer enable/mesh bake 등 별도 상태 변경이 생기고, 게임의 `Application.isPlaying` 진입 경로와도 같지 않으므로 대신 실행하지 않았다.

필요한 확인 범위는 다음과 같다.

1. 원래 EditorSettings/GraphicsSettings/QualitySettings, 씬·dirty 내용 및 추적 파일을 snapshot한다.
2. `ProjectSettings/EditorSettings.asset`의 Play 옵션을 API로 일시적으로 `enterPlayModeOptionsEnabled=true`, `DisableDomainReload`로 설정한다. 원래 값은 false/None으로 보존한다. 이 **일시 설정 변경은 아직 실행하지 않았다.**
3. GameMap1에서 정상 Play 1회로 기존 shell/E399 생성·ready/connected를 기다린다. 기존 prefab의 `runInputTest=0`이므로 가상 입력 시험은 켜지 않는다. Editor.Step은 사용하지 않는다.
4. ready 후 잠시 pause하고 같은 pose/camera/light/time에서 런타임 전용 복제 재질·compute·소유 버퍼로 헤어만 A/B 렌더한다. 실제 가시 셀의 selected metadata/UV/primitive를 draw 표에 연결한다. 원본 sharedMaterial/RendererFeature/씬은 편집하지 않는다. 후보/원본의 history 입력도 같은 조건으로 분리해야 한다.
5. 정상 Play 종료 뒤 일시 옵션·전역 pipeline 및 원래 상태를 API로 원복하고 dirty 내용·디스크 해시·씬을 대조한다. 공유 자원이나 원본 자산을 임의 저장/삭제/정리하지 않는다. 정상 scene reload가 수반하므로 scene object entity ID 동일성을 미리 보장하지 않고 직렬화 내용/경로/참조/씬 상태를 대조해야 한다.

이 범위의 확인 전에는 Play/설정 변경을 하지 않는다. cold renderer 초기화의 전체 RT 할당 및 종료 수명도 실제 계측 대상이며, 58의 작은 offscreen 시험을 근거로 안전/누수 해결을 확정하지 않는다.

## 아직 없는 결과

실제 visible-cell → family RT, 헤어 palette/g 단계 연결, 전체 캐릭터 원본/후보 PNG, interior/경계별 LineTone·조명·AA 이후 팔레트 밖 색 수는 **미실행/미측정**이다. unknown 셀 수를 0으로 기록하지 않는다. 구성 입력/작은 source 검증을 미술 성공 또는 실제 renderer 통합 완료로 표현하지 않는다. 헤어 범위 선택은 기존 renderer의 부위 분류를 재사용할 예정이며 source family 정체성과 분리해야 한다.

## 저장자료 검사

```powershell
python map_sources59.py
python verify_sources59.py
```

실제 원본 VRM이 원래 project asset 경로에 필요하다. 두 명령 모두 저장자료/원본 파일만 읽고 Unity를 실행하지 않는다. 관련 함수/상태 색인은 기존 `docs/ai/PIXEL_ALBEDO_20261030.md`의59절에 연결한다.
