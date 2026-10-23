from pathlib import Path
import struct,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent;R=O/'FullLoop'
def geometry(f):
 b=(R/f'{f:03d}_ALT_GEOMETRY.bin').read_bytes();at=0;groups=[]
 for _ in range(2):
  nr=struct.unpack_from('<i',b,at)[0];at+=4;rs=[]
  for k in range(nr):
   n=struct.unpack_from('<i',b,at)[0];at+=4;rs.append(np.frombuffer(b,'<f4',n*2,at).reshape(-1,2));at+=n*8
  groups.append(rs)
 return groups
def region(f):
 b=(R/f'{f:03d}_ALT_REGION.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',b);n=w*h;return(x,y,w,h),np.frombuffer(b,'<f4',n,16).reshape(h,w),np.frombuffer(b,'?',n,16+4*n).reshape(h,w)
def buf(f,tag,name):
 b=(R/f'{f:03d}_{tag}_{name}.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',b);q=np.zeros((272,480,4),np.float32);q[y:y+h,x:x+w]=np.frombuffer(b,'<f4',offset=16).reshape(h,w,4);return q
def crossing(rs,y):
 out=[]
 for r in rs:
  for a,b in zip(r,np.roll(r,-1,axis=0)):
   if min(a[1],b[1])<=y<max(a[1],b[1]):
    t=(y-float(a[1]))/(float(b[1])-float(a[1]));x=float(a[0])+t*(float(b[0])-float(a[0]))
    if 198<x<205:out.append({'x':x,'a':a.tolist(),'b':b.tolist()})
 return out
rows=[]
for f in[49,50,51]:
 source,curve=geometry(f);box,area,mask=region(f);bx,by,w,h=box
 rows.append({'frame':f,'crossings':[{'y':y,'source':crossing(source,y),'curve':crossing(curve,y)}for y in[96.5,97.5,98.5,99.5,100.5]],'candidateCells':[{'xy':[201,y],'area':float(area[y-by,201-bx]),'selected':bool(mask[y-by,201-bx])}for y in range(96,101)],'baseMetaAtRemoved':buf(f,'BASE','META')[97,201].tolist(),'altMetaAtRemoved':buf(f,'ALT','META')[97,201].tolist()})
# Diagnostic integer zoom only. No new gameplay capture or interpolation.
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13);panel=Image.new('RGB',(3*360,330),'white');d=ImageDraw.Draw(panel)
for col,f in enumerate([49,50,51]):
 d.text((col*360+5,4),f'Actual Walk {f}: 527 control / 532 trial',fill='black',font=font)
 for k,tag in enumerate(['BASE','ALT']):
  crop=Image.open(R/f'{f:03d}_{tag}.png').crop((198*2,94*2,207*2,104*2)).resize((162,180),Image.Resampling.NEAREST);panel.paste(crop,(col*360+5+k*175,30))
  meta=buf(f,tag,'META');rgba=buf(f,tag,'FINAL');lines=[]
  for y in range(95,102):
   ids=np.flatnonzero(rgba[y,:,3]>.5);lines.append(str(int(ids[0]))if len(ids)else'-')
  d.text((col*360+5+k*175,220),tag+' left x by rows95..101',fill='black',font=font);d.text((col*360+5+k*175,242),','.join(lines),fill='black',font=font)
 d.text((col*360+5,275),'native 2x pixels enlarged by integer9',fill='black',font=font)
panel.save(O/'FIRST_NEW_NOTCH50_533.png')
j={'status':'NEW_SHORT_RETURN_IN_SELECTED_SILHOUETTE_CONFIRMED_AT50','pointRemoved':[201,97],'neighborProtrusionCells':[[201,98],[201,99]],'notOutsideGateLeak':True,'noAutomaticPatch':True,'rows':rows,'limits':'This saved-output test identifies the new spatial notch; it does not certify the best curve/cluster design or apply a new research term.'}
(O/'FIRST_NEW_NOTCH50_533.json').write_text(json.dumps(j,indent=2));print(json.dumps(j))
