# 제한 GPU 통합 준비와 미채택 경계

## 1. 먼저 검증 가능한 gate47 — 제품 영구 적용 전

대상: `Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/EyeFeature348.compute`.
정확 함수: `CountPacket19`에서현재최종선택과동일한nearest-centre iris 대표깊이를packet.uv.z에추가하고,기존final hair/brow/body gate통과를uv.w에기록한다. `IrisAllocated19`는면적을그대로합산하되최종가림실패셀을자격/순위에서제외한다. `BeforeIris19`의기존비용/UV/tie식과Classify/Own/ChooseLayers/Evaluate/최종합성은바꾸지않는다.

준비물: `patches/EyeFeature348_visibility_gate47.compute` 전체후보및`PROPOSED_ONLY.diff`.
상태: CPU전체packet/allocator/line간접검사완료. **GPU컴파일·실제RGBA검증미완,제품반영불가상태**.
추가검증승인범위: 임시compute자산1개import,기존EyeFeature348.candidateShader의runtime참조만A/B,현재씬저장없이임시Play에서동일open포즈최소프레임,실패셀과양눈/흰자/upper/lower-lid 버퍼확인,메모리카운터/자원회수,정상Play종료와참조·dirty·파일hash복원. 제품compute원본영구교체는이승인에포함하지않는다. 현재추가캡처중단상태이므로실행하지않았다.
리스크: CountPacket의uv.zw를다른코드가읽는지전체소스추가정적확인필요;NativeLineAllocated의간접호출;동일 pixel의 최종 가림(논리셀)와4×coverage의차이;GPU부동소수/대표tie재현. gate가실제hair가림을없애거나원래면적을최소셀수로늘리면실패.

## 2. shape/cache49 — 현재 그대로 통합하면 안 됨

정확 최소후속파일3개는아래다. 이목록은적용승인범위제안이며완료된GPUdiff라는뜻이아니다.

1. `EyeBoundaryRestore348/Runtime/EyeFeature348.cs`의Initialise/Prepare/OnDisable: 모델topology+style+TemplateRole/RGBA+명시pose/lid상태로source key form을등록. 기존template의role/cell ID/상대좌표/색출처를한번추출. 매프레임기존full.Project(headMatrix*modelEye.centre)의공통anchor만보내며새GPU readback/화면RGB캐시를추가하지않는다. 등록되지않은blink/회전은열린눈으로대체하지않고trial을중단한다. 현재완료된것은Python adapter뿐이며자동pose-state classifier나모든상태template는없다.
2. `HeadLocal367/Runtime/EyeRenderer367.cs`의Dispatch:같은CountFeatures/Evaluate pass에등록된state/fingerprint와공통translation/reference좌표를전달한다. 순서변경이나새RT/pass는필요없다. 기존16subsample source/최종가림을계속쓴다.
3. `EyeBoundaryRestore348/Shaders/EyeFeature348.compute`의IrisAllocated19/NativeLineAllocated19/ChooseLayers19/Evaluate/Own:rank가irisshape를매프레임다시만드는대신등록feature-cell ID에서role/footprint/원래template texel을선택한다. 같은feature source기하에대표표본을연결하고외부가림을적용한다. pigment는Own의nearest재매핑대신등록된source texel을직접참조한다. **NativeLineAllocated19의iris-occupancy 종속과흰자/안검충돌을함께해결해야한다.** upper-line을기존잘못된raster로그대로캐시하거나skin보다항상앞에놓는식으로해결하면안된다.

현재필수미완입력은현재open상태에서iris/sclera/upper-line을함께정의한키폼의등록근거다. 기존Template216에는role6가없고그흰자12셀은현재6pose의S1지지와맞지않는다. 원래326의상하경계있는reference 또는이미있는native upper-arc/state 자료와정확한좌표등록을먼저연결해야한다. 눈모양을새로창작하거나현재찌그러진최종raster를자동승인하지않는다.
또한sourceUV/triangle/bary를cachecell에고정바인딩하는부분과일반face-skin 위의특징레이어허용범위/실제lid가림의구분이필요하다. 현재Pythonadapter는destination의S1/S2를다시찾는단계가남아있다. “cache가있으니shape손실문제가전부해결됐다”라고보고하지않는다. 앞선흰자손실을전부실제가림으로승인하는것도금지한다.

이부분은GPU실험승인만받는다고디자인/등록공백이해소되지않는다. 현재full49를제품에바꿔달라고요청하면안된다. gate47의좁은검증과별개로남긴다. 수동key form선택이실제로필요하다면원본reference와구체후보를먼저보여승인받는다.

## 3. 테스트/복원 순서

추가승인이올경우에도①현재상태/파일hash/dirty→②작은컴파일→③한고정frame/기존반례→④필요최소phase변화→⑤정상Play종료와반납을순서대로수행한다. 이전메모리증가소유자가미확정이고최근읽기command가timeout이므로현재연결의읽기응답부터확인해야한다. GC/Unload/강제clean/재시작/씬저장/대량loop는포함하지않는다.
원복은RT수뿐아니라Allocated/Reserved/MonoUsed/MonoHeap과동일 PID의WorkingSet/PrivateCommit을같은시점에남긴다. 증가하면추가렌더를멈추고소유분석으로넘긴다. 47이frame100을고쳐도frame101대각shape가남으므로전체눈해결이라하지않는다.
