# 실행66 — Unity 복구 확인, 파서 수정, 65 제품 패치 미적용

## 현재 실제 상태

사용자의 11:27 복구 승인으로 정상 종료 요청 후에도 멈춘 Unity PID28304만 종료했다. 다른 Unity, Hub, Chrome, ChatGPT, Codex, worker는 종료하지 않았다. 같은 Unity6000.5.9f1과 프로젝트를 11:30 UTC 새 PID31520으로 한 번 재실행했다. 원본 파일, Library, cache, 세션을 삭제하거나 초기화하지 않았다.

`RECOVERED66.json`의 11:33:15 UTC 실제 읽기 결과는 GameMap1 Edit, scene clean, roots37, options false/None, timeScale1, captureDeltaTime0, 양 pipeline PC_RPAsset이다. **Mesh와 설정4의 직렬화 내용이 백업과 모두 ExactUTF8/SHA 동일**하다. 원본에 백업을 덮어쓰는 복원은 하지 않았다. 읽기 전 dirty24 → 후25이며, Mesh를 로드/직렬화한 구간에 flag가 추가됐지만 내용 해시는 같다. 전체 native/GPU/static 상태나 object identity가 동일하다는 뜻은 아니다.

**65 제품 패치 적용, import, Play, 새 캡처는 아직0.** 기존30 수정 파일과 보호110 파일 bytes를 보존했다.

## 정지 원인 보고의 정정

처음의 “TimeManager 저장 정지”는 잘못된 추정이다. 시작30 대상과 반환29 경로를 대조하면 TimeManager는 26번째로 반환했고 미완료는 **FaceSourceOwner202 Mesh**이다. 앞29 API 반환과 dirty 유지는 실제 저장의 증거가 아니며 SaveAssetIfDirty 내부 GUID lookup 성공은 기록되지 않았다. 해당 object overload는 lookup 실패 시 저장 없이 반환할 수 있다.

원래 `Save66.cs:36–37`은 Mesh JSON9,357,126bytes를 두 번 parse하고 DeepEquals로 다시 직렬화했다. 작은 packet용 `Json58.ParseValue`는 숫자마다 남은 문자열 전체를 세 번 Substring 복사한다. 숫자536,436개이며 단회 전체 parse의 예상 누적 UTF16 복사량은13.81TiB다. RAM 점유나 실제 완료량 측정이 아니다. 작은 parser를 이 큰 입력에 재사용한 것이 잘못이다.

성공 분기는 인덱스를 전진시키고 구조 loop는 값과 구분자를 소비한다. malformed 입력은 throw, recursion은 depth128 제한이다. 이 유효한 입력에서 무한 loop/인덱스 무진전 근거는 찾지 못했다. 높은 제곱 비용으로 느린 유한 작업이라는 설명이 유력하나 live stack은 미확인이다. 완료 시간은 예측하지 않았다.

OS 관측16.17초 동안 CPU16.125초, read/write bytes0. earliest/hottest TID28308은 Running이고 TID13200은 그 소유 critical section을 기다렸다. 선택5 thread의 WCT cycle 없음은 native deadlock 배제의 증명이 아니다. 정확한 멈춤 statement는 항목 내부 로그가 없어 확정하지 않는다. `OBSERVATION_RESULT66.json`과 `PARSER_STATIC_AUDIT66.json`이 과거9cdad2b의 원인 추정을 정정한다.

## 수정 함수와 실제 검증

- `Json58Linear66.cs:Parse/ParseValue`: 역사58 소스는 보존했다. suffix Substring 대신 literal 길이만 CompareOrdinal한다. 작은 입력65,536chars 제한과 duplicate member 거부를 추가했다.
- `SerializedContent66.cs:HashFile/HashText/Verify`: 파일과 현재 native string을 UTF8/SHA256 streaming으로 비교한다. 고정 추가 hash buffers81,920bytes이며 전체 JSON tree를 만들지 않는다.
- 같은 fingerprint면 ExactUTF8. 표현이 다를 때만 양쪽64KiB 이하에서 작은 의미 비교를 한다. 큰 불일치, 고정밀 숫자, invalid/duplicate는 명시적인 Unverified로 남기며 같다고 만들지 않는다. 작은 필드순서·공백 차이는 구분한다. 큰 필드순서 변경의 의미 동등성은 이 경로에서 미검증이다.
- `Save66.cs:Execute`: 새 비교기와 항목별 API 전/후·ToJson/검증 단계 기록으로 바꿨다. **수정 Save66은 실행하지 않았다.** 이전 REQUEST/SAVE_STARTED guard가 자동 재호출을 막는다.
- `build66.py`:66 command는 고친 작은 parser를 쓴다. 파일 수정이 멈춘 Unity의 로드된 코드를 자동 갱신한 것은 아니다.
- `TestVerification66.cs`: 정상/변경/필드순서/표현/Unicode/encoder 경계/duplicate/정수 정밀도/invalid/array 순서/큰 배열/큰 순서변경/parse budget 등14사례 통과.
- 외부 CLI 실제9.36MB 단회 검증: hash 입력18,714,252bytes,12.311ms, 추가 buffers81,920bytes. 입력 string 자체 메모리는 별도다. 작은 벽시계 시간은 setup/JIT 영향이 있어 선형 속도의 증명으로 쓰지 않고 hashed bytes2N으로 작업량을 확인했다.
- SDK에 Regex 참조가 없어 복구 읽기가 컴파일 전에 실패했다. 외부 assembly 추가 없이 작은 수동 scanner로 대체하고14 작은 검사를 재통과했다. HashFile/HashText는 그대로여서 큰 입력은 반복하지 않았다.
- `Recovered66.cs:Execute`: 새 Editor에서 이 검증기로 native5 비교가 정상 반환됐다. 제품 전체 C# 및 GPU 검증과는 별개다.

## 보존과 다음 단계

workspace `render-fix21/apply-capture66/backup`에 디스크110 파일11,225,609bytes와 native5 JSON, 공개 Mesh binary9,008,928bytes가 있다. Mesh binary의4060 정점,7 submesh,91 bindposes,57 morph delta를 독립 파싱·SHA 검증했다. Git에는 manifest와 검사만 보관하며 큰 백업은 중복 커밋하지 않는다.

compiled Shader cache, GPU buffers/RT, unknown global binding, 비직렬화 static state의 완전 복원은 보장하지 않는다. 이번 native5 비교와 디스크 차이는0이므로 원본을 임의 복원하지 않았다. 다음은 현재 상태를 기준으로65의 두 C#만 적용·컴파일하고 local-buffer 동작을 확인하는 단계다. 캡처는 이후64의 동일 sourceId/geometry/view/sample/backing 계약이 충족돼야 하며, 예전 O(N²) 검증은 다시 사용하지 않는다.
