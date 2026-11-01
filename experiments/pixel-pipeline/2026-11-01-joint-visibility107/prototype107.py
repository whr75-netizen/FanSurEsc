from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer,components,rgba,font
sys.path.insert(0,str(R/'live-curve106'));from analyse106 import curve_segments
from joint_reference107 import apply,tests
def main():
    states=load(sorted((R/'live-curve106/capture').glob('STATE106-*'))[-1]);rows=[];images=[]
    for e in states['sequencePackets']:
        p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');w,h=m['forward102']['canonicalSize'];a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);v=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
        base=[buffer(p/f'canonical-{k}.f32')for k in ['colour','identity','decision']];s=curve_segments(p/'curve-segments106.f32');c,i,d,audit=apply(s,a,v,*base)
        ids=i.reshape(h//4,w//4,4);bc=base[0].reshape(h//4,w//4,4);cc=c.reshape(h//4,w//4,4)
        row={'frame':e['frame'],'stage':e['testStage82'],'counts':{str(role):int((i[:,0]==role).sum())for role in [1,4,6]},'lid4':{str(eye):components((ids[...,0]==6)&(ids[...,1]==eye))for eye in [1,2]},'audit':{str(k):int((audit[:,0]==k).sum())for k in [-4,-3,-2,-1,0,3,4]}}
        rows.append(row)
        if e['frame']in [99,101,103,107,192]:images.append((row,bc,cc))
    board=Image.new('RGB',(1060,len(images)*240+70),'#20252c');dr=ImageDraw.Draw(board);dr.text((20,10),'107 CPU 가설 검사 · 실제 GPU 전 / 동결106 입력 / 채택 아님',font=font(23),fill='white')
    for j,(r,b,c)in enumerate(images):
        y=60+j*240;dr.text((20,y),str(r),font=font(13),fill='white')
        for x,a in [(20,b),(550,c)]:
            im=rgba(np.flipud(a));im=im.resize((im.width*20,im.height*20),Image.Resampling.NEAREST);board.paste(im,(x,y+30),im)
    board.save(H/'CPU_PROTOTYPE107.png');(H/'CPU_PROTOTYPE107.json').write_text(json.dumps({'tests':tests(),'frames':rows},indent=2)+'\n',encoding='utf-8');print(json.dumps({'tests':tests(),'selected':[r for r in rows if r['frame']in [99,101,103,107,192]]}))
if __name__=='__main__':main()
