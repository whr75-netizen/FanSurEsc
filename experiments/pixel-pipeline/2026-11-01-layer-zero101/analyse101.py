from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'apply-capture66'));from analyse_capture68 import plane,rgb8
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
def rgba(a):
 b=np.zeros_like(a,dtype=np.uint8);b[...,:3]=rgb8(a[...,:3]);b[...,3]=np.where(a[...,3]>0,255,0);return Image.fromarray(np.flipud(b))
def main():
 cap=H/'captureB';state=load(sorted(cap.glob('STATE101-*'))[-1]);assert state['stage']=='finished'and not state.get('error')and not state.get('restorationError')and state['PlayExited'];assert not any(x['equal']is False for x in state['nativeComparisons72']);out=H/'review';out.mkdir(exist_ok=True);results=[];images=[]
 for packet in state['sequencePackets']:
  p=Path(packet['output']);m=load(p/'RAW_MANIFEST.json');assert(p/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest();a={}
  for f in p.glob('*.plane'):
   meta,v=plane(f);assert meta['sourceId']==m['sourceId']and meta['frameIndex']==packet['frame']and meta['renderSerial']==packet['serial']and np.isfinite(v).all();a[f.stem]=v
  c=a['L0-RGBA'];z=a['L0-META'];q=a['L0-LIGHT'];isproxy=(z[...,0]>0)&(z[...,1]>.5);covered=(z[...,0]>0)&(c[...,3]>0)
  reference=np.zeros_like(covered)
  for i in [0,1,2]:reference|=(a[f'S{i}-meta'][...,0]>0)&(a[f'S{i}-meta'][...,3]>1e-6)
  missing=reference&~covered;errors=[];cols=[]
  for eye in m['layer101Source']['eyes']:
   eid=eye['eyeId'];mask=isproxy&(np.rint(z[...,2])==eid);rgb=rgb8(c[mask,:3]);ks=np.rint(q[mask,1]).astype(int);palette=np.array(eye['paletteRGB8'],dtype=np.uint8);bad=(ks<0)|(ks>=len(palette));assert not bad.any();mismatch=np.any(rgb!=palette[ks],axis=1)
   errors.extend([[int(y),int(x)]for y,x in np.argwhere(mask)[mismatch]]);cols.append({'eyeId':eid,'samples':int(mask.sum()),'referenceRGB8':eye['referenceRGB8'],'paletteRGB8':eye['paletteRGB8'],'observedRGB8':np.unique(rgb,axis=0).tolist(),'outsideExactConfiguredPalette':int(mismatch.sum()),'kRange':[int(ks.min()),int(ks.max())]if len(ks)else None})
  er=m['grid101']['eyeTopLeftROI'];hr=m['grid101']['headROI'];x=er[0]-hr[0];y=(272-er[1]-er[3])-hr[1];control=a['H-product77-final'][y:y+er[3],x:x+er[2]];preview=c[1::4,1::4];assert control.shape==preview.shape
  # Diagnostic preview uses one declared 4x sample per logical cell. It is not
  # whole-eye joint allocation, coverage majority, AA, or a product replacement.
  combined=a['H-product77-final'].copy();sub=combined[y:y+er[3],x:x+er[2]];ok=preview[...,3]>0;sub[ok]=preview[ok]
  stage=packet['stageIndex82'];rgba(control).save(out/f'product77-{stage}-1x.png');rgba(preview).save(out/f'canvas-{stage}-1x.png');rgba(combined).save(out/f'head-canvas-{stage}-1x.png');rgba(c).save(out/f'canvas-{stage}-4x-samples.png')
  maskimage=np.zeros_like(c);maskimage[covered]=[.15,.15,.15,1];maskimage[isproxy]=[.4,.8,.3,1];maskimage[missing]=[1,0,1,1];rgba(maskimage).save(out/f'coverage-{stage}.png')
  hair=int(((a['H-sourceMETA'][...,1]>=12)&(a['H-sourceMETA'][...,1]<=15)&(a['H-sourceMETA'][...,0]>0)).sum());results.append({'stage':packet['testStage82'],'frame':packet['frame'],'sourceId':m['sourceId'],'hairSourceCells':hair,'referenceSamples':int(reference.sum()),'canvasSamples':int(covered.sum()),'socketProxySamples':int(isproxy.sum()),'referenceCoveredButCanvasMissing':int(missing.sum()),'missingXYBottomLeft':np.argwhere(missing)[:,::-1].tolist(),'proxyPalette':cols,'paletteErrorsXY':errors,'nativeFaceUniqueRGB8':int(len(np.unique(rgb8(c[covered&~isproxy,:3]),axis=0))),'fullFaceFinitePaletteImplemented':False})
  images.append((rgba(control),rgba(preview),rgba(combined),rgba(maskimage)))
 assert len(results)==3 and [r['hairSourceCells']>0 for r in results]==[True,False,True]
 board=Image.new('RGB',(1200,950),'#20252c');d=ImageDraw.Draw(board);d.text((20,12),'101: 구버전 눈을 입력받지 않는 Layer0 — 격리 GPU 시험',font=font(24),fill='white');d.text((20,48),'눈 전체 공동 배치·얼굴 전체 유한 팔레트·미술 완성은 아직 아님',font=font(17),fill='#f4c876')
 headings=['제품77 눈','새 얼굴 바탕 (1/4표본 미리보기)','참고 합성 (머리 가림 미적용)','4x coverage: 초록=피부 proxy']
 for j,title in enumerate(headings):d.text((20+j*295,85),title,font=font(15),fill='white')
 for i,imgs in enumerate(images):
  yy=115+i*265;d.text((20,yy),['머리 ON','머리 OFF','원상 복원'][i]+f' / frame {results[i]["frame"]}',font=font(18),fill='white')
  for j,im in enumerate(imgs):
   scale=min(10,260//im.width,205//im.height);scale=max(1,scale);im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);board.paste(im,(20+j*295,yy+32),im)
 d.text((20,916),'색 블러·피부 주변 RGB 추정·이전 눈 결과 복사는 없음. native 얼굴은 원색 진단 출력.',font=font(16),fill='#bcd0d9');board.save(out/'LAYER0_COMPARE101.png')
 summary={'candidate':'101 isolated Layer0 only','productDefault':77,'firstAttempt':'capture/ failed before image: missing additional camera data; restored; default existing URP renderer link fixed','successfulPlayEntries':state['PlayEntries'],'states':results,'serializedExact':sum(x['equal']is True for x in state['nativeComparisons72']),'serializedUnavailable':[x for x in state['nativeComparisons72']if x['equal']is None],'serializedDifferent':[x for x in state['nativeComparisons72']if x['equal']is False],'inputRestored':state['editInputRestoration82'],'motionRestored':state['motionRestoration82'],'optionsRestored':state['optionsRestored'],'timeRestored':state['timeRestored'],'pipelineRestored':state['pipelineRestored'],'globalRestoreErrors':state['globalRestoreErrors'],'PlayExited':state['PlayExited'],'RTBeforeAfter':[state['beforeMemory']['renderTextureCount'],state['afterMemory']['renderTextureCount']],'missingFullEyeLayer':True,'fullFaceRegionResolverPending':True,'actualMotionNotTested':True}
 save(H/'RESULT101.json',summary);print(json.dumps({'states':len(results),'missingCoverage':[r['referenceCoveredButCanvasMissing']for r in results],'proxyPaletteViolations':[sum(v['outsideExactConfiguredPalette']for v in r['proxyPalette'])for r in results],'sourceReferences':[[x['referenceRGB8']for x in r['proxyPalette']]for r in results],'serializedExact':summary['serializedExact'],'serializedUnavailable':summary['serializedUnavailable'],'RT':summary['RTBeforeAfter']},ensure_ascii=False))
if __name__=='__main__':main()
