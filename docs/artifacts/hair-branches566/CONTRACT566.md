# 566 현재 결정: 원곡선 가지와 입구를 격자보다 먼저 보존

요청:16의일시1×2틈을억제하면서51의기존틈을보존. 조건/문턱/시간필터변형이아니라source표현의누락수정.564원자료와손561철회상태보존.

입력은기존511의스킨변형anchor→head480×272논리픽셀폐곡선→CurveArea511양의winding sweep다. 기존NegativeRegion563의구간은연속양의폭겹침으로접속된다. 전체connectedcomponent로합친뒤픽셀소유권을재탐색하는564대신,접속방향의입/출차수가1인연속구간을최대chain으로묶고분기/합류에서끝낸다. 이접속은source기하에서이미계산하던것이다.

최소기록은Branch{axis,orderedLeftArcPath,orderedRightArcPath,startEvent,endEvent,neighbourBranchIDs,continuousSpans,area}다. Event{cap/split/merge/open-mouth,continuousLevel,interval,boundaryIDs}는원곡선에서정의한다. ID는두경계의순서와양끝source사건으로만구성한다. 셀수/면적>.5/이전프레임은존재·정체성입력이아니다. 좌표구간은source변형에따라갱신되며상태이력은없다.

그다음기존정확구간적분의셀면적을가지에첨부한다. 기존면적오차와8이웃cut을그대로소비하며별도후단mask를덧씌우지않는다. 0셀가지도원기록에존재한다. sourcearc→기존Control511의원triangle/barycentricanchor가연결되며새의미추론은없다. 실제앞가림은기존source-ray512/513과최종Draw/Gate권위이며가지구성으로가림을무효화하지않는다. 저장음의영역데이터만으로연속영역전체의3D가시성이증명됐다고하지않는다.

고정조건:sourcecurve/positiveArea/선택비용(.14경계항)/가림/색/카메라/몸범위. 변경은강제결합에공급하는source영역표현1곳뿐이다. parent영역밖쓰기,원고정좌표/모델별branch특례,이전mask복사,팽창/closing,전역시간DP금지.

R3:저장15–17/50–52에동일정의. 원곡선배열/교차edge쌍/접촉과국소입구가유지되는지확인. 각연속band를임의2분할해ID/area/cellIntegral/endpoint가같은지검사. 16H/H/H와51틈open/open/open을동시만족하지못하면기각. 두사례통과후같은정의로저장81입력을한번대조. 실제Unity6쌍은그결과를확인하는것이며전체실시간/모든시간품질채택증거가아니다.

자체검토한한계:source축에따른분해와원2D전체위상은다르다. 분기그래프가시간/회전/전체가림에서항상같다고약속하지않는다. source기하사건이면기록변경을허용하고단순격자교차로identity를종료하면실패다. 독립검토자없이현재source반례와정의의불변성을자체검토했다. 외부논문전체알고리즘을재현한것이아니다.
