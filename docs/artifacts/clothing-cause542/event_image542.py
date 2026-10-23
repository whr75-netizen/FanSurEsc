from pathlib import Path
from PIL import Image,ImageDraw
import struct,numpy as np
O=Path(__file__).resolve().parent;R=O.parent/'Common540/FullLoop540'
def read(f,s):
 b=(R/f'{f:03d}_CLOTH_{s}.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',w*h*4,16).reshape(h,w,4);return a
for frames in [[64,65,66]]:
 board=Image.new('RGB',(864,600),'white');d=ImageDraw.Draw(board)
 for col,f in enumerate(frames):
  im=Image.open(R/f'{f:03d}_CLOTH.png').convert('RGB');body=im.crop((350,52,550,342));board.paste(body,(col*288,22));d.text((col*288+4,3),f'540 CLOTH ON actual Walk{f}',fill='black');zoom=im.crop((196*2,56*2,219*2,90*2)).resize((184,272),Image.Resampling.NEAREST);board.paste(zoom,(col*288,315));d.text((col*288+188,320),'LEFT\nelbow\n8x logical',fill='black')
 board.save(O/f'ELBOW_EVENT542_{frames[1]}.png')
 for col,f in enumerate(frames):
  d.rectangle((col*288+51,115,col*288+56,122),outline='#d63e28',width=1)
  d.rectangle((col*288+39,450,col*288+49,468),outline='#d63e28',width=1)
 board.save(O/f'ELBOW_EVENT542_{frames[1]}_MARKED.png')
