# 추가 확인 — 눈 색·carrier가 무엇을 캐시했는가

앱 종료 요청은 철회된 것으로 반영했습니다. Chrome/Unity/ChatGPT를 닫거나 저장하지 않았습니다. 기존 파일 분석을 이어 수행한 결과입니다.

1. `TemplateRGBA`의 alpha>0은 정확히20셀이고, 그 밖에 숨은 안검 픽셀은0입니다. `TemplateRole`의 유효 role은iris1/white4이며 z/w는모두0입니다. native UV/primitive/lid ID가 숨어 있는 필드가 아닙니다.
2. `EyeAuthoredSurface205/Palettes`의 눈별IrisPupil/White 팔레트를 비교했습니다. Template20셀의RGBA8은모두 **같은eye/같은assigned family 팔레트안에존재**합니다. 팔레트전체와일대일동일한것은아니며,특히White에는Template20셀에선택되지않은추가색이있습니다.205 셰이더는해당`_MainTex`를직접출력하며 native eyeline 색을합성하는입력이없습니다.
3. 이것은 “이전 authored palette와같다”는증거입니다. 그팔레트를최초로만들때원본MToon/다른part가포함됐는지까지증명하지는못합니다. 어두운iris색을보고“이미안검까지구워졌다”거나“원본native iris의순수UV색이다”라고추정하지않습니다. 별도안검pixel/sourceID가없다는사실은변하지않습니다.
4.205의Iris carrier는17정점/16삼각형,White는25정점/24삼각형의 **contour polygon fan**입니다. 실제20개pixel quad를ID별로보관한표현이아닙니다. nearest palette와연속3D carrier가있어도래스터가매번contour에서재결정되면feature footprint가보존된다는보장은없습니다.
5. 현재348의샘플경로는`CurrentSurface330.source`의Body/Face/Hair와material submesh를직접그립니다.205 carrier shape를iris footprint의권위로읽지않습니다.43/49의source-cell배치는그보다나아가20셀ID를보존하지만안검/parent/state바인딩이빠져있습니다. 따라서“과거에레이어가있었다”와“현재작은눈의형태가캐시된다”를같은완료상태로다루면안됩니다.

다음구현은205를그대로켜거나새팔레트를만드는것이아닙니다.51에묶어둔기존parent/iris/native lid/morph와현재색출처를한source feature정의로연결하고,그정의에cell footprint/state를등록해야합니다. 실제lid와iris가한셀에서충돌하면다른빈셀로안검을밀거나미등록blink에열린눈을대입하지않습니다. 최종RGBA검증은별도GPU통합이필요하며현재수행하지않았습니다.

source별색/메쉬hash/정확한팔레트목록은 `PALETTE_AND_CARRIER_PROVENANCE.json`, 분석코드는 `audit_carriers.py`입니다. 원본·제품·49커밋·50결과는변경하지않았습니다.
