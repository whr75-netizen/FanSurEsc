Chibi / Kenney 본 재사용 시험 01 — 2026-09-05

[현재 결과]
ChibiKenneyRigReview01.prefab: 승인된 chibi 외형에 기존 Kenney 좀비 에셋의
본 계층을 복사·체형 맞춤 후 스키닝한 별도 작업본. 기존 Player/좀비/씬은 교체하지 않음.
본 58개 유지, 주요 22개 본에 가중치 사용, 부품 9개 SkinnedMeshRenderer 유지.
원본 삼각형 15,992개 및 눈 텍스처/UV/체형 보존. 내보내기 복사본만 좌표계 등록.

[사용]
프리팹의 자식 Animator는 유효한 새 Humanoid Avatar를 사용함.
기존 Assets/Animations/Enemies/KenneyZombie.controller를 읽기 전용 재사용.
IsMoving=false: Idle, true: Moving(Run을 speed 0.8로 재생하는 기존 설정).
applyRootMotion=false. 실제 이동·충돌·게임플레이 스크립트는 붙이지 않았음.
프로젝트에 들어온 Kenney 동작은 Idle/Run뿐이며, Walk라고 이름만 바꾸지 않음.

[제작 경로 / 재개할 때]
원본: LocalOnly/Eye_TextureFit_20260905/review03/Eye_TextureFit_review03.blend
본 작업본: LocalOnly/Eye_TextureFit_20260905/rig_review01/Chibi_KenneyRig_review01.blend
본 출처: Assets/ThirdParty/Kenney/AnimatedCharactersRetro/Model/characterMedium.fbx
기존 에셋 LICENSE.txt의 CC0를 따름. 새로운 외부 에셋을 다운로드하지 않았음.

rig_review01/build_fitted_rig.py: 원본 58본 복사, 체형별 위치 조정,
Blender bone heat 자동 웨이트 → 최대4본/합1 정규화. 얼굴 상부와 헤어·눈·눈썹은 Head 고정.
rig_review01/export_unity_registered.py: 내보내기 복사본에 전역 Rz180,+Z0.5 적용.
즉 Unity에서 발바닥 원점/+Z 정면이 되도록 등록하고 prefab child transform은 identity.
Blender 원본의 중심원점/-Y 정면용 static prefab 보정을 다시 더하면 안 됨.
실제 Assets의 FBX는 Chibi_KenneyRig_unity01.fbx를 동일 GUID 대상 이름으로 임포트한 것.
본/메시를 다시 만들지 않고 기존 Unity Humanoid Run/Idle이 체형 차이를 재타겟함.
별도 run.fbx/idle.fbx의 Blender rest/roll은 모델과 달라 액션 채널 직접복사는 금지.
재생성 스크립트는 기존 결과가 있으면 중단하므로 승인본을 덮어쓰지 않음.

[실제 검사 / 합격 범위]
독립 Blender 검사: 승인본 geometry/UV 동일, 주요 좌우 관절 위치 대칭,
무가중치·유효하지 않은 본 가중치0, 최대4본·합1, 팔↔다리 가중치 누수0.
Unity 격리 PreviewRenderUtility+PlayableGraph: Run16개 위상, Idle1개 위상 재생/렌더.
실제 프리팹 Animator도 IsMoving 전환에 따라 Idle→Moving→Idle 확인(격리 Editor 호출).
유효 Human Avatar,9개 스킨,15,992삼각형, 본·텍스처 참조와 가중치 합계 확인.
원본 정적 캐릭터/좀비의 git diff 없음. 게임 씬 저장·Play 전환 호출하지 않음.
Console Error0. 새로 관측된 RenderTextureBaker/MainMenuManager 경고는 이번 변경 파일 아님.
진단 코드의 Mesh 이름 충돌은 UnityEngine.Mesh 한정으로 수정 후 실행 성공.

[중간 문제와 수정]
초기 프리팹은 정적 FBX용 +0.5Y/180도 래퍼를 사용해 Humanoid 보정과 중복됨.
결과가 위로 뜨고 뒤를 봄. 뼈/외형 재생성 없이 export 좌표계 등록으로 수정.
이전 unity_motion_preview는 오류 증거이며 최종 결과가 아님.
최종 미리보기: LocalOnly/Eye_TextureFit_20260905/rig_review01/unity_motion_registered/
동영상: 같은 rig_review01/Unity_Kenney_Run_Review01.mp4 (정면/45도, Run 원속도 24fps, 8초 반복)
본 오버레이: 같은 rig_review01/rig_fit_overlay.png
독립 검사: 같은 rig_review01/independent_rig_diagnostic.json

[미검증 / 제한]
시각 합격은 사용자 확인 대기. 실제 게임 Player 대체/입력/빌드 검증은 하지 않음.
긴 헤어는 Head에 강체 고정이라 팔과 관통/겹침 가능. 헤어 본/물리는 이번 범위 아님.
손가락 개별 굽힘, 표정·눈깜빡임, 얼굴 리그, IK 발 접지, 옷/장비는 미구현.
런타임 스킨 culling bound는 프로토타입용 보수적 크기; 성능 최적화는 아직 안 함.
미세 관절 꺾임/가랑이 등 최종 아트 변형 품질을 자동 검사 통과로 승인하지 않음.
