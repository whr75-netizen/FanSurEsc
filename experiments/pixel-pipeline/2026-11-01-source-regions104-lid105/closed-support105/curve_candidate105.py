"""Offline complete-Close fixture only. No runtime blink classifier or GPU fix.

Rasterise the existing evaluated native ring upper arc, retaining only cells
with same-eye, same-cell certain native lid pigment AFTER real skin occlusion.
No target cell count, unsupported fill, RGB blending or guessed depth is used.
Skin-ring/lash registration, partial Close, rotation and finite lid P are still
prerequisites for product adoption. This is a source-geometry candidate.
"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent;D=H/'direct'
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer,rgba,font,components
from analyse_capture68 import plane,rgb8
from source_curve105 import intersects

def curve_cells(curve,size):
    w,h=size;out=np.zeros((h,w),bool)
    for y in range(h):
        for x in range(w):out[y,x]=any(intersects(a,b,x,y)for a,b in zip(curve,curve[1:]))
    return out

def distance2(point,curve):
    a=curve[:-1];v=np.diff(curve,axis=0);t=np.clip(np.sum((point-a)*v,axis=1)/np.maximum(np.sum(v*v,axis=1),1e-30),0,1)
    return float(np.sum((a+t[:,None]*v-point)**2,axis=1).min())

def source_support(curve,eye,layers,visibility):
    h,w=layers.shape[2:4];touch=curve_cells(curve,(w//4,h//4));colour=np.zeros((h//4,w//4,4),np.float32)
    identity=colour.copy();mask=np.zeros(touch.shape,bool);missing=[];ties=[];proof=[]
    for y,x in np.argwhere(touch):
        samples=[]
        for sy in range(y*4,y*4+4):
            for sx in range(x*4,x*4+4):
                v=visibility[3,sy,sx]
                if v[0]>0 and v[0]==v[1]and round(float(layers[3,1,sy,sx,2]))==eye:
                    key=(distance2(np.array([(sx+.5)/4,(sy+.5)/4]),curve),-float(v[0]))
                    samples.append((key,sy,sx))
        if not samples:missing.append([int(x),int(y)]);continue
        best=min(c[0]for c in samples);choices=[c for c in samples if c[0]==best]
        if len({tuple(layers[3,0,sy,sx,:3])for _,sy,sx in choices})!=1:
            ties.append([int(x),int(y)]);continue
        _,sy,sx=choices[0];colour[y,x]=layers[3,0,sy,sx];colour[y,x,3]=1
        meta=layers[3,1,sy,sx];identity[y,x]=[7,eye,meta[0],layers[3,3,sy,sx,2]];mask[y,x]=True
        proof.append({'canonicalXY':[int(x),int(y)],'nativeSubsampleXY':[int(sx),int(sy)],
          'sourceUV':layers[3,3,sy,sx,:2].tolist(),'sourcePrimitive':int(round(layers[3,3,sy,sx,2])),
          'postQueryAlpha':float(visibility[3,sy,sx,0]),'linearRGB':colour[y,x,:3].tolist(),
          'RGB8':rgb8(colour[y,x,:3]).tolist(),'actualDepth':float(meta[0])})
    return {'colour':colour,'identity':identity,'mask':mask,'missing':missing,'colourTies':ties,
            'proof':proof,'curveCells':int(touch.sum()),'components4':components(mask)}

def hard_hair(eye,owner,hair,hmeta):
    output=eye.copy();finalOwner=owner.copy()
    for y in range(eye.shape[0]):
        for x in range(eye.shape[1]):
            coverage=0;best=-1;chosen=None
            for yy in range(y*4,y*4+4):
                for xx in range(x*4,x*4+4):
                    h=hmeta[yy,xx];v=hair[yy,xx]
                    if h[0]>0 and h[3]>0 and v[3]>0 and(owner[y,x,2]<=0 or h[0]<owner[y,x,2]-3e-5):
                        weight=float(np.clip(h[3],0,1));coverage+=weight
                        if weight>best:best=weight;chosen=(v,h)
            if coverage>=8:
                v,h=chosen;output[y,x]=[*v[:3],1];finalOwner[y,x]=[round(float(h[1])),round(float(h[2])),h[0],0]
    return output,finalOwner

def tests():
    short=curve_cells(np.array([[2.2,3.2],[3.7,3.4]]),(12,8));long=curve_cells(np.array([[1.2,3.2],[8.7,3.4]]),(12,8))
    assert short.sum()<long.sum()
    curve=np.array([[1.2,2.4],[4.7,4.2],[7.4,3.6]]);a=curve_cells(curve,(12,8))
    rotated=np.column_stack([8-curve[:,1],curve[:,0]])
    assert np.array_equal(np.rot90(a,-1),curve_cells(rotated,(8,12)))
    assert components(a)==[int(a.sum())]
    layers=np.zeros((4,5,32,48,4),np.float32);vis=np.zeros((4,32,48,4),np.float32)
    missing=source_support(curve,1,layers,vis)
    assert not missing['mask'].any()and len(missing['missing'])==a.sum()
    return {'sourceSpanChangesBudget':True,'rotate90Equivalent':True,'curveSupportConnected':True,'noUnsupportedFill':True}

def main():
    state=load(sorted(D.glob('STATE102-*'))[-1]);curves=load(D/'SOURCE_CURVE105.json');rows=[]
    board=Image.new('RGB',(1300,1110),'#20252c');draw=ImageDraw.Draw(board)
    draw.text((20,12),'105 · 닫힌 안검 곡선 지지 후보 — 저장 입력의 오프라인 적용',font=font(25),fill='white')
    draw.text((20,48),'실제 GPU102 대조 / 새 GPU 통합·최종 팔레트·회전·부분 Close 미검증 / 제품77 유지',font=font(18),fill='#f4c880')
    for j,e in enumerate(state['sequencePackets']):
        p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');w,h=m['forward102']['canonicalSize']
        eye=plane(p/'F-EyeRGBA.plane')[1];owner=plane(p/'F-EyeOwner.plane')[1]
        oldFinal=plane(p/'F-FinalRGBA.plane')[1];hair=plane(p/'S4-rgba.plane')[1];hmeta=plane(p/'S4-meta.plane')[1]
        candidate=eye.copy();co=owner.copy();data=next(r for r in curves if r['sourceId']==m['sourceId']);close=m['motion82']['requestedClose'];details=[]
        if close==100:
            assert m['motion82']['evaluatedVsOwnedBakeMax']==0
            layers=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);visibility=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
            cc=np.zeros((h//4,w//4,4),np.float32);ci=cc.copy();cm=np.zeros(cc.shape[:2],bool)
            for r in data['eyes']:
                assert r['numericMapValidated']and r['mapSource'].startswith('direct existing public')
                a=source_support(np.asarray(r['canonicalCurve']),r['eye'],layers,visibility)
                details.append({'eye':r['eye'],**{k:v for k,v in a.items()if k not in('colour','identity','mask')}})
                cc[a['mask']]=a['colour'][a['mask']];ci[a['mask']]=a['identity'][a['mask']];cm|=a['mask']
            info=m['forward102']['nativeRegistration'];anchor=np.array(info['anchor'])+np.array(info['bounds'][:2]);roi=m['grid102']['eyeTopLeftROI']
            for y in range(eye.shape[0]):
                for x in range(eye.shape[1]):
                    absolute=np.array([roi[0]+x+.5,roi[1]+roi[3]-y-.5]);q=np.floor(absolute-anchor).astype(int)
                    if 0<=q[0]<w//4 and 0<=q[1]<h//4 and cm[q[1],q[0]]:
                        candidate[y,x]=cc[q[1],q[0]];co[y,x]=ci[q[1],q[0]]
        final,fo=hard_hair(candidate,co,hair,hmeta)
        if close!=100:assert np.array_equal(candidate,eye)and np.array_equal(final,oldFinal)
        row={'frame':e['frame'],'sourceId':m['sourceId'],'evaluatedClose':close,
          'beforeLidCells':int((owner[...,0]==7).sum()),'afterLidCells':int((co[...,0]==7).sum()),
          'changedEyeCells':int(np.any(candidate!=eye,axis=-1).sum()),'changes':[],'sourceProof':details,
          'finiteLidPaletteImplemented':False,'GPUcandidateImplemented':False}
        for y,x in np.argwhere(np.any(candidate!=eye,axis=-1)):
            row['changes'].append({'ROIbottomLeftXY':[int(x),int(y)],'beforeRGB8':rgb8(eye[y,x,:3]).tolist(),
              'afterRGB8':rgb8(candidate[y,x,:3]).tolist(),'owner':co[y,x].tolist()})
        rgba(final).save(D/f'OFFLINE_curve105-frame{e["frame"]}-1x.png')
        yy=100+j*305;draw.text((20,yy),f'frame {e["frame"]} · evaluated Close {close}',font=font(20),fill='white')
        for i,(a,title)in enumerate([(eye,'실제 GPU102 · 머리 가림 전'),(candidate,'오프라인 source-curve 후보'),(final,'오프라인 후보 + 같은 외부 머리 가림')]):
            im=rgba(a);scale=min(20,390//im.width,220//im.height);im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
            board.paste(im,(20+i*425,yy+36),im);draw.text((20+i*425,yy+248),title,font=font(16),fill='#bcd5e1')
        rows.append(row)
    result={'candidate':'offline complete-Close source-curve support only; product adoption pending',
      'frames':rows,'tests':tests(),'limitations':['native skin-ring vs lash pigment mapping not authored',
      'open eye2 sample check exceeded 0.0005px; tolerance unchanged','finite lid palette missing',
      'partial Close/rotation/actual temporal sequence not validated','cell count derives from source intersections, not a target']}
    (D/'CURVE_CANDIDATE105.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');board.save(D/'CLOSED_CURVE_CANDIDATE105.png')
    print(json.dumps({'frames':[{k:v for k,v in r.items()if k not in('changes','sourceProof')}for r in rows],
      'tests':result['tests'],'parts':[{k:v for k,v in d.items()if k!='proof'}for d in rows[1]['sourceProof']]},ensure_ascii=False))
if __name__=='__main__':main()
