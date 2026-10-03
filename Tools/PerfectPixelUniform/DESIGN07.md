# V7 — 과장된 돌출 프레임을 평판 전면으로 교체

## 최신 요구·원인·수정 범위

사용자는 V6의 카툰 같은 과한 입체감과 외곽만 돌출/안쪽 전부 함몰된 서랍 구조를 거부했다. 실제 모델의 front/side frame -2tick와 inset -.4tick 차이는50mm이고 투영길이3.58px다. 손잡이는panel에서112.5mm, 모듈 간 몸체노출은125mm, 상판두께51.03mm였다. 수학 계산 성공을 사용자 디자인 요구 충족으로 잘못 판정하지 않는다.

수정 원인은 기하 프로필이다. 색/원화/나뭇결/명암 밴드/카메라/픽셀밀도/반복20tick/2·3칸과V6결과는 보존한다. 문틀·inset·sideframe을 제거하고 같은 깊이의 실제 평판 문/서랍으로 교체한다. 게임통합/새생성/필터·조명 보정/범용모딩 구현은 제외한다. V6제작 코드도 보존하며 같은 native BVH/색 채움/가시 경계 함수를 재사용한다.

## 고정 프로필과 좌표

V6의world `(-z/32,x/32,y/(32sqrt6))`, camera45°/30°/64sqrt2 px/m, `u=2x-2z,v=-x-z-y`를 유지한다. 프레임에 대응하는 별도 면/선/색 띠를 만들어 평판 위에 다시 붙이지 않는다.

- 폭 `W=4+20n`, bayStart `2+20i`; cap/높이72/깊이20 유지.
- body y6..70, counter y70..72: 두께25.52mm. 상판의바깥x/z범위와무늬UV는 유지.
- flat door/drawer x=bayStart+.25..bayStart+19.75, front z=-.4..0. 틈 .5tick=15.625mm; 틈과plate의높이는기하에서계산한다.
- door y7..53.5, drawer y54.5..69.5. 위아래의1tick=12.76mm 분리틈; border/inset그룹없음.
- drawer pull은plate centre x=bayStart+10, 길이5tick, 높이1tick, y61..62. door pull은x=bayStart+17.5..18, y36..41. 두 종류 모두z=-1.25..-1, bracket은-1..-.4. 최대판기준돌출26.56mm(투영1.90px).
- side는body의한평면이다. 별도돌출테두리·함몰패널없음. plinth기존치수유지.

이 치수는 사용자의 정정에 맞춰 선택한 평판 디자인 프로필이며 수학이 미술 취향이나 단일 최적디자인을 자동결정한다는 뜻은 아니다. 모든 반복판/손잡이는같은식이며 부위별렌더offset/scale/rotation은없다.

## 실행과 판별

graph-v7은 geometry→pixels→validate3노드다. geometry는새프로필의실제box를기존raster_variant에전달한다. pixels는V6재료출력을byte동일복사하여기존pixels 함수에전달한다. shade 계약은recipe06이고 geometry 계약은recipe07이다. 의존관계를별도기록하며V6코드·산출물을고치지않는다.

마지막1회: Frame/Inset그룹0, 모든front plate z동일, plate/handle치수와counter접합, 판/손잡이가시pixel, 독립box-slab최근접깊이, 실제PNG와팔레트/alpha/가시경계, 평행2중선검사, 두모듈치수/밀도/위상, exact4x 및V6원본보존을확인한다. 색출처/UV알고리즘은변경원인이없어V6의기존검증과입력해시를재사용한다. 생산파일존재나기술검사로미술승인을선언하지않는다.

## 실제 결과

실제 flat front profile은Frame/Inset그룹0이며2/3칸 모두같은전면깊이의문/서랍판을사용한다. source/V6실제입력·산출물·코드 SHA는그대로다. Parametric07-fixed의native152×150/192×170은V6와같은canvas/pixel밀도/12색이며shadow388/430px, semantic group11/15개다. 부품최근접깊이와실제경계/팔레트/alpha/정수4배·모듈규격을저장출력에서관측했고244조건통과했다. 같은geometry/shading알고리즘을재사용했으며미술승인으로승격하지않는다.

첫실행에서Blender의script sibling import경로가없어ModuleNotFoundError가발생했다. Blender프로세스exit0과작업완료는별개였으며첫그래프가잘못다음pixels로이어져입력부재로차단됐다. 실패코드/로그/자료/blockedstate는Parametric07에보존했다. script디렉터리의명시import와worker_completed생산metadata를연결했고프로필변경없이새경로에서수정실행을완료했다. 최종Blender기하실행3.218초/픽셀.257초이며추가시각재보정은없다. V6웹/Unity통합은변경하지않았다.
