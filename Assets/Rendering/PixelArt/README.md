# 3D Pixel Art 렌더링 시험 기능

이 폴더는 Godot용 `3DPixelArt_Tutorial`에서 사용한 시각 원리를 Unity 6 URP에 맞게 독립 구현한 시험 기능입니다. Godot 프로젝트 파일이나 데모 모델은 Unity 프로젝트에 복사하지 않았습니다.

## 현재 동작

- 전체 화면 색상을 정사각형 가상 픽셀 격자에 맞춰 포인트 샘플링합니다.
- 깊이 차이는 어두운 외곽선으로, 노멀 차이는 약한 하이라이트로 표시합니다.
- Play Mode와 Player 빌드의 `CameraType.Game`에만 실행하므로 Scene View와 편집 상태 미리보기에는 적용되지 않습니다. 메뉴·로딩을 포함한 실제 런타임 Game 카메라는 같은 스타일을 사용합니다.
- 현재 UI Canvas는 `Screen Space Overlay`이므로 HUD와 인벤토리는 원래 해상도를 유지합니다.
- `Assets/Settings/PC_Renderer.asset`의 `3D Pixel Art (Game Cameras)` 항목에서 전체 기능을 켜거나 끌 수 있습니다.

## 조절 값

`PixelArtFullscreen.mat`에서 다음 값을 조절합니다.

- `Pixel Size`: 화면의 가상 픽셀 한 칸 크기입니다. 값이 클수록 더 거칠어집니다.
- `Depth Edge Threshold / Softness`: 물체 실루엣과 깊이 단차 검출입니다.
- `Normal Edge Threshold / Softness`: 같은 깊이대의 면 방향 변화 검출입니다.
- `Outline Color / Strength`: 깊이 외곽선의 색과 강도입니다.
- `Normal Highlight`: 면 방향 경계의 밝은 선 강도입니다.

기본값은 튜토리얼의 매우 낮은 해상도보다 플레이 가독성을 조금 더 보존하도록 설정했습니다. 최종 아트 방향이 정해지면 게임 해상도와 카메라 이동을 기준으로 다시 조율해야 합니다.

## 알려진 제한

- 투명 오브젝트는 색상 픽셀화는 되지만 깊이·노멀 외곽선이 제한될 수 있습니다.
- 카메라가 연속 좌표를 따라 움직이므로 큰 `Pixel Size`에서는 픽셀 흔들림이 보일 수 있습니다. 필요하다면 이후 렌더 카메라 위치만 별도로 스냅해야 하며 Player 이동 좌표를 양자화하면 안 됩니다.
- 이 시험 기능은 PC URP Renderer에만 연결합니다. 모바일 품질 설정은 별도 검증 전까지 변경하지 않습니다.
- 이 구현은 실제 저해상도 RenderTexture로 월드 렌더 비용을 낮추는 구조가 아니라, 원본 해상도 후처리로 픽셀 모양을 만드는 구조입니다. 전체 화면 색상 복사와 픽셀당 색상 1회·깊이/노멀 각 5회 샘플 비용이 있고 같은 블록 안에서도 계산이 반복되므로 최종 수치는 특히 4K GPU Profiler로 결정합니다.

출처와 라이선스 기록은 `ThirdPartyNotices.txt`에 있습니다.
