from pathlib import Path
import json
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;G=H/'face40';A=G/'analysis-authored'
def main():
    result=json.loads((A/'ACTUAL_CONTOUR40.json').read_text());frames=[Image.open(A/('frame'+str(n)+'.png')).convert('RGB')for n in result['actualFrames']]
    out=Image.new('RGB',(1440,1060),(35,37,43));d=ImageDraw.Draw(out)
    d.text((12,10),'SOURCE CONTOUR 40 | actual GPU head ROI | 6 consecutive game-input frames',fill='white')
    d.text((12,30),'Each pair: existing product77 / isolated candidate. Native size + integer 8x nearest preview.',fill='white')
    for i,im in enumerate(frames):out.paste(im,((i%2)*720,60+(i//2)*310))
    d.text((12,1000),'Source dt=1/60 s; walk x3, turn x3 (~54 degrees). Original outline RGB is directly selected.',fill='white')
    d.text((12,1020),'NOT a final-face palette result. Variable line thickness, world occlusion and temporal art quality remain incomplete.',fill='white')
    out.save(G/'FACE_SOURCE_CONTOUR40.png')
    frames[0].save(G/'FACE_SOURCE_CONTOUR40_MOTION.webp',save_all=True,append_images=frames[1:],duration=200,loop=0,lossless=True)
    print(json.dumps({'image':'FACE_SOURCE_CONTOUR40.png','motion':'FACE_SOURCE_CONTOUR40_MOTION.webp','sourceDeltaTime':1/60,'previewFrameMs':200,'slowdown':12,'integerNearest':8}))
if __name__=='__main__':main()
