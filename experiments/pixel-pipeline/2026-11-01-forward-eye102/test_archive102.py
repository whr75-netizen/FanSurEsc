from pathlib import Path
import json,hashlib,zipfile,io,struct,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;D=H if(H/'ARTIFACTS102.json').exists()else H/'archive';sys.path.insert(0,str(D))
from reader68 import plane,rgb8
from selection102 import cell,tests
class Memory:
 def __init__(self,b):self.b=b
 def open(self,mode):assert mode=='rb';return io.BytesIO(self.b)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def buf(b):
 n,stride=struct.unpack_from('<ii',b);assert stride==16 and len(b)==8+n*stride;return np.frombuffer(b,offset=8,dtype='<f4').reshape(n,4)
def main():
 for f in load(D/'ARTIFACTS102.json')['files']:assert hashlib.sha256((D/f['path']).read_bytes()).hexdigest()==f['SHA256']
 v=load(D/'HIERARCHY_VALIDATION102.json');assert v['CPUReferenceCells']==4092 and not v['CPUGPUSelectorMismatches']and not any(v['unresolvedByFrame'])and v['phaseIdentityVariants']==1 and v['phaseRGB8Variants']==2 and v['phaseRGB8Changes'][0]['part']==6
 evidence=load(D/'source-regions103/SOURCE_EVIDENCE103.json');counter=load(D/'source-regions103/COUNTEREXAMPLES103.json');assert evidence[0]['coarseRegions']==5 and evidence[0]['fineRegions']==1368 and counter[0]['sourceLRange'][1]-counter[0]['sourceLRange'][0]>.7
 files=0;packets=0;refs=0;paletteBad=0;bank=np.load(D/'TEMPLATE_REFERENCE100.npz');pal={r:{tuple(x)for x in bank['TemplateRGBA'][bank['TemplateRole'][...,0]==r,:3]}for r in [1,4]}
 with zipfile.ZipFile(D/'RAW102.zip')as z:
  folders=sorted({n.rsplit('/',1)[0]for n in z.namelist()if n.endswith('/RAW_MANIFEST.json')})
  for folder in folders:
   raw=z.read(folder+'/RAW_MANIFEST.json');m=json.loads(raw);assert z.read(folder+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(raw).hexdigest();packets+=1
   for name in [n for n in z.namelist()if n.startswith(folder+'/')and n.endswith('.plane')]:
    h,a=plane(Memory(z.read(name)));assert h['sourceId']==m['sourceId']and h['frameIndex']==m['frameIndex']and h['renderSerial']==m['mainSerial']and np.isfinite(a).all();files+=1
   ids=buf(z.read(folder+'/canonical-identity.f32'));colour=buf(z.read(folder+'/canonical-colour.f32'))
   for role in [1,4]:paletteBad+=sum(tuple(rgb)not in pal[role]for rgb in rgb8(colour[np.rint(ids[:,0])==role,:3]))
   if folder.startswith('motionH/'):
    w,h=m['forward102']['canonicalSize'];layers=buf(z.read(folder+'/canonical-layers.f32')).reshape(4,5,h,w,4);vis=buf(z.read(folder+'/canonical-visibility.f32')).reshape(4,h,w,4);dec=buf(z.read(folder+'/canonical-decision.f32'))
    for y in range(h//4):
     for x in range(w//4):
      r=cell(layers,vis,x,y)['winner'];code=-1 if r<0 else[1,4,6,0][r];assert code==round(float(dec[y*(w//4)+x,0]));refs+=1
 assert packets==75 and refs==4092 and paletteBad==0
 for name in ['reviewH/EYE_FORWARD_COMPARE102.png','reviewH/EYE_MOTION102.webp']:
  with Image.open(D/name)as im:assert im.width>100
 assert tests()==10
 print(json.dumps({'packets':packets,'planes':files,'CPUReferenceCells':refs,'CPUGPUSelectorMismatches':0,'irisScleraOutsidePalette':0,'sourceRegionCounterexamplePreserved':True,'syntheticTests':10,'UnityCalls':0,'productIntegrated':False}))
if __name__=='__main__':main()
