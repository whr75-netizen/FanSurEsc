# 픽셀 책상 명암 — 공식 제작 자료와 적용 후보

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
