"""One art experiment: metric diagrams -> external image -> existing PerfectPixel.

No Unity writes. The SVG-like geometry below is a technical guide, not game art.
The only image conversion is the user's requested existing normalization path.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DESIGN = Path(__file__).with_name('design.json')
ENGINE = ROOT / 'LocalOnly/PerfectPixelPalette_20260906/trigger_cli.py'


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', size)


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    spec = json.loads(DESIGN.read_text(encoding='utf-8'))
    write_json(out / 'plan.json', spec)
    im = Image.new('RGB', (1280, 810), '#18252f')
    d = ImageDraw.Draw(im)
    d.text((36, 26), '생활잡화점 01  /  맵 → 건물 → 동선', font=font(29), fill='#f5e7ce')
    d.text((36, 74), '설계도입니다. 완성 아트·Unity 적용 결과가 아닙니다.  |  단위 m', font=font(17), fill='#aac4c9')
    def rectangle(rect, origin, s, fill, label=None):
        x, z, w, dep = rect
        b = (origin[0]+x*s, origin[1]+z*s, origin[0]+(x+w)*s, origin[1]+(z+dep)*s)
        d.rectangle(b, fill=fill, outline='#e3d8bc', width=2)
        if label:
            d.text((b[0]+6, b[1]+7), label, font=font(13), fill='#15202a')
    # A site plan and two floors, all derived from metric plan data.
    d.text((36, 125), '주변 맵 아트 계획', font=font(23), fill='#f5e7ce')
    origin=(55,184); scale=22
    rectangle([0,0,12,16],origin,scale,'#64746b')
    rectangle([0,0,12,3],origin,scale,'#56666a','REAR DELIVERY')
    rectangle([0,3,2,10],origin,scale,'#82765f')
    rectangle([10,3,2,10],origin,scale,'#82765f')
    rectangle([2,3,8,10],origin,scale,'#b3a287','SHOP + RESIDENCE')
    rectangle([0,13,12,3],origin,scale,'#9d9684','FRONT WALK')
    rectangle([-0.3,16,12.6,2],origin,scale,'#3f525e','ROAD')
    d.text((36,620),'부지 12 × 16 / 건물 8 × 10\n뒤: 납품 / 옆: 서비스 골목\n앞: 주거·상가 별도 출입',font=font(17),fill='#c4d6d4',spacing=8)
    for floor, ox in [(0,445),(1,870)]:
        origin=(ox,184); scale=35
        d.text((ox,125),f'{floor+1}층  /  '+('잡화점·독립 계단' if floor==0 else '주거 공간 계획'),font=font(23),fill='#f5e7ce')
        for room in spec['rooms']:
            if room['floor']==floor: rectangle(room['rect'],origin,scale,room['color'],room['id'])
        for op in spec['openings']:
            if op['floor']!=floor: continue
            x,z=op['p']; h=op['width']/2
            a,b=((x-h,z),(x+h,z)) if op['axis']=='x' else ((x,z-h),(x,z+h))
            d.line([(ox+a[0]*scale,184+a[1]*scale),(ox+b[0]*scale,184+b[1]*scale)],fill='#72edc3',width=7)
        rectangle(spec['stairs']['rect'],origin,scale,'#535c70','UP / DOWN')
        for i in range(9):
            y=origin[1]+(1.1+i*.28)*scale
            d.line((ox+.15*scale,y,ox+2.25*scale,y),fill='#b9c3cc',width=1)
        d.text((ox,566),'초록색: 출입 / 층간 코어 같은 위치',font=font(16),fill='#b6cfc9')
    d.text((445,620),'1층: 판매장·재고실·WC·지원 복도\n2층: 거실·주방·침실·욕실\n계단은 배치 예약이며 실제 물리 이동은 미검증',font=font(17),fill='#c4d6d4',spacing=8)
    im.save(out/'01-map-and-floorplans.png')
    im=Image.new('RGB',(1040,830),'#18252f'); d=ImageDraw.Draw(im)
    d.text((34,24),'사물 배치 설계 / 1층',font=font(28),fill='#f5e7ce')
    origin=(62,116); scale=57
    for room in spec['rooms']:
        if room['floor']==0: rectangle(room['rect'],origin,scale,room['color'],room['id'])
    for f in spec['fixtures']: rectangle(f['rect'],origin,scale,f['color'],f['id'])
    pts=[(origin[0]+x*scale,origin[1]+z*scale) for x,z in spec['reserved_route']]
    d.line(pts,fill='#76edbd',width=13)
    rectangle(spec['stairs']['rect'],origin,scale,'#535c70','STAIRS')
    for index,f in enumerate(spec['fixtures']):
        d.text((570,132+index*42),f"{f['id']}  {f['name']}",font=font(16),fill='#d3dfdb')
    d.text((570,602),'초록: 비워 둘 주요 이동 동선\n상품·장식은 설비 위/안에 배치\n비율용 인물 1.8m / 최종 캐릭터 아님',font=font(17),fill='#aac4c9',spacing=9)
    d.text((62,739),'출입·점유 위치의 설계 입력입니다. 자동 NavMesh 합격 판정이 아닙니다.',font=font(17),fill='#aac4c9')
    im.save(out/'02-object-placement.png')
    # Deterministic projection sketch. This is deliberately not an art renderer.
    im=Image.new('RGB',tuple(spec['native_size']),'#0e1421'); d=ImageDraw.Draw(im)
    def project(x,z,h=0):
        p=spec['projection']; u,v=p['origin']
        return (round(u+20*(x-z)),round(v+10*(x+z)-p['height_ppm']*h))
    def polygon(points,fill): d.polygon([project(*p) for p in points],fill=fill,outline='#242431')
    def box(rect,h,color):
        x,z,w,dep=rect
        rgb=tuple(bytes.fromhex(color.lstrip('#')))
        shade=lambda k:tuple(round(c*k) for c in rgb)
        polygon([(x+w,z,0),(x+w,z+dep,0),(x+w,z+dep,h),(x+w,z,h)],shade(.67))
        polygon([(x,z+dep,0),(x+w,z+dep,0),(x+w,z+dep,h),(x,z+dep,h)],shade(.83))
        polygon([(x,z,h),(x+w,z,h),(x+w,z+dep,h),(x,z+dep,h)],color)
    for room in spec['rooms']:
        if room['floor']==0: box(room['rect'],.04,room['color'])
    polygon([(0,0,0),(8,0,0),(8,0,3),(0,0,3)],'#4c566f')
    polygon([(0,0,0),(0,10,0),(0,10,3),(0,0,3)],'#465467')
    # Structural boundaries are cut down in the guide to expose the program.
    box([2.3,0,.1,10],.65,'#596879')
    box([2.4,2.7,5.6,.1],.65,'#596879')
    box([5.5,0,.1,2.8],.65,'#596879')
    for i in range(9): box([.2,.3+i*.28,.95,.28],(9-i)*.17,'#9b7b65')
    for i in range(9): box([1.25,.3+i*.28,.95,.28],1.55+i*.17,'#9b7b65')
    for f in sorted(spec['fixtures'],key=lambda f:sum(f['rect'][:2])): box(f['rect'],f['height'],f['color'])
    person=spec['scale_person']; u,v=project(*person['foot']); ht=round(person['height']*spec['projection']['height_ppm'])
    d.ellipse((u-7,v-ht,u+7,v-ht+13),fill='#dfb991')
    d.rectangle((u-7,v-ht+13,u+7,v-10),fill='#b1bbb4')
    d.rectangle((u-6,v-10,u-1,v),fill='#494655'); d.rectangle((u+2,v-10,u+6,v),fill='#494655')
    im.resize((1536,1536),Image.Resampling.NEAREST).save(out/'03-projection-guide.png')
    write_json(out/'prepare-receipt.json',{'design_sha256':sha(DESIGN),'projection':'u=210+20(x-z); v=135+10(x+z)-10sqrt(6)h','guide_size':[1536,1536],'native_size':[384,384],'purpose':'technical guide only'})
    return {'guide':str(out/'03-projection-guide.png'),'plan':str(out/'plan.json')}


def normalize(out, payload):
    spec=json.loads(DESIGN.read_text(encoding='utf-8'))
    source=Path(payload['source']).resolve()
    if not source.is_file(): raise ValueError('No observed generated source')
    target=out/'04-generated-source.png'
    if target.exists(): raise ValueError('Existing source is preserved; choose a new run')
    shutil.copy2(source,target)
    with Image.open(target) as image:
        image.load()
        if image.width!=image.height: raise ValueError('Generation aspect differs from square guide; no stretch/crop allowed')
        actual_size=list(image.size)
        rgba=image.convert('RGBA')
        if rgba.getchannel('A').getextrema() != (255,255): raise ValueError('This scene contract requires opaque art')
        rgba.save(out/'normalizer-input-rgba.png')
    config={'source':'normalizer-input-rgba.png','base_grid':spec['native_size'],'scale':'1.0','preview_zoom':1,'export_color_layers':False,
            'features':{'cell_sampling':{'enabled':True,'scope':{'kind':'all'},'options':{'method':'source_regions','coverage':.5,'color_edge_threshold':.08}}}}
    write_json(out/'normalizer-config.json',config)
    result=subprocess.run([sys.executable,'-B',str(ENGINE),'--config',str(out/'normalizer-config.json'),'--output',str(out/'normalized')],capture_output=True,text=True,encoding='utf-8',errors='replace')
    (out/'normalizer-log.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode: raise RuntimeError(result.stderr or result.stdout)
    native=out/'normalized/pixel_native.png'
    if not native.is_file():
        raise ValueError('Expected CLI pixel_native.png missing')
    shutil.copy2(native,out/'05-native-384.png')
    with Image.open(native) as image:
        z=spec['preview_zoom']; image.resize((image.width*z,image.height*z),Image.Resampling.NEAREST).save(out/'06-preview-3x.png')
    write_json(out/'conversion-receipt.json',{'source':str(source),'source_sha256':sha(source),'preserved_sha256':sha(target),'actual_source_size':actual_size,'native_size':spec['native_size'],'method':'existing PerfectPixel source_regions only','engine_sha256':sha(ENGINE),'input_rgba_sha256':sha(out/'normalizer-input-rgba.png'),'visual_approval':'pending','lost_information':'subcell lines and textures can be lost; geometry not corrected'})
    return {'native':str(out/'05-native-384.png'),'preview':str(out/'06-preview-3x.png')}


def validate(out):
    spec=json.loads(DESIGN.read_text(encoding='utf-8')); errors=[]
    for floor in (0,1):
        rooms=[r for r in spec['rooms'] if r['floor']==floor]
        for i,a in enumerate(rooms):
            x,z,w,h=a['rect']
            if min(x,z)<0 or min(w,h)<=0 or x+w>8+1e-8 or z+h>10+1e-8: errors.append('room bounds '+a['id'])
            for b in rooms[i+1:]:
                bx,bz,bw,bh=b['rect']
                if min(x+w,bx+bw)-max(x,bx)>1e-8 and min(z+h,bz+bh)-max(z,bz)>1e-8: errors.append('room overlap '+a['id']+'/'+b['id'])
        if abs(sum(r['rect'][2]*r['rect'][3] for r in rooms)-80)>1e-8: errors.append('floor coverage')
    with Image.open(out/'05-native-384.png') as image:
        image.load()
        if image.size!=(384,384): errors.append('native size')
        if image.convert('RGBA').getchannel('A').getextrema()!=(255,255): errors.append('alpha')
    receipt=json.loads((out/'conversion-receipt.json').read_text(encoding='utf-8'))
    if sha(out/'04-generated-source.png')!=receipt['source_sha256']: errors.append('source changed')
    checks={'errors':errors,'scope':'room bounds/nonoverlap/coverage, output size/alpha, source hash only','room_area_each_floor_m2':80,'pixel_basis':[[20,10],[-20,10]],'appearance':'user review required','generated_geometry_match':'not certified','unity':'not modified or run'}
    write_json(out/'validation.json',checks)
    if errors: raise ValueError(str(errors))
    return checks


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['prepare','normalize','validate']); parser.add_argument('out',type=Path)
    args=parser.parse_args(); out=args.out.resolve()
    result=prepare(out) if args.stage=='prepare' else normalize(out,json.load(sys.stdin)) if args.stage=='normalize' else validate(out)
    print(json.dumps(result,ensure_ascii=False))
