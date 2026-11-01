from pathlib import Path
import json,sys,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'apply-capture66'));from analyse_capture68 import plane,rgb8
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rgba(v):
 a=np.zeros(v.shape,np.uint8);a[...,:3]=rgb8(v[...,:3]);a[...,3]=np.where(v[...,3]>0,255,0);return Image.fromarray(np.flipud(a))
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
def buffer(p):
 b=p.read_bytes();n,stride=struct.unpack_from('<ii',b);assert stride==16 and len(b)==8+n*16;return np.frombuffer(b,offset=8,dtype='<f4').reshape(n,4)
def components(mask):
 left=set(map(tuple,np.argwhere(mask)));sizes=[]
 while left:
  todo=[left.pop()];n=0
  while todo:
   y,x=todo.pop();n+=1
   for q in [(y+1,x),(y-1,x),(y,x+1),(y,x-1)]:
    if q in left:left.remove(q);todo.append(q)
  sizes.append(n)
 return sorted(sizes,reverse=True)
def main():
 mode=sys.argv[1:];assert mode in [[],['--motion'],['--hierarchy'],['--motion-hierarchy']];motion=mode in [['--motion'],['--motion-hierarchy']];hierarchy=mode in [['--hierarchy'],['--motion-hierarchy']]
 state=load(sorted((H/(('motion'if motion else'capture')+('H'if hierarchy else''))).glob('STATE102-*'))[-1]);assert state['stage']=='finished'and not state.get('error')and not state.get('restorationError')and state['PlayExited'];assert not any(x['equal']is False for x in state['nativeComparisons72']);out=H/(('review-motion'if motion else'review')+('H'if hierarchy else''));out.mkdir(exist_ok=True)
 bank=np.load(R/'hair-isolation100/TEMPLATE_REFERENCE100.npz');pal={role:{tuple(x)for x in bank['TemplateRGBA'][bank['TemplateRole'][...,0]==role,:3]}for role in [1,4]};reports=[];imgs=[]
 for e in state['sequencePackets']:
  p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');assert(p/'RAW_COMPLETE76.marker').read_text()==hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest();a={}
  for f in p.glob('*.plane'):
   h,v=plane(f);assert h['sourceId']==m['sourceId']and h['frameIndex']==e['frame']and h['renderSerial']==e['serial']and np.isfinite(v).all();a[f.stem]=v
  eye=a['F-EyeRGBA'];owner=a['F-EyeOwner'];final=a['F-FinalRGBA'];fowner=a['F-FinalOwner'];dec=buffer(p/'canonical-decision.f32');cid=buffer(p/'canonical-identity.f32');col=buffer(p/'canonical-colour.f32');role=np.rint(owner[...,0]).astype(int)
  parts={}
  for r,native in [(2,1),(5,4),(7,6)]:
   mask=(role==r)&(owner[...,2]>0);cs=rgb8(eye[mask,:3]);row={'visibleCells':int(mask.sum()),'components4':components(mask),'uniqueRGB8':np.unique(cs,axis=0).tolist(),'sourcePaletteOutside':None}
   if native in pal:row['sourcePaletteOutside']=sum(tuple(c)not in pal[native]for c in cs)
   parts[str(native)]=row
  overlay=np.any(final!=eye,axis=-1);viol=[]
  for y,x in np.argwhere(overlay):
   candidates=a['S4-rgba'][y*4:(y+1)*4,x*4:(x+1)*4,:3].reshape(-1,3);assert any(np.array_equal(c,final[y,x,:3])for c in candidates);assert 12<=round(float(fowner[y,x,0]))<=15
  er=m['grid102']['eyeTopLeftROI'];hr=m['grid102']['headROI'];x=er[0]-hr[0];y=272-er[1]-er[3]-hr[1];control=a['H-product77-final'][y:y+er[3],x:x+er[2]];combined=a['H-product77-final'].copy();sub=combined[y:y+er[3],x:x+er[2]];valid=final[...,3]>0;sub[valid]=final[valid]
  row={'frame':e['frame'],'sourceId':m['sourceId'],'stage':e['testStage82'],'stageIndex':e['stageIndex82'],'motion':m['motion82'],'parts':parts,'unresolvedCanonicalCells':int((dec[:,0]<0).sum()),'sourceCanonicalRoleCounts':{str(r):int((np.rint(cid[:,0])==r).sum())for r in [1,4,6]},'hardHairChangedCells':int(overlay.sum()),'hardHairRGBSourceExact':True,'eyeRGBSourcePaletteVerified':[1,4],'nativeLidPalettePending':True,'fullFaceRegionResolverPending':True,'changedPixels':[]}
  for yy,xx in np.argwhere(np.any(control!=final,axis=-1)):row['changedPixels'].append({'headXYBottomLeft':[int(er[0]+xx),int(272-er[1]-er[3]+yy)],'product77RGB8':rgb8(control[yy,xx,:3]).tolist(),'forwardRGB8':rgb8(final[yy,xx,:3]).tolist(),'eyeOwner':owner[yy,xx].tolist(),'finalOwner':fowner[yy,xx].tolist()})
  reports.append(row);panel=[rgba(control),rgba(eye),rgba(final),rgba(combined)];imgs.append(panel)
  for name,im in zip(['product77','eye-before-hair','final-hard-hair','head-final'],panel):im.save(out/f'{name}-frame{e["frame"]}-1x.png')
  # Use literal integer enlargement only.
  panel[2].resize((panel[2].width*16,panel[2].height*16),Image.Resampling.NEAREST).save(out/f'final-frame{e["frame"]}-nearest16.png')
 assert len(reports)==(28 if motion else 9)
 board=Image.new('RGB',(1200,152+len(reports)*238),'#20252c');d=ImageDraw.Draw(board);d.text((20,12),'102: clean Layer0 → 전체 눈 공동 배치 → 머리 이산 가림',font=font(23),fill='white');d.text((20,47),'격리 GPU 후보 / 제품77 유지 / 얼굴·안검 전체 팔레트 경로는 미완',font=font(17),fill='#f5c681')
 for j,title in enumerate(['제품77','새 눈 (머리 가림 전)','새 눈 + 머리 깊이/coverage','머리 영역 참고 합성']):d.text((20+j*295,82),title,font=font(16),fill='white')
 for i,panel in enumerate(imgs):
  row=reports[i];yy=112+i*238;label=(row['stage']+':'+str(row['stageIndex']) if motion else '머리 OFF'if i==0 else '머리 ON'if i==1 else 'Close='+str(row['motion']['requestedClose']))+f' / frame {row["frame"]}';d.text((20,yy),label,font=font(16),fill='white')
  for j,im in enumerate(panel):
   scale=max(1,min(14,260//im.width,185//im.height));im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);board.paste(im,(20+j*295,yy+28),im)
  d.text((20,yy+213),'홍채/흰자/안검: '+str([row['parts'][str(k)]['visibleCells']for k in [1,4,6]])+' · 미확정 canonical: '+str(row['unresolvedCanonicalCells']),font=font(14),fill='#bfced8')
 board.save(out/'FORWARD_EYE_COMPARE102.png');save(H/(('MOTION_FRAMES102'if motion else'FRAMES102')+('H'if hierarchy else'')+'.json'),reports)
 summary={'candidate':'102 isolated forward canvas','productDefault':77,'PlayEntries':state['PlayEntries'],'actualStates':len(reports),'sourceIrisScleraPaletteViolations':sum(sum(r['parts'][str(k)]['sourcePaletteOutside']for k in [1,4])for r in reports),'unresolvedByFrame':[r['unresolvedCanonicalCells']for r in reports],'eyeCellsByFrame':[[r['parts'][str(k)]['visibleCells']for k in [1,4,6]]for r in reports],'evaluatedClose':[r['motion'].get('requestedClose')for r in reports],'serializedExact':sum(x['equal']is True for x in state['nativeComparisons72']),'serializedUnavailable':[x for x in state['nativeComparisons72']if x['equal']is None],'input':state['editInputRestoration82'],'scopeRestore':state['motionRestoration82'],'options':state['optionsRestored'],'time':state['timeRestored'],'pipeline':state['pipelineRestored'],'globals':state['globalRestoreErrors'],'RTBeforeAfter':[state['beforeMemory']['renderTextureCount'],state['afterMemory']['renderTextureCount']],'PlayExited':state['PlayExited'],'productIntegrated':False,'fullFaceRegionResolverPending':True,'nativeLidFinitePalettePending':True,'rotationAndPhaseNotYetTested':not motion}
 save(H/(('MOTION_RESULT102'if motion else'RESULT102')+('H'if hierarchy else'')+'.json'),summary);print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
