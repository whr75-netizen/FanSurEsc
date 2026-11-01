from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageSequence
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'live-underlay98';OUT=HERE/'deliverables'
def font(n,bold=False):return ImageFont.truetype(str(Path('C:/Windows/Fonts')/('malgunbd.ttf'if bold else'malgun.ttf')),n)
def main():
    OUT.mkdir(exist_ok=True);pol=json.loads((OLD/'POLICIES98C.json').read_text());row=next(r for r in pol['rows']if r['frame']==127);names=['strict','eye-first','background-first'];titles=['엄격 보존','눈파트 우선','바탕·흰자 우선'];sub=['미확정은 기존 결과 유지','홍채 → 흰자 → 선 → 바탕','바탕 → 흰자 → 홍채 → 선']
    pics=[Image.open(OLD/f'policy-review-c/frame127-{n}-native1x.png').convert('RGB')for n in names];points=np.array([c['nativeROIxy']for p in row['policies']for c in p['changes']]);lo=points.min(0)-3;hi=points.max(0)+4;w,h=pics[0].size;box=(int(lo[0]),h-int(hi[1]),int(hi[0]),h-int(lo[1]));canvas=Image.new('RGB',(1200,690),'#20242a');d=ImageDraw.Draw(canvas);d.fontmode='1';d.text((24,16),'눈의 동률 표현 선택 — 같은 frame127, 같은 원본 색',font=font(25,True),fill='white');d.text((24,56),'기존 실험98의 재배치 자료입니다. 새 미술 후보·제품 적용은 없습니다.',font=font(18),fill='#c9d5df')
    for i,(name,title,im)in enumerate(zip(names,titles,pics)):
        x=24+i*396;d.text((x,108),title,font=font(23,True),fill='#9dd7ff');d.text((x,144),sub[i],font=font(16),fill='white');d.text((x,184),'PNG 내부 원배율 1:1',font=font(15),fill='#c9d5df');canvas.paste(im,(x,212));d.text((x,306),'같은 눈 부위 nearest ×16',font=font(15),fill='#c9d5df');crop=im.crop(box);canvas.paste(crop.resize((crop.width*16,crop.height*16),Image.Resampling.NEAREST),(x,340));changed=0 if i==0 else row['policies'][i-1]['changedNativeRGBPixels'];d.text((x,510),f'엄격 보존 대비 RGB 변화: {changed} native 픽셀',font=font(15),fill='white')
    d.text((24,565),'정확한 coverage 동률에만 적용하는 오프라인 정책 비교 · 두 우선순위는 미채택',font=font(18,True),fill='#ffd18a');d.text((24,600),'미확정 0은 우선순위를 추가한 결과이며 미관 성공의 증거가 아닙니다.',font=font(17),fill='white');d.text((24,634),'원배율·색은 PNG 기준입니다. 앱의 표시 크기는 달라질 수 있습니다.',font=font(16),fill='#c9d5df');canvas.save(OUT/'EYE_TIE_CHOICES_99.png')
    frames=[]
    for f in range(127,137):
        board=Image.new('RGB',(1056,370),'#20242a');dr=ImageDraw.Draw(board);dr.fontmode='1';dr.text((18,8),f'같은 실제 회전 프레임 {f} / 10장 연속 — 보기 위해 0.25초씩 느리게 표시',font=font(18,True),fill='white')
        for i,(n,title)in enumerate(zip(names,titles)):
            im=Image.open(OLD/f'policy-review-c/frame{f}-{n}-native1x.png').convert('RGB');dr.text((18+i*348,42),title,font=font(19,True),fill='#9dd7ff');board.paste(im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST),(12+i*348,78))
        frames.append(board)
    # Lossless animated WebP avoids GIF's256-colour conversion of the1473-colour
    # source sequence. Verify all decoded RGB frames, not only the first image.
    path=OUT/'EYE_TIE_TURN_99.webp';frames[0].save(path,save_all=True,append_images=frames[1:],duration=250,loop=0,lossless=True,quality=100,method=6,exact=True)
    decoded=Image.open(path);assert decoded.n_frames==10
    for i in range(10):decoded.seek(i);assert np.array_equal(np.asarray(decoded.convert('RGB')),np.asarray(frames[i]))
    manifest={'existingSourceCommit':'cf8b14147e94ff87f2487efc523e62ea9456877f','frame127SourceId':row['sourceId'],'policies':list(zip(names,titles,sub)),'newArtCandidates':False,'priorityPoliciesAdopted':False,'sequenceSourceFrames':list(range(127,137)),'displayFrameDurationMs':250,'sequenceExactRGBDecodeAll10':True,'files':[{'file':p.name,'bytes':p.stat().st_size,'SHA256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in OUT.iterdir()if p.suffix in ['.png','.webp']]};(OUT/'DELIVERY99.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False))
if __name__=='__main__':main()
