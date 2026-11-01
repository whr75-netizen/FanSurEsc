from pathlib import Path
import json,hashlib,sys,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import plane
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import rgb8
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import read as eye_read
from provenance100 import trace

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def colours(v,mask):
 a=v[mask,:3];c=rgb8(a);return {'pixels':len(a),'uniqueLinearFloatRGB':len(np.unique(a,axis=0)),'uniqueSRGB8':len(np.unique(c,axis=0)),'RGB8List':np.unique(c,axis=0).tolist(),'partialAlphaPixels':int(((v[mask,3]>0)&(v[mask,3]<1)).sum())}
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
def main():
 cap=HERE/'capture';s=load(sorted(cap.glob('STATE100-*'))[-1]);assert s['stage']=='finished'and not s.get('error')and not s.get('restorationError')and s['PlayExited']and s['motionRestoration82']['allRestored'];out=HERE/'review';out.mkdir(exist_ok=True);reports=[];images=[]
 parts={'face_skin':4,'iris':2,'sclera':5,'native_lid':7,'brow':6,**{'source_role'+str(i):i+1 for i in range(7,15)}}
 bank=np.load(HERE/'TEMPLATE_REFERENCE100.npz')
 for e in s['sequencePackets']:
  p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');assert(p/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest();a={};heads={}
  for f in p.glob('*.plane'):
   h,v=plane(f);assert h['sourceId']==m['sourceId']and h['frameIndex']==e['frame']and h['renderSerial']==e['serial']and np.isfinite(v).all();a[f.stem]=v;heads[f.stem]=h
  roles=a['H-sourceMETA'][...,1];hair=int(((roles>=12)&(roles<=15)&(a['H-sourceMETA'][...,0]>0)).sum());assert hair==0 if e['stageIndex82']==1 else hair>0
  r={'stage':e['testStage82'],'frame':e['frame'],'sourceId':m['sourceId'],'product':77,'headHairSourceCells':hair,'stages':{},'lineChanges':{},'eyeSourceProvenance':[],'actualFinitePaletteLUTConfigured':False,'paletteOutsideDefinition':'No finite P[k] LUT is configured in product77. Source RGB-set membership is a diagnostic, not membership in an invented global palette.'}
  stages=[('source-original','H-sourceOriginal','H-sourceMETA',1,0),('source-shader','H-sourceRGBA','H-sourceMETA',1,0),('prepare-before-style','H-prepare-before-style','H-palette-owner',0,2),('head-palette-before-line','H-palette-before-lines','H-palette-owner',0,2),('main-palette-before-line','M-palette-before-lines','M-palette-owner',0,2),('main-after-line','M-after-lines','M-palette-owner',0,2),('main-after-eyes','M-after-eyes','M-final-owner',0,2),('native-final','native-final','native-owner',0,2),('eye348-selected','eye-output','eye-owner',0,2)]
  for name,cname,oname,rolech,depthch in stages:
   v=a[cname];own=a[oname];r['stages'][name]={k:colours(v,(np.rint(own[...,rolech])==role)&(own[...,depthch]>0)&(v[...,3]>0))for k,role in parts.items()}
  for name,role in parts.items():
   b=a['M-palette-before-lines'];l=a['M-after-lines'];own=a['M-palette-owner'];mask=(np.rint(own[...,0])==role)&(own[...,2]>0)&(b[...,3]>0);delta=mask&np.any(b[...,:3]!=l[...,:3],axis=-1);source={tuple(x)for x in rgb8(b[mask,:3])};lc=rgb8(l[delta,:3]);outside=[tuple(x)not in source for x in lc];coords=[]
   for y,x in np.argwhere(delta):coords.append({'mainAbsoluteXY':[int(x+m['grid100']['mainROI'][0]),int(y+m['grid100']['mainROI'][1])],'beforeLinear':b[y,x].tolist(),'afterLinear':l[y,x].tolist(),'beforeRGB8':rgb8(b[y,x,:3]).tolist(),'afterRGB8':rgb8(l[y,x,:3]).tolist(),'owner':own[y,x].tolist()})
   r['lineChanges'][name]={'changedPixels':int(delta.sum()),'changedPixelsOutsideSameFramePreLineRGB8Set':sum(outside),'coordinates':coords}
  _,z=eye_read(p/'eye-records100.bin.partial',False);z=z.reshape(z.shape[0],z.shape[1],16,4)
  # Visibility representative and pigment source are separate producers.
  # ComposedSource76 preserves295: compare actual pigment/atlas provenance.
  r['eyeSourceProvenance']=trace(z,a,bank)
  mask=(np.rint(a['H-sourceMETA'][...,1])==4)&(a['H-sourceMETA'][...,0]>0)
  r['faceQValues']=np.unique(a['H-style3'][mask,0]).tolist()
  r['lineSettings']=m['lineSettings100'];r['sourceViewMatrices']=m['grid100'];reports.append(r)
  im=Image.fromarray(np.flipud(rgb8(a['native-final'][...,:3])));im.save(out/(e['testStage82']+'-native1x.png'));im.resize((im.width*8,im.height*8),Image.Resampling.NEAREST).save(out/(e['testStage82']+'-nearest8.png'));images.append(im)
 save(HERE/'COLOUR_STAGES100.json',reports)
 w=1200;canvas=Image.new('RGB',(w,850),'#20242a');d=ImageDraw.Draw(canvas);d.text((20,12),'제품77 실제 캡처 — 머리카락 켬 / 끔 / 원래 상태 복구',font=font(24),fill='white');d.text((20,52),'원본 메시 데이터 유지 · runtime draw 범위만 임시 억제 · 실험98/99 미사용',font=font(17),fill='#bcd1dc')
 for i,(im,r)in enumerate(zip(images,reports)):
  x=20+396*i;d.text((x,96),['머리카락 켬','머리카락 끔','원래 상태 복구'][i]+f' — frame{r["frame"]}',font=font(20),fill='#9dd7ff');d.text((x,130),f'실제 머리카락 표본 {r["headHairSourceCells"]}셀',font=font(16),fill='white');d.text((x,161),'원배율1:1',font=font(16),fill='white');canvas.paste(im,(x,190));d.text((x,310),'동일 ROI nearest ×4',font=font(16),fill='white');canvas.paste(im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST),(x,345))
 d.text((20,796),'양자화·외곽선·눈 색은 아래 단계별 수치로 별도 진단합니다. 미관 성공 판정이 아닙니다.',font=font(16),fill='#ffd18a');canvas.save(out/'HAIR_ON_OFF_RESTORED100.png')
 print(json.dumps([{'stage':r['stage'],'hair':r['headHairSourceCells'],'faceRGB8':[r['stages'][k]['face_skin']['uniqueSRGB8']for k in ['source-original','main-palette-before-line','main-after-line','native-final']],'faceQ':r['faceQValues'],'lineChanged':{k:v['changedPixels']for k,v in r['lineChanges'].items()},'bankReferences':sum(x.get('RGB8EqualsSourceBank',False)for x in r['eyeSourceProvenance']),'bankMismatches':sum(x.get('RGB8EqualsSourceBank')is False for x in r['eyeSourceProvenance']),'retainedPre348':sum(x['control'][2]>0 for x in r['eyeSourceProvenance'])}for r in reports],ensure_ascii=False))
if __name__=='__main__':main()
