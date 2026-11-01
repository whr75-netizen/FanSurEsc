from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from analyse89 import Reader,rgb8
HERE=Path(__file__).resolve().parent
def load(path):
 r=Reader(path);assert r.s()=='final-palette89-GPU/v1';identity=[r.s(),r.s(),r.i(),r.i()];w,h=r.i(),r.i();a=r.a(w*h*4).reshape(h,w,4);r.end();return identity,a
def main():
 root=HERE/'final-gpu89';g=json.loads((root/'FINAL_GPU89.json').read_text());assert g['dispatchComplete']and not g.get('error');gpu=Path(g['output']);assert(gpu/'DISPATCH_COMPLETE89.marker').exists();index=json.loads((HERE/'final-input89/INPUT_INDEX89.json').read_text());out=HERE/'final89';out.mkdir(exist_ok=False);frames={};validation=[]
 for row in index:
  stem=Path(row['file']).stem;expected=np.load(HERE/'final-input89'/(stem+'-expected.npz'));actual=[]
  for ch,key in enumerate(['colour','owner','valid']):
   identity,a=load(gpu/(stem+f'-{ch}.bin'));assert identity==[row['sourceId'],row['variant'],row['frame'],next(x['serial']for x in g['rows']if x['frame']==row['frame'])];assert np.array_equal(a,expected[key]),(stem,key,float(abs(a-expected[key]).max()));actual.append(a)
  scope=expected['scope'];invalid=expected['invalid'];assert not(scope&expected['protected']).any();assert not(scope&expected['foreground']).any();c=actual[0];P=expected['palette'];assert all(any(np.array_equal(v,p)for p in P)for v in np.unique(c[scope],axis=0));im=np.flipud(np.concatenate([rgb8(c[...,:3]),np.rint(np.clip(c[...,3:4],0,1)*255).astype(np.uint8)],-1));Image.fromarray(im).save(out/(stem+'-native.png'));Image.fromarray(im).resize((im.shape[1]*8,im.shape[0]*8),Image.Resampling.NEAREST).save(out/(stem+'-nearest8.png'))
  debug=np.flipud(rgb8(c[...,:3]));mask=np.flipud(invalid&scope);debug[mask]=[225,45,185];Image.fromarray(debug).save(out/(stem+'-invalid-debug.png'));validation.append({**row,'GPU_CPUFloatDifferences':0,'outsideScopeChanges':0,'paletteOutsideColours':0,'protectedChanges':0,'foregroundChanges':0,'interpretation':'Equality validates direct final LUT fill only. Invalid source/backing selections remain invalid.'});frames.setdefault(row['frame'],{})[row['variant']]={'rgba':im,'debug':debug,'row':row}
 # Original native output is the exact same actual capture; no simulated base.
 from analyse89 import packet
 state=json.loads(sorted((HERE/'capture89f').glob('STATE89*.json'))[-1].read_text());groups={};summary=[]
 for entry in state['sequencePackets']:
  d=packet(Path(entry['output']));frame=entry['frame'];original=np.flipud(rgb8(d['a']['native-final-rgba'][...,:3]));h,w=original.shape[:2];a=frames[frame];canvas=Image.new('RGB',(w*8*3,h*8+44),'#171d25');draw=ImageDraw.Draw(canvas)
  for col,(label,pic)in enumerate([('Actual product77',original),('Coupled - NOT ACCEPTED',a['coupled']['debug']),('Source ray - NOT ACCEPTED',a['ray-visible']['debug'])]):canvas.paste(Image.fromarray(pic).resize((w*8,h*8),Image.Resampling.NEAREST),(col*w*8,44));draw.text((col*w*8+4,5),label,fill='white')
  draw.text((4,23),f'frame {frame} {entry["testStage82"]}{entry["stageIndex82"]} | pink = indeterminate, NOT a palette colour',fill='#eaa4d5');name=f'{entry["testStage82"]}{entry["stageIndex82"]}-final-comparison8.png';canvas.save(out/name);Image.fromarray(original).save(out/f'{frame:04d}-actual77-native.png');groups.setdefault(entry['testStage82'],[]).append(canvas)
  summary.append({'frame':frame,'stage':entry['testStage82'],'index':entry['stageIndex82'],'comparison':name,'coupledInvalid':a['coupled']['row']['invalidNativePixels'],'rayInvalid':a['ray-visible']['row']['invalidNativePixels']})
 for stage,images in groups.items():
  images[0].save(out/(stage+'-final.gif'),save_all=True,append_images=images[1:],duration=400,loop=0)
  choose=list(range(len(images)))if len(images)<=8 else[0,1,3,5,7,9];strip=Image.new('RGB',(images[0].width,images[0].height*len(choose)),'#171d25')
  for y,i in enumerate(choose):strip.paste(images[i],(0,y*images[i].height))
  strip.save(out/(stage+'-final-strip.png'))
 result={'status':'GPU_LUT_EQUALITY_PASSED_UPSTREAM_CANDIDATE_NOT_ADOPTED','actualSavedFrames':32,'GPUreplayPackets':64,'GPUfieldsCompared':192,'GPU_CPUFloatDifferences':0,'paletteOutsideColours':0,'outsideScopeChanges':0,'protectedChanges':0,'foregroundChanges':0,'invalidSelectionNativePixels':sum(x['invalidNativePixels']for x in validation),'missingBackingNativePixels':sum(x['missingBackingNativePixels']for x in validation),'countsAreSummedOverFramesAndBothVariants':True,'jointAllocationGPUIntegrated':False,'runtimeDefaultChanged':False,'GPUreplayPlayEntries':0,'GPUreplayGlobalWrites':0,'GPUreplayResources':{'RTbefore':g['before']['RTcount'],'RTafter':g['after']['RTcount'],'internalAllocatedDeltaMiB':(g['after']['allocated']-g['before']['allocated'])/1048576,'physicalRAMMeasured':False},'frames':summary,'packets':validation,'limitations':['Pink pixels are debug overlays, not output palette colours. Literal palette PNGs are separate.','Joint selection is an offline candidate from actual GPU-source data. Final GPU replay tests finite LUT fill only.','Continuous illumination equivalence failed. Missing backing and unresolved source visibility prevent final acceptance.','The source-visible case retains a possible sclera fragment at fully evaluated Close in an indeterminate query; it is not a passed blink regression.','No product integration or complete temporal stability claim.']};(HERE/'FINAL_VALIDATION89.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['frames','packets']},indent=2))
if __name__=='__main__':main()
