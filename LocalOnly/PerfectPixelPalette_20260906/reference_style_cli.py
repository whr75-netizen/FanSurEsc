"""Generic source native image + reference palette transfer. No object presets."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from perfect_pixel.reference_colors import transfer_reference_colors


def read_image(path):
    with Image.open(path) as im:
        return np.array(im.convert('RGBA' if 'A' in im.getbands() or 'transparency' in im.info else 'RGB'))


def verify_palette_only(source, output):
    """A lookup may merge labels, but must never split an existing color area."""
    if source.shape != output.shape:
        raise ValueError('Palette transfer changed the native dimensions/channels.')
    if source.shape[2] == 4 and not np.array_equal(source[..., 3], output[..., 3]):
        raise ValueError('Palette transfer changed alpha.')
    visible = source[..., 3] > 0 if source.shape[2] == 4 else np.ones(source.shape[:2], bool)
    before = source[..., :3][visible]
    after = output[..., :3][visible]
    if not len(before):
        return {'same_source_rgb_same_target_rgb': True, 'split_source_colors': 0,
                'source_colors': 0, 'target_colors': 0, 'merged_source_colors': 0}
    _, inverse = np.unique(before, axis=0, return_inverse=True)
    pairs = np.unique(np.column_stack((inverse, after)), axis=0)
    split = int(np.count_nonzero(np.bincount(pairs[:, 0]) > 1))
    if split:
        raise ValueError('Palette-only contract violated: a source RGB has multiple targets.')
    nsource = int(inverse.max()) + 1
    ntarget = len(np.unique(after, axis=0))
    return {'same_source_rgb_same_target_rgb': True, 'split_source_colors': split,
            'source_colors': nsource, 'target_colors': ntarget,
            'merged_source_colors': nsource - ntarget}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path,help='Already rasterized native grid; not resampled by this step.')
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--reference-box',help='Optional reference selection left,top,right,bottom. Not source/object coordinates.')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--tones',type=int,default=3)
    p.add_argument('--zoom',type=int,default=6)
    args=p.parse_args()
    if not 1<=args.zoom<=16:p.error('zoom must be1..16')
    if args.output.exists() and any(args.output.iterdir()):p.error('Output must be new/empty; previous reviews are never overwritten.')
    source=read_image(args.source)
    reference=read_image(args.reference)
    box=None
    if args.reference_box:
        box=tuple(int(v) for v in args.reference_box.split(','))
        if len(box)!=4 or not (0<=box[0]<box[2]<=reference.shape[1] and 0<=box[1]<box[3]<=reference.shape[0]):p.error('Invalid reference selection.')
        reference=reference[box[1]:box[3],box[0]:box[2]].copy()
    if source.shape[0]*source.shape[1]*args.zoom**2>24_000_000:p.error('Preview exceeds24MP; lowerzoom. No files created.')
    width=max(source.shape[1]*args.zoom,reference.shape[1])
    height=max(source.shape[0]*args.zoom,reference.shape[0])
    if (width*3+64)*(height+88)>72_000_000:p.error('Comparison sheet exceeds72MP; no files created.')
    restyled,metadata=transfer_reference_colors(source,reference,tones=args.tones)
    metadata['palette_only_check']=verify_palette_only(source,restyled)
    metadata['spatial_reclassification']=False
    metadata['implementation_sha256']={
        rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
        for rel in ('reference_style_cli.py','src/perfect_pixel/reference_colors.py',
                    'src/perfect_pixel/palette.py')}
    metadata.update({'source_file':str(args.source.resolve()),'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
                     'reference_file':str(args.reference.resolve()),'reference_sha256':hashlib.sha256(args.reference.read_bytes()).hexdigest(),
                     'reference_selection_box':box,'source_pixel_positions_changed':False,'native_size':[source.shape[1],source.shape[0]],
                     'preview_zoom':args.zoom,'design_approval':'pending_user_review'})
    args.output.mkdir(parents=True,exist_ok=True)
    Image.fromarray(restyled).save(args.output/'restyled_native.png')
    def enlarge(a):
        im=Image.fromarray(a)
        return im.resize((im.width*args.zoom,im.height*args.zoom),Image.Resampling.NEAREST)
    enlarged=enlarge(restyled)
    enlarged.save(args.output/'restyled_preview.png')
    panels=[('CURRENT / SOURCE COLORS',enlarge(source)),('STYLE REFERENCE',Image.fromarray(reference)),('REFERENCE PALETTE / SAME GRID',enlarged)]
    width=max(im.width for _,im in panels)
    height=max(im.height for _,im in panels)
    sheet=Image.new('RGB',(width*3+64,height+88),(242,242,247))
    draw=ImageDraw.Draw(sheet)
    fontpath=Path('C:/Windows/Fonts/segoeui.ttf')
    font=ImageFont.truetype(str(fontpath),18) if fontpath.exists() else ImageFont.load_default()
    for i,(title,im) in enumerate(panels):
        x=16+i*(width+16)
        draw.text((x,8),title,fill=(25,25,35),font=font)
        rgba=im.convert('RGBA')
        sheet.paste(rgba,(x+(width-im.width)//2,42+(height-im.height)//2),rgba)
    draw.text((16,height+56),'Fixed native grid %sx%s | color-only transfer | no body/face coordinates' % (source.shape[1],source.shape[0]),fill=(25,25,35),font=font)
    sheet.save(args.output/'comparison.png')
    (args.output/'style_mapping.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'output':str(args.output.resolve()),'native':[source.shape[1],source.shape[0]],'mappings':len(metadata['mappings']),'palette_only_check':metadata['palette_only_check']},ensure_ascii=False))


if __name__=='__main__':main()
