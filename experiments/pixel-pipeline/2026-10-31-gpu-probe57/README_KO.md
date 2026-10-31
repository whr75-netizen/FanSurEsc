# GPU 팔레트 조회57 — 제품 미통합

54의 원본 source 출처→명암 인덱스→P[k] 계약 중 **GPU 조회와 최종 sRGB 인코딩**만 확인한 격리 시험이다. 실제 캐릭터 머리/눈 이미지나 공간 영역 보정·시간 안정화 결과가 아니다.

## 코드 위치

- `SourcePaletteGpuProbe57.cs:Execute`: 기존 공식 Unity_RunCommand에서 메모리 컴파일/실행. **Assets 밖에 보관**해 새 script import/domain reload를 피한다. `Violations`가 원래 dirty JSON/entity ID/디스크 해시/씬/root/build 목록을 전후 비교한다.
- `Assets/Editor/SourcePalette54Probe/SourcePaletteProbe57.compute:Probe57`: family ordinal와 Float32 g를 받아 `SourceShade54→SourceLookup54`로 uint4 출력.
- 같은 폴더 `SourcePaletteOffscreen57.shader:Frag57`: 같은 조회→RGB8 sRGB decode1회→linear fragment. `R8G8B8A8_SRGB` RT가 encode1회한다. 조명/G/HairFinal/LineTone/혼합/톤매핑은 이 **시험 경로**에 없다.
- 같은 폴더 `SourcePalette54.hlsl`: 54 보관본과 바이트 동일. 파일 첫 주석은 54의 미검증 당시 설명이며 실제57 컴파일/실행 결과는 여기와 GPU_RESULT.json이 소유한다.
- `replay57.py`: 동결 CPU/GPU/RT 및 nearest PNG를 오프라인 대조한다. Unity를 다시 실행하지 않는다.

## 실행과 입력

2026-10-31 08:12:41 UTC, 현재 Editor PID28304/6000.5.9f1/Direct3D11/Linear, GameMap1 Edit에서 실행했다. 새 C#은 import하지 않았다. 새 compute/shader/include만 한정 import했다. Play/scene render/SaveAssets/전체 Refresh/기존 재질 또는 RendererFeature 수정은 없다. 실행기는 기존 명령기의 허용된 표준 C#만 사용한다.

PACKET57.bin은 검증된54 PACKET와 RESULTS의 little-endian 동결본(1,020bytes)이다. header24 + palette12×uint4 + threshold9×float32 + family3×uint4 + case30×(uint,float32) + expected30×uint4. source 출처는 PACKET_RECEIPT.json의 model/material/image/triangle/UV/texel과54 해시로 연결한다. **새 장면 조명 입력이 아니다.** 표본0–9 원본 hair material12,10–19 원본 cloth material10,20–29 별도 합성 청록 fixture다. fixture의4/3/5단계가 미술 최적값이라는 뜻은 아니다.

## 결과 및 보존

- dispatch1회·30×1 offscreen draw1회, compute30/30 및 RT30/30 정확 RGB8 일치. 팔레트 밖0. GPU57_COMPARISON.png의 CPU/GPU/RT 세 줄과 원본30×1/nearest16× PNG를 직접 열어 확인했다.
- 기존 dirty24 native JSON3,438,997bytes/entity ID, 디스크49파일 해시, GameMap1 clean/37root, build 목록과 domain1은 동일했다. 원본 dirty 내용 덤프는 원래 작업폴더의 SAFETY_BEFORE/CURRENT.json에 보존하며 사용자 미저장 내용 자체는 이 실험 커밋에 복사하지 않는다.
- 직접 소유 ComputeBuffer5/NativeArray2/Material/Compute clone/RT/CommandBuffer만 회수했다. borrowed GetData 메모리 Dispose 없음. shader compiler message0, Console 신규 오류/경고0. Console을 지우지 않았다.
- 즉시 RT30 identity 같음. 후속 읽기에서는 수30 유지·2개 identity 교체, 원인/소유자는 미확정이다. 공유 자원을 임의 Destroy하지 않았다.
- **메모리 전체 원복 미입증:** probe 구간 Unity allocated +60.95MiB/reserved −16MiB/mono +87.84MiB. 별도 읽기 전후 스냅샷 구간 allocated +203.56MiB/reserved +141.28MiB/mono +129.25MiB. API별 정확한 시각/bytes는 VERIFICATION.json. 물리 working set이 아니며 잔류 owner 미확정이다. GC/Unload/추가 캡처를 실행하지 않았다.
- 실행 전 타입 오류 및 불필요한 interop namespace 사전 거절은 각각 GPU 미실행이었다. 도구의 제거 후 재시도 안내에 따라 그 namespace/속성을 없앴으며 정책/권한/실행 경로 변경은 없다. 성공한 GPU 실행은1회뿐이다.

## 재생

```powershell
python replay57.py --source54 ../2026-10-31-source-palette54
```

이 명령은 저장 결과의 재생이며 live GPU/현재 Editor 상태를 다시 검증하지 않는다. probe는 one-shot이므로 자동 반복 실행하지 않는다. C# 안의 Output은 승인된 원래 작업폴더 경로를 명시하며 제품 런타임 도구가 아니다.

공식 API 근거: [RequestIntoNativeArray](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rendering.AsyncGPUReadback.RequestIntoNativeArray.html) 소유 NativeArray는 요청 완료 뒤 해제, [GetComputeShaderMessages](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/ShaderUtil.GetComputeShaderMessages.html), [GraphicsFormatUsage](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Experimental.Rendering.GraphicsFormatUsage.html), [6000.5 GetEntityId](https://docs.unity3d.com/6000.5/Documentation/ScriptReference/Object.GetEntityId.html). 이 API 근거는 실제 미술 품질을 보장하지 않는다.

## 다음 연결과 한계

원본 source 추출/관측색 medoid/팔레트 생성은 아직54의 JS CPU 프로토타입이다. 제품 초기화용 C# 이식과 실제 material/UV family 공급이 필요하다. `RestoreStyle335.ApplyShadeBoundary`의 old==q 조기 반환 뒤에만 조회를 넣으면 미변경 셀은 여전히 기존색이므로 모든 interior 최종 기록 경로가 필요하다. 후단 alpha/outline/LineTone/AA와 실제 source ID 채널도 별도 검증해야 한다. 기존 제품 하드코딩·곱셈 경로는 이번 작업으로 변경되지 않았다. 눈 clean backing6표본/부분 가림/전체 keyform도 미해결이다.

최신 알고리즘/함수/관련 커밋 색인은 `docs/ai/PIXEL_ALBEDO_20261030.md`의57절과 Git 이력에 유지한다.
