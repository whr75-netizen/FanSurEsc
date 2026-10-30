"""Finalize read-only evidence. No Unity or product mutation."""
from pathlib import Path
import datetime, hashlib, json, re, urllib.parse
from PIL import Image

out = Path(__file__).resolve().parent / 'eye-cache42'
verified = json.loads((out / 'VERIFIED.json').read_text(encoding='utf8'))
changed = [p for p, digest in verified['productInputSHA256'].items()
           if hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest]
assert not changed, changed

enlargements = []
for name in ['neutral', 'walk-00', 'walk-01', 'walk-02', 'walk-03']:
    small = Image.open(out / f'{name}-saved-final-1x.png').convert('RGBA')
    large = Image.open(out / f'{name}-saved-final-12x.png').convert('RGBA')
    expected = small.resize((small.width * 12, small.height * 12), Image.Resampling.NEAREST)
    assert expected.size == large.size and expected.tobytes() == large.tobytes()
    enlargements.append({'pose': name, 'originalSize': list(small.size),
                         'integerScale': 12, 'RGBAExactNearest': True})

page_path = out / 'INDEX.html'
page = page_path.read_text(encoding='utf8')
marker = '<!-- verified-visual-review42 -->'
if marker not in page:
    note = (marker + '<section><h2>실제 이미지 검수와 자료 시점</h2>'
            '<p>현재 분류식을 과거 저장 입력에 적용한 오프라인 진단입니다. '
            '최종 화면은 저장된 5포즈이며 새 제품 렌더가 아닙니다. '
            '후보 마스크는 source 정체성 검사이고 최종 눈 보정 결과가 아닙니다.</p>'
            '<p><a href="VISUAL_REVIEW_KO.md">직접 열어 본 이미지·관측·한계</a> · '
            '<a href="FINAL_READONLY_CHECK.json">11개 입력 해시·5개 최근접 확대 검사</a></p></section>')
    page = page.replace('</html>', note + '</html>')
    page_path.write_text(page, encoding='utf8')

missing = []
for q in re.findall(r'(?:href|src)="([^"]+)"', page):
    t = urllib.parse.unquote(q).split('#', 1)[0]
    if t and ':' not in t and not (out / t).exists() and t != 'FINAL_READONLY_CHECK.json':
        missing.append(t)
assert not missing, missing
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'trackedProductAndTemplateFiles': len(verified['productInputSHA256']),
          'hashDifferences': changed, 'exactNearestEnlargements': enlargements,
          'missingLocalLinks': missing, 'newUnityCalls': 0, 'DesktopWrites': 0,
          'newFinalEyeRender': False, 'prototypeScope': 'source identity only; not joint cluster placement',
          'currentEditorOrDirtyStateMeasured': False}
(out / 'FINAL_READONLY_CHECK.json').write_text(json.dumps(result, indent=2), encoding='utf8')
manifest_path = out / 'MANIFEST.json'
manifest = json.loads(manifest_path.read_text(encoding='utf8'))
manifest['finalReadOnlyCheckUTC'] = result['utc']
manifest['visualReviewFile'] = 'VISUAL_REVIEW_KO.md'
manifest['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in out.iterdir() if p.is_file() and p.name != 'MANIFEST.json'}
manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf8')
print(json.dumps(result))
