"""Compare existing93/95 CPU mappings on current actual960 UV/Q inputs.
This never writes a shader, applies a product mapping, or calls Unity/GPU.
"""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet
from review_motion64 import srgb
H=Path(__file__).resolve().parent

def stats(rgb,mask):
 edges=int((mask[:,1:]&mask[:,:-1]&(rgb[:,1:]!=rgb[:,:-1]).any(2)).sum()+(mask[1:]&mask[:-1]&(rgb[1:]!=rgb[:-1]).any(2)).sum());same=np.zeros(mask.shape,bool)
 for dy,dx in [(0,1),(1,0)]:
  left=(slice(None,-dy)if dy else slice(None),slice(None,-dx)if dx else slice(None));right=(slice(dy,None),slice(dx,None));value=mask[left]&mask[right]&(rgb[left]==rgb[right]).all(2);same[left]|=value;same[right]|=value
 return edges,int((mask&~same).sum())

def main():
 root=H/'face99'/sys.argv[1];r=json.loads((root/'capture/COMPLETE.json').read_text());source=np.fromfile(H/'face99/original99/details/ORIGINAL99.rgba',np.uint8).reshape(1024,1024,4);meta=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=meta['cropOffset'];regions=np.load(H/'face86/REGIONS86.npz')['regions'];range93=np.load(H/'face93/SOURCE_RANGE_CANDIDATE93.npz')['labels'];nearest95=np.load(H/'face95/source/SOURCE_MAPPING95.npz')['labels'];p93=np.fromfile(H/'face93/range-palette/CONSTRAINED92.rgb',np.uint8).reshape(-1,3,3);p95=np.fromfile(H/'face95/source/CONSTRAINED92.rgb',np.uint8).reshape(-1,3,3);actualTable=np.fromfile(root/'capture/RUNTIME_PALETTE89.rgb',np.uint8).reshape(-1,3,3);previous=None;steps=[];shape=np.zeros((3,2),np.int64);gpuTableErrors=0;sourceSSE=np.zeros(3);samples=0;pictures=[]
 for f in r['stream77']['frames']:
  a,_,_=packet(root,f);uv=a[1,:,:,:2];sx=np.floor(uv[:,:,0]*np.float32(1024)).astype(int)%1024;sy=np.floor(uv[:,:,1]*np.float32(1024)).astype(int)%1024;tx=sx-ox;ty=1023-sy-oy;valid=(a[4,:,:,3]==1)&(a[4,:,:,0]>0)&(tx>=0)&(ty>=0)&(tx<range93.shape[1])&(ty<range93.shape[0]);reg=np.zeros(valid.shape,int);reg[valid]=regions[ty[valid],tx[valid]];q=a[4,:,:,2].astype(int);native=source[sy,sx,:3].astype(int);gpu=np.flipud(np.asarray(srgb(a[5])))[:,:,:3].astype(int);c93=gpu.copy();c95=gpu.copy();c93[valid]=p93[range93[ty[valid],tx[valid]],q[valid]];c95[valid]=p95[nearest95[ty[valid],tx[valid]],q[valid]];family=a[4,:,:,0].astype(int)-1;gpuTableErrors+=int((gpu[valid]!=actualTable[family[valid],q[valid]]).any(1).sum());samples+=int(valid.sum())
  for i,c in enumerate([gpu,c93,c95]):shape[i]+=stats(c,valid);sourceSSE[i]+=((c[valid]-native[valid])**2).sum()
  if previous is not None:
   before,oldNative,oldRGBs,oldValid,oldReg=previous;mask=valid&oldValid&(reg==oldReg)&(reg>0)&(a[0,:,:,1]==before[0,:,:,1])&(a[0,:,:,3]==before[0,:,:,3])&(a[4,:,:,2]==before[4,:,:,2])
   for y,x in np.argwhere(mask):
    ds=native[y,x]-oldNative[y,x];delta=[c[y,x]-old[y,x]for c,old in zip([gpu,c93,c95],oldRGBs)];steps.append({'frame':f['frame'],'xy':[int(x),int(y)],'source':ds.tolist(),'RGBSteps':[v.tolist()for v in delta]})
  previous=a,native,[gpu,c93,c95],valid,reg
  if f['frame']in[102,149,585]:
   board=Image.new('RGB',(780,286),'#20252c');d=ImageDraw.Draw(board);d.text((8,6),f"Frame {f['frame']} actual UV/Q;93/95 panels are CPU counterfactuals, not GPU renders",fill='white')
   for i,(c,title)in enumerate([(gpu,'Actual GPU226'),(c93,'CPU range93/510'),(c95,'CPU nearest95/510 REJECTED')]):
    im=Image.fromarray(np.flipud(c.astype(np.uint8)));board.paste(im,(8+258*i,30));board.paste(im.resize((208,208),Image.Resampling.NEAREST),(8+258*i,64));d.text((42+258*i,34),title,fill='white')
   pictures.append(board)
 sn=np.array([np.linalg.norm(v['source'])for v in steps]);dn=np.array([[np.linalg.norm(v)for v in row['RGBSteps']]for row in steps]);ratios=np.divide(dn,sn[:,None],out=np.zeros_like(dn),where=sn[:,None]>0);out={'CPUCounterfactualOnActualGPU960Input':True,'actualRGBSamples':samples,'actualGPUByteTableErrors':gpuTableErrors,'comparedPairs':len(steps),'candidates':['actual226','CPU_range93_510','CPU_nearest95_510'],'sameSupportSelectedQChangingPairs':(dn>0).sum(0).tolist(),'maximumPointStepGain':ratios.max(0).tolist(),'sourceSSEIncludesShadingSoNotUnshadedFidelityProof':sourceSSE.tolist(),'equalRGBBoundaryEdges':shape[:,0].tolist(),'singletonPixels':shape[:,1].tolist(),'range93StepNormImprovedPairs':int((dn[:,1]<dn[:,0]).sum()),'range93StepNormWorsenedPairs':int((dn[:,1]>dn[:,0]).sum()),'range93ActualGPUOrArtAdopted':False,'rows':steps};(root/'RANGE_COMPARISON99.json').write_text(json.dumps(out,indent=2));sheet=Image.new('RGB',(780,286*len(pictures)),'#20252c')
 for i,p in enumerate(pictures):sheet.paste(p,(0,286*i))
 sheet.save(root/'CPU_RANGE_COMPARISON99.png');print(json.dumps({k:v for k,v in out.items()if k!='rows'},indent=2))
if __name__=='__main__':main()
