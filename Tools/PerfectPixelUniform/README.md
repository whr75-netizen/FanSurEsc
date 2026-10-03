# PerfectPixel Uniform — 전역 격자와 원본 해상도 색 정리

## 현재 결정 V3 · 2026-10-03 — 해상도 유지와 색 번짐 정리

최신 요구: V2는 실제 생성형 시트에 결과를 주지 못했고, 확대할수록 주변의 여러 색·미세 명암이 더러워 보인다. **무손실 반복 제거와 색 잡음 정리는 다른 연산**이다. V2의 byte equality를 색 정리의 통과 조건으로 쓴 요구 해석을 수정한다. 원본·과거 출력·Unity를 보존하며 원본 크기에서 색만 정리하는 별도 경로를 웹 기본 모드로 제공한다. 정규 격자 복원을 성공했다고 바꿔 말하지 않는다.

### 구현 전 선택·수학 계약

- 후보: (A) nearest 축소/고정 목표 크기 — 특징을 버려 제외. (B) 작은 반경 bilateral + 오차 제한 팔레트 매핑 — 채택. (C) guided filter — 같은 역할의 대안이며 연속 추가하지 않는다. 미확정 격자의 강제 정렬·local warp는 제외한다.
- 좌표: `RGB(A) source[y,x] → 동일 source pixel 좌표의 색 연산 → 동일 W×H PNG`. 좌상단 원점, X오른쪽/Y아래, source px 단위, 중심 `(x+.5,y+.5)`, 부모/회전 없음, 기하 Jacobian=identity. resize/crop/sample 이동 없음. alpha와 alpha0의 숨은 RGB는 byte 그대로 유지한다.
- 색 거리: sRGB를 표준 D65 CIELAB로 변환해 `ΔE76=||Lab(a)-Lab(b)||₂`로 계산한다. 색공간 변환은 가중치·오차 측정용이며 저장 모드는 원래 RGB(A)다.
- 필터: 반경2px, `σSpace=1px`, `σColor=t`인 bilateral 1회. `w=exp(-||i-j||²/2-ΔE76(i,j)²/(2t²))*alpha(j)/255`, alpha0 이웃 제외. 저장된 sRGB byte의 weighted RGB를 round한 후보가 원본에서 t보다 멀면 원본을 유지한다. 이미지 밖 이웃은 제외한다. t=2/4/8은 보수적/표준/강 정리의 명시된 색 오차 설정이며 문헌의 보장값이 아니다.
- 팔레트: alpha≥16인 색에서 Pillow median-cut 후보 팔레트 K=64/128/256을 만든 뒤 **dithering NONE**으로 매핑한다(해당 pixel이 없으면 전체 보이는 색). 낮은 coverage의 원색 fringe가 팔레트를 과점하는 것을 줄인다. 원본 대비 ΔE76≤t인 후보만 수락하고, 초과하면 오차 제한 필터 결과를 유지한다. 보호 색도 남으므로 최종 색 수가 K 이하여야 한다고 주장하지 않는다. 이미 보이는 RGB 색 수≤K인 입력은 그대로 유지한다.
- 경계: source 4-neighbor 색 차이가 `max(12,3t)` 이상인 양 끝 pixel의 RGB를 정확히 유지한다. 이는 명시된 강한 경계와 고대비 1px 특징 보호이며, 낮은 대비의 의미 있는 특징과 잡음을 자동 구별한다는 보장이 아니다. 강한 경계를 보호하면서 잔색을 정리하는 정도를 실제 시트로 관찰한다.
- 불변조건: 입력 불변, W/H/채널 불변, alpha 및 hidden RGB byte equality, 보호 pixel RGB equality, 모든 변경 pixel ΔE76≤t(+float tolerance .001), 디더링 없음. 오류는 해당 색 단계에 귀속하며 결과 저장 전에 중단한다. 출력 label은 `source_resolution_cleanup`이고 grid 검증 상태와 분리한다.

가설/판별: 내부 저대비 변동은 감소하고 고대비 선·실루엣·크기는 유지된다. 합성 flat+noise/1px 눈·선/alpha 경계와 실제 사용자 run을 검사한다. 새 격자·재저작·게임 통합은 이번 범위가 아니다. 색 fringe가 높은 대비를 가진 원본 결함이면 이 보수적 경로에서 남을 수 있으며, alpha/matte 변경을 몰래 추가하지 않는다.

근거: [OpenCV bilateral 설명](https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html), [guided 원 논문](https://people.csail.mit.edu/kaiming/publications/eccv10guidedfilter.pdf), [Aseprite ColorQuantization](https://www.aseprite.org/api/command/ColorQuantization), [Aseprite dithering none](https://www.aseprite.com/docs/cli/#--dithering-algorithm), [Pillow quantize](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize). 외부 fixer/OpenCV를 새로 설치하지 않으며 NumPy의 직접 bilateral 식과 기존 Pillow를 사용한다. alpha 분리·색오차 제한·경계 고정은 이 도구의 보존 계약이다.

### 실행·판별 결과

웹 기본은 **색 번짐 정리 · 해상도 유지**이며 정리 강도/후보 팔레트만 선택한다. 확대 1/2/4/8배는 원본과 결과에 똑같이 적용하고 PNG를 다시 확대 저장하지 않는다. API는 `mode: cleanup, strength: 4, palette_colors: 256`; mode 생략은 과거 V2 호출 호환을 위해 lossless다. CLI는 `cleanup.py --source <원본> --output-dir <새 폴더>`이고 격자 규격/목표 해상도를 받지 않는다.

사용자 run `20261003T092818576216Z-59a6e7b8655b4cf4a637cf98f68e32a7`은 B37와 같은 source다. `graph-v3.json` WorkLoop3단계 완료: 실제 source 계산 1회 → 독립 fixture/저장결과 검사 → HTTP9조건. `docs/artifacts/building37/Uniform03/output.png`는 **1489×1056 그대로**인 색 정리 후보, 계산3.630초, alpha/hidden RGB byte 동일, 강한 경계215329px의 RGB 동일, 최대색변화3.999974ΔE76≤4. source SHA 불변. RGB 고유색154249→136682, 변경357806 visible px. 원본에서 선택한 저대비 인접쌍의 제곱색차 비율0.938642로6.14%감소했다. 이 수치는 국소 색 변동이며 특징/인지/미술 합격 점수가 아니다. 효과는 보수적인 수준으로, 고대비 fringe·원래 격자·픽셀아트 저작 문제를 해결했다고 주장하지 않는다.

9개 fixture/실제artifact 검사와 HTTP9조건 통과. 실제 아트는 재생성 없이 저장결과를 읽어 검사했다. `comparison-crop-x4.png`는 같은128×128 영역을 nearest4배로 보여주는 별도 미리보기(1032×540)이며 게임 자산이 아니다. 실제 원본의 매우낮은alpha1~15에 원색 red3367/yellow223px가 있어 matte 오염 가능성은 있지만 원인은 확정하지 않았다. 해당 색을 몰래 삭제하거나 alpha를 다시 만들지 않았다.

실제8768서버가V2로남아있어 경로/유휴상태를확인한PID36976만종료하고V3로교체했다. `live-server.json`의version3/계산SHA일치와netstat의리스너PID40068을확인했다. OS프로세스조회는기본sandbox에서거부되어승인된조회로대상을확인했고,Stop-Process실행오류후동일PID의taskkill성공을관측했다. 화면버전과색처리/격자/웹코드의합성SHA를확인해오래된계산기를새화면에서재사용하지않도록했다. 실제개인브라우저UI자동화와Unity변경/Play검사는하지않았다.

남은 범위: source-resolution 색 정리는 확인했지만 fake-pixel의 진짜 저작 격자를 복원한 것은 아니다. 낮은 대비의 유효 무늬도 색 정리 강도에 영향을 받을 수 있다. 외곽 matte 정리와 확실한 격자 복원은 해당 단계의 별도 증거/명세가 있어야 추가한다. 원본/V1/V2/Unity는 보존하며 같은 입력의 반복 생성이나 강제 축소로 대체하지 않는다.

## V2 설계·증거 — 보존 기록

사용자 확인: V1의 휘어짐은 사라졌지만 특징이 모자이크처럼 소실됐다. 원인 수정 범위는 **간격 검출 → 셀 표본화 → 출력 허용**이다. 원본·V1 결과·Unity는 보존한다. V1의 등간격 검사 성공을 정확한 픽셀 복원으로 승격하지 않는다.

후보 비교: 원본 FFT/gradient의 최소4px·강한 경계 간격·축 평균은 이번 source에 맞지 않는다. 다중 주기/배수 후보와 재구성 오차를 비교하는 근사법도 가능한 기술이지만, 미세 특징의 허용 손실을 사용자가 정하지 않았으므로 이번 기본 출력에 도입하지 않는다. **관찰된 동일 RGBA 블록을 정확히 축약하고 동일 source canvas에 완전히 복원할 수 있는 경로**를 채택한다. 숨은 작가의 원래 해상도나 미술 합격을 추정하는 알고리즘은 아니다.

구현 전 수학 계약:

1. 입력 `I[y,x,c]`는 원래 RGB/RGBA uint8, source 원점 좌상단, X오른쪽/Y아래, 단위 source px, pixel centre `(x+0.5,y+0.5)`. 부모/회전 없음. 분석 중 색·alpha threshold·crop·resize 없음.
2. 각 축의 **모든 채널 실제 변화 경계** 좌표를 구한다. 한 축의 변화 위치 차분 GCD는 그 축을 설명하는 정수 step의 상한이다. X/Y의 공통 step은 두 GCD의 GCD이며 축 평균이 아니다. flat 축은 다른 축의 증거를 재사용한다. 정수 약수 후보를 기록하고 가장 큰 무손실 반복 표현을 선택한다. 2/3px 기본 단위를 배제하지 않는다. 관찰된 동일색 그룹 때문에 더 작은 작가 격자와 구분할 수 없는 한계는 공개한다.
3. 전역 위상은 `o=첫 변화 경계 mod s`. 정수 cell map `q(x)=floor((x-o)/s)`로 source 전체를 덮는다. canonical index는 `q-min(q)`다. cell의 source 교집합 안에서 중심을 취한다. source에서 잘린 가장자리 cell도 명시적으로 보존하며 source canvas와 full-cell canvas의 차이를 receipt에 기록한다. 내부 affine inverse는 `source=s*(canonical+0.5)+offset`, Jacobian `diag(s,s)`다. 경계별 이동·누적 round·비균등 scale 없음.
4. 출력 `O[j,i]`에서 **같은 cell map**으로 재구성 `R[y,x]=O[qy(y),qx(x)]`. 전체 source의 RGBA 불일치가 정확히 **0**이어야 출력한다. 허용오차는 uint8 byte equality 0, 기하 정수 계산 오차0. 이 조건은 단일 픽셀 눈·선·alpha 연결/구멍도 source 재표시 범위에서 보존한다. 전체 평균 오차로 작은 특징 손실을 숨기지 않는다.
5. 공통 step≤1, 경계 증거 부족, 비균일/분수/보간/연속 명암으로 정확 복원이 안 되면 `rejected`로 중단한다. 원본과 실패 진단만 보존하며 PNG를 성공 결과로 쓰지 않는다. 이미 native1px인 입력과 격자 없는 그림의 의미는 raw byte만으로 구별할 수 없으므로 이 경로에서 새 정규화라고 꾸미지 않는다.
6. 확대는 canonical의 정수 nearest 반복 표시다. 임의 축소는 서로 다른 픽셀을 버릴 수 있으므로 모든 작은 화면 해상도에서 특징 보존을 약속하지 않는다. 이번 변경은 Unity의 실제 표시·공통PPU를 바꾸지 않는다.

최소 마지막 검사: 2/3/4/8배의 알려진 RGBA 복원, 가는 선/눈·alpha-only 격자, 축별 다른 배수의 공통기본간격, 잘린 가장자리, 블록 내부1px반례·연속 gradient·단색 거부, 실제B37 거부, HTTP에서 거부입력의 PNG 미생성/진단노출. 원본 B37 측정은 source와 보존된 출력만 읽었다: visible RGB 154,249색, alpha256단계, RGB 변화 경계 차분 GCD X/Y=1. 기존 inverse 표시의 visible 불일치89.56%는 특징 손실률이나 미술 점수가 아니다.

근거: [Aseprite 정수 nearest 확대](https://www.aseprite.com/api/command/SpriteSize), [CLI 확대](https://www.aseprite.com/docs/cli/); [공개 fixer의 배수·콘텐츠주기·drift·재구성 오류 논의](https://github.com/Retro-Diffusion/pixel-art-fixer/blob/main/docs/HOW_IT_WORKS.md). nearest는 아는 격자의 표시 기능이지 격자 복구 증명이 아니다. V2의 GCD+정확 byte 재구성은 이 프로젝트의 명시적인 보수적 구현이며 외부 fixer를 설치·실행했다는 뜻은 아니다.

### 현재 실행·실제 증거

`Start_Uniform_Web.cmd`·`http://127.0.0.1:8768`의 V2를 사용한다. 같은 입력을 선택하면 verified_lossless 결과 또는 **변환 중단 진단**이 표시된다. 성공 PNG는 정규 native 크기로 저장하고 확대는 CSS에서만 한다. 실패에는 source bytes와 failure.json만 남으며 output.png는 없다. CLI 실패 exit code2는 무손실 모델 거부다. `--engine/--deps`는 V1 호출의 경로 호환 인자이며 V2 검출은 원본 엔진을 호출하지 않는다. 원본 엔진 파일도 수정하지 않았다.

`graph-v2.json`의 실제 시트 판정 → 독립 fixture → HTTP 마지막 검증은 3단계 완료했다. `docs/artifacts/building37/Uniform02/failure.json`: source 1489×1056, 양축 변화 경계 차분 GCD1, **NO_LOSSLESS_COARSER_LATTICE**, 판정0.032초. 12개 기술검사(배율2/3/4/8, 가는 선/눈, 축별 배수 공통2, 부분 가장자리, 미세주입·gradient·단색·hiddenRGB 거부, alpha-only, flat축, 실제source/CLI)와 HTTP7조건 통과. 알려진 HTTP입력 처리0.042초/계산0.0016초는 그 fixture의 측정이며 일반 입력 시간 보장이 아니다. 새 V2 게임용 canonical이나 원본 아트 재제작은 하지 않았다.

정수 반복 셀 밖의 보간/명암 차이가 있는 입력·비정수 확대·혼합 격자는 이번 보수적인 모델에서 거부될 수 있다. 이 한계를 임계값 완화나 팔레트 감소로 숨기지 않는다. source가 이미 native1px이면 원본을 쓰며, 더 굵은 픽셀 아트를 원할 경우 별도 저작/근사 복원의 정보 손실 계약이 필요하다. V1의 graph.json/recovery.json과 314×223 결과는 보존된 과거 증거이며 V2 제작에 재실행하지 않는다. Unity의 바닥/가구 표시 밀도 문제는 별도 미해결이다.

마지막 실제 서버 확인에서 V2 HTML과 V1 메모리 계산 서버가 함께 남아 있던 문제를 발견했다. 이전 실행기를 교체했고 버전2/계산SHA 일치/리스너1개를 `Uniform02/live-server.json`에 기록했다. 화면은 health의버전2 확인 전 처리버튼을 활성화하지 않는다. 새실행기는Windows동일포트다중bind를막고 같은코드SHA의V2만재사용한다. 서버부분수정후 HTTP7조건을 `web-tests-final.json`으로1회재검증했으며 순수검출12건과실제source판정은변경되지않아재실행하지않았다.

## V1 설계·증거 — 보존 기록

사용자 관찰은 공식 웹 데모에서 형태가 볼록/오목 거울처럼 뒤틀리는 현상이다. 최근 upstream 변경으로 단정하지 않는다. 원본의 `refine_grids`는 각 경계를 이미지 gradient 근처로 옮기고 그 위치에서 다음 경계를 누적한다. 서로 다른 원본 폭이 각각 출력 한 칸이 되어 국소 확대/압축이 생길 수 있다. `refine_intensity=0`도 매번 반올림한 위치를 재사용하므로 분수 간격의 누적 오차를 없애지 못한다.

**채택:** 원본 PerfectPixel 자동 간격 검출을 재사용하고, 후속 sampling을 하나의 전역 등간격 좌표변환으로 교체한다. 이는 무수정 원본의 최종 출력이 아니라 별도 correction이다. 원본 엔진·입력·옛 결과·Unity 배치는 수정하지 않는다. 새 시트 제작이나 개별 사물 크기 보정은 범위에 없다.

## 좌표·계산 계약

- 입력은 원래 해상도의 RGB/RGBA uint8, 원본 픽셀 중심 좌표는 `(k+0.5,l+0.5)`다. 브라우저의 1024px 축소, 팔레트/alpha 변환, 수동 목표 해상도, 실패 시 8px fallback은 없다.
- 원본 `detect_grid_scale`의 FFT→필요 시 gradient 분기와 반환값을 변경하지 않는다. 최종 정수 크기로 반올림하기 전 검출 개수 `(gx,gy)`에서 공통 간격 `s`를 원본과 같이 계산한다: 축 간격 `W/gx,H/gy`의 비가 1.5 초과면 작은 값, 아니면 평균. 호출·backend·파일 SHA를 receipt에 기록한다.
- 각 축 경계의 RGB 차이 프로파일 `e[k]`에서 `C=Σ e[k] exp(-2πik/s)`를 계산하고 전역 경계 위상 `o=(-s arg(C)/(2π)) mod s`를 구한다. 투명 숨은 RGB는 위상 계산에서만 opacity로 가중하며 alpha 경계도 포함한다. 입력/출력 색은 변경하지 않는다. `|C|/Σe`는 진단값이고 검출 정확성의 증명이 아니다.
- 원점 `c0=(o+s/2) mod s`, 좌표 `ci=c0+i*s`를 **매번 원점에서 직접 계산**한다. X/Y가 같은 `s`를 쓴다. 원본 범위 `[0,W)×[0,H)` 안에 중심이 있는 표본만 취한다. 끝 경계를 W/H에 강제로 맞추지 않으며 마지막 칸을 늘리거나 복제하지 않는다.
- 출력 canonical PNG의 `(i,j)`는 원본 `[floor(cy_j),floor(cx_i)]`의 정확한 RGB(A)다. 잠재 좌표변환의 Jacobian은 `diag(s,s)`로 일정하다. nearest 표본 오차는 축당 원본 0.5px 이하다. 정수 source index 간격이 4/5px로 번갈아도 이 반 픽셀 양자화이며, 경계 탐색/누적 round에 의한 warp가 아니다.
- PNG를 저장한 뒤 추가 축소/확대/재정규화하지 않는다. 1/2/4/8배 표시는 CSS 정수 nearest 미리보기이며 원본과 출력 해상도를 구분한다.

## 실패·한계와 판정

검출 None/비유한 간격/1px 미만·RGB 경계 없는 단색 입력·비지원 모드는 오류로 중단한다. 격자가 불명확하거나 FFT/gradient가 다른 후보를 내는 경우 경고를 표시한다. 위상 신호가 없으면 0의 좌표 관례를 명시하고 `unconfirmed`로 표시한다. 검출된 간격과 위상이 틀리면 세부 특징을 잃을 수 있다. **등간격 성공은 가짜 픽셀의 정확한 복원·디자인 합격이 아니다.** 이미 원본에서 실제 선이 휘어 있으면 이 경로는 그것을 펴는 재그리기를 하지 않는다.

독립 판정: 알려진 정수 블록 원본의 전체 RGBA 복원, 분수 간격의 좌표 표식/직선에서 누적 변형 없음, 빈 이미지의 실패, 같은 실제 시트에서 기존 비균일 경계와 새 등간격 비교, HTTP에서 입력 bytes/결과/receipt 보존. 실제 Unity의 바닥/가구 픽셀 밀도 불일치는 이 도구 작업의 완료 기준이 아니다.

## 사용

`Start_Uniform_Web.cmd`를 실행하고 이미지를 선택한 뒤 **정규화 실행**을 누른다. 로컬 `http://127.0.0.1:8768`만 사용하며 결과와 입력은 `runs/<고유 실행>/`에 보존한다. 외부 전송은 없다. RGB/RGBA 정지 이미지, 4MP/20MiB 제한이다. 결과 PNG와 receipt를 다운로드할 수 있다. 새 탭은 같은 서버를 재사용한다.

CLI는 `uniform.py --source <원본> --output-dir <아직 없는 결과 폴더>`다. 기본 엔진은 `Desktop/GPT/3/perfectPixel-main/perfectPixel-main`, 의존성은 기존 `LocalOnly/PerfectPixelOpenCV`이며 `--engine`, `--deps`로 경로만 변경할 수 있다. 수동 출력 크기는 받지 않는다.

`graph.json`은 실제 B37 시트 → 전역 계산 → 마지막 기술 검증의 WorkLoop 그래프다. 기존 출력이나 이미 끝난 상태를 반복 실행하지 않는다. 테스트는 제작 이후 한 번에 수행하며 그래프의 완료는 이 보정 도구의 기술 조건에 한정한다.

## 실제 증거

- B37 원본 1489×1056 → 별도 결과 **314×223**, 자동 공통 간격 **4.7472324723 원본 px**. 계산 0.346초, 등간격 오차 최대 `1.98e-13` 원본 px, nearest 중심 오차 최대 `0.49929` 원본 px. `docs/artifacts/building37/Uniform01/output.png`·`receipt.json`에 원본/엔진 SHA와 선택 좌표를 보존했다. 출력 가장자리 정책 때문에 검출기의 반올림 높이 222와 실제 표본 수 223은 다르며 강제로 맞추지 않았다.
- 이 시트의 위상 coherence X=0.0213/Y=0.00173으로 약하다. **격자 미확정**으로 표시한다. 출력은 국소 warp를 하지 않지만 원본 특징이 완벽히 복원됐다고 승인하지 않는다. 기존 301×211·Unity 참조는 그대로다.
- 최초 마지막 검사에서 단색 입력이 원본 FFT의 허위 간격을 받는 반례가 실패했다. RGB 경계가 없는 입력의 거부를 추가했다. 실제 시트 출력은 재계산하지 않고 `recovery.json`에서 영향받은 실패 분기와 전체 기술 검사 5건을 통과했다. 첫 실패와 후속 통과 기록을 모두 보존했다(`tests.json`, `tests-after-blank-fix.json`).
- HTTP 6개 조건 확인: 알려진 4배 블록 입력의 정확한 RGB 복원, 원본 bytes/PNG/receipt 다운로드, 외부 Origin 거부, 단색 실패 표시·보존, HTML의 canvas 축소 없음. 시험 입력 HTTP 처리 0.081초이며 일반 이미지 전체 처리 시간 보장은 아니다(`web-tests.json`). 실제 개인 브라우저 UI 조작은 하지 않았다.
- `output-preview-x4.png`는 **314×223 canonical의 정수 nearest 4배 미리보기 1256×892**다. canonical PNG의 재가공본으로 사용하지 않는다. 새 생성 이미지가 아니다.

## 기술 근거

- [원본 PerfectPixel](https://github.com/theamusing/perfectPixel/blob/main/src/perfect_pixel/perfect_pixel.py): 자동 검출/경계 refine와 sampling을 구분한다.
- [공식 웹 구현](https://github.com/theamusing/perfectPixel_webdemo/blob/main/services/perfectPixelService.ts), [웹 입력 전처리](https://github.com/theamusing/perfectPixel_webdemo/blob/main/App.tsx): 국소 경계 탐색과 입력 축소는 각각 별도 원인 후보다.
- [NumPy DFT 정의](https://numpy.org/doc/stable/reference/generated/numpy.fft.fft.html): 위상의 부호/주기 계산 근거. 임의 주파수 한 점의 합을 직접 계산한다.
- [SciPy affine pull transform 정의](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.affine_transform.html): 출력→원본의 일정 행렬/offset 방식 근거. SciPy 추가 설치 없이 직접 nearest index로 구현한다.
