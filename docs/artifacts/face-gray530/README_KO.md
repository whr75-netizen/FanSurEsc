# 530 — 얼굴 초기화·테스트 전환 조사: 실제 음영 경로 확인, 반복 회색 원인 미확정

사용자의 반복되는 얼굴 회색 신고는 미해결입니다. 이번에 관측한 첫 얼굴의 어두운 톤은 같은 재질/UV의 기존 ×0.72 음영으로 계산 확인됐지만, 사용자가 본 모든 회색 전환을 재현했다고 단정하지 않습니다. 제품·재질·피부색·serialized 설정은 수정하지 않았습니다. 529 공간 경계 확장은 종료 상태 그대로입니다.

## 코드에서 확인한 상태 소유권

- `NativePlayer395.Awake`는 source output 전체를 숨기고 warmup90 후 전체를 다시 켭니다. 얼굴만 회색 재질로 바꾸는 분기는 없습니다. `HeadLocal367`은 얼굴/머리를 별도 RT로 렌더하고 같은 픽셀 크기로 합성합니다. 이 분리 자체와 회색 오류는 다른 문제입니다.
- `MotionView331.Initialise`는 원 재질을 복제하고 texture/색/keyword를 복사합니다. `Full319View335.Initialise`는 독립 얼굴 재질과 legacy 재질을 만들며 `HeadLocal367.CopyFields`가 head의 style/face 플래그를 복사합니다. 최근 옷 테스트는 얼굴 플래그·재질·텍스처를 쓰지 않았고 저장된527 before/after 값도 같습니다. 다른 세션이 실제 사용한 테스트 코드는 확인하지 않았습니다.
- 실제 프리팹 얼굴은 `_04` 텍스처/흰 Color, MToon shader, DebugMode0, indexed MPB 없음입니다. faceMain/faceProvider/style/integrated는 모두 true입니다. 얼굴과 몸의 role3/role7 reflectance 값은 둘 다 `(0,.95,0)`입니다. 얼굴에 다른 threshold가 설정됐다고 추정하지 않습니다.
- 회색 진단 출력은 `Auto245Fragment.hlsl`과 `BodyPalette302.hlsl`의 Stage1 `shadow.xxx`에 실제 있습니다. 그러나 현재 global Stage2이며 LegacySignals/Eyes 패스가 각 draw 전 Stage2·Membership1·Probe0을 지정합니다. 이번 관측에서 그 진단 모드가 활성화됐다는 증거는 없습니다.

## 실제로 실행한 범위

기존 PID22792의 clean Edit에서 한 번 제어된 paused Play 진입 후 첫 최종 렌더2개를 관찰했습니다. 새 Walk/전체루프/입력 합성은 없었습니다. 기존 프리팹 runInputTest=0입니다. 임시 observer는 Editor 콜백만 사용해 재질을 바꾸지 않고 first source/provider/prepared/final의 얼굴 crop을 저장한 뒤 본인 콜백 제거·배경 실행 복원·Play 종료를 요청했습니다.

첫 관찰 JSON은 Unity의 중첩 custom-list 직렬화에서 표본 목록이 빠져 float/UV 증거가 저장되지 않았습니다. 이미지8개와 lifecycle scalar 기록은 보존했습니다. 이를 숨기지 않고 **한 번의 재진입 첫 렌더1개**에서 작은 sparse binary로 필요한 값만 회수했습니다. 기존 두 렌더를 재촬영하거나 전체 루프를 반복하지 않았습니다. 초기 paused 진입은 asynchronous 자원을 warm할 수 있어 자연스러운 무정지 cold-load timing과 같다고 주장하지 않습니다.

연결 중 죽은24412의 ENOENT, 한 번의 빈 tools 응답이 있었습니다. 관찰 산출물 부재로 미실행을 확인하고 살아 있는22792의 공식 instance를 선택해 읽기로 상태/도구 등록 회복을 확인한 뒤 실행했습니다. 계정·보안·라이선스 설정을 바꾸거나 우회하지 않았습니다. 현재 blocker는 없습니다. 로그의 계정 API/라이선스 오류와 빈 도구 목록의 인과는 확정하지 않았습니다.

## 같은 재질·UV에 의한 계산 증거

source59/provider64/prepared56/final56개의 얼굴 skin role4 표본을 회수했습니다. 각 단계에서 `max(R,G,B)-min(R,G,B)<1e-5`인 무채색 skin 표본은0입니다. 이것만으로 사용자의 회색 신고가 없었다고 결론 내리지는 않습니다.

provider 중 source와 UV 오차≤1e-5로 대조 가능한43표본은39개가 `ownRGB×.72`,4개가 원색 유지였습니다. 음영 최대 오차는 **5.4836273e-8**이고 legacy classifier0/1과43개 모두 일치합니다. 나머지21개는 같은 표면으로 가정하지 않았습니다. UV 대응은 pigment lookup 비교 근거이며 source/provider의 삼각형 topology가 동일하다는 뜻은 아닙니다.

예: source 선형 RGB `(0.9609375,.74658203125,.58984375)`에서 `.72`를 곱하면 `(.691875,.5375390625,.4246875)`이고 실제 provider는 `(.6918750405,.5375390649,.4246875048)`입니다. 해당 legacy classifier는0입니다. source physical 입력의 NdotL은−.35674271, direct attenuation .57167870입니다. provider mesh의 모든 법선/조명값이 source mesh와 같다고 확대 해석하지 않습니다.

최초로 이 어두운 endpoint를 만드는 확인된 패스는 `FullFeature367.LegacySignals` → `LegacySignals335.shader` → `BodyPalette302.hlsl`입니다. `Auto245Palette`의 role3에서 shade=ownLit×.72, Stage2의 shadow 판정이 그 shade를 고릅니다. provider `LegacyProvider335.shader`는 `Restore250R2/Auto245Fragment.hlsl`의 동일 얼굴 규칙을 씁니다. source/raw 원색은 유지됩니다. 즉 이 관측은 테스트가 얼굴만 회색으로 덧칠한 결과가 아닙니다.

43표본의 legacy colour와 provider가 완전히 같았고 provider→head prepared도 RGB 오차0입니다. main final은 같은 UV를 다시 찾아 좌표차 `(0,−2)`와 깊이 offset 약.018461을 확인했으며43개 모두 RGB 오차0입니다. 같은 화면좌표나 role만으로 같은 표면이라고 가정하지 않았습니다. 여기서는 후속 합성/history가 새 회색을 만든 증거가 없습니다.

## 별도 관측과 남은 최소 증거

두 진입 모두 frame94에서 ready/connected/head=true, Canvas 표시 대상 있음, presentSerial0이었고95번에 첫 presentSerial1이 기록됐습니다. **첫 생산 전 Canvas readiness gap**은 확인됐지만 그 순간의 실제 표시 RGB는 회수하지 않았습니다. 전체 RT의 미생산 상태만으로 얼굴만 회색인 현상을 설명하거나 이 별도 gap을 얼굴 원인으로 패치하지 않았습니다.

반복 회색 원인 확정에는 **실제 회색이 보이는 순간과 바로 전/후**의 동일 프레임 자료가 더 필요합니다: 어떤 테스트의 시작/종료/Play 단계인지, 사용자가 본 출력이 GameView/local target/provider인지, source·legacy class·provider·final의 RGBA/UV/meta, Stage/Debug 값과 재질/텍스처/MPB, 실제 capture/history 상태입니다. 기존 작은 sparse 포맷으로 회수할 수 있고 새 전체 애니메이션이나 새 렌더 엔진은 필요하지 않습니다. source부터 회색인지, provider에서 생기는지, final/history에서 생기는지를 그 사건에서 구별해야 합니다. 현재 자료 없이 피부 상수·fallback·그레이 제거 보정은 하지 않습니다.

두 관찰 후 직접 Play=false/paused=false/compiling=false/updating=false, cloth/curveOFF, background=false, capture0, clean GameMap1을 확인했습니다. 임시 콜백은 종료 경로에서 제거했습니다. 사용자 QualitySettings/TimeManager 해시도 보존합니다. Library403은 재시도하지 않았고 산출물은 로컬입니다. 초기 회색 문제나 전체 프로젝트가 해결됐다는 표시는 하지 않습니다.
