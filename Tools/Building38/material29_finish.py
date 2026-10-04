"""Actual GPU map parity and an unchanged-size comparison montage for N29."""
import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/artifacts/building39/material29/run01'

def srgb_byte(v):
    v=np.clip(v,0,1)
    s=np.where(v<=.0031308,v*12.92,1.055*v**(1/2.4)-.055)
    return np.rint(s*255).astype(np.uint8)

if __name__=='__main__':
    if (OUT/'gpu-validation.json').exists():raise ValueError('Previous GPU evidence preserved')
    data=np.asarray(Image.open(OUT/'material.png').convert('RGBA'))
    mask=data[...,3]>0
    normal=np.fromfile(OUT/'normal.f32',np.float32).reshape(*mask.shape,4)[...,:3]
    with np.load(ROOT/'docs/artifacts/building39/run02/empty_counter/geometry.npz') as z:
        handles=mask&(z['part']>=2)&(z['design_normal'][...,2]<-.99)
    report={};checks={};images={}
    for name,expected in (
        ('normal-native',srgb_byte(normal*.5+.5)),
        ('direct-left-native',srgb_byte(np.repeat(np.maximum(0,normal@np.array([-1,0,-1])/np.sqrt(2))[...,None],3,axis=-1))),
        ('direct-right-native',srgb_byte(np.repeat(np.maximum(0,normal@np.array([1,0,-1])/np.sqrt(2))[...,None],3,axis=-1)))):
        actual=np.asarray(Image.open(OUT/(name+'.png')).convert('RGBA'));images[name]=actual
        if actual.shape!=data.shape:raise ValueError('GPU native raster size mismatch')
        error=np.abs(actual[...,:3].astype(int)-expected.astype(int))
        report[name]={'coverage_mismatches':int(np.sum((actual[...,3]>0)!=mask)),
          'max_rgb_byte_error':int(error[mask].max()),'handle_max_error':int(error[handles].max())}
        checks[name]=report[name]['coverage_mismatches']==0 and report[name]['max_rgb_byte_error']<=1
    x=normal[...,0]
    left=images['direct-left-native'][...,0];right=images['direct-right-native'][...,0]
    neg=handles&(x<0);pos=handles&(x>0)
    checks['actual_direction_reversal']=bool(left[neg].mean()>left[pos].mean() and right[pos].mean()>right[neg].mean())
    report['response_changed_handle_cells']=int(np.sum(handles&(left!=right)))
    report['checks']=checks;report['passed']=all(checks.values())
    report['final_three_colour_guarantee_claimed']=False
    (OUT/'gpu-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not all(checks.values()):raise ValueError('Actual GPU normal/directional parity failed')
    before=Image.open(OUT/'detail-before.png').convert('RGB');after=Image.open(OUT/'detail-after.png').convert('RGB')
    if before.size!=after.size:raise ValueError('Same camera raster required')
    # Camera was translated to the unchanged display quad's centre. Crop only;
    # no resize, resample, smoothing or pixel-art production takes place here.
    w,h=before.size;native_w,native_h=data.shape[1],data.shape[0]
    rect=(int(w/2-native_w-8),int(h/2-native_h-8),int(w/2+native_w+8),int(h/2+native_h+8))
    a=before.crop(rect);b=after.crop(rect)
    view=Image.new('RGB',(a.width*2+12,a.height+36),(32,34,40))
    view.paste(a,(0,36));view.paste(b,(a.width+12,36))
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    draw=ImageDraw.Draw(view);draw.text((12,6),'이전 — 실제 Unity 화면',(240,240,240),font=font)
    draw.text((a.width+24,6),'적용 후 — 동일 2px 배율',(240,240,240),font=font)
    view.save(OUT/'comparison.png')
    print(json.dumps({'passed':True,'gpu':report,'comparison_crop':rect}))
