# Radical Fish Games 캐릭터 애니메이션 조사

조사일: 2026-09-20. 범위: CrossCode와 Alabaster Dawn(개발명 Project Terra)의 캐릭터·적·보스 애니메이션에 관한 제작자 공개 설명. 게임 다운로드, 실행 파일 분석, 에셋 추출, 본 프로젝트 구현은 수행하지 않았습니다.

## 결론과 근거 수준

**Alabaster Dawn은 3D 스켈레톤을 움직이고, 각 부위 위치에 픽셀 스프라이트/빌보드를 배치하는 방식입니다.** 본의 카메라 상대 각도와 자세에 맞춰 준비된 그림을 선택·교환하고 일부는 회전·스케일 조정합니다. 보통의 스킨드 메시를 본으로 변형하는 방식과 다릅니다. 제작자는 이 차이를 직접 명시했습니다.[A1][A2][A3]

**CrossCode는 대부분 손으로 만든 애니메이션이라는 아티스트의 증언이 있습니다.** 다만 대형 보스용으로 여러 sub-entity와 스프라이트를 타임라인에서 조립하는 도구도 공개했으므로, 모든 캐릭터·보스가 완성된 전신 프레임을 한 장씩 바꾸기만 한다고 일반화할 수 없습니다.[C1][C2]

| 질문 | 공개 자료로 확인한 답 | 남은 한계 |
| --- | --- | --- |
| Alabaster Dawn에서 픽셀을 본에 붙이나요? | 3D skeleton의 위치에 여러 2D sprites/billboards를 올립니다.[A1][A2] | 단순 2D 리깅이나 단일 그림의 자동 입체화라고 보면 부정확합니다. |
| 모든 방향의 모든 동작 프레임을 각각 그렸나요? | Alabaster Dawn은 부위 그림을 만들고 엔진에서 투영·회전·보간하여 조립합니다. 아티스트는 CrossCode에서 하던 모든 관점의 전신 조합 제작을 줄였다고 설명했습니다.[C1] | 파츠 자체의 각도별 그림과 맞춤 프레임 작업은 남아 있습니다.[A4] |
| 몇 방향인가요? | 2023년 개발자가 당시 시스템을 최대 16방향이라고 설명했습니다.[A3] | 모든 캐릭터·적·보스·파츠가 항상 16개의 고유 그림을 쓴다는 뜻은 아닙니다. 출시판의 전체 에셋별 표는 확인하지 않았습니다. |
| 좌우는 미러링하나요? | 이번에 확인한 제작자 설명에는 범위와 규칙이 없었습니다. | 좌우 반전 유무·예외·절감량을 단정하지 않습니다. |
| CrossCode 캐릭터도 이 방식인가요? | 아티스트가 CrossCode 대부분은 손으로 애니메이션을 만들었고, Terra에서 새로운 3D rig 방식을 쓴다고 구분했습니다.[C1] | CrossCode 모든 동작의 방향 수, 프레임 수, 미러링 표는 확인하지 못했습니다. |

## Alabaster Dawn의 확인된 메커니즘

1. 일반 3D 캐릭터와 비슷한 3D 스켈레톤을 애니메이션합니다.[A1][A2]
2. 머리·상완·하완 등 개별 부위의 작은 스프라이트를 준비합니다. 전신의 모든 동작·관점 조합을 각각 그리는 작업과 구분됩니다.[C1]
3. 본 위치에 빌보드를 배치하고, 본의 카메라 상대 각도에 적합한 그림을 선택합니다.[A2][A5]
4. 일부 빌보드는 화면에서 보이는 본 모양에 맞춰 회전·크기를 조정하고, 부위 방향에 따라 그림을 교환합니다.[A1]
5. 엔진의 보간을 사용하지만, 픽셀아트에 맞게 애니메이션의 fps도 낮춥니다. 이 설명을 게임 전체 렌더링 fps 제한으로 해석하면 안 됩니다.[A2][C1]
6. 종이 인형처럼 보이는 현상을 줄이려고 신체 부위의 맞춤 프레임도 많이 추가합니다.[A4]

이 과정을 요약하면 **부위별 픽셀 그림 + 3D 본 애니메이션 + 관찰 각도별 그림 선택/변환 + 수작업 보완**입니다. 완성된 캐릭터 한 장에서 보이지 않는 뒷면까지 자동 생성한다는 근거는 없습니다.

### 확실히 공개된 제약

2026년 Felix의 직접 답변은 일부 회전이 부정확하고 일부는 아예 없다고 명시합니다. 제작진은 보기 좋은 자세를 선택하고, 빠르게 지나가는 중간 자세에서는 더 많은 생략을 사용합니다. 확대할수록, 천천히 움직일수록 약점이 드러나며, 멀리서 보는 픽셀아트 화면에 맞춘 시스템이라고 설명했습니다.[A1]

따라서 이 방식은 모든 각도에서 정확한 캐릭터 메시를 보장하는 시스템이 아닙니다. 동작과 카메라 범위에 맞춘 파츠 세트·자세 설계·시각 보정이 제작의 일부라는 결론이 타당합니다. 이는 제작자의 제약 설명에서 도출한 해석이며, 공개되지 않은 내부 알고리즘을 복원했다는 뜻이 아닙니다.

### 방향 수의 정확한 해석

2023년 Stefan의 표현은 `up to 16 directions`입니다.[A3] 이를 “한 장을 16방향으로 자동 생성한다”, “항상 16방향을 모두 따로 그린다”, “모든 파츠당 16장이다”로 바꿔 말하면 근거를 벗어납니다.

캐릭터의 지면 방향, 개별 본이 카메라를 향하는 방향, 특정 동작의 시간 프레임 수는 서로 다른 변수입니다. 공개 자료는 본 각도에 따른 스프라이트 선택과 애니메이션 재사용을 설명하지만 전체 각도 샘플링 표나 파츠별 슬롯 수는 공개하지 않았습니다.

## CrossCode의 확인 범위

Thomas 'T-Free' Fröse는 공식 2023 AMA에서 CrossCode 대부분을 손으로 애니메이션했다고 설명하고, Terra에서는 개별 파츠를 엔진에서 투영·회전·보간하기 때문에 작업 방식이 달라졌다고 비교했습니다.[C1]

공식 2014 개발블로그는 대형 보스용 애니메이션 편집기가 다음을 지원한다고 공개했습니다: 여러 sub-entity, sub-entity별 sub-animation, sub-animation별 스프라이트, 타임라인 재생, 엔티티·스프라이트 위치 지정.[C2] 2023년 Stefan도 Terra의 결과가 CrossCode 보스와 유사하지만 최대 16방향을 갖는다고 설명합니다.[A3]

이에 따라 CrossCode의 전형적인 작은 캐릭터와 복합 보스 애니메이션을 같은 제작 단위로 계산하면 안 됩니다. “캐릭터 대부분은 수작업 애니메이션이며, 복합 보스에는 여러 그림과 하위 개체를 조립하는 시스템도 있다”가 확인 자료에 맞는 설명입니다.

CrossCode의 정확한 방향 수와 좌우 재사용 규칙은 이번 조사에서 제작자 명시 자료로 확정하지 않았습니다. 팬 댓글의 “8방향”이나 비공식 추출 스프라이트 시트는 제작자 확정 근거로 사용하지 않았습니다.

## 1차자료 목록

- **[A1] Felix 'Lachsen' Klein, 공식 AMA 답변, 2026-05-22.** [스켈레톤·빌보드·각도별 교환과 한계](https://www.reddit.com/r/JRPG/comments/1tkfmo3/comment/on9ioe0/). 3D skeleton을 사용하지만 mesh 변형 대신 billboards를 만들며, 일부 빌보드의 회전/크기조정과 그림 교환을 설명합니다. 회전 누락·부정확성, 중간 자세의 생략, 확대/저속에서 약해지는 제약까지 직접 답변합니다.
- **[A2] Flora 'Teflora' Valerius, 공식 AMA 답변, 2023-02-21.** [본 위치에 스프라이트 배치, 카메라 각도별 선택, 애니메이션 fps 조정](https://www.reddit.com/r/JRPG/comments/11836dh/comment/j9f5hju/). 3D mesh가 bones 주변에서 변형되는 것과 스프라이트 위치 배치를 구분합니다.
- **[A3] Stefan 'R.D.' Lange, 공식 AMA 답변, 2023-02-21.** [최대 16방향 설명](https://www.reddit.com/r/JRPG/comments/11836dh/comment/j9f594o/). 본 회전에 따른 그래픽 선택과 CrossCode 보스와의 비교를 설명합니다.
- **[A4] Felix, 공식 AMA 답변, 2026-05-22.** [적은 스프라이트로 세밀한 동작, 부위별 맞춤 프레임 추가](https://www.reddit.com/r/JRPG/comments/1tkfmo3/comment/on96301/). 공격 예고와 컷신 동작의 이점을 설명하며 puppet-like 인상을 줄이려고 개별 신체 부위의 프레임을 추가한다고 답합니다.
- **[A5] Radical Fish Games 공식 개발블로그, 2023-08-12.** [Project Terra Progress and Gamescom 2023](https://www.radicalfishgames.com/?p=7410). Thomas의 figure editor 설명을 수록합니다. 관찰자에 대한 본 각도에 따라 sprites를 표시·회전·교환한다고 명시합니다.
- **[A6] Radical Fish Games 공식 개발블로그, 2021-05-07.** [CrossCode x Quantum Protocol Collab](https://www.radicalfishgames.com/?p=7178). 본문 말미의 Project Terra 개발 설명에서 bone-based animation system으로 3D models 대신 sprites를 조립한다고 명시합니다. 글 제목의 CrossCode와 해당 기술의 대상 게임을 혼동하면 안 됩니다.
- **[C1] Thomas 'T-Free' Fröse, 공식 AMA 답변, 2023-02-21.** [CrossCode 수작업과 Terra 부위별 3D rig의 직접 비교](https://www.reddit.com/r/JRPG/comments/11836dh/comment/j9fg0fv/). CrossCode 대부분을 손으로 애니메이션했고 Terra에서 머리·상완·하완 등 파츠를 투영/회전/보간한다고 설명합니다.
- **[C2] Radical Fish Games 공식 개발블로그, 2014-04-14.** [CrossCode Update #45: It's GIF time!](https://www.radicalfishgames.com/?p=1833). 대형 보스의 복합 sub-entity/sprite animation editor 기능을 설명합니다.
- **[I1] Radical Fish Games 제작자 직접 인터뷰, 질문 8.** [TestingBuddies 인터뷰](https://testingbuddies.de/interview-mit-radical-fish-games-die-macher-von-cross-code-und-project-terra-im-gespraech). animated 3D skeleton 위 2D sprites/billboards를 선택·스케일·회전시키며 여러 시선 방향으로 돌릴 수 있다고 설명합니다. 인용된 제작자 답변만 기술 근거로 사용했습니다.
- **[G1] Radical Fish Games 공식 프레스킷.** [Alabaster Dawn](https://www.radicalfishgames.com/presskit/sheet.php?p=alabaster_dawn). Project Terra가 Alabaster Dawn의 개발명이었음을 확인합니다.

## 미확인과 재조사 조건

- 실제 본 계층, 좌표 축, 빌보드 회전축, pivot 보정식, 각도 분류식, 임계값, 아틀라스 배치, 캐릭터·적·보스별 방향 수/그림 수, 미러링 예외는 확정하지 않았습니다.
- 공개된 3D 스켈레톤 사용 사실로부터 IK, 모션 캡처, Blender 기반 3D 사전 렌더링, 특정 상용 런타임 사용을 추론하지 않습니다.
- 이 게임에 맞춘 구현 설계로 옮기려면 별도의 입력·카메라·부위 그림·좌표계 계약과 최소 실험이 필요합니다. 현재 문서는 기법 조사이며 본 프로젝트에 대한 채택 결정이나 구현 검증이 아닙니다.
