"""Local file CLI; original input and existing results are never overwritten."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from perfect_pixel import PaletteOptions, get_palette_pixel, detect_base_grid


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--base',help='Frozen base WIDTHxHEIGHT, e.g.70x73. Omit for one-time detection.')
    p.add_argument('--scale',default='1.0')
    p.add_argument('--families',type=int,default=6)
    p.add_argument('--tones',type=int,default=3)
    p.add_argument('--method',choices=['color_ranges','legacy'],default='color_ranges')
    p.add_argument('--hue-width',type=float,default=15,help='Maximum approximate hue span per color range; degrees5..60.')
    p.add_argument('--flatten',type=float,default=.75)
    p.add_argument('--features',type=float,default=1.5)
    p.add_argument('--refine',type=float,default=.2)
    p.add_argument('--priority',action='append',default=[],help='#RRGGBB=relative_weight; repeatable')
    p.add_argument('--zoom',type=int,default=6,help='Integer preview/export enlargement only.')
    args=p.parse_args()
    if not 1<=args.zoom<=16:p.error('--zoom must be 1..16.')
    if args.output.exists() and any(args.output.iterdir()):p.error('Output must be new/empty to preserve previous results.')
    raw=args.input.read_bytes()
    with Image.open(args.input) as im:
        rgba=im.mode=='RGBA' or 'transparency' in im.info
        source=im.convert('RGBA' if rgba else 'RGB')
    a=np.array(source)
    try:
        base=tuple(int(s) for s in args.base.lower().split('x')) if args.base else detect_base_grid(a)
        priority=tuple((entry.split('=')[0],float(entry.split('=')[1])) for entry in args.priority)
    except (ValueError,IndexError) as exc:p.error(str(exc))
    opts=PaletteOptions(args.families,args.tones,args.flatten,args.features,args.refine,priority,palette_method=args.method,range_hue_width=args.hue_width)
    result=get_palette_pixel(a,base,args.scale,opts)
    baseline=get_palette_pixel(a,base,args.scale,opts,mode='original')
    args.output.mkdir(parents=True,exist_ok=True)
    for name,r in [('palette',result),('center_same_grid',baseline)]:
        native=Image.fromarray(r.image)
        native.save(args.output/(name+'_native.png'))
        native.resize((native.width*args.zoom,native.height*args.zoom),Image.Resampling.NEAREST).save(args.output/(name+'_preview.png'))
    # Contact sheet only presents results; it is not fed back into the algorithm.
    pw=max(source.width,result.image.shape[1]*args.zoom)
    ph=max(source.height,result.image.shape[0]*args.zoom)
    sheet=Image.new('RGB',(pw*3+64,ph+90),'#f2f2f6')
    draw=ImageDraw.Draw(sheet)
    fontpath=Path('C:/Windows/Fonts/segoeui.ttf')
    font=ImageFont.truetype(str(fontpath),19) if fontpath.exists() else ImageFont.load_default()
    for index,(title,im) in enumerate([('ORIGINAL',source),('CENTER / SAME GRID',Image.open(args.output/'center_same_grid_preview.png')),('COLOR RANGES / UP TO %s TONES' % args.tones if args.method=='color_ranges' else 'LEGACY PALETTE',Image.open(args.output/'palette_preview.png'))]):
        x=16+index*(pw+16)
        draw.text((x,10),title,fill='#202438',font=font)
        im=im.convert('RGBA')
        sheet.paste(im,(x+(pw-im.width)//2,46+(ph-im.height)//2),im)
    draw.text((16,ph+58),'Base %sx%s | density %s | native %sx%s | preview %sx | USER REVIEW PENDING' % (*base,args.scale,*result.metadata['target_grid'],args.zoom),fill='#202438',font=font)
    sheet.save(args.output/'comparison.png')
    result.metadata['source_file']=str(args.input.resolve())
    result.metadata['source_file_sha256']=hashlib.sha256(raw).hexdigest()
    result.metadata['preview_integer_zoom']=args.zoom
    (args.output/'settings_and_result.json').write_text(json.dumps(result.metadata,ensure_ascii=False,indent=2),encoding='utf8')
    assert hashlib.sha256(args.input.read_bytes()).hexdigest()==result.metadata['source_file_sha256']
    print(json.dumps({'output':str(args.output.resolve()),'base':base,'native':result.metadata['target_grid'],'palette_size':len(result.palette),'status':'awaiting_user_visual_review'}))


if __name__=='__main__':main()
