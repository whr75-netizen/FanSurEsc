from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import packet,rgb8
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import plane

def checker(rgba):
 a=rgb8(rgba[...,:3]);h,w=a.shape[:2];y,x=np.mgrid[:h,:w];back=np.where(((x//2+y//2)%2)[...,None],np.array([50,55,65]),np.array([75,80,90]));return np.rint(a*rgba[...,3,None]+back*(1-rgba[...,3,None])).astype(np.uint8)
def main():
 state=json.loads(sorted((HERE/'capture91b').glob('STATE91*.json'))[-1].read_text());analysis=json.loads((HERE/'CAPTURE_ANALYSIS91B.json').read_text());board=Image.new('RGB',(980,570),'#141923');draw=ImageDraw.Draw(board);draw.text((12,8),'Current evaluated backing: geometry/alpha available; RGB control FAIL. Not adopted.',fill='white')
 stages=[0,5,7]
 for row,index in enumerate(stages):
  entry=state['sequencePackets'][index];d=packet(Path(entry['output']));m=d['m'];a=d['a'];sx,top,sw,sh=m['eyeFeature']['roiTopLeft'];rx,ry,rw,rh=d['roi'];x0=sx-rx;y0=272-top-sh-ry;cached=a['base-rgba'][y0:y0+sh,x0:x0+sw];pics=[('Cached base (already333)',cached),('Actual source S0 current4x',a['S0-rgba']),('Candidate current2x (colour differs)',a['current91-g2-0'])]
  y=45+row*168;draw.text((10,y),f'index{index} frame{entry["frame"]} Close getter{m["eyeFeature"]["closeMorphs"]["Fcl_EYE_Close"]}',fill='white')
  for col,(title,pic)in enumerate(pics):
   image=Image.fromarray(np.flipud(checker(pic)));w=sw*14;h=sh*14;board.paste(image.resize((w,h),Image.Resampling.NEAREST),(col*320+10,y+32));draw.text((col*320+10,y+16),title,fill='white')
  meta=a['current91-g2-1'];Image.fromarray(np.flipud(checker(a['current91-g2-0']))).save(HERE/f'backing-index{index}-native2x.png')
  mask=((meta[...,0]>0)&(meta[...,1]==4)&(meta[...,3]>=.999)).astype(np.uint8)*255;Image.fromarray(np.flipud(mask)).save(HERE/f'backing-index{index}-skinmask2x.png')
 board.save(HERE/'BACKING_COMPARISON91.png')
 # Actual normal-producer probe, frame101; no reinterpretation as a final eye RGB.
 s=json.loads(sorted((HERE/'capture92').glob('STATE92*.json'))[-1].read_text());entry=s['sequencePackets'][-1];path=Path(entry['output']);a={p.stem:plane(p)[1]for p in path.glob('*.plane')};valid=a['S3-meta'][...,0]>0;actual=a['S3-shade'][...,0];manual=a['current91-g0-4'][...,0];diff=abs(actual-manual);canvas=Image.new('RGB',(1000,390),'#141923');dr=ImageDraw.Draw(canvas)
 for col,(title,v)in enumerate([('Actual RenderGraph g (0..1)',actual),('endCamera manual g (0..1)',manual),('abs difference /0.07 (display only)',diff/.07)]):
  value=np.rint(np.clip(v,0,1)*255).astype(np.uint8);value[~valid]=0;im=Image.fromarray(np.flipud(value)).convert('RGB');im.save(HERE/f'lighting-field{col}-1x.png');canvas.paste(im.resize((256,144),Image.Resampling.NEAREST),(col*330+12,45));dr.text((col*330+12,20),title,fill='white')
 dr.text((12,215),'Same frame101/serial8; primitive110; sample memory(6,17).',fill='white');dr.text((12,240),'normal equal; SH both0; available0.12232020 equal.',fill='white');dr.text((12,265),'Actual mainLit0.02909740 / manual mainLit0.02143633.',fill='white');dr.text((12,290),'Actual g0.23787895 / manual g0.17524764. Main-light context differs.',fill='white');dr.text((12,325),'SH binding changes the model and does not restore equivalence. No RGB gain applied.',fill='white');dr.text((12,350),'In-graph fix is not GPU-validated: attachment failure followed by URP job errors.',fill='#ffb587');canvas.save(HERE/'LIGHTING_COMPARISON92.png')
 result=json.loads((HERE/'VISIBILITY_RESULT91.json').read_text());im=Image.new('RGB',(1050,260),'#141923');dr=ImageDraw.Draw(im);dr.text((10,10),'Remaining56 native pixels:36 backing missing +20 eyeline source-visibility unknown',fill='white')
 dr.text((10,40),'Canonical raster cell    Line samples    Actually occluded    Upper line mass/16    Decision',fill='white')
 for i,c in enumerate(result['cells']):
  outcome='background proven (4 native pixels)'if c['decision']['winner']==0 else'unknown: foreign geometry absent for old source';colour='#8ee0bb'if c['decision']['winner']==0 else'#ffcf81'
  for x,value in[(10,str(c['rasterCell'])),(200,str(c['candidateSamples'])),(350,str(c['definitelyOccludedLineSamples'])),(520,f'{c["decision"]["massBounds"]["6"][1]:.6f}'),(680,outcome)]:dr.text((x,70+i*30),value,fill=colour)
 dr.text((10,235),'No unknown was treated as transparent; no new final RGB or whole-cell silhouette deletion.',fill='white');im.save(HERE/'VISIBILITY_TABLE91.png')
 print('Created actual source/backing comparison, lighting fields, and uncertainty table. No product rendering.')
if __name__=='__main__':main()
