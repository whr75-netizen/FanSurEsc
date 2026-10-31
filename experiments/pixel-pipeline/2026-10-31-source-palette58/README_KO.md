# 원본 재질·UV → C# 팔레트 → 초기/최종 LUT58

제품 기본값은 미적용이다. 실제 원본 VRM 입력을 읽는 C# 공급기·54 CPU 이식과 작은 offscreen 색 경로를 검증했다. 실제 캐릭터 프레임/영역 정돈/눈/움직임/가림 완성 결과가 아니다.

| 코드·함수 | 실제 역할 |
|---|---|
| `SourcePalette58.cs:SourceColours/ExtractReference/MakePalette/ShadeIndex/Resolve` | 54 JS의 source factor·alpha 가중 관측 OKLab medoid, OKLCH 램프, Float32 임계값 및 직접 P[k] 이식 |
| `OriginalMaterialUv58.cs:Read/ReadAccessor/FamilyKey/ResolveFamily` | 원본 GLB material→texture→embedded PNG, POSITION/TEXCOORD_0/indices를 읽어 원본 UV point 색과 source family ordinal 공급 |
| `ReadSource58.cs:Execute` | 기존 Unity_RunCommand에서 원본18,495,680bytes SHA를 먼저 검사하고 두 명시 primitive의63표본을 새로 읽음. 한 번에 decoded image 최대16MiB, 소유 Texture2D만 해제 |
| `State58.cs:Read/Changes` | dirty 객체마다 native JSON을 한 번만 만들고 해시/identity만 저장. 원본 JSON 전체를 중복 보관하지 않음 |
| `Json58.cs/SourceJson58.cs` | 실행기의 제한된 참조 집합용 명시 JSON 경계. 패키지 로딩/Reflection/보안설정 변경 없음 |
| `GpuProbe58.cs:Execute/ReadFloat/ReadByte` | 위 실제 표본에서 C# 팔레트를 다시 계산해 후보에 공급. 직접 소유 readback 배열만 요청 완료 뒤 Dispose |
| `Assets/Editor/SourcePalette58Probe/SurfaceLayerOutput58.hlsl:SurfaceLayerOutput335` | 현재 제품 함수의 작은 clone. family를 명시 입력으로 추가하고 표시모드0에서 P[Q(g)] 직접 출력 |
| 같은 폴더 `RestoreStyle58.compute:ApplyShadeBoundary` | 현재 제품 compute clone. 유효한 bound opaque 분기를 role/old==q gate 앞에 넣어 P[k′] 기록. alpha/깊이 등 기존 class 성분 보존, factor RGB=1 |
| `Recheck58.cs:Execute`, `verify58.py`, `oracle58.cjs` | 저장된 GPU/원본/JS의 대조. 추가 GPU 렌더 없이 검사 정밀도 오판을 재현·교정 |

## 확인 결과

Unity6000.5.9f1/Direct3D11/Linear에서 C#은 Assets 밖에서 메모리 컴파일했다. 원본 source PNG 63/63 정확 일치. 두 실제 재질의 대표색/출처와 4/3색 팔레트가54 JS와 정확 일치했다. Lab/팔레트 좌표 최대 오차2.220446049250313e-16, medoid cost 오차5.082197683525802e-21. 대표색은 원본 native `(66,42,41)` 및 `(250,238,228)`이며 모델별 고정 기본색을 넣지 않았다.

GPU는 **새 source58 입력**으로 draw2회·compute1회만 실행했다. 64표본=불투명62+부분alpha 원본1+미등록 sentinel1. 초기 float RGB 및 최종 sRGB64/64, alpha/class/factor64/64 일치. linear 최대오차2.423339741097763e-7, bound opaque 팔레트 밖0. 변경 k′10개와 old==q52개를 포함한다. old==q가 초기 LUT를 그대로 유지해서 거짓 통과하지 못하도록 **최종 join 검사 입력에서만** 해당52셀 RGB를 magenta로 오염시켰고 전부 LUT로 교체됐다. 원본 source/UV/g/alpha는 유지했다. 따라서 이 검사는 초기/최종 함수와 최종 join 반례이며, 중간 오염 없는 전체 캐릭터 프레임의 연속 렌더라고 부르지 않는다.

첫 C# GPU 보고서의 `gpuPass=false/classMismatches=63`은 검사식의 중간 정밀도 오판이었다. saved Float32와 `.4f+i*.001f`의 미저장 중간값을 직접 비교했다. 원본 GPU58.json을 수정하지 않았다. 오프라인64표본과 **C# saved-data 재검사**가 원래식63불일치/실제 업로드 Float32 성분0불일치를 함께 재현했다. 현재 C# 검사기는 업로드 Color 배열의 성분을 직접 비교하도록 고쳤고, GPU는 재실행하지 않았다. 실제 제출 코드 `RUN_GPU58.cs.txt`와 교정 후 `GpuProbe58.cs`를 구분한다.

간격배율 .5로 바꾼 두 C# 램프는 JS와 같고 Q는 유지됐다. 임계값 변경은 두 집합에서4/3개 분류값을 바꾸고 팔레트는 유지했다. 원본 모델/선택 primitive/UV는 그 조절로 바뀌지 않는다.

기존 dirty24 내용/identity·관련49파일·씬 clean/37root·Edit/domain을 보존했다. 모든 소유 Texture2D/RT/ComputeBuffer/Material/Compute clone/CommandBuffer/NativeArray를 회수했고 신규 Console 오류/경고0이다. source 및 GPU 종료에서 원래 texture/RT identity가 유지됐다. SaveAssets/Play/RendererFeature/기존 재질·제품 변경/CUA/GC/앱 종료/push 없음.

## 57 메모리 감사와58 한계

57 submitted 코드에는 큰 배열을 잡는 static 필드/이벤트 구독/비동기 callback이 없고, 요청 완료 후 owned 배열·buffer·RT를 해제한다. 그러나 `DirtyLines`가 native JSON을 한 객체에 두 번 생성했고 문자열·UTF8 복사·전체 snapshot 읽기에서 반복 할당했다. 큰 배열의 **영구 잔류**나 두 Editor RT 교체 소유자는 이 코드만으로 확정하지 못했다. 58은 JSON 한 번/객체/스냅샷과 작은 해시 요약으로 줄였다. source 단계 allocated −33.248MiB/reserved +16.008MiB/mono −39.059MiB, GPU 단계 allocated −242.670MiB/reserved −173.273MiB/mono −20.977MiB였다. Unity 내부 카운터이고 물리 working set이나 누수 해결의 증거가 아니다. GC/Unload로 강제 정리하지 않았다.

## 범용 부분과 아직 명시 입력인 부분

알고리즘은 material명/역할 번호/삼각형 구간/스크린샷 평균색에 의존하지 않는다. material→texture/image/factor는 원본 primitive에서 읽고 sample UV에서 native 색을 읽는다. 키는 model SHA+mesh+primitive+실제 material이다. 반면 두 **시험 domain 선택**과 램프/임계값은 CONFIG58.json의 명시 설정이다. 한 primitive 내부 painted feature/의미론 자동 분할, 현재 Unity renderer의 가시 셀→원본 primitive provenance 버퍼 공급은 아직 없다. 기존 제품 `Full319View335.Initialise`의 renderer 역할 분류도 그대로다. 따라서 자동 범용 모델 통합을 완료했다고 하지 않는다.

지원범위는 GLB2 embedded PNG·float32 POSITION/UV·triangle primitive·TEXCOORD_0·identity texture transform이다. 비identity KHR transform/다른 UV set/sparse accessor/다른 재질 모델은 명시적으로 미지원이다. ASCII provider sample key에서 JS tie-break 출처가 같았지만 임의 Unicode ID의 언어별 collation 동일성은 입증하지 않았다. native point authoring 표본은 bilinear/mip/실제 가림·깊이를 재현하지 않는다. 부분alpha 원본 표본1개는 최종 opaque LUT 범위에서 제외해 그대로 보존했다.

## 재생

```powershell
node oracle58.cjs ../2026-10-31-source-palette54
python verify58.py
# 원본 VRM이 CONFIG58.json 위치에 있을 때만 원본 PNG 추가 대조:
python native58.py
```

위 명령은 저장자료 검사이고 Unity를 실행하지 않는다. 코드·원본 출처·함수·관련 commit 색인은 `docs/ai/PIXEL_ALBEDO_20261030.md`58절과 Git 이력에 유지한다. GPU import 전역 Refresh나 제품 활성화는 자동 수행하지 않는다.
