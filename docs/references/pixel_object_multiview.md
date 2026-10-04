# 픽셀 사물의 실제 3D와 방향별 프레임 — O23

현재 단계: 2026-10-04 코드 대조·공식 도구/원논문 연구. 사용자는 현재 사물을 실제3D메시+이미지 재료로 만들고 지정 방향마다 완전한 픽셀프레임을 만드는 방법을 물었다. **이번에는 사물을 재제작하거나 도구를 설치하지 않았다.** 조명 수선은 별도 N23 계약이다.

## 현재 사실과 입력 공백

`Assets/Editor/NativeBuilding16Importer.cs`의 CreateDisplayMesh는4정점·2삼각형 고정카메라 평면이며, CreateCasterMesh의 폐곡면 기하는 ShadowsOnly로 연결된다. `NativePaletteSurface16.shader`는 Position/Normal/MaterialMap의 같은texel을 읽어 세계 위치·깊이·실시간광을 계산한다. **현재 표현은 고정뷰 표면캐시+그림자용 실제메시**이며 완전한 면별UV텍스처 메시가 아니다. `Tools/Building38/building16.py`는 전체 PNG를 UV에 붙이지 않고 관측팔레트·표면좌표의 목재 reference에서 재질/rank를 제작한다. geometry는 재사용할 수 있으나 숨은 면 재질·UV와 방향별 캐시가 추가로 필요하다.

단일 정사영 PNG는 깊이를 결정하지 않는다. 한 픽셀의 광선은 `P=O+uR+vU+tF`이며 t가 입력에 없다. 서로 다른 구조/가림면이 같은 그림을 만들 수 있다. 관측 RGB도 재료색과 원래조명으로 유일하게 분리되지 않는다. 디자인 참조와 실제 구조·치수·숨은 면·albedo의 저작 계약을 분리한다. 이미지1장의 뒷면을 자동으로100%복원했다는 판정은 불가능하다.

## 후보와 실제 도구

| 입력→제작→출력 | 적용 도구/근거 | 맞는 범위·실패 조건 |
|---|---|---|
| 픽셀 tileset→실제3D면/면별UV→메시 또는 카메라 프레임 | [Crocotile3D 공식 문서](https://www.crocotile3d.com/howto.html), [Sprytile 공식 배포](https://jeiel.itch.io/sprytile) | 사각형 가구·건물에 직접 맞음. Crocotile은 카메라/회전GIF/glTF·glb출력과BasePixelUnit을 설명한다. 사선 투영된 UV텍셀은 화면 정사각픽셀과 같지 않으므로 Point만으로 모든 시점의 격자/1px윤곽을 보장하지 않는다. Sprytile은 오래된Blender버전용이므로 현버전 호환 확인이 필요하다. |
| 기존 메시→정수texel-density UV→면에서 픽셀 재료 제작 | [Pixel Art Studio 문서](https://pardalltools.github.io/pixel-art-studio-docs/quickstart-tutorial.html), [Freebambase 저장소](https://github.com/illusionofmana/Freebambase) | PixelArtStudio는texel격자/px·m/Point·기존텍스처 경로를 제공한다. 복잡한메시는별도UV필요. Freebambase는Aseprite↔Blender UV/texture동기화이며 자동복원도구가아니다. 최신Blender호환과라이선스는설치전대조해야한다. |
| 그림+깊이→기준카메라 역투영→작은시차/기준뷰 | [Blender UV Project](https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/uv_project.html) | 기준방향외관은가져올수있지만 새가림면·뒷면은없고 회전시늘어짐/공백이생긴다. UVProject는카메라투영을제공하며 숨은자료를만들지않는다. |
| 복셀/층별sprite→부피→방향별sprite sheet | [SpriteStack 공식](https://spritestack.io/) | 자체저작부피로회전가능. 명암/장식도부피로오인하는 단일이미지단순extrusion은부적합. lowpoly+normalmap설명은upcoming/alpha와출시판설명이섞여있어현재완성기능이라고단정하지않는다. |
| 실제메시·재료→방향별정사영ray표본→color/position/normal/material/depth캐시 | 현재geometry/native표본화의확장안 | 지정4/8방향의정보·가림·색상표시를공유할수있음. 실제후면저작과방향별자료필요. 완성RGB만저장하면명암이고정되므로동적조명에는재질·위치·법선분리가필요하다. 미구현제안이다. |
| 실제3D→cubemap표면texel→world-space quad splat→회전안정표시 | [Texel Splatting 원논문/데모](https://arxiv.org/html/2603.14587v1), 2026-03-15 | 위치·법선·재질의texel별조명/단계명암·외곽선. probe에서숨은면이새로보이는disocclusion은주한계이며움직이는eye-probe는그영역의shimmer를남긴다. 원본PNG한장→완전3D복원이아니며프로젝트통합/성능미검증이다. |

## 고정 몇 방향에 대한 확장 제안

`참조 디자인+명시된 구조/치수/숨은 면 → 현재 폐곡면 geometry → 면별UV/재질 → 공통30° 정사영·yaw방향 목록 → native 픽셀중심 최근접교점 → 같은index의 재질/위치/법선/깊이 → 방향별표시 → 기존Unity광원`

Unity는Y-up미터와기존부모TRS를유지하고, 표본화기의canonical축변환은N17geometry계약을재사용한다. O/R/U/F는각방향의카메라원점/right/up/forward이며 `u=(i+.5-W/2)/PPU`, `v=(H/2-j-.5)/PPU`다. PPU와pivot/기준바닥은전방향공통이다. 회전은한mesh의명시된yaw목록으로만하고사물별stretch/임의offset을넣지않는다. 가림은최소유효t의면이소유한다. 같은메시의투영bounds와공통anchor에서W/H를계산하며큰사물은픽셀수를더갖는다. 모든출력을같은64×64슬롯에맞추지않는다.

정사영30°가모든경계에2:1픽셀대각선을만드는것은아니다. 화면의선분은면/방향의투영에서파생하며 integer raster로출력한다. 2:1도트규칙을필수로삼으려면별도의dimetric투영계약을선택해야하고지금카메라를조용히바꾸지않는다. 1px경계는가시성/면role표본에서한쪽소유자를정한뒤1회만제작한다. UV의장식검정·실제틈·윤곽은서로구분한다.

출력RGBA는원래native해상도·Point·정수배율로표시하고후단재축소/전체화면모자이크를추가하지않는다. 조명을바꾸려면색상albedo/재질무늬와position/normal/depth를함께저장하고runtime에한번계산한다. 반사/접촉그림자를RGB에구워놓고다시조명하는것은동일계약이아니다.

## 판별 실험과 재개

다음구현을한다면기존수납장1개만대상으로구조·원본디자인·PPU·camera를고정해정면/측면/뒷면4방향을계산한다. 검사범위는동일실물치수/pivot·표면UVcoverage·재질과광량분리·가림/깊이·native격자·원본변형0이며, 각방향의실제게임표시를함께제출한다. 역투영만으로공백이없는지, UV재료의명암이기하로중복되었는지,texel의늘어짐/실루엣/최소특징이사라지는지를반례로본다. 현재원화99%일치·모든방향완벽·도구호환·런타임완성을확인하지않았다. **실제3D기법은있고현재geometry를활용할수있지만,아직현재게임의다방향완성기능은아니다.**
