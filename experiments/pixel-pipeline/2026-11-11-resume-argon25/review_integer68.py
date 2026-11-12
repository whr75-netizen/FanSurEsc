from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from integer_exterior68 import resolve as integer
from face_parent62 import resolve,child_gate
from replay_outline_class66 import exterior_candidate
from native_contour42 import coordinates
from review_motion64 import srgb
from test_flat67 import region_at
H=Path(__file__).resolve().parent;G=H/'face68';SUFFIX=68

def main():
 stage=sys.argv[1]if len(sys.argv)>1 else'';root=G/stage if stage else G;C=root/'capture';api.C=C
 r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['pendingOwners']==0 and r['ownedResourcesReleased']and not r['errors']and r['sourceFlatTexturesRemaining67']==0
 spec=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());mask=np.fromfile(H/'face67/REGION_BOTTOM67.rgba',np.uint8).reshape(spec['sourceHeight'],spec['sourceWidth'],4)
 board=Image.new('RGB',(1050,len(r['frames'])*230+70),(27,29,35));d=ImageDraw.Draw(board);rows=[];film=[]
 for fi,f in enumerate(r['frames']):
  read=lambda n:api.plane(r,f,n);w=f['QROI'][2];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];b=read('ownerReceipts47');o=b[:,:w];uv=b[:,w:2*w];s=b[:,2*w:3*w];dom=b[:,3*w:4*w].copy();designed=dom[:,:,0]==-4;dom[:,:,0]=designed;v=read('featureProducer49')[:,w:2*w];before=fields[9];actor=fields[14][:,:,2]==1;info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);valid=inside&(fields[14][:,:,:2]==q).all(2)
  pinfo=f['frameInfo']['sourcePalette67'];palette=np.asarray(pinfo['paletteLinear'],np.float32).reshape(pinfo['levels'],4);known=np.zeros(actor.shape,bool);k=np.zeros(actor.shape,int);receipt=np.zeros(before.shape,np.float32);receipt[:,:,1]=-1
  for y,x in np.argwhere(b[:,3*w:4*w,0]==4):
   receipt[y,x,2]=uv[y,x,2];region=region_at(mask,uv[y,x,:2],pinfo['wrap'])
   if region:
    k[y,x]=round(float(uv[y,x,2])*(len(palette)-1));known[y,x]=True;receipt[y,x]=[region,k[y,x],uv[y,x,2],1]
  assert np.array_equal(receipt,read('sourcePaletteReceipt67'))
  table=f['frameInfo']['integerExterior68']['sourceTable'];maximum=np.zeros(16,int);enabled=np.zeros(16,bool);inks=np.zeros((16,3),np.float32)
  for row in table:
   role=row['role'];maximum[role]=row['triangles'];enabled[role]=row['sourceEnabled'];inks[role]=row['sourceInkLinear']
  roles=np.rint(o[:,:,0]).astype(int);ix=np.clip(roles,0,15);source=valid&actor&~designed&(o[:,:,0]==roles)&(roles>0)&(roles<16)&enabled[ix]&(s[:,:,0]==o[:,:,2])&(s[:,:,1]==o[:,:,0])&(s[:,:,2]==o[:,:,1])&(s[:,:,3]>=1)&(s[:,:,3]==np.rint(s[:,:,3]))&(s[:,:,3]<=maximum[ix])
  zero_rejected=0;unfiltered_source=source.copy()
  if 'zeroWidth69'in pinfo:
   zinfo=pinfo['zeroWidth69'];flags=np.fromfile(H/'face69/ZERO_TRIANGLES69.r8',np.uint8);tri=np.clip(np.rint(s[:,:,3]).astype(int)-1,0,zinfo['triangles']-1);reject=source&(roles==zinfo['role'])&(flags[tri]>0);zero_rejected=int(reject.sum());source&=~reject
  keys=np.stack([o[:,:,0],s[:,:,3],uv[:,:,0],uv[:,:,1]],2);integer_out,integer_owner,integer_mask,_=integer(before,actor,source,o[:,:,2],np.where(valid,fields[13][:,:,0],0),fields[12][:,:,0],keys,inks[ix],1)
  correction=[]
  if 'zeroWidth69'in pinfo:
   prior,prior_key,prior_mask,_=integer(before,actor,unfiltered_source,o[:,:,2],np.where(valid,fields[13][:,:,0],0),fields[12][:,:,0],keys,inks[ix],1)
   changed_key=(prior_key!=integer_owner).any(2)
   for yy,xx in np.argwhere(changed_key):correction.append({'localXY':[int(xx),int(yy)],'CPUUnfilteredSourceKey':prior_key[yy,xx].tolist(),'actualFilteredSourceKeyExpected':integer_owner[yy,xx].tolist(),'unfilteredWasOnlyCPUCounterfactual':True,'RGBChanged':bool((prior[yy,xx]!=integer_out[yy,xx]).any()),'currentlyVisibleAlternativeRetained':bool(integer_mask[yy,xx])})
  assert not(integer_mask&actor).any()and not(integer_mask&known).any();outputs=read('widthCompositeAtlas61');owners=read('widthOwnerAndLayerAtlas62');cases=[]
  for ci,scale in enumerate([0,1,8,32,32]):
   field=[20,18,22,24,24][ci];line=read('nativeLogicalHull60'if field==18 else'widthCaseField'+str(field))if ci else np.zeros(before.shape,np.float32);proof=read('nativeLogicalHullProof60'if field==18 else'widthCaseField'+str(field+1))if ci else np.zeros(before.shape,np.float32);ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32)
   old,gate,blocked=resolve(line,proof,before,fields[12],fields[13],fields[14],inside,q,info['depthOffset'],ink,4232,v,dom,o)
   if ci==1:expected=integer_out.copy();use=integer_mask;blocked=np.zeros(actor.shape,bool)
   else:
    expected,rejected=exterior_candidate(before,old,gate,fields[14])if ci<4 else(old,np.zeros(actor.shape,bool));use=(gate[:,:,3]==1)&~rejected
   if ci<4:expected[known,:3]=palette[k[known],:3]
   actual=outputs[:,ci*2*w:(ci+1)*2*w];owner=owners[:,ci*2*w:(ci*2+1)*w];layer=owners[:,(ci*2+1)*w:(ci+1)*2*w]
   assert np.array_equal(actual,np.repeat(np.repeat(expected,2,0),2,1)),('RGB',f['frame'],ci)
   if ci==1:
    assert np.array_equal(owner[:,:,0]>=100,use)
    wanted=integer_owner[use].copy();wanted[:,0]+=100;assert np.array_equal(owner[use],wanted)
    assert np.array_equal(read('nativeAfter42'),actual);actual_integer=actual
   else:
    assert np.array_equal(owner[:,:,0]==6,use)and np.array_equal(owner[use,1],proof[use,3])and np.array_equal(owner[use,2:],proof[use,1:3])
   assert np.array_equal(layer[:,:,:3],v[:,:,:3])and np.array_equal(layer[:,:,3]==1,blocked)
   cases.append({'case':ci,'integerExteriorWidth':1 if ci==1 else 0,'nativeHullScale':None if ci==1 else scale,'RGBAndOwnerAndLayerExact':True})
  child=child_gate(v,dom,o,fields[14]);assert not(integer_mask&child).any();assert np.array_equal(integer_out[child],before[child])
  ims=[srgb(read('nativeBefore42')),srgb(actual_integer),srgb(outputs[:,8*w:10*w])]
  for col,(im,title)in enumerate(zip(ims,['Actual native baseline','Actual GPU integer exterior1 + partial LUT','Actual GPU old hull32 (control)'])):
   d.text((col*350+8,fi*230+8),f"F{f['frame']} {title}",fill='white');board.paste(im,(col*350+8,fi*230+35));board.paste(im.resize((w*6,im.height*3),Image.Resampling.NEAREST),(col*350+100,fi*230+35))
  film.append(ims[1].resize((ims[1].width*4,ims[1].height*4),Image.Resampling.NEAREST));rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'registeredCurrentVisibleSources':int(source.sum()),'zeroWidthSourceCellsRejected69':zero_rejected,'zeroWidthCorrection69':correction,'integerExteriorCells':int(integer_mask.sum()),'sourceRolesUsed':np.unique(integer_owner[integer_mask,0]).astype(int).tolist(),'actorOrEyeOverwrite':0,'LUTSamples':int(known.sum()),'cases':cases})
 d.text((8,len(rows)*230+8),'Actual private GPU ROI. Width1 is a test parameter, not the original subpixel hull or an adopted default.',fill='white');d.text((8,len(rows)*230+30),'Current visible source primitive/UV/depth and original material ink; no history colour or hidden-source resurrection.',fill='white')
 if SUFFIX==69:d.text((8,len(rows)*230+50),'69: original zero-width source triangles rejected. Full face regions, native varying-width equality and history remain unfinished.',fill='white')
 board.save(root/f'ACTUAL_INTEGER{SUFFIX}.png');size=(max(x.width for x in film),max(x.height for x in film));padded=[]
 for im in film:
  frame=Image.new('RGB',size,(27,29,35));frame.paste(im,(0,0));padded.append(frame)
 padded[0].save(root/f'ACTUAL_INTEGER{SUFFIX}.webp',save_all=True,append_images=padded[1:],duration=200,loop=0,lossless=True)
 result={'actualGPUFrames':len(rows),'actualCases':5*len(rows),'allRGBAndOwnerAndLayerAndLUTReceiptsExact':True,'wholeCharacterMaterialRegistryUsed':True,'wholeCharacterScreenCaptured':False,'product77Changed':False,'nativeSubpixelWidthEquality':False,'historyFeedback':False,'longTermStability':False,'rows':rows};(root/f'ACTUAL_INTEGER{SUFFIX}.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
