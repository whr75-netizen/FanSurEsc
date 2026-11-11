"""Two-sided SOURCE colour extrema, not semantic labels or output filtering.

A fixed RGB direction certifies both flanks lie beyond the centre even under
independent half-code perturbations. Failure is unknown, never permission to
erase source data. Monotone two-colour AA has no such interior extremum.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parent;G=H/'face28'
DIRECTIONS=((1,0),(0,1),(1,1),(1,-1))

def extract(rgb,mask,radii=(1,2,4),tile=128):
 h,w=mask.shape
 scale=np.zeros((h,w),np.uint8);axes=np.zeros((h,w),np.uint8)
 scale_bits=np.zeros((h,w),np.uint8)
 strength=np.zeros((h,w),np.float32)
 for y0 in range(0,h,tile):
  for x0 in range(0,w,tile):
   y1=min(h,y0+tile);x1=min(w,x0+tile)
   yy,xx=np.mgrid[y0:y1,x0:x1];centre=rgb[y0:y1,x0:x1].astype(np.float64)
   for ri,radius in enumerate(radii):
    for bit,(dx,dy)in enumerate(DIRECTIONS):
     ax,ay=xx-dx*radius,yy-dy*radius;bx,by=xx+dx*radius,yy+dy*radius
     valid=(ax>=0)&(ay>=0)&(bx>=0)&(by>=0)&(ax<w)&(bx<w)&(ay<h)&(by<h)
     ax=np.clip(ax,0,w-1);bx=np.clip(bx,0,w-1);ay=np.clip(ay,0,h-1);by=np.clip(by,0,h-1)
     valid &= mask[y0:y1,x0:x1]&mask[ay,ax]&mask[by,bx]
     left=rgb[ay,ax].astype(float)-centre;right=rgb[by,bx].astype(float)-centre
     direction=(left+right)*.5;norm=np.linalg.norm(direction,axis=2)
     normal=direction/np.maximum(norm[...,None],1e-30)
     # Each flank-centre RGB delta can change by at most1 per channel.
     bound=abs(normal).sum(2)
     margin=np.minimum((left*normal).sum(2),(right*normal).sum(2))-bound
     certified=valid&(margin>1e-12)
     scale_bits[y0:y1,x0:x1][certified] |= np.uint8(1<<ri)
     previous=scale[y0:y1,x0:x1];active=certified&((previous==0)|(previous==radius))
     previous[active]=radius
     axes[y0:y1,x0:x1][active] |= np.uint8(1<<bit)
     strength[y0:y1,x0:x1][active]=np.maximum(strength[y0:y1,x0:x1][active],margin[active])
 return {'scale':scale,'axes':axes,'scaleBits':scale_bits,'margin':strength,'positive':scale>0}

def main():
 G.mkdir(exist_ok=True)
 p=G/'SOURCE_NATIVE28.npz';data=np.load(p);rgb=data['rgba'][...,:3];mask=data['mask']&(data['rgba'][...,3]==255)
 result=extract(rgb,mask)
 np.savez_compressed(G/'SOURCE_EXTREMA28.npz',**result)
 points=[]
 for x,y in [(382,704),(380,704),(384,704)]:
  points.append({'cropXY':[x,y],'RGB8':rgb[y,x].tolist(),'positiveTwoSidedExtremum':bool(result['positive'][y,x]),'firstNativeRadius':int(result['scale'][y,x]),'axisWitnessBits':int(result['axes'][y,x]),'nativeScaleWitnessBits':int(result['scaleBits'][y,x]),'marginAboveRoundoffBound':float(result['margin'][y,x]),'old64ThinRidge':bool(data['thinX'][y,x]or data['thinY'][y,x])})
 rgba=data['rgba'];view=Image.new('RGB',(690,300),'#202020');draw=ImageDraw.Draw(view)
 box=(310,620,425,710);source=Image.fromarray(rgba).crop(box).convert('RGB');debug=source.copy();pixels=np.array(debug)
 take=result['positive'][620:710,310:425];pixels[take]=[25,210,225]
 for i,(im,title)in enumerate([(source,'Native source'),(Image.fromarray(pixels),'Positive source extrema (cyan)')]):
  view.paste(im.resize((345,270),Image.Resampling.NEAREST),(i*345,25));draw.text((i*345+4,5),title,fill='white')
 view.save(G/'WEAK_SOURCE28.png')
 report={'inputSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'inputUnchanged':True,'radiiNativeTexels':[1,2,4],'directions':'4 unoriented lattice axes, D4 symmetric; no arbitrary winning orientation','positiveTexels':int(result['positive'].sum()),'points':points,
  'meaning':'Positive two-sided native-colour extremum evidence; no semantic identity or approved whole-region fill inferred. All other source fields/weak marks remain retained and unknown.',
  'notDone':['No source RGB blur/averaging/output colour edit','No minimum-area deletion or palette-family assignment','No forced closure of open contours','No threshold sweep or assertion that authored half-code marks are noise'],'UnityGPUCalls':0}
 (G/'SOURCE_EXTREMA28.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'positiveTexels':report['positiveTexels'],'points':points}))
if __name__=='__main__':main()
