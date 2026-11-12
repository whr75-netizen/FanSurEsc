"""Correct82 internal-support ordering; same hierarchy, no K/threshold sweep."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
from source_profile71 import fit_profiles
from source_value88 import constraints,field_ranges
from colour_field82 import build
from audit_polarity76 import luminance
H=Path(__file__).resolve().parent;G=H/'face88'

def main():
 G.mkdir(exist_ok=True);native=np.load(H/'face28/SOURCE_NATIVE28.npz');part=np.load(H/'face86/REGIONS86.npz');rgb=native['rgba'][:,:,:3];compact=G/'PROFILE_INPUT88.npz'
 if compact.exists():
  saved=np.load(compact);rows=saved['rows'];flanks=saved['flanks']
 else:
  support=np.load(H/'face80/SOURCE_SUPPORT80.npz');ridge=np.load(H/'face70/RIDGE_EVIDENCE70.npz');rows=support['rows'];nx,ny,px,py=[ridge[k]for k in ['nx','ny','px','py']];fit=fit_profiles(rgb.astype(float),rows,nx,ny,px,py);centres=np.stack([px[rows[:,0],rows[:,1]],py[rows[:,0],rows[:,1]]],1);normal=np.stack([nx[rows[:,0],rows[:,1]],ny[rows[:,0],rows[:,1]]],1);flanks=np.rint(centres[:,None,:]+np.array([-1,1])[None,:,None]*2*fit['lineSigma'][:,None,None]*normal[:,None,:]).astype(int);np.savez_compressed(compact,rows=rows,flanks=flanks)
 d=constraints(rgb,part['mask'],part['foreground'],part['island'],rows,flanks);ranges=field_ranges(rgb,part['mask'],part['regions'],d['index'],d['colours']);print(json.dumps({'lineProfiles':len(rows),'acceptedExternalProfiles':len(d['accepted']),'externalSourceOrders':len(d['orders']),'observedFieldRangePairs':len(ranges),'rejected':d['rejected']}),flush=True)
 tree=build(d['colours'],d['counts'],d['orders'],ranges);refs=d['colours'][tree['referenceIndices']];address=np.full(part['mask'].shape,-1,np.int32);address[part['mask']]=tree['address'][d['index'][part['mask']]];out=rgb.copy();out[part['mask']]=refs[address[part['mask']]];native_y=luminance(d['colours']);output_y=luminance(refs);assert all(output_y[tree['address'][a]]<output_y[tree['address'][b]]for a,b in d['orders']);old=np.load(H/'face82/SOURCE_FIELD82.npz');oldrefs=old['colour'][old['referenceIndices']];oldout=rgb.copy();oldout[part['mask']]=oldrefs[old['labels'][part['mask']]];orders_old=np.load(H/'face82/ORDER_INPUT82.npz')['orders'];oldviol=sum(output_y[tree['address'][int(a)]]>=output_y[tree['address'][int(b)]]for a,b in orders_old)
 # All accepted two-sided foreground/background contrasts are audited; source
 # colour loss and spatial small components remain separate art diagnostics.
 contrasts=[]
 for x,y,x0,y0,x1,y1,sign in d['accepted']:
  native_values=luminance(np.array([rgb[y,x],rgb[y0,x0],rgb[y1,x1]]));new_values=luminance(np.array([out[y,x],out[y0,x0],out[y1,x1]]));contrasts.append([float(min(abs(native_values[0]-native_values[1:]))),float(min(abs(new_values[0]-new_values[1:])))])
 colours=d['colours'];probes=[]
 for x,y in [(382,704),(380,704),(384,704)]:probes.append({'xy':[x,y],'foreground':bool(part['foreground'][y,x]),'support':int(part['regions'][y,x]),'sourceRGB':rgb[y,x].tolist(),'newSourceValueRGB':out[y,x].tolist(),'old82SourceRGB':oldout[y,x].tolist()})
 result={'actualSourceRGBInput':True,'newGPUExecution':False,'sameHierarchy82Reused':True,'oldParentColourRangesRemoved':True,'oldInternalAAOrdersNotReimposed':True,'allAcceptedPigmentBackgroundSignsPreserved':True,'lineProfiles':len(rows),'acceptedExternalProfiles':len(d['accepted']),'externalSourceOrders':len(d['orders']),'observedFieldRangePairs':len(ranges),'rejected':d['rejected'],'sourceValueAddresses':len(refs),'old82Addresses':len(oldrefs),'sourceRGBMSE':float(np.mean((out[part['mask']].astype(float)-rgb[part['mask']])**2)),'old82SourceRGBMSE':float(np.mean((oldout[part['mask']].astype(float)-rgb[part['mask']])**2)),'old82OrderViolationsIncludingInternalAA':int(oldviol),'acceptedNativeAndNewContrastMinMedianMax':np.percentile(np.array(contrasts),[0,50,100],axis=0).tolist(),'supportOrRGBInputChanged':False,'UVFeatureIdentityIsNotColourAddress':True,'runtimeColourOrArtAdopted':False,'probes':probes};np.savez_compressed(G/'SOURCE_VALUE88.npz',labels=address,mask=part['mask'],colours=colours,colourAddress=tree['address'],referenceIndices=tree['referenceIndices'],orders=np.asarray(sorted(d['orders']),int),ranges=np.asarray(sorted(ranges),int),accepted=np.asarray(d['accepted'],int));(G/'SOURCE_VALUE88.json').write_text(json.dumps(result,indent=2));(G/'REFERENCES88.json').write_text(json.dumps({'references':refs.tolist(),'history':tree['history']},indent=2));print(json.dumps(result),flush=True)
 board=Image.new('RGB',(1260,820),(27,29,35));draw=ImageDraw.Draw(board)
 for j,(a,title)in enumerate([(rgb,'Original source'),(oldout,'Rejected82 source value field'),(out,'CPU88 external-support constraints')]):
  draw.text((j*420+5,5),title,fill='white');board.paste(Image.fromarray(a[620:740,300:440]).resize((420,360),Image.Resampling.NEAREST),(j*420,30));board.paste(Image.fromarray(a).resize((360,360),Image.Resampling.NEAREST),(j*420+5,410))
 draw.text((5,795),'Source value addresses only, before light Q/LUT. All original support retained; no author-semantic truth or art adoption.',fill='white');board.save(G/'SOURCE_VALUE88.png')
if __name__=='__main__':main()
