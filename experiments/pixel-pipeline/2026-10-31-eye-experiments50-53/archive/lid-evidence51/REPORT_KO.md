# 눈 source 근거51 — 정보 부재와 전달 누락을 분리

**기존 정보가 있습니다.** 현재 prefab은 `FaceSourceOwner202.asset`를 실제 face source로 참조하고, 원래 parent24/iris16 contour, 눈마다24점 native boundary, `Fcl_EYE_Close/Close_L/Close_R` 변형을 보유합니다. 따라서 사용자에게 처음부터 눈 경계나 blink 전부를 다시 그려달라고 요청할 단계가 아닙니다. 다만 일반 face-skin과 실제 lid를 구분하는 별도 binary semantic mask는 찾지 못했습니다. 이 차이를 감추지 않습니다.

49는 커밋d0ca21f로 보존했고50도 변경하지 않았습니다.51은 별도 미커밋 작업폴더입니다. Unity 호출/새 렌더/캡처/GC/제품 변경/화면 제어/reset/앱 종료/kill은 없습니다. 아래 PNG는 저장 입력의 파일 분석이며 화면 screenshot이 아닙니다.

## 1. 현재 원본과 일치하는 근거

- `OriginalIntegration399/Export/ValidatedPresentation399.prefab`의 `CurrentSurface330.source[1]`은 GUID `43db8c7a3695b164eb6112af020fb082`, 즉 `EyeContoursLayers202/Meshes/FaceSourceOwner202.asset`입니다.
- source mesh4060정점/UV/삼각형/bindpose를 파일에서 해석해 `EyeBoundaryBinding348.Hash`와 같은 순서로 계산했습니다. prefab의 `modelTopologySHA256=1e9bb2ce154c5e0b449d58433b5065390ba0a507b771c3d0c8621a3138da65f6`와 정확히 일치합니다. Head bind index는18입니다.
-47에서 흰자를 가린239개의 S0 rest point를 source skin 삼각형에 연결했습니다. 최대 위치 오차4.2159e-8, primitive 후보 모호성0입니다. UV/bary/control을 추정 색이 아닌 원본 삼각형 보간으로 재구성했습니다.231개에서 기존 carrier control>1e-5였습니다.
- 이 결과는 **동결47의 source 위치와 디스크 asset의 일치**입니다. 현재 Editor의 dirty mesh UV2를 새로 읽은 결과가 아니며 GPU의 실제control을 측정한 것도 아닙니다. 런타임 topology hash에는UV2가 포함되지 않으므로 hash 일치만으로 live control까지 동일하다고 주장하지 않습니다.

## 2. `LidSkinCarrier`는 실제 안검 분류가 아님

`Eye202Layers.Selected`의 FaceSkin(part0)과 LidSkinCarrier(part5)는 둘 다 `role==3`을 그립니다. part5만 `Eye202Fragment`에서 `max(e202Control.x,y)>1e-5`로 자릅니다. 이 control은 `Hair153Vertex`/`E162R3HeadAperture`에서 눈 주변 skin을 벌리는 변형 가중치로 사용됩니다.

skin submesh가 참조하는 고유 정점2266개 중246개가 carrier이며116성분은0/1이 아닌 연속값입니다. 원래VRM은 FaceSkin material3과 FaceEyeline material6을 별도로 갖지만, lid-skin material은 없습니다. 원본 attribute는POSITION/NORMAL/TEXCOORD_0/JOINTS_0/WEIGHTS_0이며 이 custom UV2 control은 원래VRM의 semantic mask가 아닙니다.

반면 원래 `Fcl_EYE_Close`는 전체 source1066정점, 그중skin451정점에 변형을 보유합니다.246개 carrier와 같은 집합/의미라고 볼 수 없습니다. Close는 두 native ring의24점 모두를 움직이고, Close_R은stableId2만, Close_L은stableId1만 움직입니다.0/50/100 native geometry를 원본 delta로 재구성했습니다. **native geometry가 있다고 곧바로 해당 상태의 저해상도 눈 디자인이 승인됐다고 하지 않습니다.**

## 3. 이미 있는 전체 눈 경계와 현재 누락 필드

prefab `Full319View335.contours`에 기록된 source는 Authored202/Almond4x3, sourceSHA256은 `284eab0902207eb71fa85be08dea99c8409898d46d7878f3fc51c352a2251b7d`입니다. 원래 외부JG 파일 자체를 다시 읽거나 그 hash를 재검증한 것은 아닙니다. **현재 prefab에 보존된 숫자**를 확인했습니다.

각눈 parent24점과iris16점에 원래 sample(.75,.25)를 적용하면 기존TemplateRole의20셀과 **불일치0**입니다. 위/아래 arc는 기존parent의 좌우 극점 사이 두 연결 경로를 나눠 얻었습니다. 새 곡선/색/두께를 창작하지 않았습니다.

|기존 정보|실제 사용/누락|
|---|---|
|parent/iris contour|`Full319View335.BindEyes`→`EyeCompose333`에서는 사용. 후단 `EyeFeature348`은 이 배열 대신 `Classify`의 정규화 상하 곡선과 area/rank를 사용|
|native `ModelEye.closedBoundary`|원본skin 구멍의24점. radii 측정에 사용되지만 native upper-arc 경로는 `UseLashRegion583 && UseClosedLash590`에서만 생성.47의583=false이므로 그 경로 비활성|
|UV2 apertureControl|실제S0 공급자 `EyeSkin348` vertex에서 `e202Control`로 읽지만 fragment는target0..3만출력하여control을기록하지않음. S1/S2/S3의 `EyeSurface348`도control을출력하지않으며shade는S3 명암용|
|43/49 cache Cell|ID/eye/role/xy/RGBA만 보유. parent/iris 경계, 위·아래안검 경로, native ring, 실제lid state, source UV/triangle/bary 바인딩이 없음|
|Template216 role|iris1/white4만 있음. upper-line6/lower-lid3의 별도pixel key-form 없음|

frame101에서3셀로 남는 이유는 source 정보 자체가 전혀 없어서가 아닙니다. **iris/white bitmap cache와 source 안검이 하나의 등록된 형태로 묶이지 않아 겹치는 한 셀을 두 part가 경쟁하는 것**입니다.50은 안검을 빈 칸으로 밀어내는 오류를 막았지만, 완전한 복합 눈 key-form을 만든 결과가 아니었습니다.

## 4. 실제로 준비·검사한 최소 후보

### source 연결

`KEYFORM_BUNDLE51.json`과 `keyform51.py`에 기존parent/iris, upper/lower arc, native ring IDs, 원본native close geometry, pigment 출처를 한 feature 정의로 묶었습니다.20셀의 원래RGBA는 그대로이며 새lid pixel/color를 생성하지 않습니다.1,089개 공통위상에서 셀과 경계가 동일변환을 공유하고 endpoint/색/role을 보존했습니다. 미등록blink/yaw에 열린pixel key-form을 대입하지 않습니다.

`EyeSkin348_control51.shader`/`CONTROL_OUTPUT_ONLY.diff`는 기존S0 shade MRT에 `e202Control.xy`를 보존하는 계측 후보입니다. 새RT를 만들지 않고 기존RGB/alpha/depth/UV/owner 연산은 그대로입니다. **미import·미GPU컴파일**이며 control을lid mask로 적용하는 코드가 아닙니다. 마지막supplier대조에서S0는`e.skinMaterial`을쓴다는것을확인해초기EyeSurface후보를정정했습니다. 이전`EyeSurface348_control51.shader`는잘못된S0대상으로기각한기록이며실행하지않았습니다.

### 등록된 열린 aperture 안의 skin 순서

기존 `EyeCompose333.Compose`에는 “skin/socket first, eye over skin” 규칙이 있고, authored aperture 안에서 generic skin(meta.y4)을 eye보다 앞의 opaque 가림으로 처리하지 않습니다. 반면348/49는 S0가앞이면 source weight를줄여 흰자를 없앴습니다.

`registered_aperture51.py`는 이 기존규칙만 **보존된6개 sourceId, Close=0, 같은style, authored parent에 일치하는20셀, 같은eye의FaceSkin role3**에 한정해 적용했습니다. 실제S1/S2 source가 없는 셀은 그리지 않습니다. S3/native line, hair/brow/body 가림은 유지하고, 다른 material·다른eye·미등록상태는 이 underlay 규칙으로 제거하지 않습니다. 이전composer의 selected-hair 양보 규칙은 복사하지 않았습니다.

|가시 흰자/12|96|97|98|99|100|101|
|---|---:|---:|---:|---:|---:|---:|
|49|4|4|4|4|4|5|
|등록 aperture의face-underlay 후보51|10|10|10|9|9|10|
|50의source 안검 보존까지 결합|10|9|9|9|9|10|

source 안검을 보존한ID1 iris는 `4,4,4,4,4,3`, ID2는 `3,4,4,4,4,4`입니다. frame100의 기존 소실을 되살리는 cache효과는 유지하되 frame101 완전한shape는 여전히 해결되지 않았습니다. 앞쪽hair로 전체feature가 가려지는 반례, 비face material 유지, 원색출처/상태거부 등을42검사로 확인했습니다. 이 수치를 미감/전체시간안정성 통과로 부르지 않습니다.

직접 연 원배율/정수확대에서51은 아래쪽흰자와eye색면이49보다 더 남는 것이 보입니다. 동시에 부분가림과안검 때문에reference20셀이 완전히 같은모양으로 출력되지는 않습니다. PNG는 **분리레이어 비교**이며 실제후보GPU얼굴 합성이 아닙니다.

## 5. 통합에 필요한 정확한 범위

기존정보가 충분하므로 우선 사용자에게 새경계를 보충 그리도록 요구하지 않습니다. 남은것은 기존정보의 등록·합류·실제출력 검증입니다.

1. `EyeFeature348.cs`의Initialise/Prepare: `full.contours`/template + native ring/morph state를 같은source key에 연결하고 source UV/triangle/bary를 묶음으로 보존. genericSkin과native aperture/lid 역할을 구분. reference-open과 다른blink의native geometry가 같다는 가정 금지.
2. `EyeRenderer367.cs::Dispatch`: 이미있는homography와 함께 parent/iris/state를348에 전달. native안검과cache가같은feature좌표를사용하게함. 새카메라/격자/RT해상도 변경 불필요.
3. `EyeFeature348.compute`: 등록된 aperture의선택/skin합류와 source-native-lid를 결합하고, 캐시의 각part를 별도로rank재배치하지않음. 실제hair/body와source없는state는보존.51의skin예외를전체얼굴이나모든blink로확대하지않음.
4. 선택적인control진단은 실제S0공급자 `EyeSkin348.shader` 하나의임시후보로가능. 기존S0shade에기록하고,같은frame의S0meta/point/UV와대조. 새GPU resource는필요하지않음. activecompute에서그control을쓰려면renderer binding/compute 입력을추가하되binarylid라고잘못명명하지않음.

추가승인이필요한실행범위는 임시shader import/연결,한open frame의소량MRT읽기와CPU기대값대조,정상Play종료와참조·dirty·hash·Allocated/Reserved/Mono/OS메모리 확인입니다. 지금은새Unity실행금지에따라수행하지않았습니다. 이진단승인을제품영구적용·Closed픽셀디자인승인·대량캡처로확대하면안됩니다. 기존메모리잔류원인도미확정이므로RT복귀만으로메모리정상이라판정하지않습니다.

정확한blink의최종pixel key-form을현재reference와다르게선택해야하는미술문제가남으면그때기존326/원본reference와nativegeometry후보를나란히비교해야합니다. 원본Close변형자료가이미있는데“lid입력이전혀없다”고추가그림을요청하거나열린template를복제하지않습니다.
