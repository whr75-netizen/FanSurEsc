"""Frame/source comparisons; unknown geometry remains unknown."""
from pathlib import Path
import json,sys,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from report_full24 import read,full,rgba,buffer,plane,H

def analyse(root):
 s=read(next(root.glob('STATE113-*-finished.json')));result=read(root/'RESULT_FULL24.json');rows=[]
 for i,pkt in enumerate(s['sequencePackets']):
  p=Path(pkt['output']);m=read(p/'RAW_MANIFEST.json');owner=plane(p/'F-FinalOwner.plane')[1]
  h,w=owner.shape[:2];depth=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4)
  visibility=buffer(p/'ASSIGNED-visibility24.f32').reshape(h,w,16,4)
  unknown=[]
  for y,x in np.argwhere(owner[:,:,3]==-116):
   q=depth[y,x];v=visibility[y,x];rect=result['frames'][i]['pixelRectBottomLeft']
   unknown.append({'tile':[int(x),int(y)],'fullPixelBottomLeft':[rect[0]+int(x),rect[1]+int(y)],'validDepthSamples':int(np.sum(q[:,2]>0)),
                   'depth':q[:,2].tolist(),'depthProvenanceStatus':v[:,3].tolist(),'finalOwner':owner[y,x].tolist()})
  rows.append({'sourceId':pkt['sourceId'],'frame':pkt['frame'],'serial':pkt['serial'],'stage':pkt['testStage82'],'index':pkt['stageIndex82'],
               'unknownCarrier':unknown,'confirmedBlockedCells':int(np.sum(owner[:,:,3]==-117)),
               'renderErrorFlags':m['regionErrorFlags113'],'evaluatedError':m['motion82'].get('evaluatedVsOwnedBakeMax'),
               'paletteRGB8Errors':sum(q['paletteRGB8Errors']for q in result['frames'][i]['finalVisibleParts'])})
 return rows,s,result

def animation(root,label,name):
 rows,s,result=analyse(root);frames=[];font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',19)
 for i,(pkt,row)in enumerate(zip(s['sequencePackets'],rows)):
  a=Image.new('RGB',(1000,485),'#18202a');d=ImageDraw.Draw(a)
  d.text((12,8),f'{label} | 실제 frame {pkt["frame"]} / serial {pkt["serial"]} | {pkt["testStage82"]} {pkt["stageIndex82"]}',font=font,fill='white')
  for col,variant in enumerate(['control','candidate']):
   x=12+col*490;d.text((x,42),'제품77'if col==0 else'격리 runtime24',font=font,fill='white')
   im=Image.open(root/'results'/f'{i:02d}-{variant}.png').convert('RGB');a.paste(im,(x,70))
   eye=Image.open(root/'results'/f'{i:02d}-{variant}-eye.png').convert('RGB');a.paste(eye,(x,345))
  d.text((550,362),f'미확정 지지 표면: {len(row["unknownCarrier"])}셀',font=font,fill='#ffcc88')
  d.text((550,393),'실제 관측 순서 · 표시 시간 180ms',font=font,fill='#ffcc88')
  d.text((550,424),'전체 시간 안정성/미관 완성 판정 아님',font=font,fill='#ffcc88');frames.append(a)
 path=H/name;frames[0].save(path,save_all=True,append_images=frames[1:],duration=180,loop=0,lossless=True,method=4)
 return rows

q=H/'sequence24';m=H/'motion24'
close=animation(q,'Close / reopen / hair','GPU_RUNTIME24_CLOSE_HAIR.webp')
motion=animation(m,'위상 / 보행 / 회전','GPU_RUNTIME24_MOTION.webp')
s=read(next(m.glob('STATE113-*-finished.json')));packets=[Path(x['output'])for x in s['sequencePackets']]
ids=[buffer(p/'curve-identity.f32').reshape(-1,4)for p in packets[:10]]
col=[buffer(p/'curve-colour.f32').reshape(1,-1,4)for p in packets[:10]]
assert all(np.array_equal(x[:,:2],ids[0][:,:2])for x in ids)
phaseColourChanges=[int(np.sum(np.any(rgba(x)!=rgba(col[0]),axis=2)))for x in col]
raw=[read(p/'RAW_MANIFEST.json')['motion82']['worldRootProjectedRaw']for p in packets[:10]]
report={'actualRuntimeFrames':41,'separatePlayRuns':[1,12,28],
 'phaseCanonicalRoleOwnerStable':True,'phaseCanonicalRGB8Changed':phaseColourChanges,'measuredPhaseDelta':[x[0]-raw[0][0]for x in raw],
 'eyePaletteRGB8Errors':sum(x['paletteRGB8Errors']for x in close+motion),
 'closeMaxUnknown':max(len(x['unknownCarrier'])for x in close),'motionMaxUnknown':max(len(x['unknownCarrier'])for x in motion),
 'close':close,'motion':motion,'adoptedAsProductDefault':False,
 'remaining':['Close75 destination carrier missing1; no fabricated depth','turn destination carrier missing up to2','final physical occlusion changes visible white/lid under subpixel phase','whole face UV regions, finite palette and outline remain unfinished'],
 'GPUTimeMeasured':False,'historical115ResetCauseResolved':False}
(H/'REVIEW_FULL24.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items()if k not in ['close','motion']},ensure_ascii=False))
