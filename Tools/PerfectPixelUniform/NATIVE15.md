# N15 — 유한 입체의 가시성·법선에서 직접 픽셀 제작

## 현재 결정 (2026-10-04)

요청은 N14의 하단 1px 돌출, 검정 내부선, 잘못된 명암, 상판 밑 추가선을 원인부터 고치고 다른 방식의 실제 결과도 만드는 것이다. 최신 정정이 N14의 전 구조선 검정 계약을 대체한다. 기존 N14·Unity·생성 참고·나뭇결·치수는 보존한다.

직접 원인은 Bresenham의 A→B와 B→A가 다른 반올림 위치를 선택하는 것이다. 앞 바닥선은 두 방향의 점 집합이 128점 달랐으며, 면과 perimeter의 합집합은 연속 면 밖 alpha 110px를 만들었다. 모든 선을 검정으로 칠해 표면 모서리와 틈을 혼동했다. 같은 평면 rail에 임의 tone을 넣었고 상판 아래 검정 cap선·금속띠·밝은 rail을 중첩했다. N14 검사는 이 반례를 통과시켰으므로 검사 성공을 디자인 성공으로 해석하지 않는다.

비교 A는 전개도 quad의 해석적 coverage와 선 역할 교정이다. B는 실제 유한 3D 입체의 최근접 광선 교차, 법선·그림자, 가시 경계를 계산한다. B를 새 제작 후보로 채택하고 A는 같은 재료의 비교 실험이다. 원화 색을 새 조명으로 착각하거나 기하를 늘려 방향을 맞추지 않는다.

## Canonical과 단계 계약

1. **기하:** tick `(x,y,z)`는 폭·높이·깊이, world 미터는 `(-z/32,x/32,y/(32√6))`. 화면은 `u=2x-2z,v=-x-z-y`, azimuth 45°·elevation 30°. 기존 3문 치수 W=64,H=72,D=20을 보존한다. 화면 사선 2:1과 카메라 고도를 혼동하지 않는다.
2. **Coverage:** 화면 표본은 `(pixelX-originX+.5,pixelY-originY+.5)`. B의 primary ray는 `O=(-v/2+u/4-1000,2000,-v/2-u/4-1000),D=(1,-2,1)`. slab의 `entry<exit`인 양의 교차만 인정하며 최근접 hit가 part·face·position·normal을 함께 소유한다. 접선으로 alpha를 추가하지 않는다. A는 각 quad의 half-open `0≤UV<1`과 명시된 가림 순서를 사용한다. 어느 방식도 perimeter 선을 alpha에 붙이지 않는다.
3. **형태:** 실제 입체는 몸체·얇은 상판·작은 손잡이다. 문은 같은 몸체 앞면의 semantic partition과 평면 인레이다. coplanar 문 입체를 중복 생성하지 않는다. 돌출 틀·문 전체 후퇴·부위별 임의 offset은 없다. JSON 치수와 world OBJ를 편집할 수 있다.
4. **재료:** 생성 참고의 관측 RGB 팔레트와 나뭇결은 `native14_materials.Appearance`를 재사용한다. 목재 무늬는 4개 관측색의 rank다. 순수 albedo를 복원했다고 주장하지 않는다. 목재 UV 주기 66tick을 유지해 2문은 같은 재료의 앞 46tick을 사용한다. 몸체·금속의 원화 명암 이미지를 붙이지 않는다. 몸체에 평면 brass decal을 별도 mask로 저장한다.
5. **명암:** normal은 world에서 계산한다. `L=normalize(.50,-.20,.84)`와 `dot(top/front/side)≈(.84,.50,.20)`, thresholds `(.32,.72)`로 geometric band `(2,1,0)`를 선택한다. paint는 `side[1],navy[1],navy[2]`, cap fascia는 `wood[band]`, cap top은 `wood[clamp(grainRank+band-2)]`, brass는 `brass[band]`다. B의 실제 shadow ray가 막힐 때 재질의 최암색을 선택한다. geometric band와 shadow는 독립 버퍼다. A에는 입체 그림자가 없다. 기본광100·PBR·AO·specular·연속 광량은 없다.
6. **장식:** 모서리 금속·힌지·문 인레이는 몸체 coverage 안의 평면 재질 분할이다. 장식을 먼저 배치한 뒤 명암을 계산하므로 밝은 장식이 실제 그늘을 덮지 않는다. 상판 아래 upper gold strip·밝은 top rail·별도 body 상단선을 추가하지 않는다.
7. **선:** silhouette와 문 사이 module join의 틈만 검정이다. 몸체 모서리는 paint 계열, 상판은 wood 계열, 금속은 brass 계열이다. 실제 재질 ID로 선 색을 선택한다. 가시 surface pair마다 카메라 방향과 깊이에 따라 한쪽 owner만 쓴다. cap/body 접촉은 재질·실제 그림자로 표현하며 추가 검정선을 넣지 않는다. 문틈은 body front의 다른 bay label이 만나는 y=[6,66)의 세로선이다. 문 전체 테두리는 검정이 아니다.
8. **출력:** alpha는 기하 mask와 동일하다. 색·선·장식은 mask 안에서만 쓴다. 장식 Bresenham은 끝점 순서를 정규화하고 단일 endpoint phase를 사용한다. 원본 변형·완성 PNG 축소·강제64×64·이중 픽셀화는 없다. 4배 nearest는 표시용이다.

## 최소 실험과 완료 범위

같은 재료·치수의 2문/3문을 A/B로 제출한다. 최종 PNG의 alpha, 검정 역할, 재질색 모서리, 실제 명암 band, 상판 그림자, upper strip 부재를 확인한다. 하단·상판 모서리는 독립 Fraction slab로 coverage·owner를 비교한다. 장식이 그림자를 덮거나 가려진 면의 선이 나오면 실패다. 공통 모듈의 손잡이 기하와 목재 주기는 같아야 한다.

기존 WorkLoop의 `geometry → material → shade → raster → validate`가 실제 계산을 순차 실행한다. 단계별 버퍼·JSON·PNG·코드·입력 해시를 남긴다. 실패는 담당 단계에 귀속하며 새 원인 없이 반복하지 않는다. 미술 승인·AI티0%는 기술 검사로 증명할 수 없다. 실제 PNG·편집 원본·출처·실행 시간·미검증을 제출하고 형식적 만족도 질문으로 종료하지 않는다.

## 실행

`Run-Native15.cmd` 또는 아래 명령으로 고정 입력을 재생성한다. 출력은 새 폴더여야 하며 이전 결과를 덮어쓰지 않는다.

```powershell
& 'C:/Users/JG/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B Tools/PerfectPixelUniform/native15_cli.py --output LocalOnly/Native15-new
```

## 기술 근거와 입력 적합성

- [PBRT slab 교차와 nearest hit](https://pbr-book.org/4ed/Shapes/Basic_Shape_Interface): 유한 box와 광선 범위 교차에 적합하다. 출력 표본과 경계 규칙은 이번 계약에서 정의한다.
- [PBRT diffuse cosine](https://pbr-book.org/4ed/Reflection_Models/Diffuse_Reflection): 같은 world 공간의 normal·light 내적을 사용한다. 이번에는 연속 radiance 대신 작은 팔레트 band를 선택한다.
- 기존 `common.surface_boundaries`의 가시 surface pair와 `handle_raster09.exact_hits`의 slab 원리를 재사용한다. 모든 경계를 검정으로 찍는 `consistent_edges`와 V6 돌출 frame 생성은 이번 입력에 부적합하다.

고정 시점 가구 template의 제작 후보다. 모든 생성 이미지를 자동 3D 복원하는 제품이 아니며 Unity 수정·동적 조명 통합을 포함하지 않는다.
