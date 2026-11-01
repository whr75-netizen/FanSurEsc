from pathlib import Path
import json,sys,hashlib,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import Reader,rgb8
def read(path):
 r=Reader(path);assert r.s()=='feature-layer88-GPU/v1';source,frame,serial=r.s(),r.i(),r.i();w,h=r.i(),r.i();a=r.a(w*h*4).reshape(h,w,4);r.end();return {'sourceId':source,'frame':frame,'serial':serial},a
def main():
 run=HERE/'gpu88';gpu=json.loads((run/'GPU_RESULT88.json').read_text());assert gpu['dispatchComplete']and not gpu.get('error')and len(gpu['frames'])==24;folder=Path(gpu['output']);assert (folder/'DISPATCH_COMPLETE88.marker').exists();rows=[];pictures=[];diffs=[];allmax=0
 for frame in gpu['frames']:
  actual=[]
  for channel in range(3):
   h,a=read(folder/f"frame{frame['frame']}-{channel}.bin");assert h=={k:frame[k]for k in ['sourceId','frame','serial']};actual.append(a)
  ex=np.load(HERE/f"validated/frame{frame['frame']}/EXPECTED88.npz");errors=[]
  for actuala,key in zip(actual,['colour','identity','coverage']):
   delta=abs(actuala-ex[key]);allmax=max(allmax,float(delta.max()));bad=np.any(delta>1e-6,-1);errors.append({'field':key,'maxError':float(delta.max()),'changedPixels':int(bad.sum())})
   if bad.any():
    for yy,xx in np.argwhere(bad):diffs.append({'frame':frame['frame'],'field':key,'outputXY':[int(xx),int(yy)],'GPU':actuala[yy,xx].tolist(),'CPU':ex[key][yy,xx].tolist()})
  rows.append({'frame':frame['frame'],'sourceId':frame['sourceId'],'comparisons':errors});pictures.append((frame['frame'],actual[0]))
 before=json.loads((run/'CURRENT88.json').read_text());post=json.loads((run/'POST88.json').read_text());keys=['dirty','scenes','domain','playing','paused','optionsEnabled','options','timeScale','captureDeltaTime','graphicsPipelinePath','qualityPipelinePath','runInBackground','playerRunInBackground','input'];restore={k:before[k]==post[k]for k in keys};assert all(restore.values());assert len(gpu['nativeComparisons'])==45 and all(x['equal']is True for x in gpu['nativeComparisons']);assert gpu['before']['RTcount']==gpu['after']['RTcount']==30
 out={'status':'GPU_SAVED_INPUT_MATCH'if not diffs else'GPU_COMPARISON_FAILURE_NOT_ADOPTED','frames':rows,'maxAbsDifference':allmax,'differences':diffs,'stateEqual':restore,'nativeExact':45,'RTbeforeAfter':[30,30],'PlayEntries':gpu['PlayEntries'],'globalWrites':gpu['globalWrites'],'internalAllocatedDeltaMiB':(gpu['after']['allocated']-gpu['before']['allocated'])/1048576,'largestReadbackBytes':max(f['largestReadbackBytes']for f in gpu['frames']),'largestInputMaskBytes':max(f['maskBytes']for f in gpu['frames']),'limits':['Saved actual87 buffers supplied to isolated GPU; not a newly rendered scene or product integration.','Source-native lid remains an observed visibility layer; not an authored canonical pixel key-form.','Current4x sampled visibility still changes through pure phase. Intrinsic canonical invariance is not final temporal stability.']}
 q=HERE/'GPU_VALIDATION88.json';assert not q.exists();q.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['frames','stateEqual','differences']},indent=2));print('discrete/numeric differences',len(diffs));print(json.dumps(diffs[:8],indent=2))
 if not diffs:
  payload=json.dumps({'validationSHA256':hashlib.sha256(q.read_bytes()).hexdigest(),'status':'isolated GPU validated, no product activation'},indent=2);(folder/'VALIDATED88.marker').write_text(payload+'\n')
  # Real GPU pixels, never screenshots or simulated expected-image substitutes.
  imgs=[(f,a)for f,a in pictures if 124<=f<=133];h,w=imgs[0][1].shape[:2];sheet=Image.new('RGB',(w*10*len(imgs),h*10+22),'#171d24');dr=ImageDraw.Draw(sheet)
  for i,(frame,a)in enumerate(imgs):sheet.paste(Image.fromarray(rgb8(a[...,:3])).resize((w*10,h*10),Image.Resampling.NEAREST),(i*w*10,22));dr.text((i*w*10+3,3),f'{frame} actualGPU',fill='white')
  sheet.save(HERE/'GPU_VISIBLE88-nearest10.png')
if __name__=='__main__':main()
