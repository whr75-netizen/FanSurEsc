"""Actual runtime GPU Q history versus a same-input CPU oracle.

No RGB output is fabricated. Images show the actual native control and actual
GPU label fields. Complete face-colour family segmentation is still separate.
"""
from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from selected_light84 import geometry
from shade_history85 import choose,prior_address
from audit_history85 import source_valid
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face85';C=G/'capture'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];previous=None;rows=[];panels=[];film=[]
 for f in r['stream77']['frames']:
  w,h=f['QROI'][2:];raw=decode((C/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];a=np.frombuffer(raw,'<f4').reshape(h,17,w,4).transpose(1,0,2,3);valid=source_valid(a);actual=a[16];assert np.array_equal(actual[:,:,3]==1,valid);expected=a[8,:,:,0].copy();old_values=expected.copy();used=np.zeros((h,w),bool);geo=geometry(C/f"geometry-frame{f['frame']}.bin");assert geo['frame']==f['frame']and geo['sourceId']==f['sourceId'];mapped=0;nohistory_flips=0;history_flips=0;visible_nohistory=0;visible_history=0;events=[]
  if previous is not None:
   old,oldf,oldg,oldvalid=previous;assert f['frame']==oldf['frame']+1
   for y,x in np.argwhere(valid):
    primitive=int(a[9,y,x,3]);uv=a[11,y,x,:2];pos,reason=prior_address(oldg,primitive,uv,oldf['QROI'])
    if pos is None:continue
    px,py=pos
    if not oldvalid[py,px]or not np.array_equal(old[9,py,px,1:],a[9,y,x,1:]):continue
    mapped+=1;previous_q=old[16,py,px,0];old_values[y,x]=previous_q;expected[y,x],used[y,x]=choose(expected[y,x],a[8,y,x,1],previous_q,f['light84']['faceSteps']);nflip=a[8,y,x,0]!=old[8,py,px,0];hflip=actual[y,x,0]!=previous_q;nohistory_flips+=int(nflip);history_flips+=int(hflip);visible=a[12,y,x,3]==1;visible_nohistory+=int(nflip and visible);visible_history+=int(hflip and visible)
    if used[y,x]:events.append({'localXY':[int(x),int(y)],'UV':uv.tolist(),'primitive':primitive,'previousLocalXY':[px,py],'g':float(a[8,y,x,1]),'rawQ':float(a[8,y,x,0]),'previousGPUQ':float(previous_q),'candidateGPUQ':float(actual[y,x,0]),'visibleOrdinary':bool(visible)})
  assert np.array_equal(actual[:,:,0],expected),('Q',f['frame'],np.argwhere(actual[:,:,0]!=expected).tolist());assert np.array_equal(actual[:,:,1],old_values),('prior Q',f['frame']);assert np.array_equal(actual[:,:,2]==1,used),('used',f['frame']);visible=a[12,:,:,3]==1
  row={'frame':f['frame'],'sourceId':f['sourceId'],'motion':f['motion']['stage'],'sourceValid':int(valid.sum()),'visibleFace':int(visible.sum()),'sameCarrierMapped':mapped,'historyUsed':int(used.sum()),'visibleHistoryUsed':int((used&visible).sum()),'sameInputNoHistoryQTransitions':nohistory_flips,'actualHistoryQTransitions':history_flips,'visibleNoHistoryQTransitions':visible_nohistory,'visibleHistoryQTransitions':visible_history,'events':events};rows.append(row)
  ims=[srgb(a[0])]
  for field in [a[8,:,:,0],actual[:,:,0]]:
   rgb=np.zeros((h,w,3),np.uint8);rgb[visible]=np.uint8(np.rint(field[visible,None]*255));ims.append(Image.fromarray(rgb[::-1]))
  diff=np.zeros((h,w,3),np.uint8);diff[used&visible]=[70,200,255];ims.append(Image.fromarray(diff[::-1]));panels.append((f,ims));small=Image.new('RGB',(w*8*3,h*8+24),(27,29,35));ImageDraw.Draw(small).text((3,3),f"Actual GPU F{f['frame']} | native / Q / Q history",fill='white')
  for j,im in enumerate(ims[:3]):small.paste(im.resize((w*8,h*8),Image.Resampling.NEAREST),(j*w*8,24))
  film.append(small);previous=a,f,geo,valid
 selected=[panels[i]for i in np.unique(np.linspace(0,len(panels)-1,min(8,len(panels))).astype(int))];board=Image.new('RGB',(1120,len(selected)*190+35),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(f,ims)in enumerate(selected):
  for j,(im,title)in enumerate(zip(ims,['Actual native RGB','Actual current Q','Actual GPU Q history','Changed visible Q'])):draw.text((j*280+3,i*190+3),f"F{f['frame']} {title}",fill='white');board.paste(im,(j*280+3,i*190+25));board.paste(im.resize((w*5,h*5),Image.Resampling.NEAREST),(j*280+40,i*190+25))
 draw.text((4,len(selected)*190+8),'Q fields only. Not a fabricated final colour rendering or complete face-palette/width result.',fill='white');board.save(G/'ACTUAL_Q_HISTORY85.png');film[0].save(G/'ACTUAL_Q_HISTORY85.webp',save_all=True,append_images=film[1:],duration=150,loop=0,lossless=True)
 result={'actualGPUFrames':len(rows),'allQPreviousValueAndUsageCPUOracleExact':True,'GPUReadsPreviousActualAtlas':True,'CPUSelectionUploaded':False,'RGBHistory':False,'historyUsed':sum(x['historyUsed']for x in rows),'visibleHistoryUsed':sum(x['visibleHistoryUsed']for x in rows),'sameInputNoHistoryQTransitions':sum(x['sameInputNoHistoryQTransitions']for x in rows),'actualHistoryQTransitions':sum(x['actualHistoryQTransitions']for x in rows),'newFinalRGBOrArtAdopted':False,'longTermStabilityProven':False,'restorationChecksPass':r['restorationChecksPass'],'ownedResourcesReleased':r['ownedResourcesReleased'],'rows':rows};(G/'ACTUAL_Q_HISTORY85.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':
 import sys
 if '--long'in sys.argv:G=G/'pulse120';C=G/'capture'
 main()
