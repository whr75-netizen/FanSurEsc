# V9 — 반복 손잡이의 정확한 경계 교차 판정

## 요구·관측·최초 원인

사용자: 옆칸을 추가하면 문손잡이가 잘리므로 확인·수정한다. 현재 V8 PNG의 입력은 V7 geometry이며 이미지 복붙/crop으로 제작하지 않았다. 같은 치수·같은 정수 이동인데 문손잡이 가시 픽셀은 2칸 `[14,9]`, 3칸 `[14,9,9]`, 서랍손잡이는 `[16,15]`, `[16,15,15]`다. 추가 문의 오른쪽 1열 5px와 서랍 끝점 1px가 geometry buffer에서 이미 panel로 판정됐다. 첫 문의 normal도 2칸/3칸에서 face1/face3으로 달라졌다. V8 색칠 단계는 이를 그대로 사용했다.

해당 ray는 원래 손잡이 box의 모서리에 정확히 닿아 slab의 entry==exit다. float32 BVH의 동일 모듈 병진 불일치를 보정할 대상으로 좁힌다. 기존 V6에도 같은 계열 경계 문제가 있었으며 새 복사 기능 탓으로 단정하지 않는다.

## 고정 조건과 선택

원본 V6/7/8 코드·산출물을 보존하고 실제 mesh box 치수·모듈20tick·camera45/30·밀도·canvas·alpha·원화색·목재4단계·UV·조명을 유지한다. 손잡이 관련 primary ray의 교차 판정만 정확 slab로 교체한다. 손잡이를 늘리거나 뒤에 있는 것을 앞으로 칠하지 않는다. 다른 표면의 기존 buffer는 재사용한다. 경계 변경에 인접한 stroke의 재계산은 이 수정의 의존 단계다.

[PBRT §6.1.2](https://www.pbr-book.org/4ed/Shapes/Basic_Shape_Interface)의 ray–box slab 교집합을 채택한다. 다음 정수 좌표 특수화와 경계 convention은 이번 프로젝트의 연결 구현이며 PBRT가 이 모델/미술 결과를 보증한다는 뜻이 아니다. float epsilon 확대나 임의 손잡이 이동은 동일 입력의 병진 불변성을 보장하지 못하므로 제외한다.

## canonical ray·면 소유권

화면 중심 u,v에서 현재 투영의 ray는 `q(t)=(u/2+t,-v-u/2-2t,t)`, 방향 `(1,-2,1)`, t=z다. box의 세 slab 교집합은

```text
entry = max(xlo-u/2, (-v-u/2-yhi)/2, zlo)
exit  = min(xhi-u/2, (-v-u/2-ylo)/2, zhi)
hit   = entry <= exit                  # 닫힌 solid의 정확 모서리 포함
front = 모든 실제 box 중 최소 entry    # 숨은 손잡이를 강제 노출하지 않음
```

JSON bounds를 `Fraction(str(value))`로 읽고 분모 LCM과 pixel centre 분모8을 포함한 정수 단위에서 교차·동률을 판정한다. t가 같으면 더 camera-facing인 입구면을 고른다. 현재 x/z 입구면의 score가 같으므로 world face1(-local z), face2(-local x), face5(+local y) 순서를 고정한다. 같은 깊이의 서로 다른 solid는 face 순서 뒤 canonical bounds 순서로 결정한다. part 이름/생성 순서를 draw priority로 쓰지 않는다.

실제 수정 영역은 이전 owner 또는 정확 최근접 owner가 손잡이인 ray다. 이는 primitive별 교차 판정의 교체이며 색/마스크로 가림을 우회하는 overlay가 아니다. 위치·normal·part·face·depth를 같은 hit에서 함께 기록하고 그림자 ray도 실제 box와 기존 광원에서 계산한다. 나머지 primary surface/그림자는 기존 값을 보존한다. 임의 회전 메시나 다른 camera에 이 box 전용 수식을 적용하지 않으며 입력 불일치는 실패로 반환한다.

## 단계와 마지막 판별

`geometry → pixels → validate`: 기존 실제 scene.blend/parts와 재료를 보존·재사용하고 수정 surface buffer를 새 경로에 작성한다. 기존 pixel shade/edge 함수로 surface base를 계산한 뒤 **기존 V8 wood-levels**를 같은 `min(band+level,3)`로 채운 final PNG를 작성한다. 새 생성·재료 재해석·해상도 변경은 없다.

마지막 한 번에 원래 5px/1px 반례, 모든 2/3칸 손잡이의 이동 정렬 mask/normal/face/ink/RGBA 일치, 수정 ray의 독립 Fraction slab 최근접 owner/depth, 외부 canvas·alpha·비손잡이 buffer/목재 RGB 보존·팔레트 출처·정수4배를 확인한다. 경계 영향은 수정 ray의 인접1셀 이내여야 한다. 검사가 실패하면 측정값을 남기고 담당 연산을 수정하며 치수/색/허용 범위를 결과에 맞춰 바꾸지 않는다.

실제 PNG를 제출하며 Unity 표시는 이번 작업 범위에 없다. 미술 만족도 질문으로 수정 완료를 대신하지 않는다.

## 실제 결과

독립 Fraction의 제작 전 bbox 실험과 최종 저장 출력 모두 문14/서랍16px를 지지한다. 2/3칸의 모든 손잡이에서 mask·face·normal·ink·RGBA가 정수 이동으로 일치한다. 기존 픽셀 삭제0, 추가 칸의 문5px·서랍1px를 복구했다. 모든 목재RGBA·alpha·canvas·비손잡이 buffer·경계 인접1셀 밖RGBA는 그대로다. geometry .114초/pixels .354초/최종 검사 .240초이며 3단계 실행기 process 포함2.24초다. 조사·코드 작성 시간과 구분한다.

73개 마지막 기술 조건을 실제 PNG/배열/독립 Fraction ray에서 확인했다. LocalOnly의 handle-boundary09-20261003에서 1회 실행했고 Parametric09는 해당 산출물을 byte동일 보존한 snapshot이다. publication.json과 workloop-state/graph/binding에 출처를 남겼다. mesh는 기존 실제 scene.blend와 byte동일이며 Blender를 다시 실행하지 않았다. 그림자 포함 손잡이 ray만 기존 광원·실제 box에서 재계산했고 Unity 적용/미술 승인은 주장하지 않는다.
