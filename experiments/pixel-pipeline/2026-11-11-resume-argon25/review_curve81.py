from pathlib import Path
import json,hashlib,sys,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from review_motion64 import srgb
H=Path(__file__).resolve().parent;K=sys.argv[1]if len(sys.argv)>1 else'';assert K in['','depth-probe','fixed6'];G=H/'face81'/K;C=G/'capture'
RASTER_SOURCE83=False

def main():
 report=json.loads((C/'COMPLETE.json').read_text());assert report['packetComplete']and report['restorationChecksPass']and report['ownedResourcesReleased']and not report['errors']and not report['globalErrors'];frames=report['stream77']['frames'];rows=[];panels=[];film=[]
 for f in frames:
  w,h=f['QROI'][2:];raw=decode((C/f['compressedFile']).read_bytes(),f['bytes']);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];data=np.frombuffer(raw,'<f4').reshape(h,23*w,4);p=[data[:,i*w:(i+1)*w]for i in range(23)];before=p[0];meta,world,cell=(p[1],p[2],p[3])if K=='fixed6'else(p[3],p[4],p[5]);actor=cell[:,:,2]==1;doc=json.loads((C/f"curve-source-frame{f['frame']}.json").read_text());assert doc['sourceId']==f['sourceId']and doc['frame']==f['frame'];vertices=np.asarray(doc['vertices']);ink=np.asarray(doc['inkLinear'],np.float32);edges={int(vertices[i,3]):vertices[i:i+2]for i in range(0,len(vertices),2)};rr=[]
  layouts=[('raw',5,11),('joint',8,13)]if K=='fixed6'else[('raw',13,19),('joint',16,21)]
  for kind,first,final in layouts:
   colour,proof,projection=p[first:first+3];out,receipt=p[final:final+2];coverage=colour[:,:,3]==1;used=receipt[:,:,3]==1;depth=np.float32(proof[:,:,0]+np.float32(f['depthOffset']));expected_depth=(world[:,:,0]>0)&(depth<=np.float32(world[:,:,0]+np.float32(.0001)))&((meta[:,:,0]<=0)|(depth<=np.float32(meta[:,:,0]+np.float32(.0001))));expected_target=~actor;assert not(used&actor).any();assert np.array_equal(out[~used],before[~used]);assert np.array_equal(out[used,:3],np.tile(ink,(int(used.sum()),1)))and(out[used,3]==1).all();active=receipt.any(2);assert np.array_equal(receipt[active,1]==1,expected_depth[active])and np.array_equal(receipt[active,2]==1,expected_target[active]);assert np.array_equal(used,coverage&(receipt[:,:,0]==1)&expected_depth&expected_target)
   errors=[];depth_errors=[];ts=[];unknown_edge=0
   for y,x in np.argwhere(coverage):
    eid=int(round(float(proof[y,x,1])));t=float(proof[y,x,2]);ts.append(t)
    if eid not in edges:unknown_edge+=1;continue
    a,b=edges[eid];tau=(t-a[4])/(b[4]-a[4])if K!='fixed6'else(t if a[4]==0 else 1-t);expected=a+(b-a)*tau;errors.append(float(np.linalg.norm(projection[y,x,:2]-expected[:2])));depth_errors.append(float(abs(proof[y,x,0]-expected[2])));assert np.array_equal(projection[y,x,2:],a[7:9])
   item={'kind':kind,'actualCurvePixels':int(coverage.sum()),'sampleAdmittedExteriorPixels':int(used.sum()),'actorOverwrite':int((used&actor).sum()),'unmappedEdgePixels':unknown_edge,'sourceProjectionMaxErrorCells':max(errors,default=None),'sourceDepthMaxError':max(depth_errors,default=None),'minT':min(ts,default=None),'maxT':max(ts,default=None),'sourceEligibilityObservedOnGPUNotIndependentlyRecomputed':K!='fixed6'}
   if K=='fixed6':
    sc,so,selected,domain=p[15:19]if kind=='raw'else p[19:23];src=np.stack([projection[:,:,0]-.5,272-projection[:,:,1]-.5],2)+np.asarray(f['join'],np.float32);sq=np.floor(src+.5);conditions={'cellCoordinate':(sc[:,:,:2]==sq).all(2),'actorPresent':sc[:,:,2]==1,'faceRole':so[:,:,0]==report['sourcePalette67']['zeroWidth69']['role'],'ordinaryDomain':domain[:,:,0]<.5,'producerIdentity':(selected[:,:,:3]==so[:,:,[2,0,1]]).all(2),'validPrimitive':(selected[:,:,3]>=1)&(selected[:,:,3]<=4232),'incidentPrimitive':(selected[:,:,3]==projection[:,:,2])|(selected[:,:,3]==projection[:,:,3])};source=np.logical_and.reduce(list(conditions.values()));expected_source=((projection[:,:,2:]>=1)&(projection[:,:,2:]<=4232)).all(2)if RASTER_SOURCE83 else source;assert np.array_equal(receipt[coverage,0]==1,expected_source[coverage]);item['oldRepresentativeFailedConditions']={key:int((coverage&~v).sum())for key,v in conditions.items()};item['oldRepresentativeAdmittedPixels']=int((source&coverage).sum());item['sourceProofIndependentCPU']=not RASTER_SOURCE83;item['actualNativeSourceDepthRaster']=RASTER_SOURCE83
   rr.append(item)
  rawfinal,jointfinal=(11,13)if K=='fixed6'else(19,21);rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'motion':f['motion']['stage'],'inputMatches':f['motion']['matches'],'anchor':doc['anchor'],'snapped':doc['snapped'],'rawJointFinalRGBDifferences':int((p[rawfinal]!=p[jointfinal]).any(2).sum()),'variants':rr});panels.append((f,srgb(before),srgb(p[rawfinal]),srgb(p[jointfinal])));film.append(srgb(p[jointfinal]).resize((w*8,h*8),Image.Resampling.NEAREST))
 board=Image.new('RGB',(1080,len(panels)*200+32),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(f,*images)in enumerate(panels):
  for j,(im,title)in enumerate(zip(images,['Native actual','Actual raw curve sample-gated','Actual joint curve sample-gated'])):draw.text((j*360+5,i*200+5),f"F{f['frame']} {title}",fill='white');board.paste(im,(j*360+5,i*200+25));board.paste(im.resize((im.width*6,im.height*6),Image.Resampling.NEAREST),(j*360+45,i*200+25))
 draw.text((5,len(panels)*200+7),'Actual GPU6 frames. Source sample gate is not complete footprint/alpha proof. Private prototype.',fill='white');board.save(G/'ACTUAL_CURVE81.png');film[0].save(G/'ACTUAL_CURVE81.webp',save_all=True,append_images=film[1:],duration=150,loop=0,lossless=True)
 observed=sum(all(r['actualCurvePixels']>0 for r in row['variants'])for row in rows)
 result={'actualGPUFrames':len(frames),'framesWithBothGeometriesObserved':observed,'validPlacementComparison':observed==len(frames)and K!='depth-probe','depthStateIsolationOnly':K=='depth-probe','actualCurrentEvaluatedSource':True,'sameFrameRawAndJoint':True,'allTargetDepthRGBAndActorProtectionChecksPass':True,'sourceSampleEligibilityIndependentCPUProof':K=='fixed6'and not RASTER_SOURCE83,'actualOriginalAlphaDepthRaster':RASTER_SOURCE83,'wholeFootprintAlphaVisibilityProven':False,'generalVariableThicknessProven':False,'artAdopted':False,'restorationChecksPass':report['restorationChecksPass'],'resourcesReleased':report['ownedResourcesReleased'],'rows':rows};(G/'ACTUAL_CURVE81.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
