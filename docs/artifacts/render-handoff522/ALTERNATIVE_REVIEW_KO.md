# 전역 arc DP를 없애는 대안 — 기존 자료 1회 검토522

## 판단

**기존 연구·현재 코드에, 사용자 목표를 모두 충족해 즉시 채택할 검증된 대체 구현은 없습니다.**521의 공유셀 메시지/거대한 이력 bank 경로는 종료합니다. 그 경로의 세부 API를 더 확장하거나 새 알고리즘을 자동 구현하지 않습니다.

구조적으로 가장 작은 별도 후보는 **511의 곡선·면적·패킷·공통 경계를 유지하고, SelectRegions 한곳의 목적을 제한된 시공간 이진 joint-cut으로 바꾸는 것**입니다. 이는 검증된 완제품 추천이 아니라 아래 근거에서 도출한 설계 추론입니다. 전역 span 편집거리의 정확 재현을 포기하는 별도 목적식이며, 기존 실패를 그대로 두고 후단 filter를 얹는 방식으로 제안하지 않습니다.

## 확인한 기존 연구

| 자료 | 재사용할 근거 | 이 프로젝트의 완성 대안이 아닌 이유 |
|---|---|---|
|[Feature-Aware Pixel Art Animation](https://www.yongliangyang.net/docs/pixelAnim_pg16.pdf),§4–5|현재 연속형태·선 품질·시간 일관성을 분리해 평가함|저장 line animation 최적화이며50×50 wolf예도 평균5초/frame. 고정 feature 구조와 명시적 대응이 전제이고 topology 변화는 지원하지 않음. 현재 전역 edit DP를 실시간으로 정당화하는 근거가 아님.|
|[Superpixelator 저자 서지·설명](https://cs.uwaterloo.ca/~csk/publications/),Inglis/Vogel/Kaplan2013|벡터 형태의 대칭·비율·각 같은 디자인 특성을 픽셀 선에 반영|정적 vector-line rasterization의 근거. 임의 변형3D의 닫힌 채움·눈/몸 가림·시간 선택까지 검증된 모듈이 아님.|
|[Active Strokes 연구팀 설명](https://radar.inria.fr/report/2012/maverick/uid68.html)|움직이는3D 선과 표현용 parameterization을 분리해 추적하며 interactive rendering을 지향|연속 stylized line의 일관성 연구이지 픽셀 영역·계단 배열의 완성 quantizer가 아님.511의 지속 anchor가 있다는 사실만으로 부족했던 부분을 해결했다고 할 수 없음.|
|[Kolmogorov–Zabih](https://www.cs.cornell.edu/~rdz/Papers/KZ-PAMI04.pdf)|특정 unary/pairwise binary energy는 graph-cut 표현 가능|임의 span·계단·클러스터 미관 비용을 모두 한 cut으로 변환해 주는 결과가 아님. 목적식의 표현 가능성과 미관/시간 품질은 별개.|

논문의 화면·단위·입력·기능을 현재 구현과 같은 것으로 보지 않았습니다. Superpixelator와 Active Strokes를 직렬로 붙이는 새 복합 렌더러도 제안하지 않습니다. 독립 선을 control-point ID로 쪼개는 방식은516의 재매개화 문제를 다시 만들 수 있으므로 최소 대안으로 채택하지 않았습니다.

## 현재 코드에서 실제로 재사용할 부분

- `HeadCurve511.cs`:자동 전처리한3분절선/94지속 anchor와 현재 변형 평가. 새 모델 전부에 대한 의미 있는 tip 판별이나 Bézier 자산은 아님.
- `CurveArea511.cs`:현재 positive-winding 닫힌 영역의 셀 면적. 원본 저해상도 alpha 복사와 다른 형태 입력임.
- `HeadRegion502.cs:207–220`:모든 셀을 함께 결정하는 unary area＋8이웃 boundary joint-cut과 기존 `Cut`. 성분을 독립이라 가정하지 않고도 현재 공간 결합을 처리하는 기반임.
- 같은 `Draw/Gate`·Native/레이어/눈/최종 공통 경계와 현재 source packet/512 몸 가림. 새 시간 비용이 허용 영역 밖 원본 mesh alpha를 되살리는 경로는 필요하지 않음.

기존511 측정에는 curve update0.0343ms/area0.5322ms와 별도 grouped packet/quad/upload212.3354ms가 있습니다. 이는16포즈 Editor 측정의 서로 다른 span이며 제품 FPS나 새 대안의 성능이 아닙니다. 현재 min-cut 자체를 새로 계측한 결과도 아닙니다. **전역 arc DP를 제거해도212ms 문제가 해결되지는 않습니다.**

## 하나의 별도 구조 후보와 정확한 손실

전역 arc 전체 mask-state 이력 대신, 고정된 물리 시간 범위의 **설계 label**을 현재 곡선 근거와 유효한 국소 기하 대응 아래 함께 선택하는 binary graph를 생각할 수 있습니다. unary 형태 비용과 graph-representable 국소 상호작용만 사용하면 상태 bank를 열거하지 않고 `W×N` node형태로 표현할 수 있습니다. 이 계산 가능성은 graph-cut 구조에서의 추론이며 pixel-art animation 완성법이 검증됐다는 뜻이 아닙니다.

이 후보는 다음 의미를 분명히 해야 합니다.

- 선택기는 하나이고 현재 frame의 최종 권위 mask 하나를 반환해야 합니다. 과거 RGB/최종mask를 출력 후 복사하거나 majority/closing으로 덮지 않습니다.
- 과거 확정 출력 mask를 window 경계에 hard 고정하면516의 장벽을 다시 만들 수 있습니다. 과거의 현재기하 근거를 재사용하는 것과 과거 출력에 종속되는 것은 다릅니다.
- 현재 실제 앞가림과 source/owner 지원은 hard한 현재 조건입니다. 유효하지 않은 대응을 시간 edge로 연결하지 않습니다.
- span add/delete/merge/split 전체 거리와 완전 이력 최적성은 유지하지 않습니다. 기존36 비용을 더 싸게 같은 값으로 계산한다는 제안이 아닙니다.
- 실제 픽셀 덩어리·세부 생략/통합·계단 리듬을 이 제한된 목적식으로 충분히 표현할 수 있다는 근거가 **아직 없습니다**. area/perimeter만 다시 실행하거나 임의 시간 edge를 추가하면514의 실패를 새 해법이라고 포장하게 됩니다.
- 시간 범위/국소 비용/기하 대응과 모든frame의 정상속도 검증이 없는 상태에서는 실시간·시간 일관성·아트 통과를 보장하지 않습니다. 기존 packet 비용도 별도입니다.

따라서 **재사용할 최소 구현 기반은 존재하지만, 목표를 보존한 새 선택기가 이미 존재하는 것은 아닙니다.** 이 후보를 이번 작업의 채택안으로 확정하지 않습니다. 추가 의존성을 하나씩 구현하는 현 arc-DP 경로는 여기서 끝내고, 새 구조의 코드·촬영·계수 조정은 시작하지 않았습니다. 제품은348 활성/511·512 OFF와 기존 사용자 설정을 유지합니다.

## 검토 범위

기존510/511/514/515 기록, 현재 HeadRegion502/HeadCurve511/Visibility511 코드,360의 기존 연구 인계, 위 원저자 자료만 대조했습니다. 새 라이브러리·새 모델·전체 재빌드·런타임 실험·새 벤치마크는 없었습니다.522는 인수인계와 판단 문서이며 새 시간 선택기 실험 번호가 아닙니다.
