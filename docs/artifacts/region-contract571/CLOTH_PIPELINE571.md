# 과거 의상 재현 Python — 실제 경로와 단계

**읽기 전용 코드/파일 조회다. Blender 실행·렌더·베이크·플러그인 설치는 하지 않았다.** 선택된04/07의 A 명암과 upstream의 B UV베이크를 구분한다. 사용자가 기억한 특정 편집이 어느 분기인지는 아직 확정하지 않는다.

아래 root는 `C:/Users/JG/Documents/Codex/2026-10-06/task-7/`이다. [입력/출력 파일 존재와 크기 확인](CLOTH_PATHS571.json).

|단계/실제 스크립트|입력|처리|출력/한계|
|---|---|---|---|
|`E_static_pixel_01/cloth_texture_mask.py`|`../task-8/meshy_E_D0_01/textures/image_0.jpg`|G−R≥8,G−B≥3,G≥30인 보수적 옥색 UV선택|`cloth_uv_mask.png`,preview,definition JSON. 일반 의상ID/완전 자동 분할 아님|
|`E_static_pixel_01/cloth_experiment.py`의`mask` stage|`E_static_diagnostic.blend`, **cloth_uv_mask_verified.png**|원UV마스크를Emission으로 보여주고정면/게임카메라 렌더|`cloth_mask_verified_renders/{front,game}_semantic_mask.png`. verified마스크는 전제 입력이며 위 생성기가 자동으로 verified파일까지 만든다고 확인하지 않음|
|같은`cloth_experiment.py`의`variants` stage|같은scene/검증mask/기하/수입normal,render_manifest|A와B를 한 실험에 구성,아래분기참조|`cloth_renders/{view}_{L1,L2}_{A_flat,B_motif}.png`,실험manifest,`E_cloth_experiment.blend`. `.blend`는 여러실험을담은컨테이너이며그대로열면선호A라고가정하면안됨|
|`E_cloth_texture_vs_flat_04/render_matched_texture.py`|`E_cloth_experiment.blend`,원basecolor unlit노드,검증mask,기존A캐시|의상안원텍스처만Emission1/밖은PBR로맞춘대조|`renders/{front,game}_cloth_texture_unlit.png`,render_manifest. 오른쪽A는기존캐시로이파일이재생성하지않음|
|`E_favorite4_shading_07/render_three_variants.py`|같은blend/mask,기존`game_L1_A_flat.png`|정규화N·L→smoothstep→shade/lit혼합→Emission,그림자색/threshold/L변수각각비교|`renders/condition_1.png`,2.png,3.png,branch_manifest.0은캐시. 최초3방향은후속에서정정됨|
|`E_favorite4_shading_07/adjust_screen_direction.py`|같은setup,branch_manifest|화면(.6,.8,1)을실제camera basis로변환|`renders/condition_3_screen_right_top.png`,정정manifest|
|`E_favorite4_shading_07/render_one_combination.py`|정정3조건/manifest|같은화면방향에threshold.35만조합|`renders/condition_4_direction_plus_narrow.png`,combined_case기록|
|04/07의`assemble_verify.py`,07의`assemble_combination.py`|PNG/mask/manifest|비교판조립,mask밖/alpha/밝은면범위검증|04비교판,07`E_favorite4_shading_review_ko.png`/`E_favorite4_direction_narrow_combo_ko.png` 및검증JSON.새렌더아님|

## A: 선택된 단색 명암 — 새 명암 텍스처 베이크 아님

`cloth_experiment.py`93–106행 및07 생성기에서 확인했다.

`f=smoothstep(.22,.28,dot(normalize(N),L))`
`color=mix(shadow,lit,f) → Emission1 → 의상mask/PBR밖 혼합`

기준색은lit114/147/135,shade57/94/85,L1=normalize(−3,−4,7)이다. 수입 shading normal을 유지하고 의상 안 normal-map/bump는 쓰지 않는다.04 선호4번은기존`E_static_pixel_01/cloth_renders/game_L1_A_flat.png`다.07은같은수학을Python노드로만들어변수비교했다.이경로는이미스크립트자동화되어있지만모든옷의주름설계/마스크획득까지자동화된것은아니다.

## B: 실제로 존재하는 EMIT UV베이크 — AO가 아닌 저작 영역ID

추가로 확인한 upstream `E_static_pixel_01/cloth_experiment.py`56–85행에는 **bpy.ops.object.bake(type='EMIT')**가 있다.570의“04/07 선택경로는새베이크가아님”을전체과거작업에확대하면안된다.

이분기는world position의`F=X+.22Z`로패널`F<−.06`/리본`.02<F<.10`/나머지를ID0/.5/1로만들고,2048²`cloth_motif_ids_uv.png`에베이크한다(Cycles CPU1sample,margin2).그ID가서로다른lit/shade팔레트를선택하고NdotL명암과함께렌더된다. **AO/곡률/물리주름명암을추출한텍스처가아니며 원JPG알베도에쓰는코드도아니다.** 파라미터는저작된형태구도다.

현재`cloth_motif_ids_uv.png`와manifest는존재한다.선호A와별도실험이며04/07의A명암에사용됐다고하지않는다.생성기전체`variants`를재실행하면이B베이크까지수행하므로“A만재현하는도구”라고소개할수없다.본작업에서는실행하지않았다.

## 자동화의 정확한 범위

- 이미 자동화:입력blend/mask/팔레트가주어졌을때수학노드구성,일부영역ID베이크,정적렌더/비교판생성.
- 미확인/미완:verified UV마스크의완전자동생성·범용옷파츠분류·주름의미선택·AO/곡률→사용자원하는미관자동변환·Unity런타임자동통합. 같은폴더`inspect_mask_hit.py`는검토지점의ray/UV를`mask_hair_spot_hit.json`으로기록하는진단일뿐verified PNG를내보내지않는다.
- 재현조건:렌더스크립트는`bpy`가필요하고기존출력존재시assert로중단하는것들이있다.기존결과를덮어쓰지않는출력설계가필요하며지금실행명령을내리지않았다.
- 원기하구김/수입normal비교는07의`inspect_wrinkle_origins.py`239점읽기검사다.메시/normal수정이나베이크자동화가아니다.

이자료는원Meshy E의정적256frame/224px 실험이다.현재Unity 실제Walk/광원·픽셀격자와동일결과라고검증하지않았다.외부플러그인조사나새AO베이크는이번작업에서하지않았다.
