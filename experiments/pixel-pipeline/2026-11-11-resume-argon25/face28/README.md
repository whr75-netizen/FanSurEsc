# 얼굴 원본 특징 및 실제77 단계 검증28

기준 커밋 dc4e9155. 제품77 기본값과 사용자 tracked30은 변경하지 않았습니다.
GPU115 평가기는 포함되지 않으며 새 shader/kernel/import/dispatch를 추가하지 않았습니다.

## 구현 및 실제 확인

- `source_features28.py::extract`: 원본 RGB/UV에서 양쪽 색 극값의 양성 근거를 구합니다. 반코드 반올림 불확실성보다 큰 양쪽 투영 차이를 확인하며 native 반경1/2/4와 D4 대칭 방향을 따로 기록합니다. 기존64가 놓친 (382,704) 볼 선은 세 반경 모두 양성입니다. 실패한 검출은 미정이며 잡음/삭제 허가가 아닙니다. 색 평균, Lab bin 절단, 최소 면적 삭제, 팔레트 배정은 없습니다. 이것은 전체 영역 분할 완성이 아닙니다.
- `test_features28.py::main`: 단조 RGB 경사,8텍셀 AA,약한3텍셀 선,회전/반사,미정 domain19검사 통과. `SOURCE_NATIVE28.npz`는 실제103 입력의 rgba/mask/thinX/thinY만 보존한 부분집합입니다. 원본/부분집합/VRM/image5 해시는 `SOURCE_INPUT28.json`입니다. NumPy/Pillow가 있는 Python에서 `python test_features28.py`, `python source_features28.py`로 CPU 검사를 재현할 수 있습니다.
- `prepare_face28.py::main` / 외부 `CommandScript.CaptureStages28`: 검증된27 runner에 한 프레임의 main/head 단계16개를32행씩 추가 관측했습니다. 실제 shader는 SurfaceCarrier27이고 제품은77입니다. 첫 `capture`는 함수 호출 연결 누락으로 단계 관측0건이었고 정상 복원했습니다. 수정 후 `capture-stages`의 frame99/serial6/sourceId geometry24-20261111T073713778Z-bd898f51-frame99만 최종 단계 근거입니다. 첫 실행을 성공으로 세지 않았습니다. 새 디렉터리/생성 전용 파일/완료 marker 계약을 유지합니다.
- `review_face28.py::stage/main`: 같은 프레임/영역에서 main prepared→postLine의459변경 모두 audit 선 사유가 있고 role7/8/9/10/12/13입니다. 얼굴 role3은59셀, 선형 RGB53색/sRGB8 32색이 전후 동일합니다. final은51선형색/33sRGB8입니다. 아직 얼굴 region LUT가 없어 임의 팔레트 밖 개수로 바꾸지 않습니다. 기존 눈 LUT 검증27과 별개입니다.
- 실제 순서: `FullFeature367.DispatchPost` Restore→`HeadLocal367.JoinBare`→main OwnerLines→`DeferredEyes.MainToHead`→눈 합성→EyesToMain. head의 자체 OwnerLines는 건너뛰지만 main이 합친 머리에 선을 처리합니다. Head prepared/postLine 차이는 MainToHead copy를 포함하므로 별도 선 오류2661개라는 뜻이 아닙니다. main beforeStyle은 합치기 전이므로 합친 뒤 얼굴 마스크와 직접 색 개수를 비교하지 않습니다.
- `VISIBLE_SOURCE_EVIDENCE28.json`: 실제 얼굴 UV59셀을 native image5의2×2 증거에 대응,8셀에 양성 witness가 있습니다. bilinear weight는 진단 근거이지 셀 전체가 한 색 특징이라는 판정이나 새 family가 아닙니다.
- `review_turn28.py::main`: 이미 저장한 최종27 frame128/129/130,132/133/134를 원배율/nearest로 확인했습니다. 소멸2셀은 owner2 canonical(4,5), actual ROI(4,6), -117, 실제16표본 중 가시2표본입니다. CPU32개 ray가 GPU와 일치합니다. 혼합 피부2643/2644의 반대 눈 blink 우세/다른 hit의 반대 소속 때문에 현재2.5 AND gate가 기각합니다. 이것은 정책 일치이며 유일한 미술 정답 증명이 아닙니다. 피부 무시/눈 덧칠/가상 대안 이미지는 만들지 않았습니다.

## 남은 문제와 필요한 계약

1. **원본 근거는 있지만 전체 얼굴 partition은 미완입니다.** 실제 볼 선을 soft importance/child evidence로 전달할 수 있게 됐습니다. 그러나 source extremum만으로 그 주변 gradient/AA를 어디까지 같은 닫힌 색 영역으로 묶고 어떤 parent/family를 공유할지 결정되지는 않습니다. 이전104의 과분절 또는 parent8 평탄화는 이 반례를 해결하지 않습니다. 양성55704텍셀을 모두 독립 family로 만드는 것도 하지 않았습니다. 필요한 것은 원본 특징을 보존하는 경계/영역 목적함수와 그 반례 검증이지 새 갈색/고정 색 수가 아닙니다. 자동 분할이 원천 불가능하거나 사용자 추가 입력이 반드시 필요하다고 증명한 결과는 아닙니다.
2. **외곽선 색 출처와 선 분류는 다릅니다.** 원본 MToon outlineColorFactor와 width는 확보했습니다. 현재 `OwnerLines333.OwnerLines`는 role3을 eligible에 넣지 않으며 대상 부위에서는 `c.rgb*_LineTone`입니다. 얼굴 선 사유를 UV의 색소선/실루엣/안쪽 색 경계/명암 경계/부분AA로 구분하는 생산자 계약은 없습니다. 원본 outline slot 하나를 모든 어두운 얼굴 픽셀에 대입하지 않았습니다. geometry/alpha로 확인한 선 클래스와 원본 material outline slot을 연결하는 일이 남았습니다. 새 색 선택은 필요하지 않습니다.
3. 이미 있는 `ResolvedRegionInput.Build/LookupRGB8`(87a5475c)와58 수학은 재사용 대상입니다. 실제 region/Q/outline 클래스 공급이 확정되기 전 전체 피부를 단일 family 또는 source texel별 family로 연결하지 않았습니다. 제품 `RestoreStyle335.ApplyShadeBoundary`83행의 old≈q 조기 반환,89행 RGB*factor는 기존 경로에 남습니다. 이 단계 결과로 그 제품 연결이 고쳐졌다고 주장하지 않습니다.

## 복원·메모리·보관

최종 실행 native44내용 동일, InputSettings 동일 참조/JSON/장치/keyboard, scene/pipeline/time/background/Play 옵션/global74 복원, borrowed GPU buffer 해제0, pending0. 07:45:38UTC PID28080은 Edit/비컴파일/비전환이며 RT30입니다. 첫 관측의 clean AssetImporter 수명1건 Unavailable은 그 내용 변경과 구분했습니다.

단계 관측 allocated+36.28MiB/reserved0/Mono used-47.73MiB. 추가 관측은1회245760B/동시1개, 완료 후 소유 NativeArray만 Dispose합니다. 디스크 단계량33.4MB를 그대로 메모리 잔류라고 세지 않습니다. 내부 카운터와 OS WorkingSet64/PrivateMemorySize64도 서로 다릅니다. heap/native root 프로파일은 없으므로 누수 확정/해소 모두 미확정입니다. GC/Unload/임의 정리는 하지 않았습니다.

`ACTUAL_STAGE28.zip`은 최종 한 프레임의 실제 plane/원시 입력/manifest/marker입니다. `CAPTURE_EVIDENCE28.zip`은 두 시도의 원래 명령/상태/검증 로그입니다. 이전27 회전 packet은 형제 producer/support/surface27의 ACTUAL_GPU_FINAL27.zip과 sourceId로 대응합니다. 실행기에는 원래 절대경로와 Editor 연결 의존성이 있어 저장소에서 자동 실행하지 않습니다. CPU 입력/테스트는 독립 보관했으나 전체 실시간 재현 이식성을 주장하지 않습니다.

검수 PNG3개 Library 저장 성공, 정확한 ID는 `LIBRARY28.json`. Windows `os.setxattr` 미지원으로 로컬 xattrs 적용만 실패했고 identity JSON을 보관했습니다. 최종 상태는 `STATUS28.json`, 파일 무결성은 `ARCHIVE28.json`입니다. 커밋 탐색: `git log -- experiments/pixel-pipeline/2026-11-11-resume-argon25/face28`.
