from pathlib import Path
import hashlib,json,io,zipfile,re,struct
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
from reader68 import plane
class MemoryPath:
 def __init__(self,b):self.b=b
 def open(self,mode):assert mode=='rb';return io.BytesIO(self.b)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
 for f in load(HERE/'ARTIFACTS100.json')['files']:assert hashlib.sha256((HERE/f['path']).read_bytes()).hexdigest()==f['SHA256']
 s=load(HERE/'SUMMARY100.json');assert s['productDefault']==77 and not s['productAlgorithmChanged']and not s['experimental98or99Connected']and s['PlayEntries']==1 and s['hairSourceCells']==[367,0,367]and s['dirtyBeforeAfter']==[31,31]and s['serializedNativeExact']==47 and not s['publicDifferences']and not s['newConsoleErrors']and s['RTBeforeAfter']==[30,30]
 c=load(HERE/'COLOUR_STAGES100.json');assert c[1]['faceQValues']==[0,.5,1]and c[1]['stages']['main-palette-before-line']['face_skin']['uniqueSRGB8']==110 and c[1]['stages']['native-final']['face_skin']['uniqueSRGB8']==107
 assert sum(x.get('RGB8EqualsSourceBank',False)for x in c[1]['eyeSourceProvenance'])==15 and not any(x.get('RGB8EqualsSourceBank')is False for x in c[1]['eyeSourceProvenance'])
 assert sum(x['control'][2]>0 for x in c[1]['eyeSourceProvenance'])==17
 lid=[x for x in c[1]['eyeSourceProvenance']if x['encodedRole']==7 and x['control'][0]>0];assert len(lid)==1 and lid[0]['sameUVExactTimesShade']
 b=load(HERE/'BLUEPRINT_CHECKS100.json');assert b['Lcorner']['components4Before']==1 and b['Lcorner']['components4After']==2 and not b['Lcorner']['rotationCovariant']and b['exampleHLSLShadeIndices']==[1,2,3]and b['formulaGeneratedIndices']==[0,1,2]
 planes=0;hair=[]
 with zipfile.ZipFile(HERE/'RAW100.zip')as z:
  for folder in sorted({n.split('/')[0]for n in z.namelist()}):
   raw=z.read(folder+'/RAW_MANIFEST.json');m=json.loads(raw);assert z.read(folder+'/RAW_COMPLETE76.marker').decode()==hashlib.sha256(raw).hexdigest()and m['renderPath100'].startswith('actual product77')
   assert m['runtimeShader100'].endswith('/EyeFeature348.compute')
   for f in [n for n in z.namelist()if n.startswith(folder+'/')and n.endswith('.plane')]:
    h,a=plane(MemoryPath(z.read(f)));assert h['sourceId']==m['sourceId']and h['frameIndex']==m['frameIndex']and h['renderSerial']==m['mainSerial']and np.isfinite(a).all();planes+=1
    if f.endswith('/H-sourceMETA.plane'):hair.append(int(((a[...,1]>=12)&(a[...,1]<=15)&(a[...,0]>0)).sum()))
 assert planes==234 and hair==[367,0,367]
 for name in ['review/HAIR_ON_OFF_RESTORED100.png','review/EYES_NO_HAIR100.png','review/COLOUR_STAGE_PATH100.png']:
  with Image.open(HERE/name)as im:assert im.width>=1000 and im.height>=400
 for ref in re.findall(r'(?:href|src)="([^"]+)"',(HERE/'INDEX.html').read_text(encoding='utf-8')):assert not re.match('https?://',ref)and(HERE/ref).exists()
 print(json.dumps({'actualProduct77States':3,'planes':planes,'hairSourceCells':hair,'restored47':True,'irisScleraSourceBankExact':15,'nativeLidSameUVTimesShadeExact':1,'slotAndTopologyDraftCounterexamples':True,'productFixNotClaimed':True,'UnityCalls':0,'writes':0}))
if __name__=='__main__':main()
