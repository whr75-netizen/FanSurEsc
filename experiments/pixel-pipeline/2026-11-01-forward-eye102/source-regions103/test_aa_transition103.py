from pathlib import Path
import sys,json,numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'uv-features64'))
from aa_transition103 import peaks,tests
from inspect_source103 import colours
def main():
 toy=tests();print(json.dumps(toy),flush=True);rows=[]
 for part in [3,6]:
  p=H/f'part{part}';z=np.load(p/'hierarchy.npz')
  if(p/'aa-transition.npz').exists():
   cached=np.load(p/'aa-transition.npz');r={k:cached[k]for k in cached.files};r['scales']=[1,2,4];r['count']=int(r['labels'][z['mask']].max())+1
  else:
   r=peaks(z['rgba'][...,:3],z['mask']);Image.fromarray(colours(r['labels'],z['mask'])).save(p/'aa-transition-regions.png');np.savez_compressed(p/'aa-transition.npz',labels=r['labels'],x=r['x'],y=r['y'],fineX=r['fineX'],fineY=r['fineY'])
  counts=np.bincount(r['labels'][z['mask']]);row={'part':part,'regions':r['count'],'sizes':counts.tolist(),'scales':list(r['scales']),'xEdges':int(r['x'].sum()),'yEdges':int(r['y'].sum()),'sourceRGBModified':False,'paletteApplied':False}
  if part==3:row['knownScalpSkinSeparated']=bool(r['labels'][9,503]!=r['labels'][760,461])
  rows.append(row);print(json.dumps({k:v for k,v in row.items()if k!='sizes'}),flush=True)
 (H/'AA_TRANSITION_TEST103.json').write_text(json.dumps({'synthetic':toy,'real':rows,'status':'hypothesis only; region count is not art quality'},indent=2),encoding='utf-8')
if __name__=='__main__':main()
