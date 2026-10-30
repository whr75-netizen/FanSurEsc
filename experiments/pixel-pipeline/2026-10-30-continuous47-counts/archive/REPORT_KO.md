# 47 눈 특징 셀 순위·가림 원인 검증

실제 sequence **counts47-087454994917423fa13c5fe72eceb7f4**에서 새6프레임을 얻었다. Unity frame 번호가96–101로 같아도 이전46과 sourceId/실행시각이 다른 독립 재현이다. [비교](INDEX.html) · [전 packet 재생](analysis/PACKET_REPLAY_AND_ALLOCATOR.json) · [final 가림](FINAL_OCCLUSION_TRACE.json).

## 확정된 두 단계 원인

실제 플래그는 전6프레임 `LayerMode19=true`, 582/583/502=false, ClosedLash590=true다. FeatureCounts19 전체 ROI16×8×양눈, stride48의 **프레임당12,288bytes**를 공식 ComputeBuffer.GetData로 읽었다. S0–S6의 필요한 META/POINT와 기존 class/style를 사용한 CPU CountPacket19 전체 재생은 **1536 packet×12성분**, GPU 대비 최대 절대차 **5.96046448e-08**였다. 이로써 이전46의 부분 CPU budget 추정을 실제 GPU packet으로 대체했다.

1. **셀 순위 재선정**: frame99→100에서 `(223,52)`의 iris=5, sclera=2, 전체 budget=2는 그대로다. whole-eye area는2.196533→2.187010으로 작게 변했지만 반올림 경계를 넘지 않았다. `BeforeIris19`의 비용 `max(sclera,upperLine,lowerLid)−iris`에서 이 셀은 -3→-2.898825가 되고, `(224,52)`는 -2.289243→-3.984314가 된다. 경쟁 셀이 앞서면서 대상 셀의0-based rank는1→2, `rank<budget`는true→false다. 동률 순회나 미세 부동소수점 오차가 아니라 비용 순서의 실제 교환이다.
2. **할당과 최종 가림의 단위 불일치**: frame100에 새로 할당된 `(224,52)`는4×4 표본에서 iris가중치5.992157을 갖지만, 최종 logical-cell `_HairMETA`는 depth13.666405/alpha1이고 iris 대표 depth는13.714664다. Evaluate 후단이 실제 앞쪽 머리를 덮고 visibleFeature=0으로 만든다. 즉 선택한 두 셀 중 하나가 후단에서 사라져 보이는 홍채가1셀이 된다. `(223,52)`는 해당 final-cell 가림이 없는 채 sclera로 선택된다. frame101에는 `(224,52)`의 centre hair metadata가 없어져 두 셀이 대각으로 보인다.

현재 경로는 **매 프레임 별개 셀 top-K 배치 → 다른 단위의 최종 가림 판정**이다. Classify가 S2를 통째로 흰자로 바꾼 것이 아니며 Own이 잘못된 family를 골라 시작된 것도 아니다. target의 source S2 eligible와 iris가중치5가 유지되고, semantic winner가 먼저 바뀐 뒤 Own(role4)이 흰자색을 공급한다. 이 선택 결과가 head/native 최종까지 보존된다. 실제 머리 depth를 거짓 가림이라고 취급하거나 머리를 삭제할 근거는 없다.

## 준비한 최소 후보 — 제품/GPU 미적용

`candidate/EyeFeature348_visibility_gate47.compute`는 작업폴더의 **미import·미GPU컴파일 원문 후보**다. 제품 파일은 그대로다. 변경은 한 compute 파일의 다음 부분에 한정했다.

- `CountPacket19`: 현재 Evaluate와 동일한 iris 대표 표본의 depth를 구한다. 기존 count/mean.xy는 유지하고 사용하지 않던 packet.uv.zw에 depth/final-cell 가시성을 넣는다.
- `IrisAllocated19`: 기존 area와 반올림 budget을 유지한다. 최종 단계에서 이미 가려질 셀은 후보 자격과 rank 경쟁에서 제외한다. 후처리 뒤 다시 돌리는 재시도·최소셀 강제·화면 좌표 예외가 아니다.
- Classify/Own/LayerSample19/BeforeIris19/ChooseLayers19/Evaluate/색/최종 가림 코드는 바꾸지 않았다. 기존 Hair/Brow/RawMETA가 이미 dispatch에 바인딩되므로 이 좁은 후보에는 새 C# writer나 버퍼 소유자가 필요하지 않다.

실제 저장 packet/metadata를 사용한 **오프라인 가시성 counterfactual**에서12개 eye-frame 쌍 중 **frame100/eye1 하나만** 할당이 달라졌다. 기존의 가려지는224,52 대신 실제 가림 없는223,52가 선택되며, 원래 area budget2를 유지한다. 나머지11쌍은 동일하다. 이 결과는 iris 셀 배치·가림 predicate의 계산 비교이며 **대안 GPU 영상/RGBA를 렌더한 결과는 아니다**. 위아래 도표의 색은 feature ID 진단색이다.

이 한 파일 후보는 **1셀 누락의 원인 하나**를 수정한다. frame101의 대각2셀과 eye2의 pose별 배치 변경은 그대로 남으므로 특징 캐시/공동 클러스터 문제 전체를 해결했다고 하지 않는다. broad joint-placement 통합에는 이전 계획의 EyeFeature348.cs(owner/cache/state), EyeRenderer367.cs(bind), EyeFeature348.compute(place/select)의3파일 검토가 여전히 필요하다. 미등록 blink나 회전에 열린 템플릿을 복사하지 않는다.

## 다음 GPU 회귀검사와 현재 한계

미승인 제품에 바로 넣지 않는다. 후보를 명시적인 임시 compute 자산/런타임 참조로 시험하는 승인이 있다면 같은 정상 연속 경로에서 baseline/candidate를 분리한다. 동일 source 입력에서 실제 alloc flag·representative·eye-owner·RGB·final Hair/Brow/Body 가림을 비교한다. 특히 `NativeLineAllocated19`가 IrisAllocated19를 참조하므로 upper-line/sclera 선택의 간접 변화도 검사해야 한다. 고립된6프레임 수치만으로 그 회귀를 통과했다고 쓸 수 없다. 기존 Template216의 가족/알파·상하 경계·흰자, 눈 밖0변경, 메모리·원복이 필요하다.

추가 상시 버퍼/감시나 새로운 미술색은 도입하지 않는다. 이번에 더 필요한 누락 입력은 없다. 새6프레임에서 CountPacket→rank→winner→final hair까지 원인을 재생했다. 회전·blink·긴 실제 이동/광원 변화와 대안 GPU는 여전히 미검증이다.

## 실행·메모리·원복

정상 Gameplay397.Present 경로의6연속 프레임이며 RenderPose 호출과 resetHistory 대입은0이다. 실제 dt는 약.02초, source phase5.6→8.6이다. GetData는1.02–7.76ms로 동기화했고 추가 texture readback과 함께 Editor/GPU 타이밍에 영향을 줄 수 있다. 각 읽기 전후 render serial/frame이 동일한 것은 다른 프레임 혼입이 없다는 증거이며 무교란·게임 FPS 증거가 아니다. 6개 packet 총73,728bytes, texture ROI 총2,973,696bytes다. 빌린 제품 ComputeBuffer를 Release하지 않았고, 직접 소유 readback 배열만 요청 완료 뒤 Dispose했다.

최초 진단 코드는 Stopwatch 참조 누락으로 컴파일 실패해 미실행이었다. 다음에는 불필요한 Interop layout 속성이 도구의 namespace 검사에 거부돼 미실행이었다. 도구가 안내한 대로 속성을 제거하고 일반 C# value struct+공식 GetData를 사용한 코드가 승인·컴파일·실행됐다. 보안 설정이나 namespace 허용 목록을 바꾸지 않았다.

observer 제거/임시 pose·설정 복원 뒤 정상 Play 종료했다. **Edit/scene clean/기존 dirty25**, 씬 객체·컴포넌트3065개 직렬화·dirty 차이0, tracked12파일 SHA차이0이다. 기존 persistent asset 메모리 내용 전체 감사를 한 것은 아니다. RT는30개/114,517,796bytes로 돌아왔다. 다만 최종 total allocated는 **2,001,161,288bytes**로 이전46 종료보다 약372MB 높다. 추가 캡처는 종료했고 CPU cache/domain reload/계측 수명 중 원인은 확정하지 않았다. 이를 메모리 정상화라고 주장하지 않는다.

Console 기존53→54개, 기존 VCS 오류16개는 유지다. 새 type/message/stack 여부는 CONSOLE_DELTA.json을 따른다. 프로젝트 저장·Unity 재시작·제품/31/34 변경·새 자격증명·Git stage는 하지 않았다. 모든 실행 명령은 종료됐고 Editor는 열린 Edit 상태다.
