from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from analyse102 import load,save,buffer,rgb8
H=Path(__file__).resolve().parent
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
def main():
 s=load(sorted((H/'motionH').glob('STATE102-*'))[-1]);c=load(sorted((H/'captureH').glob('STATE102-*'))[-1]);validation=load(H/'HIERARCHY_VALIDATION102.json');assert not validation['CPUGPUSelectorMismatches']and not any(validation['unresolvedByFrame']);phase=[];phaseChanges=[]
 for e in s['sequencePackets'][:10]:
  a=buffer(Path(e['output'])/'canonical-colour.f32');ids=buffer(Path(e['output'])/'canonical-identity.f32');phase.append((e,rgb8(a[:,:3]),ids))
 base=phase[0][1]
 for e,a,ids in phase[1:]:
  for k in np.flatnonzero(np.any(a!=base,axis=1)):phaseChanges.append({'frame':e['frame'],'canonicalIndex':int(k),'part':int(round(ids[k,0])),'eye':int(round(ids[k,1])),'beforeRGB8':base[k].tolist(),'afterRGB8':a[k].tolist()})
 validation['phaseRGB8Variants']=len({hashlib.sha256(a.tobytes()).hexdigest()for _,a,_ in phase});validation['phaseRGB8Changes']=phaseChanges;validation['phaseColourStable']=not phaseChanges;save(H/'HIERARCHY_VALIDATION102.json',validation)
 # Compact real-render comparison. This is a subset of saved GPU frames, not
 # a re-render or a counterfactual generated from a different scene.
 entries=[('머리 OFF','captureH',c['sequencePackets'][0]),('머리 ON','captureH',c['sequencePackets'][1]),('실제 Close 100','captureH',c['sequencePackets'][5]),('재개방','captureH',c['sequencePackets'][7]),('실제 보행','motionH',s['sequencePackets'][10]),('실제 회전','motionH',s['sequencePackets'][19])]
 board=Image.new('RGB',(1200,1540),'#20252c');d=ImageDraw.Draw(board);d.text((20,12),'102: 눈 특징 전체 → 내부 파츠 → 외부 머리 가림',font=font(25),fill='white');d.text((20,52),'현재 제품77과 분리된 실제 GPU 후보. 셀 수/배치 하드코딩 없음.',font=font(18),fill='#f3c47a')
 for j,title in enumerate(['제품77','머리 가림 전 공동 배치','머리 이산 가림 후','머리 영역 참고 합성']):d.text((20+j*295,92),title,font=font(17),fill='white')
 for i,(title,dataset,e)in enumerate(entries):
  yy=130+i*210;d.text((20,yy),title+' / frame '+str(e['frame']),font=font(19),fill='white');folder=H/('reviewH'if dataset=='captureH'else'review-motionH')
  for j,n in enumerate(['product77','eye-before-hair','final-hard-hair','head-final']):
   im=Image.open(folder/f'{n}-frame{e["frame"]}-1x.png');scale=max(1,min(14,260//im.width,160//im.height));im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);board.paste(im,(20+j*295,yy+30),im)
 d.text((20,1410),'CPU/GPU 4,092셀 일치 · 위상/보행/회전 28프레임 미확정0 · Close/reopen 실제 기하 확인',font=font(17),fill='#bdd4df');d.text((20,1444),'남음: 닫힌 안검 1셀 표현, 안검 RGB8 1코드 변동, 얼굴/안검 UV region→finite P, 외곽선',font=font(17),fill='#f3c47a');d.text((20,1480),'미관 완성·제품 적용·모든 각도 안정성을 주장하지 않음. RGB 평균/잔상/색 혼합 없음.',font=font(16),fill='white');(H/'reviewH').mkdir(exist_ok=True);board.save(H/'reviewH/EYE_FORWARD_COMPARE102.png')
 frames=[]
 for e in s['sequencePackets']:
  p=H/'review-motionH'/f'final-hard-hair-frame{e["frame"]}-1x.png';im=Image.open(p);tile=Image.new('RGB',(480,310),'#20252c');draw=ImageDraw.Draw(tile);draw.text((12,10),e['testStage82']+' / frame '+str(e['frame']),font=font(19),fill='white');draw.text((12,38),'실제 GPU / 느리게 재생 / 단계 사이 warmup 간격 있음',font=font(14),fill='#f3c47a');scale=min(22,450//im.width,215//im.height);im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST);tile.paste(im,(12,75),im);frames.append(tile)
 frames[0].save(H/'reviewH/EYE_MOTION102.webp',save_all=True,append_images=frames[1:],duration=140,loop=0,lossless=True)
 post=load(H/'motionH/POST102.json');logs=load(H/'motionH/Post102_CONSOLE_AFTER.json')['data']['logs'];errors=[x for x in logs if x.get('type')in ['Error','Exception','Assert']];save(H/'PRESERVATION102.json',{'lastUTC':post['utc'],'Edit':not post['playing'],'dirty':len(post['dirty']),'inputSame':s['editInputRestoration82'],'nativeExact':sum(r['equal']is True for r in s['nativeComparisons72']),'nativeUnavailable':[r for r in s['nativeComparisons72']if r['equal']is None],'historicalUnavailableImporter':'Earlier captures47 baseline had temporary ProjectSettings AssetImporter unavailable on exit. Later baseline46 excludes that expired wrapper; actual PlayerSettings remained exact. No ClearDirty/save/reset.','RT':[s['beforeMemory']['renderTextureCount'],s['afterMemory']['renderTextureCount']],'newConsoleErrorLogTail':errors,'options':s['optionsRestored'],'time':s['timeRestored'],'pipeline':s['pipelineRestored'],'globals':s['globalRestoreErrors'],'PlayExited':s['PlayExited'],'productDefault':77,'currentCaptureCallsPending':False})
 print(json.dumps({'phaseRGB8Variants':validation['phaseRGB8Variants'],'phaseColourChanges':phaseChanges,'lastUnityUTC':post['utc'],'dirty':len(post['dirty']),'consoleErrorsInLatestTail':len(errors)},ensure_ascii=False))
if __name__=='__main__':main()
