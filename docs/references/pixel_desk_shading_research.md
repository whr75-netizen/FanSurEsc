# 픽셀 책상 명암 — 공식 제작 자료와 적용 후보

## D22 현재 결정 — Unity 기지의 고정 PNG / 실제 메시 조명 비교

사용자는 명암을 이미 명암이 들어간 텍스처로 대체했는지 확인하고, 기지 조명 옆에서 이미지와 3D를 함께 시험하도록 요청했다. D21 최종 PNG에는 계산된 명암이 고정돼 있지만 원재료는 별도 4색 목재 무늬이며, 저장된 Blender 모델은 재질 없는 12개 상자였다. Unity에는 실제 메시와 원재료를 연결하고 주광 normal·shadow 및 기존 로컬광을 3단계 명암에 입력하는 비교 셰이더를 새로 적용했다. 최종 PNG를 3D 재질로 쓰지 않았다.

실제 GameMap1 PlayerCamera의 96PPU 고정 투영에서 PNG RGB 오차0, 실루엣 IoU1.0, 무조명 3D 출력의 재료4색 외 픽셀0. 주광 반전은 이미지0/3D1,015픽셀 변화였다. 기존 로컬광은 양자화 전9,133픽셀의 입사광이 달라졌지만 최종색은1픽셀만 변했다. **현재 램프 반응은 시각적으로 충분하다고 판정하지 않는다.** 첫 실행의 Forward+ 변형 누락과 trial02 촬영 중단을 보존하고 수정 후 trial03에서만 기술조건을 충족했다.

기법·변환·실패와 실행 증거의 상세 계약은 [D22 Unity 비교](../../Tools/PixelUnityProbe/README.md). 씬의 `PixelDeskLightingComparison_D22`와 실제 `LocalOnly/PixelUnityProbe22/trial03` 캡처가 결과다. 고정 시점 내부선 캐시, Point/무압축/밉맵 없음, AA/후처리 OFF 조건이며 자유 줌·회전 전체의 픽셀 보존은 미검증이다. 생성 목재의 순수 albedo 분해, 유색광 틴트, 추가 Point/Spot, 임의 메시/시점과 외형 만족도는 완료로 확대하지 않는다. 조명 표현을 바꾸라는 후속 요청 시 재료 재생성보다 양자화 입력·임계값과 조명 종류의 계약부터 재개한다.

## 사용자 확정과 현재 사실

사용자는 D15/base02 텍스처가 훨씬 나아졌다고 확인했다. 첨부 원본의 나뭇결·원본PerfectPixel66×64 재료·UV밀도를 유지한다. 명암과3D느낌은 미승인이다. 최신 요청은 명암 관련 웹자료 조사이며 아래 대안은 아직 구현하지 않았다.

현재 출력은 `LocalOnly/DeskBlender15/base02/desk.png`, 원본은 같은 폴더 `desk.blend`. D14저장모델의 실제노드를 읽기전용으로 확인했고 D15는 동일재질설정이다. 광원0개, 최종색경로는 원본texture×면tint×AO2단계→LospecEmission(1). 실제직사광/반사잔존이 원인이라는 설명은 틀리다. 강한조명처럼보이는 색영역 배치가 문제라는 것은 구현과사용자피드백을 연결한 해석이며 단일미술원인의증명은 아니다.

## 공식 자료 비교

| 출처 | 공개 기법 | 현재 책상에 연결할 부분 |
|---|---|---|
| [Never’s End GDC2026](https://media.gdcvault.com/gdc2026/Slides/Juckett_Ryan_HowWeDrawA3DSpriteWorldTheStylizedArtOfNeversEnd.pdf) PDF페이지35,39~44 | diffuse/specular/AO ramp 분리, shade albedo/tint, vertex bias, 편집normal, 별도caster/receiver | 가장 직접적인3D→sprite사례. 그림자용색/위치제어를 분리하고 불필요한self-shadow를 제한 |
| [Unity Toon Shader 기본3색/Shadow Control Maps](https://docs.unity3d.com/Packages/com.unity.toonshader@0.8/manual/Basic.html) | Base/1st/2nd Shade Map과 UV의고정그림자위치map. BaseMap공유가능 | 승인된나무무늬를공유하면서 그림자영역과색만별도데이터로관리 |
| [Guilty Gear Xrd 제작자GDC자료](https://www.ggxrd.com/Motomura_Junya_GuiltyGearXrd.pdf) PDF페이지17~23 | threshold/light vector/normal의제어, vertex별shade bias, 물체별light vector, 독립적인lit/shade색선택 | 단순히조명을끄거나cel threshold만넣어서는의도한2D명암이되지않는구체적제작근거 |
| [ProPixelizer 공식 Uber Shader](https://propixelizer.github.io/docs/technical/ubershader/) | lighting ramp, sceneambient↔constantambient, 별도의normal/edge설정 | scene조명으로인한불필요한색변화를제한하는기성도구후보. 현재프로젝트에설치/사용하지않음 |

Unity Toon Shader와GuiltyGear는픽셀책상전용도구가아니다. 전달가능한것은명암제어원리이며동일외형을보장하는프리셋이아니다. Never’s End전체렌더러가필요하다는뜻도아니다.

## 제안 — 승인된무늬 + 부품역할기반그림자마스크

현재의일괄적인면tint×AO를최종디자인권위로삼지않는다. 기본/일반그림자/깊은틈에사용하는색관계와그림자가나오는영역을분리한다. 3색이라는말은이미지전체를3색으로재분류한다는뜻이아니다. 승인된texture는각영역에계속존재한다.

제안표현은 `C=(1-M1-M2)A0 + M1*A1 + M2*A2`, `Mi∈{0,1}`, `M1*M2=0`이다. A0는승인된재료, A1/A2는동일무늬의그림자용색설정이다. RGB를검정으로일괄곱하는한개계수보다부위/재료별로색관계를지정한다. 색설정자체의미술판정은사용자권위다.

M1/M2는책상템플릿의상판돌출밑,서랍앞판경계,깊은조립틈같은구조역할로관리하는후보를권장한다. 부품치수/공통좌표에서일관된규칙으로마스크를계산하면모딩시다시적용할수있다. 이것은자료의control-map원리를현재절차모델에적용하자는제안이며인용게임이똑같은책상알고리즘을쓴다는뜻이아니다.

현재반복나무UV와별도의mask UV/attribute를써야부품별그림자가서로겹치지않는다. 손으로임의pixel을고쳐넣는것이나모든물체에동일한부위offset을붙이는방법으로바꾸지않는다. 임의모델에는part role과mask 입력규약이필요하고무표식mesh에서자동으로그림자디자인을보장할수없다.

## 후속 최소실험과 실패 판정 — 미실행

승인된D15texture/geometry/96PPU를고정하고기존AO명암만위마스크경로로바꾼한버전을비교한다. 상판전체강한밝기대비,그림자번짐,부품틈가독성을실제렌더로사용자에게판정받는다. AO단독2단계화를새기법이라고재실행하지않는다. 모서리normal수정이나shadowproxy는이실험에서필요성이생길때만추가한다.

현재는조사완료/명암수정미실행이다. 자료만으로외형개선을검증했다고쓰지않는다.
