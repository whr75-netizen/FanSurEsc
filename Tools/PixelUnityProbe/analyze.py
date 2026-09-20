"""Measure actual Unity GameCamera outputs, never an AI visual verdict."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2];base=ROOT/'LocalOnly/PixelUnityProbe22';out=base/(sys.argv[1] if len(sys.argv)>1 else '')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    build=read(out/'build.json');cap=read(out/'capture.json');spec=read(base/'input/spec.json')
    if cap['status']!='captured' or not cap['restored']:raise ValueError('Actual capture/restoration incomplete')
    files={name:out/'captures'/f'{name}.png' for name in cap['cases']}
    frames={k:np.asarray(Image.open(p).convert('RGB')) for k,p in files.items()}
    w,h=cap['imageWidth'],cap['imageHeight']
    def crop(name,which):
        p=cap[which+'BottomLeft'];x=round(p['x']);y=cap['height']-round(p['y'])-h
        return frames[name][y:y+h,x:x+w]
    a=crop('baseline','image');b=crop('baseline','model')
    source=np.asarray(Image.open(base/'input/desk.png').convert('RGBA'));mask=source[...,3]>0
    amask=a.max(2)>0;bmask=b.max(2)>0
    diffA=np.max(abs(a.astype(int)-source[...,:3].astype(int)),axis=2)
    def delta(first,second,which):
        x=crop(first,which).astype(int);y=crop(second,which).astype(int)
        return int(np.any(abs(x-y)>1,axis=2).sum())
    palette=np.array(spec['material']['colors_srgb8'],int)
    albedo=crop('albedo','model');samples=albedo[bmask].astype(int)
    distances=abs(samples[:,None,:]-palette[None,:,:]).max(2).min(1)
    iou=float((mask&bmask).sum()/max(1,(mask|bmask).sum()))
    contextA=crop('context','image')
    contextError=np.max(abs(contextA.astype(int)-source[...,:3].astype(int)),axis=2)
    localDifference=crop('local_on','model').astype(int)-b.astype(int)
    localChanged=np.any(abs(localDifference)>1,axis=2)&bmask
    repair=read(ROOT/'LocalOnly/PixelUnityProbe23/repair.json')
    checks={'geometry_12_meshes':build['actualMeshCount']==12 and build['maxDimensionError']<1e-5,
        'original_png_bytes':sha(ROOT/'Assets/Tests/PixelDeskLighting22/desk.png')==sha(base/'input/desk.png'),
        'point_uncompressed_no_mips':all(build[k] for k in ('point','uncompressed','noMipmaps')),
        'actual_game_camera':cap['actualGameCamera'],'pixel_grid_alignment':cap['maxGridCornerError']<.001,
        'no_aa_or_post':cap['aaOff'] and cap['postOff'],
        'image_pixels_preserved':bool(np.array_equal(amask,mask) and diffA[mask].max()<=1),
        'model_silhouette_same_grid':iou>=.995,
        'unshaded_model_only_four_grain_colors':bool(np.all(distances<=1)),
        'image_fixed_shadows_under_changed_sun':delta('baseline','opposite','image')==0,
        'model_responds_to_sun_direction':delta('baseline','opposite','model')>0,
        'model_receives_visible_local_light':int(localChanged.sum())>=int(bmask.sum()*.1),
        'image_pixels_preserved_in_full_base':bool(np.all(contextError[mask]<=1)),
        'no_underground_card_or_model':abs(repair['imageOpaqueBottom'])<.00001 and repair['modelMinimumY']>=-.00001,
        'native_pbr_material_preserved':repair['materialPreserved']}
    report={'accepted':bool(all(checks.values())),'checks':checks,'actual_size':[w,h],'ppu':cap['ppu'],
        'image_max_rgb_error':int(diffA[mask].max()),'model_silhouette_iou':iou,
        'model_albedo_nonpalette_pixels':int((distances>1).sum()),
        'sun_direction_changed_pixels':{k:delta('baseline','opposite',k) for k in ('image','model')},
        'local_light_changed_pixels':{k:delta('baseline','local_on',k) for k in ('image','model')},
        'full_base_image_different_pixels':int((mask&(contextError>1)).sum()),
        'local_light_mean_rgb_change':localDifference[bmask].mean(axis=0).tolist(),
        'evidence_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [out/'build.json',out/'capture.json',*files.values()]},
        'limits':['fixed view and integer native96PPU only','original wood is not proven pure albedo',
                  'SteppedLocalLight has no shadow occlusion','art satisfaction not automatically approved']}
    (out/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    scale=4;board=Image.new('RGB',(w*scale*2+48,h*scale*3+168),(235,231,223));draw=ImageDraw.Draw(board)
    try:font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
    except OSError:font=ImageFont.load_default()
    for row,(case,label) in enumerate([('baseline','로컬광 꺼짐'),('local_on','기지 로컬광 켜짐'),('opposite','주광 반대 방향')]):
        for col,(which,title) in enumerate([('image','A: 고정 명암 PNG'),('model','B: 실제 3D · 동적 명암')]):
            x=16+col*(w*scale+16);y=16+row*(h*scale+48)
            draw.text((x,y),title+' / '+label,fill=(36,28,20),font=font)
            im=Image.fromarray(crop(case,which));board.paste(im.resize((w*scale,h*scale),Image.Resampling.NEAREST),(x,y+30))
    board.save(out/'comparison.png')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
