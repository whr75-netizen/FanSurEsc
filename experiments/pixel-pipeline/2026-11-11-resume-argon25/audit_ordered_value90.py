"""Single explicit source-field hypothesis: ordered scalar value strata.

Reuse82's tested exact minimum-cut-count/weighted-luminance-SSE DP on the
corrected88 feature constraints. Source88's740 RGB-tree addresses are not a
proven minimum. A one-dimensional field may lose chroma; test, don't hide it.
No requested K, threshold sweep, new GPU code or semantic region relabeling.
"""
from pathlib import Path
import json,subprocess,numpy as np
from PIL import Image,ImageDraw
from source_levels82 import partition
from audit_polarity76 import luminance
from frame_bytes77 import decode
from review_motion64 import srgb
H=Path(__file__).resolve().parent;G=H/'face90'

def main():
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True);native=np.load(H/'face28/SOURCE_NATIVE28.npz');base=np.load(H/'face88/SOURCE_VALUE88.npz');rgb=native['rgba'][:,:,:3];mask=base['mask'];colours,inv,counts=np.unique(rgb[mask],axis=0,return_inverse=True,return_counts=True);assert np.array_equal(colours,base['colours']);ys=luminance(colours);order=np.argsort(ys,kind='stable');rank=np.empty(len(order),int);rank[order]=np.arange(len(order));pairs=list(base['orders'])+list(base['ranges']);strict=[]
 for a,b in pairs:
  lo,hi=sorted([int(rank[a]),int(rank[b])]);assert ys[order[lo]]<ys[order[hi]],'scalar-value hypothesis cannot separate an equal-Y chromatic range';strict.append((lo,hi))
 assert np.all(np.diff(ys[order])>0),'scalar-value hypothesis needs a separate chromatic branch for equal Y';p=partition(ys[order],counts[order],strict);refs=[];labels=np.zeros(len(colours),np.int32)
 for label,(lo,hi)in enumerate(p['ranges']):
  ids=order[lo:hi+1];c=colours[ids].astype(np.int64);w=counts[ids].astype(np.int64);s=(c*w[:,None]).sum(0);cost=w.sum()*(c*c).sum(1)-2*c@s;at=int(np.lexsort((c[:,2],c[:,1],c[:,0],cost))[0]);refs.append(ids[at]);labels[ids]=label
 refs=np.asarray(refs);mapped=colours[refs[labels[inv]]];out=rgb.copy();out[mask]=mapped;addresses=np.full(mask.shape,-1,np.int32);addresses[mask]=labels[inv];reference=colours[refs];pairs_out=sorted(set((int(labels[a]),int(labels[b]))for a,b in base['orders']));assert all(a!=b for a,b in pairs_out);reference.tofile(G/'REFERENCES90.rgb');np.asarray(pairs_out,'<i4').tofile(G/'ORDERS90.i32');contrast=[];opposite=[]
 for x,y,x0,y0,x1,y1,sign in base['accepted']:
  for xx,yy in [(x0,y0),(x1,y1)]:
   before=rgb[y,x].astype(float)-rgb[yy,xx];after=out[y,x].astype(float)-out[yy,xx];cos=float(before@after/(np.linalg.norm(before)*max(1e-30,np.linalg.norm(after))));contrast.append(cos)
   if cos<=0:opposite.append({'sourceXY':[int(x),int(y)],'flankXY':[int(xx),int(yy)],'originalDeltaRGB':before.tolist(),'candidateDeltaRGB':after.tolist(),'cosine':cos})
 np.savez_compressed(G/'SOURCE_VALUE90.npz',labels=addresses,mask=mask,colours=colours,colourAddress=labels,referenceIndices=refs,ranges=np.asarray(p['ranges']),orders=np.asarray(pairs_out));result={'CPUOnly':True,'hypothesis':'ordered scalar source-value field, not semantic feature regions','minimumOrderedStrata':p['strata'],'old88RGBTreeAddresses':len(base['referenceIndices']),'allAcceptedNativeLuminanceSignsPreserved':True,'criticalSourceRGBVectorReversals':len(opposite),'criticalRGBVectorCosineMinMedian':np.percentile(contrast,[0,50]).tolist(),'sourceRGBMSE':float(np.mean((mapped.astype(float)-rgb[mask])**2)),'sourceRGBMaxChannelError':float(np.max(abs(mapped.astype(float)-rgb[mask]))),'nativeObservedReferencesOnly':True,'sourceIdentityMaskChanged':False,'uniqueNativeColours':len(colours),'globalVectorQuantizationOrSemanticOptimumProven':False,'artAdopted':False,'reversalExamples':opposite[:8]};(G/'SOURCE_VALUE90.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 board=Image.new('RGB',(840,800),(27,29,35));draw=ImageDraw.Draw(board)
 for j,(a,title)in enumerate([(rgb,'Original source'),(out,'CPU90 minimum ordered source-value strata')]):
  draw.text((j*420+4,4),title,fill='white');board.paste(Image.fromarray(a[620:740,300:440]).resize((420,360),Image.Resampling.NEAREST),(j*420,28));board.paste(Image.fromarray(a).resize((360,360),Image.Resampling.NEAREST),(j*420+4,405))
 draw.text((4,780),'CPU source-field hypothesis only. Minimum scalar strata is not a semantic/chroma preservation proof.',fill='white');board.save(G/'SOURCE_VALUE90.png')
 # CPU-only same-source preview under the actually observed89 floor. Reuse
 # the existing standalone C# source palette builder; never upload CPU output.
 live=json.loads((H/'face89/fix2/capture/RUNTIME_PALETTE89.json').read_text());exe=H/'face88/build/runtime89-core.exe';subprocess.run([str(exe),str(G/'REFERENCES90.rgb'),str(G/'ORDERS90.i32'),str(live['liveLinearFloor']),str(G/'build/palette90.rgb')],check=True);pal=np.fromfile(G/'build/palette90.rgb',np.uint8).reshape(-1,3,3);v=pal.astype(float)/255;v=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).astype(np.float32);capture=H/'face89/fix2/capture';r=json.loads((capture/'COMPLETE.json').read_text());info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());ox,oy=info['cropOffset'];tw,th=info['textureSize'];rows=[];board=Image.new('RGB',(1050,len(r['stream77']['frames'])*190+35),(27,29,35));draw=ImageDraw.Draw(board)
 for i,f in enumerate(r['stream77']['frames']):
  w=f['QROI'][2];a=np.frombuffer(decode((capture/f['compressedFile']).read_bytes(),f['bytes']),'<f4').reshape(w,22,w,4).transpose(1,0,2,3);visible=a[20,:,:,3]==1;uv=a[11,:,:,:2].astype(float);x=np.floor(uv[:,:,0]*tw).astype(int)-ox;y=np.floor((1-uv[:,:,1])*th).astype(int)-oy;new=a[0].copy();k=np.rint(a[16,:,:,0][visible]*2).astype(int);new[visible,:3]=v[addresses[y[visible],x[visible]],k];ims=[srgb(a[0]),srgb(a[19]),srgb(new)];rows.append({'frame':f['frame'],'actualNativeUniqueFaceRGB8':len(np.unique(np.array(ims[0])[np.flipud(visible)],axis=0)),'actual89UniqueFaceRGB8':len(np.unique(np.array(ims[1])[np.flipud(visible)],axis=0)),'CPU90UniqueFaceRGB8':len(np.unique(np.array(ims[2])[np.flipud(visible)],axis=0)),'sourceUnknownCells':0})
  for j,(im,title)in enumerate(zip(ims,['Actual native RGB','Actual GPU89,740 source addresses','CPU90 ordered source values, NOT GPU'])):
   draw.text((j*350+3,i*190+4),f"F{f['frame']} {title}",fill='white');board.paste(im,(j*350+3,i*190+27));board.paste(im.resize((w*5,w*5),Image.Resampling.NEAREST),(j*350+45,i*190+27))
 draw.text((4,len(rows)*190+8),'Same observed89 source/Q/floor.90 is CPU only. Chroma/source range/art errors remain separate diagnostics.',fill='white');board.save(G/'CPU_COLOUR90.png');(G/'CPU_COLOUR90.json').write_text(json.dumps({'newGPUExecution':False,'liveFloorFromActual89':live['liveLinearFloor'],'rows':rows},indent=2));print(json.dumps(rows))
if __name__=='__main__':main()
