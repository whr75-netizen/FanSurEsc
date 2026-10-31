# 승인 실행66 — 백업 완료, 개별 저장 결과 불확실

이 작업은65 패치 적용/import 전 단계에서 멈췄다. **패치 적용·import·재컴파일·Play·렌더 0**. 저장 호출이 진행 중일 수 있으므로 어떤 저장/실행도 중복 호출하지 않는다.

## 확인 사실

- `Read66.cs:Execute`: 공식 relay PID28304, Unity6000.5.9f1, 같은 프로젝트/GameMap1, Edit/scene clean, dirty30. 2026-10-31T11:13:49Z에 확인. 첫 명령은 `Mesh` namespace 충돌로 컴파일/실행 실패했고 `UnityEngine.Mesh`로 한정한 한 번의 재시도만 실행됐다.
- dirty30은 Shader25, 얼굴 `FaceSourceOwner202.asset` Mesh1, `EditorBuildSettings/EditorSettings/GraphicsSettings/TimeManager`4다. 기존의 큰 Shader native JSON은 만들지 않았다.
- `Backup66.cs:Execute/MeshBackup`: 디스크110파일11,225,609bytes 원본/.meta/기존30수정 파일을 workspace의 별도 `backup/disk`에 복사·SHA 검증. Mesh와 설정4의 native serialized JSON도 별도 보관했다. Mesh 공개 binary9,008,928bytes는 4,060정점/3 streams/7submesh/91bindposes/57morph의 실제 delta를 담는다. `check_backup66.py`가 끝까지 독립 파싱했다. 원본 자료를 Git에서 reset/이동/삭제하지 않았다.
- Shader imported compiled cache, GPU buffers/RT, unknown global binding, 비직렬화 static 상태는 이 백업의 완전 복구 대상이 아니다. 파일 snapshot을 전체 native 복구라고 주장하지 않는다.

## 저장 호출의 불확실한 상태

`Save66.cs:Execute`는 검증된 같은30dirty 객체만 대상으로 `AssetDatabase.SaveAssetIfDirty(o)`를 순서대로 호출했다. 일괄 `SaveAssets`, `ClearDirty`, 씬 저장은 사용하지 않았다. 시작 전 `SAVE_STARTED66.json`, 각 반환 뒤 `SAVE_PROGRESS66.json`을 기록했다.

- 시작: 2026-10-31T11:15:37Z.
- 앞29건은 API가 반환했지만 dirty가 유지됐다. 디스크 byte 변경0, 확인한 non-Shader serialized 내용 변경0.
- 마지막 `ProjectSettings/TimeManager.asset`의 `SaveAssetIfDirty` 호출 전까지 진행됐고 그 뒤 반환 기록이 없다. `SAVE66.json` 최종 보고서도 없다.
- relay45초 timeout 후 정상 EOF로 relay만 종료했다. **Unity를 종료하거나 pending 저장을 취소/재실행하지 않았다.** 마지막 설정 저장의 실제 완료/실패 여부는 불확실하다.
- 호스트 Unity PID28304는 생존했으나 `Responding=False`였다. CPU/메모리 수치만 읽었고 UI/대화상자 상태는 확인하지 않았다. 기본 Editor.log는10월28일의 오래된 파일이라 이번 오류 근거로 쓸 수 없었다.
- 11:17:06Z 재검사에서 보호된110디스크파일 변경0, 기존30수정 파일 보존. 현재 실행 중인 native API의 내부 상태를 추정하지 않는다.

`Save66.cs`는 **실패/정지 재현 자료이며 다시 실행할 승인이나 안전성 근거가 아니다.** REQUEST와 SAVE_STARTED marker가 재실행을 막는다. 일반 asset용 API를 설정 객체에 적용한 실제 경로를 검토해야 하며, TimeManager가 원인이라고 단정하기 전에 반환/대화상자/에디터 응답의 실제 상태를 확인해야 한다. 현재 대화상자가 있는지는 CUA 제한 때문에 미확인이다.

## 다음 진행 조건

현재 Unity의 저장 진행/대화상자 여부를 비파괴적으로 확인해야 한다. 사용자 화면 조작·앱 종료·초기화·강제 GC는 하지 않았다. 이 상태가 해소되기 전에는65 패치/import/Play를 진행할 수 없다. 전역 binding 추정 복원이나 null 치환은 없다.

백업 본문은 원래 workspace `render-fix21/apply-capture66/backup`에 유지한다. 대용량 원본 복사본은 이 Git 실험 스냅샷에 중복 커밋하지 않는다. `BACKUP66.json`/`BACKUP_CHECK66.json`에 경로·SHA·검증 범위를 기록했다. 마지막 실제 상태와 작업 범위는 `STATUS66.json`을 확인한다.
