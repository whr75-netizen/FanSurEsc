# N15 실제 비교 산출

현재 출력은 `compare01`입니다. 이전 N14와 Unity는 보존했습니다.

| 비교 | 방법 | 실제 명암 | 3문 native | 재생성 |
|---|---|---|---|---|
| 왼쪽 A | 해석적 half-open 평면 전개도 | 면 법선의 팔레트 band, 입체 그림자 없음 | 183×165,9색 | 동일 5단계 |
| 오른쪽 B | 유한 3D box의 픽셀 중심 최근접 광선 | 면 법선 band·실제 광선 그림자 | 183×165,11색 | 동일 5단계 |

`comparison-x4.png`는 두 결과의 4배 nearest **표시용**입니다. `solid-native.png`가 실제 게임용 native PNG입니다. `geometry/solid/model3.obj`는 world 미터의 편집 가능한 입체이며 `geometry3.json`에 치수·카메라·원점·부품을 기록했습니다. 원본 무늬는 `appearance-reference.png`의 관측색과 같은 UV 주기를 사용합니다. 참조 이미지의 순수 albedo를 복원했다고 주장하지 않습니다.

N14의 오류는 방향 의존 선 raster를 coverage에 붙인 것, 표면 모서리와 깊은 틈을 모두 검정 처리한 것, 임의 면 밝기·상판 아래 3개 경계를 중첩한 것입니다. N15는 coverage를 기하만 소유하게 하고 틈·외곽만 검정, 노출 모서리는 실제 재질의 계열색으로 선택합니다. 상판 접촉부에 추가 장식선을 넣지 않습니다.

실행은 `Run-Native15.cmd` 또는 `native15_cli.py --output <새 workspace 폴더>`입니다. 기존 WorkLoop의 geometry→material→shade→raster→validate 5단계가 AI/API 호출 없이 이어집니다. 이번 실제 CLI 실행은3.220초이며 검증166조건이 통과했습니다. 시간은 코드 설계·AI 응답 시간이 아닌 고정 제작 프로그램의 실행 시간입니다. Cmd의 Windows 더블클릭은 실행하지 않았습니다.

범위는 이 고정 시점 캐비닛의 2문/3문입니다. 미술 승인·임의 물체 자동 복원·Unity 통합·동적 조명·자유 회전 완성을 뜻하지 않습니다. 조건별 실제 측정은 `validation.json`, 코드/입력/산출물 SHA는 `execution.json`입니다.
