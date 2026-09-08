"""Save masks and exact-source cutouts only; deliberately does NOT recolor art."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from perfect_pixel.regions import RegionSpec, classify_regions, extract_region


def checker(size):
    w,h = size
    y,x = np.indices((h,w))
    g = np.where((x//12+y//12)%2, 225, 245).astype(np.uint8)
    return Image.fromarray(np.repeat(g[...,None],3,axis=2)).convert('RGBA')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image',type=Path)
    p.add_argument('--regions',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise ValueError('Review output must be a new/empty folder; existing reviews are never overwritten.')
    config = json.loads(args.regions.read_text(encoding='utf8'))
    with Image.open(args.image) as im:
        a = np.array(im.convert('RGBA' if 'A' in im.getbands() or 'transparency' in im.info else 'RGB'))
    size = (a.shape[1],a.shape[0])
    if tuple(config['expected_size']) != size:
        raise ValueError('This source-coordinate configuration belongs to a different image size.')
    digest = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if config.get('source_sha256_file') and config['source_sha256_file'] != digest:
        raise ValueError('Configuration source hash does not match; no silent reuse on different art.')
    fields = ('name','hsv_ranges','seeds','boxes','priority')
    specs = [RegionSpec(**{k:v for k,v in s.items() if k in fields}) for s in config['regions']]
    labels,meta = classify_regions(a,specs)
    args.output.mkdir(parents=True,exist_ok=True)
    np.save(args.output/'region_labels.npy',labels,allow_pickle=False)
    cutouts = {}
    for i,spec in enumerate(specs):
        # Region names cannot choose paths; numbered exports use names only in metadata.
        cutout = Image.fromarray(extract_region(a,labels,i))
        cutout.save(args.output/('region_%02d.png' % i))
        cutouts[spec.name] = cutout
        Image.fromarray((labels == i).astype(np.uint8)*255).save(args.output/('mask_%02d.png' % i))
    Image.fromarray((labels == -1).astype(np.uint8)*255).save(args.output/'unassigned_mask.png')
    Image.fromarray((labels == -2).astype(np.uint8)*255).save(args.output/'conflict_mask.png')
    meta['source_sha256_file'] = digest
    meta['config'] = config
    (args.output/'region_settings_and_result.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
    titles = {s['name']:s.get('title',s['name']) for s in config['regions']}
    panels = [('원본 — 색 변경·축소 없음',Image.fromarray(a).convert('RGBA'))]
    panels += [(titles[name],cutouts[name]) for name in config['preview_regions']]
    margin,gap,header = 16,16,46
    width = size[0]*2 + margin*2+gap
    height = (size[1]+header)*((len(panels)+1)//2)+margin*2+40
    sheet = Image.new('RGB',(width,height),(247,247,250))
    draw = ImageDraw.Draw(sheet)
    font_path = Path('C:/Windows/Fonts/malgun.ttf')
    font = ImageFont.truetype(str(font_path),17) if font_path.exists() else ImageFont.load_default()
    for i,(title,picture) in enumerate(panels):
        x = margin+(i%2)*(size[0]+gap)
        y = margin+(i//2)*(size[1]+header)
        draw.text((x,y+6),title,fill=(30,30,35),font=font)
        display = Image.alpha_composite(checker(size),picture)
        sheet.paste(display.convert('RGB'),(x,y+header))
    draw.text((margin,height-34),'체커 영역은 선택 제외입니다. 모든 추출 영역은 원본 RGB 그대로입니다.',fill=(30,30,35),font=font)
    sheet.save(args.output/'region_comparison.png')
    print(json.dumps({'output':str(args.output.resolve()),'source_colors_modified':False,
                      'regions':[{ 'name':s['spec']['name'],'pixels':s['selected_pixels'],'missed_seeds':s['missed_seeds']} for s in meta['regions']],
                      'unassigned':meta['unassigned_pixels'],'conflict':meta['conflict_pixels']},ensure_ascii=False))


if __name__ == '__main__':
    main()
