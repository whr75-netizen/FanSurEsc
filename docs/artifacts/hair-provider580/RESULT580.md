# 580 얼굴 색 공급 계약 수정과 실제 회전

579의 얼굴색 오류는 **눈 합성 이전 얼굴 Base 레이어의 잘못된 셰이더 교체**였다. 이를 최소 수정했고 동일 포즈, 기존 세 방향 인접 Walk 6쌍, 좁은 회전 8쌍, 실제 100→170° 회전 50쌍을 완료했다. 전체 시간 품질·모든 방향·실시간 채택은 완료가 아니며 기본 OFF다.

## 원인과 계산

100°·Walk phase .475003362, main (227,48)/head (230,48)은 관측 위치이며 수정 조건이 아니다. 실제 코드/입력을 연결했다.

1. `FullFeature367.Eyes`는 `styleEnabled && faceProvider`일 때 원본 face-provider 재질을 선택한다. 실제 설정은 둘 다 true, 재질은 `Restore335LegacyProvider`, texture `_04`, colour factor (1,1,1,1)였다.
2. `HeadRegion502.Draw(kind=3)`가 그 재질까지 `Independent502`로 교체했다. 원래 `Auto245Fragment.hlsl`의 기존 팔레트 색 공급 대신 일반 MToon 조명 색을 계산했다. 처음 차이가 생기는 곳은 `layers[8]` Base RGB다. EyeFeature348은 최초 관측 출력이었지만 최초 생성 단계는 아니었다.
3. Base meta는 양쪽 `(13.7673817,4,2,1)`, UV는 `(0.497762084,0.493574649)`로 같다. Base RGB만 피부색 `(0.9609375,0.7871094,0.628417969)`에서 `(0.07405918,0.0846116245,0.141855076)`으로 바뀐다. Backing alpha/depth는 0이며 눈 feature winner는 0이다. Hair는 각각 0.0917759/0.0900335 깊이만큼 뒤에 있고 Brow도 비어 있다.
4. 따라서 Evaluate의 `cov(Base)=true`, Backing 교체=false, Hair 앞가림=false이며 `c=Base.rgb`, `o=(Base.role,Base.eye,Base.depth,0)`가 그대로 출력된다. 같은 소유권에서 색이 다른 이유는 표면/UV/깊이 이동이 아니라 공급 셰이더 정책의 불일치다. 피부색을 고정하는 패치는 만들지 않았다.

## 최소 수정

소스 커밋 `c216d3ebdc4922730dceb74500e8c9ff46fdb2f0`.

- `HeadRegion502.Draw`: 기존 independent draw에서 재질이 명시적인 `f.legacyProviderMat`일 때만 공급 정책을 보존하는 어댑터를 고른다. 좌표·프레임·방향·모델 삼각형 번호 분기는 없다.
- `LegacyProvider580.shader`: 원본 `LegacyProvider335.shader`의 모든 재질 속성·vertex·colour/meta/UV fragment와 기존 Auto245 색 계산을 유지하고, 같은 `Region502Clip`만 추가했다. shader 이름/include/clip을 제거하면 원본 소스와 정확히 같다. 깊이, 알파, 블렌드, 눈 특징, 영역 선택 비용, 가림 epsilon과 원본 에셋은 변경하지 않았다.

수정 후 동일 포즈의 Base RGB와 eyeOutput이 모두 원래 피부색으로 복구됐다. meta/UV/alpha/owner가 같으며 선택 마스크·영역 owner도 같다. 별도 Play 사이 원본 곡선/패킷에는 미세 차이가 있고 mask의 depth 채널21표본이 달라 전체 버퍼 비트 동등 최적화라고 주장하지 않는다. 이 변화는 얼굴색 오류 수정이지 색/명암의 새 디자인이 아니다.

## 실제 검증

| 구간 | 실제 완료 | 확인 범위 |
|---|---:|---|
| yaw80/170/260 | 각2쌍, 합6쌍 | 실제 인접 Walk, 같은 카메라/시간, 색 공급·경계·가림·눈 입력 회귀 |
| 96.47→100→96.47° | 8쌍 | 실제 Walk와 RotateTowards, 기존 문제 포즈 포함 |
| 100→170° | 50쌍 | 실제 연속 회전, 자동 입력 revision48까지 갱신, 마지막2프레임 같은 뷰 재사용 |

모든 구간에서 카메라/시간/포즈가 쌍 사이 같았다. 머리 ROI 밖 전신 RGB 변화, 선택 경계 밖 쓰기, 추가 머리가 source ray의 앞 불투명 얼굴을 덮은 판정은 0이다. 이 수치가 원본 경계를 자기 마스크로 검사한 것만으로 전체 가시/미술 품질을 인증한다는 뜻은 아니다. 원본 전신 960×544는 모두 유지하고 모든 머리 프레임의 접촉도도 확인했다.

얼굴의 같은 소유권 색 변조는 재발하지 않았다. 전체 비헤어 동일 meta 색차는20표본으로,17표본은 기존 OwnerLines333 외곽선 audit의 reason0↔1과 정확한0.55배/역수 전환으로 설명된다. 나머지3표본은 넓은 회전35/45/49번의 기존 내부선 reason2 및 어두운 팔레트 색이다. paletteAudit를 저장하지 않았으므로 정확한 팔레트 입력/디자인 타당성은 미확인이다. 이 별도 문제를 이번 얼굴 공급 수정에 섞지 않았다.

눈 intrinsic와 원본 입력은 같지만 가시성 차이는 yaw170 국소7표본, 넓은 회전126표본이다. 따라서 눈 불변/깜빡임 전체 해결이라고 보고하지 않는다. 저장 자료에서 eye2 홍채 가시 픽셀 수가17→18→19번에1→0→1이다. 기존 (224,53)은 intrinsic가 홍채3→흰자1로 이동하고, 옆 (223,53)은 source area .9925816→.7614231→.4844282, selected hair1→1→0이다. 18번에는 기존 위치가 흰자가 되고 옆 위치는 머리에 가려져 홍채가 잠깐 없다. 고정 화면 좌표만의 ABA로 판단한 것이 아니라 stable eyeID/feature 및 입력/선택을 대조했다. 정상 운동/가림과 불필요한 시간 변화를 최종적으로 구분하려면 해당3프레임의 원본 눈 subpixel 지원과 가시 영역 연결 검사가 남는다. `EYE_EVENT18_580.json`에 근거를 보존했고 시간 필터나 이전 프레임 복사를 추가하지 않았다. 속눈썹의 다른 단일 프레임 출몰도 원본과 후보 모두에 있어 별도 미판정이다.

## 전달·비용·복원

메인.html에서 새로운 전신 비교를 표시한다. 넓은 구간 GIF는1,369,514B/50프레임/830ms, 무손실 WebP는660,590B/833ms다. 좁은 구간 GIF218,194B/8프레임/130ms, WebP110,376B/133ms다. GIF의10ms 단위 제약과 정상60Hz 원본 시간을 구분했고 프레임을 버리지 않았다. 구간 끝에서 재생이 반복되는 연결은 실제 회전으로 검증한 전이가 아니다. 전체 Walk81루프나 단일80→170 연속 촬영으로 표시하지 않는다.

생성/패킷 CPU 시간은 QUALITY580.json에 별도 기록한다. 기존 비용은 여전히 남아 있으며 이번에는 성능 최적화나 할당 측정을 하지 않았다. Player FPS/GPU 시간으로 해석하지 않는다. 컴파일/실제 shader 렌더 통과, Console error0. 복사 원본에 있던 `_FORWARD_PLUS` deprecation과 새 shader/Unity meta의 템플릿 공백 경고는 별도이며 기능 오류로 숨기지 않는다.

Edit clean, Play/paused/compiling false, head/auto/clothes OFF, input0, captureDelta0, background false를 직접 확인했다. 입력·Animator·시계 복원과 사용자 Quality/Time 해시 보존. 손/Body0·추가 명암 설계·그라데이션·디스크 감사·P드라이브·Library403 재시도는 하지 않았다. 다른 전체 얼굴 회색 신고까지 동일 원인으로 확정하지 않는다.

설치된 Chrome의 실제 메인 화면과 로컬 링크7개를 검증했다. 회전은 실제 Walk와 root RotateTowards로 실행했으며 PlayerMovement 입력 컨트롤러 자체의 end-to-end 시험은 아니다. 첫 호출 로그의 오래된 좁은 구간 설명 대신 실제 ROTATION579.tsv/카메라/phase 기록을 조건 근거로 사용한다.
