"""N30 GPU/CPU map parity, old shader parity and real-light specular response."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/artifacts/building39/material30/run01'
EVIDENCE=OUT/'observation02'

def read(path):return np.asarray(Image.open(path).convert('RGBA'))
def srgb(v):return np.rint(np.where(v<=.0031308,12.92*v,1.055*np.maximum(v,0)**(1/2.4)-.055)*255)

def finish():
    if (OUT/'gpu-gate.json').exists():raise ValueError('Previous evidence preserved')
    report={};checks={}
    for name in ('legacy-readable-native','legacy-albedo-native'):
        old=read(ROOT/('LocalOnly/Material30/before-shader/'+name+'.png'))
        new=read(EVIDENCE/(name+'.png'))
        report[name]={'changed_bytes':int(np.sum(old!=new))}
        checks[name]=bool(np.array_equal(old,new))
        Image.fromarray(old).save(OUT/(name+'-before.png'))
    source=read(OUT/'material.png');mask=source[...,3]>0
    actual=read(EVIDENCE/'gpu-albedo-native.png');expected=read(OUT/'albedo-native.png')
    error=np.abs(actual[...,:3].astype(int)-expected[...,:3].astype(int))
    report['albedo']={'coverage_mismatches':int(np.sum((actual[...,3]>0)!=mask)),
        'max_rgb_byte_error':int(error[mask].max())}
    checks['extended_gpu_albedo']=report['albedo']['coverage_mismatches']==0 and report['albedo']['max_rgb_byte_error']<=1
    zero=read(EVIDENCE/'spec-zero-native.png');left=read(EVIDENCE/'spec-left-native.png');right=read(EVIDENCE/'spec-right-native.png')
    checks['zero_light_zero_spec']=bool(np.all(zero[mask,:3]==0))
    changed=np.any(left[...,:3]!=right[...,:3],axis=-1)&mask
    report['spec']={'left_active_cells':int(np.sum(mask&np.any(left[...,:3]>0,axis=-1))),
        'right_active_cells':int(np.sum(mask&np.any(right[...,:3]>0,axis=-1))),
        'direction_changed_cells':int(changed.sum())}
    checks['real_point_response']=bool(report['spec']['left_active_cells']>0 and report['spec']['right_active_cells']>0 and changed.sum()>0)
    cap=np.where(source[...,0]==3,.06,.024)
    limit=srgb(cap)+1
    checks['combined_spec_cap']=bool(np.all(np.max(left[...,:3],axis=-1)[mask]<=limit[mask]) and
        np.all(np.max(right[...,:3],axis=-1)[mask]<=limit[mask]))
    for name,a in [('spec-zero',zero),('spec-left',left),('spec-right',right)]:
        checks[name+'_coverage']=bool(np.array_equal(a[...,3]>0,mask))
    report['checks']=checks;report['passed']=all(checks.values())
    report['shadow_validation']='attenuation code inspected; fixture has no shadow caster'
    report['art_approval_claimed']=False
    (OUT/'gpu-gate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    receipt=json.loads((EVIDENCE/'observation.json').read_text(encoding='utf-8'))
    a=Image.open(EVIDENCE/'play-before.png').convert('RGB');b=Image.open(EVIDENCE/'play-after.png').convert('RGB')
    x,y,w,h=receipt['objectRect'];rect=(x,y,x+w,y+h);a=a.crop(rect);b=b.crop(rect)
    view=Image.new('RGB',(w*2+12,h+36),(32,34,40));view.paste(a,(0,36));view.paste(b,(w+12,36))
    draw=ImageDraw.Draw(view);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    draw.text((12,6),'이전 — 큰 얼룩',(240,240,240),font=font)
    draw.text((w+24,6),'수정 — 사용 흔적과 재질',(240,240,240),font=font)
    view.save(OUT/'comparison.png')
    print(json.dumps(report))
    if not report['passed']:raise ValueError('N30 GPU gate failed; do not integrate')

if __name__=='__main__':finish()
