ChibiEyeReview03 — Unity 정적 외형 검토 에셋 (2026-09-05)

사용: ChibiEyeReview03.prefab을 원하는 별도 시험 장소에 배치. 현재 Player/씬에는 연결하지 않음.
구조: 몸/얼굴 1, 헤어 4, 눈 2, 입체 눈썹 2 = MeshRenderer 9개. 총 15,992삼각형.
눈의 흰자/홍채/동공/속눈썹은 하나의 원본 이미지이며 각각 별도 메시가 아님.
Animator, 뼈, 스킨 가중치, 깜빡임/시선/입 움직임, Collider는 없음.

단위/방향: 전체 높이 1 Unity unit. 프리팹 wrapper의 자식 위치 Y=0.5로 발바닥 Y=0.
Unity 실제 FBX import 결과는 -Z 정면이므로 wrapper 자식에 Y180도를 적용하여 프리팹은 +Z 정면.
원본 FBX의 메시/UV/스케일은 변경하지 않음. raw FBX를 직접 배치하면 원점이 중앙이고 정면이 -Z임.

재질: Skin_Unlit / Hair_Unlit / EyeAtlas_Unlit. Universal Render Pipeline/Unlit 사용.
눈 PNG: 원본 1536x1024 그대로, 압축 없음, NPOT 변경 없음, mipmap 없음, Bilinear.
피부/헤어 단색, 그림자 투사/수신과 Light/Reflection Probe 비활성.
주의: 프로젝트 SSAO가 URP 기본 Unlit에도 적용되므로 Blender의 완전 무조명 렌더와 같은 출력은 아님.
이번에는 전역 Renderer/SSAO/픽셀 외곽선/Character ID 시스템을 변경하지 않았음.
파츠별 메시가 분리되어 있다는 사실과 파츠 ID/외곽선 구현 여부는 별개임.

출처: 사용자 제공 Meshy 기반 캐릭터와 사용자가 선택한 생성 눈 이미지의 수정본.
승인 Blender: LocalOnly/Eye_TextureFit_20260905/review03/Eye_TextureFit_review03.blend
눈 원본: C:/Users/JG/.codex/generated_images/01a01f9b-486c-78d3-999c-104f66928365/exec-419c692a-ecdd-4d93-9675-d242554b086c.png
외부 생성 서비스의 배포/상업이용 권리는 이번 기술 검증에서 확인하지 않음.

검증: Unity 6000.5.9f1, URP 17.5.0. 실제 prefab/mesh/material/texture 참조 검사 및 Editor PreviewRenderUtility 정면/45도 렌더.
메시 9, 삼각형 15,992, atlas 1536x1024, 필요한 재질 참조 정상, 셰이더 오류 없음.
FBX/PNG는 export 결과와 SHA256 동일. 새 Console Error 0, 기존 Warning 3개 유지(다른 작업 경고는 변동 가능).
Play Mode 애니메이션·플레이어 적용·게임 카메라 픽셀 외곽선은 미검증/미연결.

재현/이력: LocalOnly/Eye_TextureFit_20260905/unity_export/export_review03_fbx.py → unity_import_character.cs (공식 Unity MCP RunCommand).
Unity API 명령은 unity_mcp_call.py를 사용. 이 대화에서는 기본 sandbox에서 tools/list 시간 초과, 승인된 외부 실행 환경에서는 정상 연결됨.
최초 import는 에셋 저장 뒤 공유 Editor의 Play/씬 상태 변경을 감지해 마지막 보존 assert만 실패. 에셋을 재생성하지 않고 별도 조회로 검사했음.
이 작업 명령은 Play 전환/게임 씬 저장을 호출하지 않음. 공유 Editor의 현재 dirty를 임의로 지우거나 씬을 되돌리지 않음.
최종 미리보기: LocalOnly/Eye_TextureFit_20260905/unity_preview_final/front.png, quarter.png
