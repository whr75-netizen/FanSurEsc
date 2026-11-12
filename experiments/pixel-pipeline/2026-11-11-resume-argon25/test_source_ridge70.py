from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from source_ridge70 import detect,consistent
H=Path(__file__).resolve().parent;G=H/'face70'
def fixture(profile):
 a=np.full((65,65,4),255,np.uint8);a[:,:,:3]=np.uint8(np.rint(np.clip(profile,0,255)));return a
def main():
 G.mkdir(exist_ok=True);tests=[];yy,xx=np.indices((65,65));mask=np.ones((65,65),bool)
 gradient=np.stack([180+.4*xx,150+.3*xx,140+.2*xx],2)
 for name,image in [('rounded-gradient',fixture(gradient)),('AA-step',fixture(np.repeat((180+25*np.clip((np.arange(65)-30)/4,0,1))[None,:,None],65,0).repeat(3,2)))]:
  a=detect(image,mask,1);b=detect(image,mask,2);m=consistent(a,b);tests.append({'name':name,'strong':int(a['strong'].sum()),'persistent':int(m.sum())});assert not m.any(),tests[-1]
 line=gradient-np.exp(-((xx-32.2)/1.4)**2)[:,:,None]*[2,12,8];image=fixture(line);a=detect(image,mask,1);b=detect(image,mask,2);m=consistent(a,b);assert m[20:45,30:35].any();tests.append({'name':'faint-source-stroke','persistent':int(m.sum())})
 for mirror in[False,True]:
  for k in range(4):
   transform=lambda z:np.rot90(z[:,::-1]if mirror else z,k);v=transform(image);z=consistent(detect(v,mask,1),detect(v,mask,2));same=np.array_equal(z,transform(m));tests.append({'name':f'D4-{mirror}-{k}','exactMask':same});assert same,tests[-1]
 # Same input with a different tile size must not create tile seams.
 z=detect(image,mask,1,32);assert np.array_equal(z['strong'],a['strong']);tests.append({'name':'tile-seam','exact':True})
 npz=np.load(H/'face28/SOURCE_NATIVE28.npz');original=npz['rgba'];support=npz['mask'];a=detect(original,support,1);b=detect(original,support,2);m=consistent(a,b);np.savez_compressed(G/'RIDGE_EVIDENCE70.npz',persistent=m,strong1=a['strong'],strong2=b['strong'],nx=a['nx'],ny=a['ny'],px=a['px'],py=a['py'],margin=a['margin'])
 x,y=382,704;nearest=np.argwhere(m[max(0,y-4):y+5,max(0,x-4):x+5]);result={'CPUChecks':len(tests),'tests':tests,'realNativePersistentRidgePixels':int(m.sum()),'weakPaintWitnessXY':[x,y],'nativeWitnessRGBA':original[y,x].tolist(),'persistentWithin4TexelsOfWitness':bool(len(nearest)),'sourceRGBChanged':0,'semanticRegionsOrPaletteAssigned':0,'UnityGPUCalls':0,'interpretation':'Source stroke evidence only. No full Steger width/profile correction, semantic class, closed colour region or runtime RGB output is inferred.'};(G/'CPU_RIDGE70.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 box=(300,620,440,740);x0,y0,x1,y1=box;raw=original[y0:y1,x0:x1,:3];debug=raw.copy();debug[a['strong'][y0:y1,x0:x1]]=[255,160,20];debug[m[y0:y1,x0:x1]]=[0,210,240];board=Image.new('RGB',(840,420),(27,29,35));d=ImageDraw.Draw(board)
 for i,(im,title)in enumerate([(raw,'Native source, unchanged'),(debug,'Orange: scale1 | cyan: both scales')]):board.paste(Image.fromarray(im).resize((420,360),Image.Resampling.NEAREST),(420*i,30));d.text((420*i+8,8),title,fill='white')
 d.text((8,395),'CPU source-ridge evidence. No source recolour, blur output, whole-face region or art-success claim.',fill='white');board.save(G/'WEAK_STROKES70.png')
if __name__=='__main__':main()
