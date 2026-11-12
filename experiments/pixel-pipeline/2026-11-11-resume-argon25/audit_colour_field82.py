from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
from colour_field82 import build
from source_profile71 import fit_profiles
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face82'

def components(labels,mask):
 # UV connected-component statistics are not colour family IDs or owners.
 seen=np.zeros(mask.shape,bool);h,w=mask.shape;sizes=[]
 for y,x in np.argwhere(mask):
  if seen[y,x]:continue
  value=labels[y,x];todo=[(int(y),int(x))];seen[y,x]=True;count=0
  while todo:
   yy,xx=todo.pop();count+=1
   for dy,dx in[(0,1),(0,-1),(1,0),(-1,0)]:
    a,b=yy+dy,xx+dx
    if 0<=a<h and 0<=b<w and mask[a,b]and not seen[a,b]and labels[a,b]==value:seen[a,b]=True;todo.append((a,b))
  sizes.append(count)
 return len(sizes),sum(n==1 for n in sizes)

def main():
 G.mkdir(exist_ok=True);native=np.load(H/'face28/SOURCE_NATIVE28.npz');rgb=native['rgba'][:,:,:3];mask=native['mask'];colour,inv,counts=np.unique(rgb[mask],axis=0,return_inverse=True,return_counts=True);codes=colour[:,0].astype(np.int64)*65536+colour[:,1].astype(np.int64)*256+colour[:,2];yall=luminance(colour);orders=[];ranges=[];proof=[]
 def index(c):return int(np.searchsorted(codes,int(c[0])*65536+int(c[1])*256+int(c[2])))
 def pair(fg,flank):
  a=index(rgb[fg[1],fg[0]]);b=index(rgb[flank[1],flank[0]])
  if yall[a]<yall[b]:orders.append((a,b))
  elif yall[b]<yall[a]:orders.append((b,a))
 for r in json.loads((H/'face79/ACTUAL_LABEL_POLARITY79.json').read_text())['rows']:
  if r['nativePolarity']!=0:
   for p in r['nativeFlankXY']:pair(r['nativeForegroundXY'],p)
 support=np.load(H/'face80/SOURCE_SUPPORT80.npz');rows=support['rows'];a=np.load(H/'face70/RIDGE_EVIDENCE70.npz');nx,ny,px,py=[a[k]for k in['nx','ny','px','py']];fit=fit_profiles(rgb.astype(float),rows,nx,ny,px,py);height,width=mask.shape
 for j,(yy,xx)in enumerate(rows):
  centre=np.array([px[yy,xx],py[yy,xx]]);n=np.array([nx[yy,xx],ny[yy,xx]]);points=[np.rint(centre+s*2*fit['lineSigma'][j]*n).astype(int)for s in[-1,1]]
  if any(p[0]<0 or p[1]<0 or p[0]>=width or p[1]>=height or not mask[p[1],p[0]]for p in points):continue
  v=luminance(rgb[yy,xx]);flanks=luminance(np.array([rgb[p[1],p[0]]for p in points]));sign=-1 if v<flanks.min()else 1 if v>flanks.max()else 0
  if sign:
   for p in points:pair([int(xx),int(yy)],p)
   proof.append({'foregroundXY':[int(xx),int(yy)],'flankXY':[p.tolist()for p in points],'sign':sign})
 # Frozen105 patches provide source field RANGE witnesses only, not semantic
 # ownership. This prevents replacing a varying field by one constant colour.
 parent=support['parent'];field_ranges=[]
 for p in np.unique(parent[mask]):
  c=rgb[mask&(parent==p)];v=luminance(c);lo=c[int(np.argmin(v))];hi=c[int(np.argmax(v))];aa,bb=index(lo),index(hi)
  if aa!=bb:ranges.append((aa,bb));field_ranges.append({'field':int(p),'lowRGB':lo.tolist(),'highRGB':hi.tolist()})
 orders=sorted(set(orders));np.savez_compressed(G/'ORDER_INPUT82.npz',colours=colour,counts=counts,orders=np.array(orders),ranges=np.array(ranges));height=np.zeros(len(colour),int);successors={}
 for aa,bb in orders:successors.setdefault(aa,[]).append(bb)
 for aa in np.argsort(yall):
  for bb in successors.get(int(aa),[]):height[bb]=max(height[bb],height[aa]+1)
 lower={'nativeStrictOrderLongestPathLowerBound':int(height.max()+1),'isGlobalColourArtOptimum':False,'doesNotProve908AddressesNecessary':True};(G/'ORDER_LOWER_BOUND82.json').write_text(json.dumps(lower,indent=2));print(json.dumps(lower))
 if'--input-only'in sys.argv:return
 print(json.dumps({'nativeColours':len(colour),'contrastPairs':len(set(orders)),'fieldRangePairs':len(ranges)}),flush=True);tree=build(colour,counts,orders,ranges);refs=colour[tree['referenceIndices']];mapped=refs[tree['address'][inv]];out=np.zeros_like(rgb);out[mask]=mapped;labels=np.full(mask.shape,-1,np.int32);labels[mask]=tree['address'][inv];regions,singletons=components(labels,mask);probes=[]
 for x,y in[(382,704),(380,704),(384,704)]:probes.append({'xy':[x,y],'nativeRGB':rgb[y,x].tolist(),'candidateSourceRGB':out[y,x].tolist(),'colourAddress':int(labels[y,x])})
 orders=set(orders);yout=luminance(refs);assert all(yout[tree['address'][a]]<yout[tree['address'][b]]for a,b in orders);result={'nativeUniqueRGB':len(colour),'colourAddresses':len(refs),'strictNativeOrders':len(orders),'fieldRangePairs':len(ranges),'allStrictSourceOrdersPreserved':True,'sameRGBSameAddressIndependentOfMaterialOrUVRegion':True,'nativeRGBRepresentativesOnly':True,'sourceUVConnectedComponents':regions,'sourceUVSingletons':singletons,'UVComponentsNotFeatureOrOwnerLabels':True,'sourceRGBMSE':float(np.mean((mapped.astype(float)-rgb[mask])**2)),'probes':probes,'sourceLightQUsedForClassification':False,'GPUExecuted':False,'runtimeLUTOrArtAdopted':False};(G/'SOURCE_COLOUR_FIELD82.json').write_text(json.dumps(result,indent=2));(G/'HIERARCHY82.json').write_text(json.dumps({'history':tree['history'],'references':refs.tolist(),'fieldRanges':field_ranges,'provenance':[{'address':i,'nativeRGB':c.tolist(),'nativeColourIndex':int(tree['referenceIndices'][i])}for i,c in enumerate(refs)]},indent=2));np.savez_compressed(G/'SOURCE_FIELD82.npz',labels=labels,mask=mask,colour=colour,colourAddress=tree['address'],referenceIndices=tree['referenceIndices']);print(json.dumps(result))
 board=Image.new('RGB',(840,800),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(im,title)in enumerate([(rgb,'Native source'),(out,'CPU constrained source colour field')]):
  draw.text((420*i+5,5),title,fill='white');board.paste(Image.fromarray(im[620:740,300:440]).resize((420,360),Image.Resampling.NEAREST),(420*i,30));board.paste(Image.fromarray(im).resize((360,360),Image.Resampling.NEAREST),(420*i+5,410))
 draw.text((5,780),'No runtime Q/LUT yet. Colour addresses are not feature topology or occlusion owners.',fill='white');board.save(G/'SOURCE_FIELD82.png');Image.fromarray(out).save(G/'SOURCE_REFERENCE82.png')
if __name__=='__main__':main()
