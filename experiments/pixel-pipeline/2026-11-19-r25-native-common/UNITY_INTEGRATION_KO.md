# GameMap1 R25 전신 1×1 시험

`Tools > Pixel Rendering > R25 GameMap1 Front and Quarter`에서 정면과 쿼터뷰를 한 장씩 요청한다. 원본의 `Gameplay397.Present`를 사용한다. 이미 정상적으로 로드된 원본 GameMap1 Play Mode가 필요하다. 메뉴는 Play Mode로 전환하거나 에셋을 저장하지 않는다.

Unity의 공식 Pipeline CLI에서 동일한 메뉴를 호출할 수 있다.

```powershell
unity command editor invoke_menu --path 'Tools/Pixel Rendering/R25 GameMap1 Front and Quarter'
```

## 설정과 결과

프로젝트의 Git 제외 경로 `LocalOnly/R25_NATIVE_COMMON_CONFIG.json`에 다음 세 경로를 JSON으로 지정한다. 모두 기존 산출물을 읽는 입력이다.

- `cache`에 검증된 `STATIC154.json`과 `static/`이 있는 Integrated154 캐시 디렉터리
- `registry`에 대응하는 `SOURCE_REGISTRY59.json`
- `state`에 현재 보호 해시 128개가 기록된 `STATE31.json`

실행 결과는 `LocalOnly/Runtime399/R25NativeCommon/<run-id>/`에 저장한다. 두 화면은 기존 R24의 동일 포즈 스냅샷 조건을 쓴다. 본 변환이 달라지면 두 번째 렌더 전에 중단한다. 유효한 결과는 `front_1X.png`, `quarter_1X.png`와 각 결과 JSON 및 `RESULT.json`이 있어야 한다. 색·역할·깊이 조건 미달과 마지막 사용 미확인은 각각 `FAILURE.txt`와 `OWNER_RETAINED`에 표시한다.

## 경계

- `NativeWorldFeature395`의 에디터 전용 옵트인 연결은 평소에 비어 있다. 기존 눈 샘플, 기존 렌더러 설정, GameMap1 및 제품 원본 에셋은 그대로 사용한다.
- R25는 실제 눈꺼풀·안구·속눈썹·앞머리의 같은 광선 표본과 현재 월드 깊이를 받는다. 고정된 192×352 원본 재투영에서 캐릭터 1×1, 월드 색 2×2와 물리 월드 깊이를 사용한다. 캐릭터 최종 쓰기는 R25 합성 한 곳에서 수행한다. 준비용 원본 패스와 별도다.
- 정면과 쿼터의 소유권·팔레트·가시 역할·월드 깊이와 자원 회수는 별도 실제 판정이다. 이 소스의 오프라인 검사와 보관 표본 검증은 Native1 실측을 대체하지 않는다. 완료를 확인할 수 없는 자원은 해당 실행만 소유한 채 사용 중인 연결을 해제한다.
