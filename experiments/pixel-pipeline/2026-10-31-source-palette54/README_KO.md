# 원본 색→명암 단계→팔레트 직접 조회54

최신 계약·검증·미해결은 저장소 `docs/ai/PIXEL_ALBEDO_20261030.md`의54절 한 곳에서 관리합니다. Argon 전용 문서는 없습니다.

- `node test.cjs`: 원본 파일/Unity 없이 보관 fixture로 재생합니다.
- `source-palette.cjs`: sourceColours/extractReference/makePalette/shadeIndex/resolve/shade.
- `adapter.cjs`: packet/replayPacket. `PACKET.json`은 미활성 GPU 후보의 uint4/RGB8·Float32 입력입니다.
- `SourcePalette54.hlsl`: SourceShade54/SourceLookup54/SourceRGB8ToLinear54. Assets 밖이며 GPU 미컴파일·미적용입니다.
- `fixtures.json`: 실제2재질 native UV/texel63표본과 합성3표본. 실제 모델100% 범용성/모든 무늬 보존의 증거가 아닙니다.
- `RESULTS.json`, `palette-contract.png`: 오프라인 색 계약 결과. 영역/곡선/실제 캐릭터 렌더를 수정한 결과가 아닙니다.
- 원본 fixture 재추출은 `freeze_samples.py`이며 기록된 원본 VRM/PNG 해시가 필요합니다. 색·단계의 최적 미술값을 자동 확정하지 않습니다.
