# 64 — 원본 UV의 기울기/경계 계층과 다음 캡처 준비

**오프라인 구현·검사만 수행했다. Unity 접근0회, 새 Play/렌더/캡처0회다.** Python source-native 증거 추출은 실제 실행했고, C# 캡처 helper/journal은 작성·정적 검사만 했으며 컴파일·실행하지 않았다. 제품·31·34·기존 RGB/팔레트는 변경하지 않았다. 특징 영역/곡선의 최종 완성이나 미술 합격으로 채택하지 않는다.

[원본/반례 보기](INDEX.html) · [합성 검사](TEST64.json) · [원본4장](SOURCE_RESULTS64.json) · [373셀 대응](CELL_BINDING64.json) · [캡처 계약](CAPTURE_PLAN64.json) · [캡처 검사](CAPTURE_TEST64.json)

## 이번에 바꾼 전제와 코드

62는 Lab 값을 구간으로 자르고 cc4한 결과를 특징 영역처럼 취급했다.64는 **색 값의 절대 구간을 만들지 않는다.** 원본 texture의 각 인접 경계에서 기울기를 제거한 jump 증거를 계산하고, native2·4·8texel 범위에서 유지되는지 검사한다. 실제 source/UV에 귀속된 경계·열린 contour·얇은 신호를 캐시한다. 화면 RGB 캐시, g 분류, palette 선택을 특징 추출로 대신하지 않는다.

| 스크립트/함수 | 실제 역할 |
|---|---|
| `uv_features64.colour_intervals` | sRGB8 ±반 코드의 범위를 decode→양수 LMS→cuberoot→mixed-sign OKLab 행렬로 전파 |
| `intercept_weights/jump_interval/axis_evidence` | 양쪽 affine profile을 경계에 외삽하고 jump 구간·모든 스케일 검출·양쪽 모델 적합성·실제 인접 변화 검사 |
| `thin_ridges` | 부호가 반대인 양옆 곡률 lobe를 가진 native 얇은 선/봉우리 후보. 의미는 미확정 |
| `barrier_components/edge_components` | 관측된 경계로 나뉜 면과 **닫히지 않은 contour**를 별도 표현. 최소 면적 제거·임의 gap closing 없음 |
| `extract/source_key` | 부모/미세 하위영역·contour DAG export. 키는 원본RGB/UV support/scales/규칙 버전이며 g/Q/material ID/화면 위치가 아님 |
| `palette_invariant` | sourceRGB와Q가 같으나 출력이 다른 cohort 검사. 재질/구조 ID를 palette 기준으로 몰래 사용하지 않음 |
| `run_source64/test_uv64` | 원본PNG 해시 확인·원본4장 적용·저장373셀 UV 대응·합성/원본 불변 검사 |

### 실제 수식과 해석 범위

원본 OKLab 신호를 f라 하고, 경계의 양쪽 r개 표본 위치를 `x=−r+.5…−.5`, `.5…r−.5`로 둔다. 각 쪽 `f≈β0+β1x`의 절편은 `β0=Σw_i f_i`, `w_i=(Σx²−Σx·x_i)/(rΣx²−(Σx)²)`다. jump는 `J_r=β0,right−β0,left`다. 동일한 선형 기울기는 모든 r에서 jump0과 양립한다. RGB8 encoding 구간을 같은 선형 계수로 전파하므로 작은 원본 반올림을 임의 contrast 상수로 확대하지 않는다.

`persistent`는 (1) **각 스케일 자체가** jump를 검출, (2) jump 구간들이 공통 값을 가짐, (3) 양쪽 profile 내부의 second-difference 구간이 affine 모델과 양립, (4) 실제 인접 원본 표본에도 변화가 있다는 조건을 모두 요구한다. 스케일이 커져서만 보이는 신호는 `scaleEmergentUncertain`으로 분리한다. fine-only와 thin/ridge를 삭제하지 않고 하위 증거로 남긴다.2·4·8은 기울기 추정이 가능한 최소2점부터의 고정 진단 스케일이며 화면상 최적 특징 폭이나 미술 정답이 아니다.

행렬 구간 계산은 단순8꼭짓점만 보고 내부 극값을 가정하지 않는다. 양수 LMS·단조 decode/cuberoot와 부호별 Lab 구간을 사용하며 floating bound를 바깥으로 넓혔다. 이것은 모든 플랫폼의 수치 구현에 대한 형식 검증이 아니다. 원본 RGB8 내부3200개 표본을 대조한 포함 위반은0이다.

**유한 샘플만으로 진짜 수학적 불연속이나 작가의 의미를 증명할 수 없다.** 얇게 그린 무늬와 좁은 매끄러운 하이라이트가 같은 샘플을 만들 수 있다. 본 코드는 piecewise-affine와 양립하는 jump, fine edge, ridge를 구분할 뿐 “가닥” 의미를 만들어 넣지 않는다. 부드러운 곡면 조명은 여기서 계산하지 않는다. 원본 texture의 baked 변화와 독립 명암 g는 별개다.

## 반례와 실제 원본 검사

합성9사례: 일정색·선형L·이차L·계단·분리된 같은 색 두 무늬·1texel선·3texel선·1texel점·매끄러운 좁은 봉우리다.

- 일정/선형/이차: persistent 경계0, 부모 영역1.
- 계단: 원래 경계65개만 검출, 부모/미세 영역 모두2. 계단 옆에 외삽 lobe를 경계로 추가하지 않는다.
- 같은 색 두 무늬: 서로 다른 닫힌 contour2개·영역3개(배경 포함). 같은 RGB라는 이유로 위치/형태를 합치지 않는다.
-1/3texel선: coarse에서는 판단 미확정이지만 fine 양쪽 contour2개·영역3개로 남는다.1texel점도 fine에 남으며 크기로 제거하지 않는다.
- 매끄러운 좁은 봉우리: persistent0, fine/ridge 후보로 남는다. 이를 얇은 작가 무늬라고 확정하지 않는다.

실패도 보존했다(`ABLATION64.json`). 최초 구현은 계단 옆 fine 경계를65→195개로 만들었고, 매끄러운 봉우리에서 persistent130개를 잘못 만들었다. 실제 인접 변화/양쪽 모델 적합성 조건을 추가했다. 원본 검사에서는 “구간 교집합이0을 제외”하는 것만으로 모든 스케일에서 검출됐다고 잘못 판정한 오류도 찾았다. material12 X의 prefix1053→2092→11956 증가가 반례였다. **각 스케일 검출을 별도로 요구**해 현재 같은 support의 prefix는1053→31→6으로 단조 감소한다. coarse-only 신호를 삭제/확정하지 않고 불확실 레이어로 남겼다. 규칙은 `uv-affine-jump64.2`로 캐시 무효화에 포함했다.

실제 원본은59가 연결한 image15/18/20/22의 SHA를 검사했고,62의 **UV support만** 재사용했다.62의 색 label은 읽지 않았다. 원본 RGBA 변경0, 기존373셀 모두 native UV의 계층에 연결됐으며 sourceId는 기존60 그대로 명시했다. 새 프레임이 아니다.

| material(출처) | 닫힌 면 연결 성분 coarse/fine | 열린 경계 포함 contour 성분 persistent/fine |
|---|---:|---:|
|11 |2 /458 |7 /211 |
|12 |2 /310 |24 /304 |
|13 |1 /1 |180 /1096 |
|14 |1 /1 |0 /411 |

이 수는 palette 수나 의미 특징 수가 아니다. 열린 선 양쪽은 돌아서 연결될 수 있어 면 CC가1이어도 경계 증거는 남는다. 따라서 contour를 따로 저장했다. 실제 흐린/곡선 무늬의 경계가 많이 끊어져 있어 **전체 특징 마스크 구성은 아직 미완**이다. 약한 gap을 임의로 닫거나 조각 수를 줄여 성공 처리하지 않았다. 원래 반해상도 preview와 별개로 `NATIVE_SOURCE64-*`는 원본 PNG bytes, `NATIVE_EVIDENCE64-*`는512×1024의1x 증거 map이다.

sourceRGB/Q 불변식은 기존 출력에서 인접18쌍 실패를 그대로 재현했다. 서로 다른 재질/구조라도 같은 입력색과Q라는 사실을 검사하며, 그 차이를 허용하려면 별도 색 영역/palette policy 근거가 필요하다. **이 검사로 원본 RGB마다189개 family를 만들거나 새 palette를 생성하지 않았다.** 재질 ID를 바꿔도 checker의 판단은 같고, 같은 색의 다른 구조 정체성을 합치지 않는다.

## 다음 캡처 코드와 입력 계약 — 아직 실행 불가

`capture_contract64.py:validate/require`는 source/frame/renderSerial/**main/head viewId** 혼합, clean backing 누락/가짜 채움, 비복구 buffer 변경, 과대 readback을 거부한다. 합성 packet1개와 거부8사례를 검사했다. 소수 화면 좌표220.1/52.3을 정수로 반올림하지 않는다. 이 검사는 **실제 packet 확보나 C# 컴파일 검증이 아니다.**

`CpuSourceCapture64.cs`는 entry point 없는 준비 helper다. 이미 평가된 `motion.surface.outputs`의 mesh를 읽고 vertices/normals/UV/indices/material/texture/ST/factor·원래 bone/Root matrices/bindpose/blendshape를 streaming binary로 쓴다. 원본 mesh에 대입하거나 BakeMesh를 다시 하지 않는다. 각 source/view/frame/serial을 header로 묶으며 geometry/camera/plane을 별도로 쓴다. 실제 shader의 tap 좌표/개수·mode flags·source 색 공간·g 정의는 producer로부터 전달되어야 한다. 추정 기본값을 채우지 않는다.

raw camera P, raw GPU P, shifted effective P, effective GPU P, clipShift/nativeShift를 구분한다. effective P에 shift를 다시 더하는 것을 금지한다. 행렬은 column-major, 좌표계와 buffer별 y-origin을 기록한다. source UV→world→projection을 새 evaluated geometry로 재구성할 수 있도록 하며,59 topology가 같으면 hash 참조로 재사용할 수 있다.

readback helper는 ROI 하나당1MiB 이하의 직접 소유 NativeArray만 사용하고 **한 번에1개**를 완료·직접 binary streaming·Dispose한다. `ToArray`, 임시 Texture2D/PNG, 전체 RT 반복복사는 없다. CPU hash/파일/메모리 counter는 작은 요약만 요구한다. 실제 runtime 할당량은 아직 측정하지 않았으며 이 코드만으로 누수 해결을 주장하지 않는다.

clean backing은 실제 `FullFeature367.Eyes` part10이 그린 `ph.backing`의 layer10 RGBA/meta/UV를 같은 source/view/표본 위치에서 기록한다. 현재 EyeCompose는 backing meta만 사용하므로 주변 피부색을 RGBA로 만들지 않는다. layer10 RGBA는 이미 style/shading을 포함할 수 있는 **rendered pre-eye 값**이며 원본 unlit albedo와 구분해 색 공간/단계를 기록한다. 실제 alpha/coverage가 없는 경우 미확인으로 남기고 필요한 계약을 통과시키지 않는다. 이전6실패 목적지는 새 feature 좌표로 대응시키며 옛 절대 좌표를 새 프레임에 붙이지 않는다.

### global 복원과 정확한 실행 차단

`GlobalJournal64.cs`는 future snapshot을 외부 binary 파일에 쓰고 전체 값/배열을 다시 읽어 검사·SHA 기록한다. **public `Active/entries` 회수 핸들**도 유지한다. restore 후 getter의 Float32 bit/배열/texture identity를 확인해야 핸들을 해제한다. 원본 texture/buffer를 Dispose/Destroy하지 않는다. 예전60의 잃은 백업을 복구한 것은 아니다.

Legacy `SetGlobalInt`는 float storage이므로 원래 float 전체를 보존/복원하고, `Integer` API는 별도다. 빈 배열/길이 변경/회수 불가능 runtime texture는 임의로 복원 가능한 것으로 처리하지 않는다. C# journal과 capture helper는 아직 컴파일·실행하지 않았다.

**현재 정상 Play 경로는 준비 완료가 아니다.** `FullFeature367.Probe:11 → ClothRegion524.BeginProbe:134`가 `_BodyScope551` global buffer를 설정한다. 소유 필드는 private이며 `ScopeBuffer551:38`은 null이면 생성한다. 공개 Shader API에는 global buffer getter가 없다. 원래 binding을 회수하지 못한 상태에서 이 경로를 실행하지 않는다. 정확한 원래 소유 binding과 수명 보존 계약 또는 scoped local-binding 경로가 필요하며, 아직 구현/실행하지 않았다. getter 하나를 추가해도 원래 소유자가 그 buffer를 Release하면 복원이 안 되므로 참조 회수와 수명은 별개다. 새 Play 승인만으로 복구 불가능한 binding을 추정하거나 reflection으로 읽지 않는다. 남은 단계를 처리하기 전 Unity 호출도 하지 않았다.

근거: [Unity6000.5 Shader 공개 소스](https://raw.githubusercontent.com/Unity-Technologies/UnityCsReference/6000.5/Runtime/Export/Shaders/Shader.cs), [GPU projection 공식 문서](https://docs.unity3d.com/6000.5/Documentation/ScriptReference/GL.GetGPUProjectionMatrix.html), `API_EVIDENCE64.json`의 실제 프로젝트 코드 위치.

## 다음 단계와 보존

다음 구현 공백은 미세/열린 증거를 실제 색 특징의 공유 경계로 조립하는 단계와, 새 동일 프레임 투영 자료로 그 경계/얇은 폭을 검증하는 단계다. 원본에서 같은 신호인 하이라이트/무늬 의미를 임의 확정하지 않는다. R3 원본의 옛 경로가 없었던 사실을 새 알고리즘이 없다는 증거로 사용하지 않았다. 기존31 후속 함수와32 연구 색인의 근거는63 인계 그대로 유지한다.

테스트 재생: `python -B test_uv64.py`, `python -B test_capture64.py`. 실제 source 재추출은 `run_source64.py`의 기존59 registry/62 UV support/원본 model-source PNG 경로가 필요하다. 새 소프트웨어 설치·Unity·제품 default·CUA·앱 종료·reset·GC·SaveAssets·push는 수행하지 않았다. 이번 코드/증거와 기존 인계만 선택 커밋한다.
