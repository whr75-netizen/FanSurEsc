# V6 제작 계약 — 생성 디자인·재료와 기하 픽셀의 분리

## 현재 결정 · 2026-10-03

사용자는 V5의 해상도/특징 크기는 좋다고 확인했으며, 세부묘사/입체감은 부족하다고 정정했다. 최신 요청은 생성형으로 색감/디자인을 만든 뒤 원본 중심 대표색을 그대로 채우고 명암 영역을 구분하여 실제 제작하고, 같은 디자인의 여러 크기를 늘림 없이 만드는 것이다. 이번 결과는 수납장3칸과2칸의 실제 PNG 및 편집 가능한3D 기하/치수 데이터다. V5/원본/기존웹/Unity를 보존하며 게임 통합·새 외부 패키지·범용가구자동설계는 제외한다.

## 입력과 책임

내장 imagegen의 새 concept/material board는 물체 형태·색·무늬 참고다. final PNG로 제출하지 않는다. 생성 원화에는 색 견본12개(재료3×light/base/shade/edge)와 평면 목재 견본을 요청한다. 실제 위치는 생성 결과 관측 후 source ROI 입력으로 고정하고 그후 실행 중 바꾸지 않는다. 각 ROI 중앙 표본을 보이는 원본 RGB로 선택하며 평균/밝기 곱으로 새색을 만들지 않는다. 부분alpha/불완전견본은 명시적 입력 실패다. 나뭇결은 평면 견본의 원본 색 영역에서 재료 문양으로 분리하고 구조 명암과 분리한다. 한 장에서 숨은 치수를 유일하게 복원했다고 주장하지 않는다.

## 좌표와 구조

V5 local `(x,y,z)`와 투영tick을 유지: X길이/Y위/Z깊이, world Blender `(-z/32,x/32,y/(32√6))`(Z-up), 부모없음/axis-aligned부품. local저작좌표에서world로의축변환은det<0이며세계mesh의face winding/normal은Blender cube생성에서정상외향으로정한다. 기존basis의azimuth45°/elevation30°, density `64√2 px/m`로 `u=2x−2z,v=−x−z−y`를정확히재현한다. 기존204×192는3칸의기준이며 추가구조의bounds만큼여백/canvas가달라질수있다. 출력PNG를stretch하지않는다. 모든 부품은 같은치수식/공통anchors에서 생성한다.

반복: `W(n)=4+n×20`, `x_i=2+i×20`, n=2/3. 전체scale로늘리지않으며 cap/깊이20/높이72/문틀/손잡이두께를고정한다. 베이마다윗서랍+아랫문,4개틀부재+안쪽패널,손잡이돌출,상판돌출/하부받침을실제box로정의한다. 깊이/틈의픽셀표현은같은camera로계산한다. front를z=0의색사각형으로대체하지않는다.3D단면·정면도·면목록은이모델에서유도하고기준정보를따로중복저작하지않는다.

관측된원화는서랍손잡이가가로/문손잡이가세로다. 문pull은bayStart+15..16.5, y36..42,z−4..−3의3×6px정도프리즘과두브라켓이며같은규격으로반복한다. source1254×1254의12견본중심은x116/273/430, y919/996/1072/1149이고paint/wood/brass와light/base/shade/edge순서다. wood평면ROI `[552,900,1201,1175]`는기하원화영역과분리되어있다. 다음실행의고정입력으로사용한다.

## 연산 그래프

`AI source/ROI → 원본 RGB palette + UV grain → 3D part recipe → native pixel-centre finite BVH → visibility/normal/material region → shade-role palette fill → visible edges → 최종 저장결과 검사/별도정수4배표시`.

기존 PixelPipeline/common.py의 basis/consistent_edges/parallel_double_strokes를재사용한다. blender_stage.py의triangulation/BVHTree/nativecentre/shadowray계산을같은방식으로새수납장입력에연결한다. 기존CLI는12part desk전용으로사용하지않는다. 기존material의수동64grid/66×64변환/고정wood만채우는shade와outline팽창후처리는재사용하지않는다.

각 native pixel은가장가까운유한표면의world위치/법선/part/face/depth를소유한다. 색무늬는고정물리UV길이에서조회하고, n이늘어도무늬주기를늘리지않는다. source RGB를완성3D조명텍스처로붙이지않는다. 명암구간은normal·light·실제shadowvisibility에서선택하며별도정의한원본색(role)만출력한다. 구조선은보이는표면pair에한소유자,숨은표면선우선덮어쓰기없음. 기하normal과UV grain은각각저장한다.

생성 견본을 보고 다음 재료 연산을 고정했다. 12색은 각 견본의 중앙 한 점 RGB 그대로다. wood ROI의 원본휘도25백분위 미만을 어두운 나뭇결 역할로 분류하고, 현재 투영tick당2texel에서128×54의UV역할지도를 만든다. 지도 한 칸의 source좌표도 중앙값 한 점이며 RGB평균/디더링은 없다. 최종PNG를 줄이는 연산과 구별한다. 원본 작은 선을 완전 보존하는 복구가 아니라 생성 재료를 명시된 표현밀도로 저작하는 단계이며, 8연결6texel미만 독립 성분은 재료 잡음으로 제외하고 수를 기록한다. 물리UV길이는64tick/세로는source종횡비에맞춘64×275/649tick으로 고정하여 모듈수가달라도 무늬가늘어나지않는다.

광원방향은world `[.65,−.25,.72]` 정규화다. 이는현재표면법선에서상판=light/전면=base/왼쪽=shade가되는 source 원화의명암관계를 따른 고정입력이다. `normal·light` .26/.68경계와실제visibility에서3명암영역을고르고, shadow는shade를고른다. woodgrain은선택된shade-role에서한단계어두운원본견본을선택한다. 서로다른영역의RGB를평균하거나조명곱으로새색을만들지않는다.

## 후보·반례·최소 판별

- 2D9-slice Tiled는평면전면패널의고정끝단/반복중앙에적합하나사선전체PNG의상판/측면/깊이를보존하는연산이아니므로이번전체가구에사용하지않는다.
- 3D고정cap/반복bay+fixed-density UV를선택한다. Blend Array와같은배치식이며실제Modifier사용여부와동일원리구현을구분한다. n=3와2의한쌍만실제로제작하고같은모듈치수/팔레트/UV밀도/투영위상을확인한다.
- 반례는서랍틈가림/손잡이실종/문틀2중선/불균일무늬확대/반투명경계다. 실제part가림·pixel배열에서판정하고문제가있으면담당단계만수정하며이전출력을보존한다. 단지색수/파일존재검사로미술합격을선언하지않는다.

## 마지막 필수 관측

원본/기준/V5 SHA 보존, 원본 RGB 팔레트의 출처 좌표, alpha0/255, 고정 밀도·같은 모듈 규격·native 중심 표본, 정수4배 대응, part/face 최근접 깊이·가시선 일치, source 무변형·PNG 늘림 없음, 명암/나뭇결 별도 지도, 서랍/문틀/손잡이의 보이는 pixel>0, 실제 shadow pixel>0을 확인한다. 사용 RGB는 선택한 source RGB 집합 안에 있어야 한다. 정적 미술 합격·원화99%복제·Unity 연결은 별도 판정이다. 생산구간 시간과 생성/설계/AI 추론 시간을 분리한다.

근거: [Unity9-slice](https://docs.unity3d.com/6000.0/Documentation/Manual/sprite/9-slice/9-slicing.html), [Blender Array API](https://docs.blender.org/api/5.0/bpy.types.ArrayModifier.html), [정투영camera](https://www.pbr-book.org/4ed/Cameras_and_Film/Projective_Camera_Models), [3D가시선연구](https://arxiv.org/abs/1810.01175). 전체가구의성공보증이아니라각연산의기술근거이며기존mesh/BVH/visibleedge코드와적합성을확인했다.

## 실제 결과 · 2026-10-03

위 명세를 변경하지 않고 graph-v6의 material→geometry→pixels→validate 4노드를 한 번 실행했다. 생산 오류/반복 재제작 없이 완료했다. 2칸152×150/3칸192×170, 각12색·alpha0/255이며 두 크기의 고정 모듈 치수·투영 밀도·물리 UV 주기 일치를 실제 저장 배열에서 확인했다. 서랍·문 프레임/안쪽 면/손잡이/측면 패널은 모두 보이는 픽셀이 있고 shadow는1143/1345px다. 최근접 표면은 별도 box slab 계산으로 각 visible semantic group 한 점씩(17/23점) 대조했다. 기존 common의 가시 경계 소유자와 실제 최종 ink가 같고 평행 면의 고립된 긴 2중선 검사는0건이다. 모서리/교차점까지 유클리드 폭1px를 보장한다는 뜻은 아니다.

RGB는 선언한 원화12중앙표본 집합 안에만 있으며 source의 RGB에 이미 들어간 전체 원화 조명을 텍스처로 붙이지 않았다. flat 목재 ROI에서 구분한 어두운 재료 역할과 normal/shadow 기반 구조 명암은 별도 지도다. 입력 grain1791texel 중 작은 성분101개/255texel 제거,1536유지. 이 손실은 native 저작용 재료 표현 선택이고 원화의 모든 미세선 보존이 아니다.

재료 .142초/Blender 시작 포함9.147초(native 기하 .787초)/픽셀 .303초/마지막 검사 .436초. 생성·설계·코드·AI 추론 시간과 분리한다. 검사는299개의 개별 관측 조건을 통과했으며 미술 품질·원화99%복제·모든가구 자동화·Unity 표시 합격은 포함하지 않는다. V5와 실제 원본SHA 보존을 확인했고 웹/Unity를 수정하지 않았다. 실제 파일/재실행 경로와 현 한계는 README V6에 연결했다.
