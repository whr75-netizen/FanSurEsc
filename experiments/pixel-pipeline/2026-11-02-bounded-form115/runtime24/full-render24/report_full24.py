"""Render only completed actual GPU packets. Never fill missing pixels from CPU."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]/'argon23-runtime113'))
from inputs113 import plane, buffer

def read(p): return json.loads(p.read_text(encoding='utf8'))
def rgba(v):
    x=v[...,:3]
    rgb=np.rint(np.clip(np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055),0,1)*255).astype(np.uint8)
    return np.dstack([rgb,np.rint(np.clip(v[...,3],0,1)*255).astype(np.uint8)])
def full(p,name):
    data=np.zeros((272,480,4),np.float32); cover=np.zeros(272,int); sid=None
    for q in sorted(p.glob('FULL-'+name+'-y*.plane')):
        m,a=plane(q);x,y,w,h=m['roi'];assert w==480 and h<=32
        sid=m['sourceId']if sid is None else sid; assert sid==m['sourceId']
        data[y:y+h,x:x+w]=a;cover[y:y+h]+=1
    assert(cover==1).all();return data,sid
def main(root=H):
    done=sorted(root.glob('STATE113-*-finished.json'));assert len(done)==1
    s=read(done[0]); assert s['PlayExited']and not s.get('error')and not s.get('restorationError')
    checks=['optionsRestored','timeRestored','pipelineRestored','backgroundRestored','playerSettingsRunInBackgroundRestored','observerRemoved']
    assert all(s.get(k)for k in checks)
    assert all(x['equal']for x in s['nativeComparisons72'])and not s['globalRestoreErrors']
    assert all(s['editInputRestoration82'][k]for k in ['deviceEnabledStates','devicesSame','exactJSON','hideFlags','keyboardSame','sameAliveReference'])
    out=root/'results';out.mkdir(exist_ok=True);rows=[];images=[]
    palette=read(H.parents[2]/'argon23-runtime113/SOURCE113.json')
    for i,packet in enumerate(s['sequencePackets']):
        p=Path(packet['output']);m=read(p/'RAW_MANIFEST.json')
        assert hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text().strip()
        assert m['sourceId']==packet['sourceId']and m['algorithmValid113']and m['frameUnchangedDuringReadback']and m['displayPhysicalProjectionEqual113']
        a,sid=full(p,'product77');b,sid2=full(p,'candidate113');assert sid==sid2==m['sourceId']
        r=m['grid102']['eyeTopLeftROI'];offset=m['grid102']['headToMainOffset']
        x,y,w,h=[r[0]+round(offset[0]),272-r[1]-r[3]+round(offset[1]),r[2],r[3]]
        outside=np.ones((272,480),bool);outside[y:y+h,x:x+w]=False;assert np.array_equal(a[outside],b[outside])
        imgs=[Image.fromarray(rgba(np.flipud(v)))for v in [a,b]]
        for name,im in zip(['control','candidate'],imgs):
            im.save(out/f'{i:02d}-{name}.png')
            im.crop((x,272-y-h,x+w,272-y)).resize((w*16,h*16),Image.Resampling.NEAREST).save(out/f'{i:02d}-{name}-eye.png')
        images.append(imgs[1])
        ids=buffer(p/'curve-identity.f32').reshape(-1,4)
        f=buffer(p/'REGION113-frame.f32').reshape(-1,4);u=f.view(np.uint32)
        best=buffer(p/'REGION113-best.f32').reshape(2,3,4)
        visibility=buffer(p/'ASSIGNED-visibility24.f32').reshape(-1,4)
        finalOwner=plane(p/'F-FinalOwner.plane')[1];finalColour=plane(p/'F-FinalRGBA.plane')[1]
        finalRGB=rgba(finalColour)[...,:3];parts=[]
        for eye in [1,2]:
            for part,role in [(1,2),(4,5),(6,7)]:
                mask=(finalOwner[...,0]==role)&(finalOwner[...,1]==eye)
                expected=np.array([q['RGB8']for q in(palette['lidPalette']if part==6 else palette['keys'])if q['owner']==eye and(part==6 or q['part']==part)],int)
                rgb=finalRGB[mask];errors=sum(not np.any((expected==v).all(1))for v in rgb)
                parts.append({'owner':eye,'part':part,'visibleCells':int(mask.sum()),'paletteRGB8Errors':int(errors)})
        row={'sourceId':sid,'frame':m['frameIndex'],'serial':m['mainSerial'],'requestedClose':m['motion82'].get('requestedClose'),
             'pixelRectBottomLeft':[x,y,w,h],'changedPixels':int(np.sum(np.max(abs(a-b),axis=2)>1e-6)),
             'outsideEyeRectByteEqual':True,'shaderSHA':m['runtime24']['sourceHash'],'runtime24':m['runtime24'],
             'eyes':[{'owner':eye,'canonicalPartCounts':{str(k):int(np.sum((ids[:,1]==eye)&(ids[:,0]==k)))for k in [1,4,6]},
                      'header':u[(eye-1)*32].tolist(),'optima':int(best[eye-1,2].view(np.uint32)[1])}for eye in [1,2]],
             'visibilityStatuses':dict(collections.Counter(str(float(x))for x in visibility[:,3])),
             'finalVisibleParts':parts,'finalOwnerStatus':dict(collections.Counter(str(float(x))for x in finalOwner[...,3].ravel())),
             'motion':m['motion82'],'actualRuntimeGPU':True,'offlineSelectionReplay':False}
        rows.append(row)
    summary={'frames':rows,'completedRuntimeGPUFrames':len(rows),'product77DefaultChanged':False,
             'nativeContentsCompared':len(s['nativeComparisons72']),'nativeContentsEqual':True,'globalRestoreErrors':s['globalRestoreErrors'],
             'inputRestored':s['editInputRestoration82'],'restore':{k:s[k]for k in checks},'PlayExited':s['PlayExited'],
             'actualContinuousMotionValidated':False,'wholeFaceUVPaletteOutlineComplete':False}
    (root/'RESULT_FULL24.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if len(images)>1:images[0].save(out/'SEQUENCE_FULL24.webp',save_all=True,append_images=images[1:],duration=180,loop=0,lossless=True)
    print(json.dumps({'frames':len(rows),'changedPixels':[r['changedPixels']for r in rows],'eyes':[r['eyes']for r in rows],'nativeEqual':len(s['nativeComparisons72']),'restored':True},ensure_ascii=False))
if __name__=='__main__':main(Path(sys.argv[1])if len(sys.argv)>1 else H)
