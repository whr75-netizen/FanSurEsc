from pathlib import Path
import json,sys,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'feature-audit86'));from analyse87 import load,texture
from replay88 import canonical
from feature_layer88 import FeatureCache,SourcePixel
def main():
 _,_,bank=texture('TemplateRole.asset','<f4');_,_,colour=texture('TemplateRGBA.asset','u1');source=[];palette8=[]
 for y,x in np.argwhere(np.isin(bank[...,0],[1,4])&np.isin(bank[...,1],[1,2])):source.append(SourcePixel(int(x),int(y),int(bank[y,x,1]),int(bank[y,x,0]),len(palette8)));palette8.append(colour[y,x,:3].tolist())
 st=json.loads(sorted((ROOT/'feature-audit86/run87').glob('STATE87*.json'))[-1].read_text());frames=[]
 for e in st['sequencePackets']:
  if e['testStage82']=='blink':continue
  d=load(Path(e['output']));state,H=canonical(d,source,FeatureCache());m=d['manifest'];scope=(m['eyeFeature']['topologySHA256'],m['sourceForm86']['sourceSHA'],'paired-eyes/head','registered-open');frames.append({'frame':e['frame'],'sourceId':e['sourceId'],'H':{str(k):v.tolist()for k,v in H.items()},'scope':scope})
 q=HERE/'SOURCE_FIXTURE88.json';assert not q.exists();q.write_text(json.dumps({'source':[vars(s)for s in source],'paletteRGB8':palette8,'frames':frames,'role':'authored216 parent/iris/sclera; existing native eyelid is an observed occluding part, not in this bank'},indent=2)+'\n');print('Frozen source20 and24 actual view mappings; no new capture')
if __name__=='__main__':main()
