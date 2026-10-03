# PixelLab native object route — availability checked 2026-10-04

이 폴더에는 **생성된 PNG가 없습니다**. 실제 MCP balance 조회 결과가
구독 만료(2026-09-20), 가용 generation 0, credits $0.00이어서 생성 호출
전에 중단했습니다. 도구 연결 자체는 정상입니다. 계획에 표시된 2000회는
갱신 전까지 동결되어 있으며, 기존 사용 허용은 실제 가용량을 바꾸지 않습니다.

`availability.json`은 실제 조회와 원본의 SHA-256/규격을 기록합니다.
`edit-request.json`은 원본 324×292 PNG를 변형 없이 입력하고 새 생성 격자
162×146에 재작화하기 위한 **미실행** 요청입니다. 새 결과가 있다거나,
로컬 축소 이미지를 PixelLab 제작 결과라고 주장하지 않습니다.

노출된 적합 도구는 `edit_image`/`inpaint_image`/`get_image`입니다.
`edit_image`는 512×512 이하 원본을 받고 출력 width/height를 지정하며,
완료 전 job ID를 반환합니다. `inpaint_image`는 마스크 밖 픽셀을 고정하는
후속 국소 수리 경로입니다. 이 클라이언트에는 신규 map-object/create-image,
target-palette, 정확한 구조선 제약 입력이 노출되어 있지 않습니다.

[공식 Edit image Pro 문서](https://www.pixellab.ai/docs/tools/edit-image-pro)는
입력 편집, 출력 크기 선택과 구독 요구를 설명합니다. 페이지의 단일 이미지
설명과 MCP의 여러 프레임 설명이 다르므로 이번에는 한 이미지에만 사용합니다.
162×146은 공식 문서의 tier 1 최대 256×256 안에 들어갑니다.

[공식 Image to pixel art 문서](https://www.pixellab.ai/docs/tools/image-to-pixel-art)는
일반적으로 4배 축소하고 큰 출력 요구에는 배경에서 크기를 다시 조절한다고
설명합니다. 따라서 그 경로를 픽셀 단위 복구나 완전한 특징 보존으로 간주할
수 없습니다. [공식 Resize 문서](https://www.pixellab.ai/docs/tools/resize)는
단순 스케일링이 아니라 AI 재작화이며 Aseprite extension 전용이라고 명시합니다.

PixelLab의 생성 원본에도 한 줄 구조선과 명암 보존이 자동으로 증명되는 것은
아닙니다. 목표 팔레트나 선 폭을 프롬프트로 요구하는 것과, 실제 PNG의 정확한
색/연결 관계를 보장하는 것은 별개의 조건입니다. 이 차단 때문에 전체 제작을
사용자 계정 갱신 질문으로 멈추지 않고, 다른 사용 가능한 생성/로컬 경로를
계속 진행할 수 있습니다.
