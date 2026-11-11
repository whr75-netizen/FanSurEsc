from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from variable_stroke46 import sample
H=Path(__file__).resolve().parent;G=H/'face46';C=G/'capture'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['ownedResourcesReleased']and r['pending']==0 and r['stateUnchanged']and not r['globalErrors'];ink=np.asarray(r['sourceInk'],np.float32);rows=[];board=Image.new('RGB',(960,720),(35,37,43));d=ImageDraw.Draw(board);d.text((12,10),'46 | Actual offscreen GPU width operator | synthetic source-segment fixtures, NOT character renders',fill='white')
 for case in r['cases']:
  n=case['case'];colour=np.fromfile(C/f'case{n}-colour.f32',dtype='<f4').reshape(32,32,4);proof=np.fromfile(C/f'case{n}-proof.f32',dtype='<f4').reshape(32,32,4);mask=colour[:,:,3]==1;expected=np.zeros((32,32),bool);depths=np.zeros((32,32));ts=depths.copy();radius=depths.copy()
  for y in range(32):
   for x in range(32):
    a=sample((x+.5,y+.5),case['segment'][:2],case['segment'][2:],case['radii'],case['depths']);expected[y,x]=a['covered']
    if a['covered']:depths[y,x]=a['depth'];ts[y,x]=a['sourceT'];radius[y,x]=a['radius']
  mismatch=int((mask!=expected).sum());assert mismatch==0,('coverage',n,mismatch)
  assert np.isfinite(colour).all()and np.isfinite(proof).all()and np.all(colour[mask,:3]==ink)and np.all(colour[~mask]==0)and np.all(proof[~mask]==0);assert np.all(proof[mask,1]==1)and np.all((proof[mask,2]>=0)&(proof[mask,2]<=1));err=float(np.max(abs(proof[:,:,0][mask]-depths[mask]),initial=0));te=float(np.max(abs(proof[:,:,2][mask]-ts[mask]),initial=0));re=float(np.max(abs(proof[:,:,3][mask]-radius[mask]),initial=0));assert err<2e-5 and te<2e-5 and re<6e-5,('Float32 endpoint/root precision',n,err,te,re)
  rows.append({'case':n,'sourceRadii':case['radii'],'coveredPixels':int(mask.sum()),'coverageMismatch':mismatch,'depthMaxAbs':err,'sourceTMaxAbs':te,'radiusMaxAbs':re,'paletteMismatch':0})
  im=Image.new('RGB',(32,32),(19,21,26));im.putdata([tuple([232,170,145])if z else(19,21,26)for z in mask.reshape(-1)]);x=20+(n%3)*320;y=60+(n//3)*320;board.paste(im,(x,y));board.paste(im.resize((256,256),Image.Resampling.NEAREST),(x+40,y));d.text((x,y+265),'radius '+str(case['radii'])+'; '+str(mask.sum())+' cells',fill='white')
 d.text((12,695),'No RGB shading multiply/AA blend. Thin-line minimum and model/MToon width policy are separate, unaltered.',fill='white');board.save(G/'VARIABLE_WIDTH_GPU46.png')
 result={'actualGPUCases':6,'coverageExactCases':6,'CPUAnalyticOracle':'finite segment with linearly varying source-disc radius; source point chosen at nearest view depth in feasible t intervals','rows':rows,'resourcesReleased':True,'stateUnchanged':True,'modelWorldWidthPolicySpecified':False,'characterVariableWidthComplete':False,'minimumThinLineReplaced':False};(G/'ACTUAL_BAND46.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
