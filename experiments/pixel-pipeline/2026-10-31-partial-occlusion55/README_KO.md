# 부분 가림 전제55

최신 판단·수치는 기존 `docs/ai/PIXEL_ALBEDO_20261030.md`의55절에서 관리합니다. 별도 Argon 보고서는 없습니다.

- `python -B replay55.py`: NumPy/Pillow가 있는 기존 Python으로 두4×4 fixture를 재생합니다. Unity/원본 전체 asset은 필요하지 않습니다.
- `visibility55.py:joint_visibility/calculate`: source alpha/depth를 유지한 부분 투과량. 최종 cell owner/색/눈 디자인을 결정하지 않습니다.
- `cell-fixtures.json`: 기존47 frame100/101 source/target raw 표본과49/53 출처 해시.
- `freeze55.py`: 원래 workspace49/53 입력에서 위 fixture를 재추출하는 코드. portable replay의 실행 의존성은 아닙니다.
- `alpha-comparison.png`: 면적/투과량 진단 이미지이며 캐릭터 최종색 렌더가 아닙니다.
