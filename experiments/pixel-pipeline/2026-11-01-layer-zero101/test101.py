from pathlib import Path
import json,hashlib,zipfile,io,sys
import numpy as np
H=Path(__file__).resolve().parent
try:from reader68 import plane,rgb8
except ImportError:
 sys.path.insert(0,str(H.parent/'apply-capture66'));from analyse_capture68 import plane,rgb8
class Memory:
 def __init__(self,b):self.b=b
 def open(self,mode):assert mode=='rb';return io.BytesIO(self.b)
def main():
 archive=H if(H/'ARTIFACTS101.json').exists()else H/'archive';r=json.loads((archive/'RESULT101.json').read_text());assert r['productDefault']==77 and r['PlayExited']and not r['serializedDifferent']and r['serializedExact']==46 and len(r['serializedUnavailable'])==1 and r['RTBeforeAfter']==[30,30]and all(r[k]for k in ['optionsRestored','timeRestored','pipelineRestored'])and all(r['inputRestored'].values())
 total=0;states=[]
 with zipfile.ZipFile(archive/'RAW101.zip')as z:
  for folder in sorted({n.split('/')[0]for n in z.namelist()}):
   raw=z.read(folder+'/RAW_MANIFEST.json');m=json.loads(raw);assert z.read(folder+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(raw).hexdigest();a={}
   for n in z.namelist():
    if n.startswith(folder+'/')and n.endswith('.plane'):
     head,v=plane(Memory(z.read(n)));assert head['sourceId']==m['sourceId']and head['frameIndex']==m['frameIndex']and head['renderSerial']==m['mainSerial']and np.isfinite(v).all();a[Path(n).stem]=v;total+=1
   ref=np.zeros(a['L0-META'].shape[:2],bool)
   for i in [0,1,2]:ref|=(a[f'S{i}-meta'][...,0]>0)&(a[f'S{i}-meta'][...,3]>1e-6)
   valid=a['L0-META'][...,0]>0;assert not(ref&~valid).any();proxy=valid&(a['L0-META'][...,1]>.5)
   for eye in m['layer101Source']['eyes']:
    eid=eye['eyeId'];mask=proxy&(np.rint(a['L0-META'][...,2])==eid);k=np.rint(a['L0-LIGHT'][mask,1]).astype(int);pal=np.array(eye['paletteRGB8'],dtype=np.uint8);assert len(pal)==m['layer101Source']['steps'];assert(k>=0).all()and(k<len(pal)).all();assert np.array_equal(rgb8(a['L0-RGBA'][mask,:3]),pal[k]);assert eye['ringSamples']and eye['referenceSampleId'].startswith('native-vertex-')
   states.append(a)
 assert total==57 and len(states)==3
 phase={'RGBAChangesOnOff':int(np.any(states[0]['L0-RGBA']!=states[1]['L0-RGBA'],axis=-1).sum()),'coverageMaskChanges':int(np.count_nonzero((states[0]['L0-META'][...,0]>0)!=(states[1]['L0-META'][...,0]>0))),'maxDepthDifference':float(np.max(np.abs(states[0]['L0-META'][...,0]-states[1]['L0-META'][...,0]))),'maxGDifference':float(np.max(np.abs(states[0]['L0-LIGHT'][...,0]-states[1]['L0-LIGHT'][...,0]))),'QChanges':int(np.count_nonzero(states[0]['L0-LIGHT'][...,1]!=states[1]['L0-LIGHT'][...,1])),'limit':'Different frames, actual hair/shadow source also suppressed; not an identical-lighting A/B or temporal stability proof'}
 slots=0
 for n in range(2,9):
  g=np.concatenate([np.linspace(0,1,2049),[(i+.5)/(n-1)for i in range(n-1)]]).astype(np.float32);k=np.clip(np.floor(g*(n-1)+.5),0,n-1).astype(int);assert k.min()==0 and k.max()==n-1;assert np.all(k[np.argsort(g)][1:]>=k[np.argsort(g)][:-1]);slots+=len(g)
 for f in json.loads((archive/'ARTIFACTS101.json').read_text())['files']:assert hashlib.sha256((archive/f['path']).read_bytes()).hexdigest()==f['SHA256']
 out={'actualStates':3,'planes':total,'referenceCoverageMissing':0,'proxyOutsideConfiguredPalette':0,'Float32SlotSamples':slots,'nativeFaceFinitePaletteNotClaimed':True,'oldEyeNotInput':True,'threeFrameObservedDifferences':phase,'UnityCalls':0}
 (H/'TEST101.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
if __name__=='__main__':main()
