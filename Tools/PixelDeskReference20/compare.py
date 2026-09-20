"""One fixed foreground comparison. No alignment, recoloring, or aesthetic verdict."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parents[2]/'LocalOnly/DeskReference20'
reference=Image.open(OUT/'reference.png').convert('RGBA')
render=Image.open(OUT/'render.png').convert('RGBA')
assert reference.size==render.size==(1536,1024)
a,b=np.asarray(reference),np.asarray(render)
ma,mb=a[...,3]>=128,b[...,3]>=128
union=ma|mb; both=ma&mb
diff=np.abs(a[...,:3].astype('int16')-b[...,:3].astype('int16'))
den=int(union.sum())
iou=float(both.sum()/den)
near=float(((diff.max(axis=2)<=8)&both).sum()/den)
exact=float(((diff.max(axis=2)==0)&both).sum()/den)
metrics={
 'comparison_size':list(reference.size),'denominator':'foreground_union_alpha_ge_128',
 'reference_foreground_pixels':int(ma.sum()),'render_foreground_pixels':int(mb.sum()),
 'union_pixels':den,'intersection_pixels':int(both.sum()),
 'silhouette_iou':iou,'rgb_within_8_fraction':near,'exact_rgb_fraction':exact,
 'rgb_mae_intersection':float(diff[both].mean()),
 'achieved_99_operational_threshold':iou>=.99 and near>=.99,
 'source_sha256':hashlib.sha256((OUT/'reference.png').read_bytes()).hexdigest(),
 'render_sha256':hashlib.sha256((OUT/'render.png').read_bytes()).hexdigest(),
 'interpretation':'Numeric fidelity under the predeclared metric; not an aesthetic approval or impossibility proof.'
}
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')

def checker(size):
    y,x=np.indices((size[1],size[0])); c=np.where((x//24+y//24)%2==0,222,234).astype('uint8')
    return Image.fromarray(np.stack([c,c,c,np.full_like(c,255)],axis=2))

def panel(im):
    return Image.alpha_composite(checker(im.size),im).convert('RGB')

try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',32)
except OSError:font=ImageFont.load_default()
preview=Image.new('RGB',(3072,1112),(245,245,245))
preview.paste(panel(reference),(0,88));preview.paste(panel(render),(1536,88))
draw=ImageDraw.Draw(preview)
draw.text((24,24),'GENERATED REFERENCE - unchanged',font=font,fill=(30,30,30))
draw.text((1560,24),'ACTUAL 3D RENDER - independent local UV / depth',font=font,fill=(30,30,30))
preview.save(OUT/'comparison.png')
coarse=Image.open(OUT/'render_coarse.png').convert('RGBA')
coarse.resize(reference.size,Image.Resampling.NEAREST).save(OUT/'render_coarse_8x.png')
views=[Image.open(OUT/f'view_{side}.png').convert('RGBA') for side in ['left','right']]
strip=Image.new('RGB',(1536,568),(245,245,245)); d=ImageDraw.Draw(strip)
for idx,(im,label) in enumerate(zip(views,['Actual 3D: -30 degrees','Actual 3D: +30 degrees'])):
    strip.paste(panel(im),(idx*768,56));d.text((idx*768+20,10),label,font=font,fill=(30,30,30))
strip.save(OUT/'volume_views.png')
print(json.dumps(metrics,ensure_ascii=False))
