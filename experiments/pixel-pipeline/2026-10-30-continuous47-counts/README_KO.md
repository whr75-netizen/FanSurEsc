# continuous47 — 동결된 여섯 프레임 증거

이 스냅샷은 `counts47-087454994917423fa13c5fe72eceb7f4`의 frame96–101을 보관합니다. 이전46과 프레임 번호가 같아도 별도 sequence입니다. **제품 수정본이나 GPU 검증 후보가 아닙니다.** 원본 실험·Unity·미저장 dirty25를 변경하지 않았고 진행 중 메모리 추가 진단을 포함하지 않습니다.

## 재현

```powershell
python -B experiments/pixel-pipeline/2026-10-30-continuous47-counts/replay.py
python -B experiments/pixel-pipeline/2026-10-30-continuous47-counts/verify_snapshot.py
```

첫 검사는 NumPy가 필요합니다. 일반 Python에 없다면 기존 Blender bundled Python으로 실행할 수 있습니다. Blender 앱이나 Unity를 실행하지 않습니다.

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe' -B experiments/pixel-pipeline/2026-10-30-continuous47-counts/replay.py
```

원본 `analyse_counts.py`와 `eye_cache42.py`의 함수·클래스만 읽어 실행합니다. 원래 CLI의 절대 경로, 이미지 생성, 파일 저장과 현재 제품 해시 조회는 실행하지 않습니다. 외부 입력 읽기와 파일 쓰기를 차단합니다. 15종 ROI 배열과 GPU FeatureCounts19만 float32 그대로 압축한 fixture를 사용합니다. 전체225파일/씬 덤프/원본 asset을 복제하지 않습니다. 압축은 손실이 없고 위아래 배열 변환은 원래 read 함수와 같습니다.

`archive/`의 보고서·숫자·후보·capture source는 원본 바이트를 보존합니다. `SOURCE_MANIFEST.json`에 복사/추출 원본 위치·크기·SHA256이 있습니다. `EXTERNAL_INPUTS.json`은 제외한 전체 캡처와 씬 상태 덤프를 기록합니다. 이 보관본만으로 packet/allocator/최종 가림의 저장 입력 재생은 가능하지만 Unity 전체 캡처·씬 원복·현재 메모리 상태 재현은 아닙니다. `PACKAGE_MANIFEST.json`은 Git 줄바꿈 설정과 무관한 파일 해시이며 `.gitattributes`는 이 폴더에만 적용됩니다.

## 확인 결과와 한계

- 1,536 packet×12성분 전체 CPU/GPU 비교의 최대 절대 오차는 `5.960464477539063e-08`입니다.
- frame99→100에서 `(223,52)`의 iris 가중치5와 budget2는 유지되고 rank는1→2로 밀립니다. 경쟁 셀의 비용 순위가 바뀌어 대상이 탈락합니다.
- 새로 선택된 `(224,52)`는 frame100에서 최종 앞쪽 hair depth/alpha에 덮입니다. 할당2셀 중 하나가 후단에서 사라져 실제 홍채가1셀입니다. 실제 앞쪽 머리를 잘못된 가림으로 단정하지 않습니다.
- 기존 area budget을 유지한 오프라인 visibility gate는 12개 eye-frame 쌍 중 frame100/eye1만 바꿉니다. frame101의 대각 형태는 남습니다. 그림의 실제 영상과 feature-ID 진단색 도표를 구분해야 하며 대안 후보의 실제 RGBA 렌더는 없습니다.
- `archive/candidate/EyeFeature348_visibility_gate47.compute`는 **미import·미GPU컴파일·제품 미적용** 원문입니다. 런타임 밖에 보관할 뿐 실행하지 않습니다. upper-line/sclera 간접 회귀, 회전/blink와 전체 공동 배치 문제는 미검증입니다.
- 원복 기록은 Edit/scene clean/기존 dirty25, 객체·컴포넌트3065개, tracked12파일의 검사 범위입니다. 메모리 감사48의 정정에 따라 `Profiler.GetTotalAllocatedMemoryLong()`은46 종료1,628,792,522bytes→47 종료2,001,161,288bytes, 차이는372,368,766bytes=355.12MiB입니다. **2.00GB는 총값이며 증가량이 아닙니다.** Windows working set과 다른 지표이고 잔류 소유자는 미확정입니다. `MEMORY_CORRECTION.json`에 원자료 해시와 정정 이력을 기록했습니다. 현재 Unity counter 조회는40초 timeout으로 실행 결과 불명이며 재실행하지 않았습니다. **완전 원복·메모리 정상·전체 수정 성공을 뜻하지 않습니다.**

`evidence/actual-*`는 원래 실제 여섯 프레임의 복사본입니다. `actual-features-above-offline-gate-below.png`의 아래쪽은 오프라인 feature-ID 비교이며 후보 GPU 영상이 아닙니다. 동기 GetData/WaitForCompletion의 stall이 있으므로 캡처를 실제 wall-clock 성능 벤치마크로 해석하지 않습니다.

기존 코드 보관 commit1835f10과 함께 읽되 이 sequence를 이전 프레임95 팔레트 입력과 혼용하지 않습니다. 새 Unity 실행·자산 import·제품 적용·memory 진단·cache 삭제·push는 수행하지 않았습니다.

원본 capture C#의 빈 EOF와 후보 compute/diff의 기존 공백은 바이트/해시 보존을 위해 그대로 보관했습니다. Git 공백 속성의 해당 예외는 이 보관 source에만 적용되며 새 재생 코드·문서의 검사는 유지합니다. 원본 파일을 포맷하거나 제품 소스를 고친 것이 아닙니다.
