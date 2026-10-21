from pathlib import Path
import json, struct, gzip, collections, hashlib
import numpy as np
from PIL import Image, ImageDraw, features

R=Path(__file__).parent/'Loop514'
out=json.loads((R/'FINAL_REVIEW514.json').read_text())
cache={}
def rd(i,tag):
    key=(i,tag)
    if key not in cache:
        b=gzip.decompress((R/f'{i:03d}_{tag}.bin.gz').read_bytes())
        w,h,_,_=struct.unpack_from('<4i',b)
        cache[key]=np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
    return cache[key]

def exterior(cov):
    h,w=cov.shape; e=np.zeros_like(cov); q=collections.deque()
    for y,x in [(0,x)for x in range(w)]+[(h-1,x)for x in range(w)]+[(y,0)for y in range(h)]+[(y,w-1)for y in range(h)]:
        if not cov[y,x]and not e[y,x]: e[y,x]=1; q.append((y,x))
    while q:
        y,x=q.popleft()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            yy,xx=y+dy,x+dx
            if 0<=yy<h and 0<=xx<w and not cov[yy,xx]and not e[yy,xx]:
                e[yy,xx]=1; q.append((yy,xx))
    return e

body=[]
for item in out['sameRoleBodyColourDifferences']:
    i=item['target']; x,y=item['mainXY']; entries=[]
    for tag in ['BASE','ALT']:
        cov=rd(i,tag+'_FINAL')[:,:,3]>0; own=rd(i,tag+'_OWNER'); ext=exterior(cov)
        part=int(round(float(own[y,x,1]))); role=int(round(float(own[y,x,0])))-1
        outer=False; thin=False
        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            if ext[y+dy,x+dx]:
                outer=True
                core=bool(cov[y-dy,x-dx]and cov[y-2*dy,x-2*dx])
                if 2<=part<=5: core=core and int(round(own[y-dy,x-dx,1]))==part and int(round(own[y-2*dy,x-2*dx,1]))==part
                thin|=not core
        entries.append({'version':tag,'roleZeroBased':role,'part':part,'outer':bool(outer),'thinFromExterior':bool(thin),'exteriorReason':int(outer and not thin and role>=7),'coverage5x5':cov[y-2:y+3,x-2:x+3].astype(int).tolist(),'part5x5':own[y-2:y+3,x-2:x+3,1].tolist()})
    a=np.array(item['buffers']['BASE']['FINAL'][:3]); b=np.array(item['buffers']['ALT']['FINAL'][:3])
    ratio=b/a
    body.append({'target':i,'mainXY':[x,y],'sameMetadataUVAndOwner':all(item['buffers']['BASE'][k]==item['buffers']['ALT'][k]for k in ['META','UV','OWNER']),'rgbRatioALTvsBASE':ratio.tolist(),'exactRamp055Within1e7':bool(np.max(abs(b-a*.55))<1e-7),'lineReconstruction':entries,'classification':'SAME_BODY_SAMPLE_CANDIDATE_COLOUR_DEPENDENCY; outer/line evidence reconstructed, internal/Palette Audit not captured'})

seam=[]
for tag in ['BASE','ALT']:
    m0,m1=(rd(i,tag+'_META')for i in [0,80]); c0,c1=(rd(i,tag+'_FINAL')for i in [0,80]); w0,w1=(rd(i,tag+'_WORLDINFO')for i in [0,80])
    png0,png1=(np.array(Image.open(R/f'{i:03d}_{tag}.png').convert('RGB'))for i in [0,80])
    delta=np.max(abs(png0.astype(int)-png1.astype(int)),2)
    cov=(m0[:,:,0]>0)&(m1[:,:,0]>0); vis0=w0[:,:,2]>.5; vis1=w1[:,:,2]>.5
    expand=lambda m:np.repeat(np.repeat(m,2,0),2,1)
    mx=int(delta[expand(cov)].max(initial=0)); ys,xs=np.where((delta==mx)&expand(cov)); spots=[]
    for py,px in list(zip(ys,xs))[::4][:8]:
        x,y=px//2,py//2
        spots.append({'mainXY':[int(x),int(y)],'screenRGB':[png0[py,px].tolist(),png1[py,px].tolist()],'preworldRGBA':[c0[y,x].tolist(),c1[y,x].tolist()],'meta':[m0[y,x].tolist(),m1[y,x].tolist()],'worldInfo':[w0[y,x].tolist(),w1[y,x].tolist()]})
    seam.append({'version':tag,'coveredBothScreenMaxByte':mx,'coveredVisibleBothScreenMaxByte':int(delta[expand(cov&vis0&vis1)].max(initial=0)),'coveredWorldVisibilityChangedCells':int((cov&(vis0!=vis1)).sum()),'coveredPreworldLinearMax':float(abs(c0-c1)[cov].max(initial=0)),'maxCoveredExamples':spots,'limit':'WORLDINFO captures destination depth/visibility, not moving world colour, full shadow atlas, all light inputs or their first changed pass.'})

out['sameRoleBodyColourClassification']=body
out['seamWorldClassification']=seam
out['worldInfoScopeCorrection']={'captured':'f.motion.worldInfo: Compose333 legacy480 preview','actualNativePresenter':'g.player.output: Native395.Present960; independent world/depth and deliveredDelta','notCaptured':['Native395 world/worldDepth','Native395 owner/cellID/depthAudit','deliveredDelta/origin for each pose','GPU Before/Flood/OwnerLines/Palette Audit','full world shadow atlas and other light inputs'],'consequence':'WORLDINFO visibility values are not evidence of native960 world visibility. Screen-vs-local coordinate seam statistics are provisional registration comparisons, not certified same-ray native world/shadow classifications. Local preworld character invariants and paired final PNG observations remain valid within their own spaces.'}
for item in out['seamWorldClassification']:
    item['nativeVisibilityCertified']=False
for item in out['seamHead']:
    item['worldInfoIsLegacyPreviewNotNative395']=True
out['remainingLimits']=[s for s in out['remainingLimits']if '80-frame lossless normal WebP'not in s]
out['remainingLimits'].append('Normal GIF uses67 nearest time samples and omits source51; the all-frame inspection GIF and original81 records retain all observations. The additional normal-speed artifact, if present below, retains all80 loop samples without spatial interpolation.')

webp=R/'WALK514_NORMAL60_ALL_FRAMES.webp'
if not webp.exists()and features.check('webp'):
    box=tuple(out['normalGif']['nativePixelCrop']); width,height=box[2]-box[0],box[3]-box[1]; frames=[]; times=[]
    for i in range(81):
        cfg=json.loads((R/f'{i:03d}_ALT_projection.json').read_text()); times.append(cfg['gameTime'])
        if i==80: continue
        canvas=Image.new('RGB',(width*2+2,height+38),'#181818'); d=ImageDraw.Draw(canvas)
        for k,tag in enumerate(['BASE','ALT']):
            with Image.open(R/f'{i:03d}_{tag}.png')as im: canvas.paste(im.convert('RGB').crop(box),(k*(width+2),38))
        d.text((5,5),'CURRENT ACTIVE348 ORIGINAL',fill='white'); d.text((width+7,5),'CURVES511 + BODY512 / OFF',fill='white')
        d.text((5,20),f'Walk {i/80:.4f} | all60fps samples {i}/80',fill='white'); frames.append(canvas)
    ms=np.rint((np.array(times)-times[0])*1000).astype(int); dur=np.diff(ms).tolist()
    frames[0].save(webp,format='WEBP',save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True,quality=100,method=4)
if webp.exists():
    with Image.open(webp)as im:
        count=im.n_frames; elapsed=0
        for i in range(count): im.seek(i); im.load(); elapsed+=im.info.get('duration',0)
    assert count==80 and elapsed==1333,(count,elapsed)
    out['normalAllFramesWebP']={'path':str(webp),'bytes':webp.stat().st_size,'sha256':hashlib.sha256(webp.read_bytes()).hexdigest(),'frames':count,'durationMs':elapsed,'allLoopSamples':True,'pixelLossless':True,'resampling':False,'note':'Pillow12 uses webp capability flag; all80 intervals at original60fps in16/17ms, endpoint80 retained for separate seam comparison.'}

(R/'FINAL_REVIEW514.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'body':body,'seamWorld':seam,'normalAllFramesWebP':out['normalAllFramesWebP']},ensure_ascii=False))
