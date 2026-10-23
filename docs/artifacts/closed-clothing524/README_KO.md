# 524 · 옷의 선행 닫힌 영역 후보 — 실제3쌍 실패 / 기본OFF 미채택

## 결과

524는 적용 버전이 아니라 작업 기록 번호입니다. 활성된 기존348 수정44d13c0을 보존했습니다. 머리511/source-ray513(옵션512)은OFF이며 시간DP516~521 확장은 재개하지 않았습니다. 새524도OFF·미채택입니다. 전체 가시·얼굴 회색·실시간·프로젝트 완료를 주장하지 않습니다.

메인.html을523에서 현재 상태로 갱신했습니다. 실제 소매 source 래스터 원인과 독립 경계 누락 확인은523 기록입니다. 기존 프로젝트6000.5.9f1/URP17.5를PID22792로 공식 경로에서 열고 공식MCP 호스트 연결을 복구했습니다. 새 설치/패키지/보안 변경·Library403 재시도는 없습니다.

## 실제로 구현한 경계

변형된 body의 선언된 clothing submesh3(2093삼각형) 투영 → 공유 유향변 상쇄/교차 분할/positive winding 연속 합집합 → 닫힌 원경계89~90점 → .1875논리셀 이내 선분 곡선47/53/51점 → CurveArea511의 셀 교차 면적 → 기존 SelectRegions의 면적 손실＋.14*8방향 경계 길이 공동 선택입니다. 원래480 마스크/중심샘플, 박스/볼록껍질, dilation/erosion/시간이력은 경계 입력이 아닙니다. 기존 한 팔±1셀 선택은 후보 안에서 대체했습니다. 이는 면적/둘레 중심의 작은 공간 디자인 후보이며 외곽 계단 리듬·시간적 지각 품질 전체를 구현했다고 주장하지 않습니다.

면적을0.5에서 각각 자르는 방법도 아닙니다. 실제 선택의 반례 수는 REGIONAL_DECISIONS524.json입니다: [{"frame": 33, "filledWithAreaBelowHalf": 0, "emptyWithAreaAboveHalf": 0}, {"frame": 34, "filledWithAreaBelowHalf": 2, "emptyWithAreaAboveHalf": 1}, {"frame": 35, "filledWithAreaBelowHalf": 0, "emptyWithAreaAboveHalf": 0}]. 이 수치 자체가 픽셀아트 품질 합격은 아닙니다.

같은C를 source 옷 fragment의 선행discard, Prepare의채움/packet선택, 최종Resolve의경계권한에 연결했습니다. 원래옷을앞에서제외하여기존depth가뒤표면을드러내게하며최종RGB만지우는방법이아닙니다. 선택된빈셀은동일셀native2×2의실제옷primitive/UV/depth/RGBA만받고이미다른중심표면이있으면덮지않습니다. 무지정donor/후단좌표예외가없고지원불가를audit실패로남깁니다. 정상손가락/피부/머리에이선택기를적용하지않았습니다.

## 실제33/34/35의한번OFF/ON비교

Rig|Walk_Loop phase .41250253/.42500257/.43750262를실제로진행시킨뒤각발생포즈를동결했습니다. 같은pose/light/time에서OFF/ON을비교했고프레임은생략하지않았습니다. target(198,85)의C면적은 .41390166/.44286850/.42409378, C는모두false입니다. 원래source패킷은0→[depth13.90072155,role11,primitive724]→0이며native표시에서1논리셀이nominal2×2화면픽셀이됩니다.34번만튀던셀은source래스터단계에서이미제외됩니다.

경계밖옷최종쓰기0, 최종게이트위반0입니다. **하지만선택된영역을채울native donor가3/3/2셀누락되므로실패**입니다. 첫33번의(199,89)/(227,94)/(202,103)는선택면적 .521236/.822754/.534886인데비어남습니다. 정상실제프레임콜백으로33번한포즈만추가조회한마스크는원래3쌍중33번과전체비트동일이며, 이3셀의native4표본은OFF/ON모두0입니다. 경계가채움을선택해도현재4표본packet입력이영역을완성하지못합니다. 이것을지우거나원본으로fallback하여성공으로세지않았습니다. 미세연속geometry/alpha/샘플위상관계의추가판별과연속표면packet저작이남으며, 단순샘플수확대나새패치를자동시작하지않았습니다. 전체Walk는이실패후미실행입니다.

34번비옷(225,66) 한셀은같은UV/primitive5505/role8입력에서RGB .03078369가같지만OwnerLines333의outer1→0,reason1→0으로 .55배외곽선이없어져최종 .01693103→.03078369가됩니다. 후보의이웃옷영역선택이외부경계판정에미치는실제효과입니다. 얼굴회색이나원본texture변경으로분류하지않았고디자인허용여부도미판정입니다.

## 얼굴 회색 질문

HeadLocal367.DrawSource는main에body,별도head카메라에face/eyes/hair를그린뒤JoinBare/DeferredEyes로합칩니다. 얼굴분리렌더는실재하지만그사실이회색원인이라는증거는없습니다. 현재3쌍의얼굴원본/메타/Prepare/base버퍼는OFF/ON동일,얼굴의미영역의최종RGB도동일합니다. 재질/shader/texture/rendererenable/MaterialPropertyBlock/culling/RT참조와styleEnabled/faceMain/faceProvider/proofOnly상태는pair간및시작전/복원후동일합니다. 이관측에서는회색이재현되지않았습니다. 머리최종colour버퍼의7/15/8셀차이는MainToHead로복사된옷영역이며실제얼굴변경0과구별했습니다. 회색최초발생버퍼·어느초기화/다른테스트가바꾸는지·전체초기로딩구간은여전히미확인입니다. 현재정상관측을회색문제해결로확대하지않습니다.

## 비용과전달

워밍후후보geometry9.75/9.25ms,면적 .269/.248ms,선택8.65/9.54ms,업로드 .355/.331ms,합계약19.0/19.4ms입니다. 첫포즈는JIT등포함52.5ms. 같은실행HeadLocal.RenderFrame wall의OFF/ON은273/322,359/426,711/273ms로변동이크며PlayerFPS/속도개선근거가아닙니다. 셰이더/GPU총비용은별도확정하지않았습니다. 기존머리packet약212ms와혼용하지않습니다. 이값과기능실패로기본OFF미채택입니다.

전신3프레임native crop을normalWebP17/16/17ms와250ms검사용GIF로보존했습니다. 짧은구간미리보기는35→33으로돌아가며전체Walk루프가아닙니다. PNG/float버퍼원본은로컬Adjacent폴더에보존합니다. Library403은우회/재시도하지않았습니다.

## 실행실패와복원

처음임포트전Console0은새코드컴파일통과가아님을정정했습니다. RenderGraph TextureHandle API오류는수정후실제코드계산실행으로통과했습니다. 진단의GetInstanceID폐기API는GetEntityId로수정했습니다. 이는제품런타임오류와구별합니다. 최초수동포즈조회는sourcepose불일치로제외했고privatePresent조회는UnityMCP의System.Reflection금지로실행전거부됐습니다. 우회하지않고허용된정상프레임콜백으로한포즈를관측하여일치0차이를확인했습니다.

캡처의try/finally가입력/Animator/시계/후크를복원했고, 별도직접조회·초기Edit복원은RESTORED_EDIT524.json및STOP_RESTORE524.json에기록합니다. 사용자QualitySettings/TimeManager기존해시를보존합니다. 새코드는기본OFF·실패실험체크포인트로커밋하며정상버전이나채택완료라고가정하지않습니다.
