from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
import review_hull60 as api
from variable_exterior72 import resolve,source_green
from correspondence68 import read_geometry
from native_contour42 import coordinates
from review_motion64 import srgb
from test_flat67 import region_at
from face_parent62 import resolve as native_resolve
from replay_outline_class66 import exterior_candidate
H=Path(__file__).resolve().parent;G=H/'face72';C=G/'capture'
HALO=0;SUFFIX=72

def main():
 api.C=C;r=json.loads((C/'COMPLETE.json').read_text());assert r['packetComplete']and r['restorationChecksPass']and r['pendingOwners']==0 and r['ownedResourcesReleased']and not r['errors']and r['sourceFlatTexturesRemaining67']==0
 spec=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());mask=np.fromfile(H/'face67/REGION_BOTTOM67.rgba',np.uint8).reshape(spec['sourceHeight'],spec['sourceWidth'],4);zero=np.fromfile(H/'face69/ZERO_TRIANGLES69.r8',np.uint8)
 original=np.asarray(Image.open(H/'face40/analysis-directed/SOURCE_WIDTH_MASK40.png').convert('RGBA'))[::-1,:,1].astype(float)/255
 board=Image.new('RGB',(1440,len(r['frames'])*230+70),(27,29,35));draw=ImageDraw.Draw(board);rows=[];film=[];scalar_errors=[]
 for fi,f in enumerate(r['frames']):
  read=lambda n:api.plane(r,f,n);w=f['QROI'][2];a=read('atlas40');fields=[a[:,i*w:(i+1)*w]for i in range(16)];b=read('ownerReceipts47');owner=b[:,:w];uv=b[:,w:2*w];s=b[:,2*w:3*w];designed=b[:,3*w:4*w,0]==-4;actor=fields[14][:,:,2]==1;before=fields[9];info=f['frameInfo']['nativeComposite42'];q,_,inside=coordinates(f['QROI'],info['joinOffset'],info['nativeOrigin'],info['deliveredDelta']);valid=inside&(fields[14][:,:,:2]==q).all(2)
  core=np.ones(actor.shape,bool)
  if HALO:core[:HALO]=False;core[-HALO:]=False;core[:,:HALO]=False;core[:,-HALO:]=False
  table=f['frameInfo']['integerExterior68']['sourceTable'];maximum=np.zeros(16,int);enabled=np.zeros(16,bool);inks=np.zeros((16,3),np.float32)
  for row in table:role=row['role'];maximum[role]=row['triangles'];enabled[role]=row['sourceEnabled'];inks[role]=row['sourceInkLinear']
  role=np.rint(owner[:,:,0]).astype(int);ix=np.clip(role,0,15);source=valid&actor&~designed&(owner[:,:,0]==role)&(role>0)&(role<16)&enabled[ix]&(s[:,:,0]==owner[:,:,2])&(s[:,:,1]==owner[:,:,0])&(s[:,:,2]==owner[:,:,1])&(s[:,:,3]>=1)&(s[:,:,3]==np.rint(s[:,:,3]))&(s[:,:,3]<=maximum[ix]);zinfo=f['frameInfo']['sourcePalette67']['zeroWidth69'];tri=np.clip(np.rint(s[:,:,3]).astype(int)-1,0,zinfo['triangles']-1);source&=~((role==zinfo['role'])&(zero[tri]>0));keys=np.stack([owner[:,:,0],s[:,:,3],uv[:,:,0],uv[:,:,1]],2)
  # Read the actual GPU sampler output, not CPU expected values uploaded to it.
  # CPU selection equivalence uses that observed scalar; a separate original
  # PNG reference reports sampling error and does not claim exact native hull.
  scalar=read('ownerReceipts47')[:,5*w:6*w];assert np.isfinite(scalar).all();unknown=source&(scalar[:,:,2]!=1);radius=np.rint(scalar[:,:,1]).astype(int);assert not((radius<0)|(radius>2)).any()
  assert np.array_equal(radius,np.floor(2*scalar[:,:,0]+.5).astype(int))
  meshfile=C/('all-source-frame'+str(f['frame'])+'.bin');_,_,_,meshes=read_geometry(meshfile);vertices,indices=meshes[1];tu=vertices[:,3:5][indices[3]]
  def vertex_sample(points):
   centre=points.astype(np.float32)*np.array([original.shape[1],original.shape[0]],np.float32)-np.float32(.5);lo=np.floor(centre).astype(int);fraction=centre-lo;v=np.zeros(len(points))
   for dy in[0,1]:
    for dx in[0,1]:v+=original[(lo[:,1]+dy)%original.shape[0],(lo[:,0]+dx)%original.shape[1]]*(fraction[:,0]if dx else 1-fraction[:,0])*(fraction[:,1]if dy else 1-fraction[:,1])
   return v
  frame_scalar=[]
  for yy,xx in np.argwhere(source&(role==zinfo['role'])):
   t=tu[tri[yy,xx]];v=vertex_sample(t);g=source_green(t,v,uv[yy,xx,:2]);actual=float(scalar[yy,xx,0])
   if g is not None and scalar[yy,xx,2]==1:frame_scalar.append(abs(actual-g));scalar_errors.append(abs(actual-g))
  pinfo=f['frameInfo']['sourcePalette67'];palette=np.asarray(pinfo['paletteLinear'],np.float32).reshape(pinfo['levels'],4);known=np.zeros(actor.shape,bool);k=np.zeros(actor.shape,int);receipt=np.zeros(before.shape,np.float32);receipt[:,:,1]=-1
  for yy,xx in np.argwhere(b[:,3*w:4*w,0]==4):
   receipt[yy,xx,2]=uv[yy,xx,2];region=region_at(mask,uv[yy,xx,:2],pinfo['wrap'])
   if region:k[yy,xx]=round(float(uv[yy,xx,2])*(len(palette)-1));known[yy,xx]=True;receipt[yy,xx]=[region,k[yy,xx],uv[yy,xx,2],1]
  assert np.array_equal(receipt,read('sourcePaletteReceipt67'))
  outputs=read('widthCompositeAtlas61');outowners=read('widthOwnerAndLayerAtlas62');cases=[];ims=[];widths=[];results={}
  for ci in[0,1,2,3]:
   rad=np.zeros(actor.shape,int)if ci==0 else np.full(actor.shape,1 if ci==1 else 2,int)if ci<3 else radius
   eligible=source if ci<3 else source&~unknown
   expected,picked,m,rt=resolve(before,actor,eligible,owner[:,:,2],np.where(valid,fields[13][:,:,0],0),fields[12][:,:,0],keys,inks[ix],rad);expected[known,:3]=palette[k[known],:3];actual=outputs[:,ci*2*w:(ci+1)*2*w];ow=outowners[:,ci*2*w:(ci*2+1)*w];trace=outowners[:,(ci*2+1)*w:(ci+1)*2*w]
   assert np.array_equal(actual,np.repeat(np.repeat(actual[::2,::2],2,0),2,1)),('quad replication',f['frame'],ci)
   assert np.array_equal(actual[::2,::2][core],expected[core]),('RGB',f['frame'],ci)
   if ci:
    assert np.array_equal((ow[:,:,0]>=100)[core],m[core]);wanted=picked[m].copy();wanted[:,0]+=100;assert np.array_equal(ow[m],wanted)
    assert np.array_equal((trace[:,:,2]==1)[core],m[core])and np.array_equal(trace[:,:,1].astype(int)[core],rt[core])
    for yy,xx in np.argwhere(m):
     hit=(keys==picked[yy,xx]).all(2)&eligible;assert hit.any();gg=float(scalar[hit,0][0])if ci==3 else 1.;assert trace[yy,xx,0]==gg
   assert not(m&actor).any()and not(m&known).any();cases.append({'case':ci,'integerCells':int(m.sum()),'RGBAndOwnerAndRadiusExact':True,'sourceScalar':'actual GPU vertex-green barycentric'if ci==3 else'current uniform radius control'});widths.append(int(m.sum()));results[ci]=(actual,ow,m);im=srgb(actual);ims.append(im.crop((2*HALO,2*HALO,im.width-2*HALO,im.height-2*HALO))if HALO else im)
  assert np.array_equal(read('nativeAfter42'),results[3][0]);changed=(results[2][1]!=results[3][1]).any(2)&core;changes=[]
  for yy,xx in np.argwhere(changed):changes.append({'localXY':[int(xx),int(yy)],'uniformSource':results[2][1][yy,xx].tolist(),'mappedSource':results[3][1][yy,xx].tolist(),'RGBChanged':bool((results[2][0][2*yy,2*xx]!=results[3][0][2*yy,2*xx]).any())})
  for col,(im,title)in enumerate(zip(ims,['No exterior + partial LUT','Uniform radius1','Uniform radius2','Original vertex mask x radius2'])):
   draw.text((col*360+8,fi*230+8),f"F{f['frame']} {title}",fill='white');board.paste(im,(col*360+8,fi*230+35));board.paste(im.resize((w*6,im.height*3),Image.Resampling.NEAREST),(col*360+100,fi*230+35))
  film.append(ims[3].resize((ims[3].width*4,ims[3].height*4),Image.Resampling.NEAREST));rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'cases':cases,'mappedSourceCells':int((source&(role==zinfo['role'])).sum()),'UVCarrierUnknownCells':int(unknown.sum()),'PNGMathematicalBilinearScalarMaxError':max(frame_scalar,default=0),'changesFromSameFrameUniform2':changes,'LUTSamples':int(known.sum()),'actorOrEyeOverwrite':0})
 draw.text((8,len(rows)*230+8),'Actual private GPU. Uniform1/2 are explicit style tests; no product77 switch or native physical-width equality.',fill='white');draw.text((8,len(rows)*230+30),'Partial face LUT remains visibly unfinished. Sampler scalar / CPU selection / art quality are separate checks.',fill='white');board.save(G/f'ACTUAL_VERTEX_WIDTH{SUFFIX}.png');size=(max(im.width for im in film),max(im.height for im in film));pad=[]
 for im in film:out=Image.new('RGB',size,(27,29,35));out.paste(im,(0,0));pad.append(out)
 pad[0].save(G/f'ACTUAL_VERTEX_WIDTH{SUFFIX}.webp',save_all=True,append_images=pad[1:],duration=200,loop=0,lossless=True)
 result={'actualGPUFrames':len(rows),'sameFrameControlsPerFrame':5,'integerCasesCompared':4*len(rows),'CPUSelectionUsesObservedGPUWidthScalar':True,'CPUExpectedRGBUploaded':False,'PNGSamplerMaxError':max(scalar_errors,default=0),'verifiedCoreHalo':HALO,'outerObservationBorderNotOracleVerified':bool(HALO),'rows':rows,'fullFaceSegmentation':False,'nativeMetresEquality':False,'runtimeHistoryFeedback':False,'longTermStabilityValidated':False,'product77Changed':False};(G/f'ACTUAL_VERTEX_WIDTH{SUFFIX}.json').write_text(json.dumps(result,indent=2));print(json.dumps({'actualGPUFrames':len(rows),'integerCasesCompared':4*len(rows),'counts':[[c['integerCells']for c in f['cases']]for f in rows],'unknownCells':[f['UVCarrierUnknownCells']for f in rows],'PNGSamplerMaxError':max(scalar_errors,default=0)}))
if __name__=='__main__':main()
